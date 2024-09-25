import abc
import dataclasses
import datetime
import decimal
import pathlib
import types
import typing

import typing_extensions

import import_me
from import_me import Column
from import_me.parsers.base import BaseParser
from import_me.processors import (
    BaseProcessor,
    IntegerProcessor,
    StringProcessor,
    FloatProcessor,
    DecimalProcessor,
    BooleanProcessor,
    DateProcessor,
    DateTimeProcessor,
)

META_INDEX = 'im_index'
META_HEADER = 'im_header'
META_VALIDATE_HEADER = 'im_validate_header'
META_UNIQUE = 'im_unique'
META_PROCESSOR = 'im_processor'

PROCESSORS_BY_TYPE: typing.Dict[type, BaseProcessor] = {
    int: IntegerProcessor(),
    str: StringProcessor(),
    float: FloatProcessor(),
    decimal.Decimal: DecimalProcessor(),
    bool: BooleanProcessor(),
    datetime.date: DateProcessor(),
    datetime.datetime: DateTimeProcessor(),
}


def infer_processor_by_type(field_type: typing.Any) -> typing.Optional[BaseProcessor]:
    return PROCESSORS_BY_TYPE.get(field_type, None)


class _NOT_SPECIFIED:
    pass


@dataclasses.dataclass
class DtoField:
    name: str
    index: int
    header: typing.Optional[str]
    validate_header: bool
    required: bool
    unique: bool
    processor: BaseProcessor
    default: typing.Any = _NOT_SPECIFIED


class DtoFieldsGetter(typing_extensions.Protocol):
    def __call__(self, dto: typing.Any) -> typing.List[DtoField]:
        ...


class PydanticLikeFieldInfo(typing_extensions.Protocol):
    extra: typing.Dict[str, typing.Any]


class PydanticLikeField(typing_extensions.Protocol):
    name: str
    type_: type
    required: bool
    field_info: PydanticLikeFieldInfo
    default: typing.Any


@typing_extensions.runtime_checkable
class PydanticLikeDto(typing_extensions.Protocol):
    __fields__: dict[str, PydanticLikeField]


class DataclassLikeField(typing_extensions.Protocol):
    name: str
    type: type  # noqa: VNE003, A003 because it is python dataclass protocol, can't be changed
    metadata: types.MappingProxyType
    default: typing.Any


@typing_extensions.runtime_checkable
class DataclassLikeDto(typing_extensions.Protocol):
    __dataclass_fields__: dict[str, DataclassLikeField]


def get_pydantic_fields(dto: PydanticLikeDto) -> list[DtoField]:
    fields = []
    index = -1
    for field_name, pydantic_field in dto.__fields__.items():
        if field_name == 'row_index':
            continue
        index = pydantic_field.field_info.extra.get(META_INDEX, index + 1)
        fields.append(
            DtoField(
                name=field_name,
                index=index,
                header=pydantic_field.field_info.extra.get(META_HEADER),
                validate_header=pydantic_field.field_info.extra.get(META_VALIDATE_HEADER, True),
                unique=pydantic_field.field_info.extra.get(META_UNIQUE, False),
                required=pydantic_field.required,
                processor=pydantic_field.field_info.extra.get(
                    META_PROCESSOR, infer_processor_by_type(pydantic_field.type_),
                ),
                default=pydantic_field.default or _NOT_SPECIFIED,
            ),
        )
    return fields


def get_dataclass_fields(dto: DataclassLikeDto) -> list[DtoField]:
    fields = []
    index = -1
    for field_name, dataclass_field in dto.__dataclass_fields__.items():
        if field_name == 'row_index':
            continue
        index = dataclass_field.metadata.get(META_INDEX, index + 1)
        fields.append(
            DtoField(
                name=field_name,
                index=index,
                header=dataclass_field.metadata.get(META_HEADER, None),
                validate_header=dataclass_field.metadata.get(META_VALIDATE_HEADER, True),
                unique=dataclass_field.metadata.get(META_UNIQUE, False),
                required=dataclass_field.default is dataclasses.MISSING,
                processor=dataclass_field.metadata.get(
                    META_PROCESSOR, infer_processor_by_type(dataclass_field.type),
                ),
                default=(
                    dataclass_field.default
                    if dataclass_field.default is not dataclasses.MISSING
                    else _NOT_SPECIFIED
                ),
            ),
        )
    return fields


class ImportableDtoProtocol(typing_extensions.Protocol):

    def __init__(self, **kwargs: typing.Dict[str, typing.Any]) -> None:
        ...


T = typing.TypeVar('T', bound=typing.Union[
    typing.Type['BaseImportableDtoMixin'], typing.Type[ImportableDtoProtocol],
])


@dataclasses.dataclass
class ParsingResult(typing.Generic[T]):
    parsed_items: list[T]
    errors: dict[typing.Optional[int], typing.List[str]]


class BaseImportableDtoMixin(abc.ABC):
    """
    Base class for DTO parser mixin.

    `parser_base` is used to specify import_me parser to use.
    Parser attributes such (e.g. `ws_index`) could be set in `ParserMeta`.
    `fields_getter` must be a callable that gets DTO itself and returns a list of `DtoField`.
    """

    class ParserMeta:
        pass

    parser_base: typing.Type[BaseParser] = import_me.BaseXLSXParser
    fields_getter: DtoFieldsGetter

    @classmethod
    def parse_from_file(
        cls: typing.Type[T],
        file_path: typing.Union[pathlib.Path, str, None] = None,
        file_contents: typing.Optional[typing.IO] = None,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> ParsingResult[T]:
        fields = cls.fields_getter(cls)
        parser = cls._construct_parser(
            fields=fields, file_path=file_path, file_contents=file_contents, *args, **kwargs,
        )
        parser.parse_data(raise_errors=False)
        parsed_items = cls._serialize_cleaned_data(parser=parser, fields=fields)
        return ParsingResult(parsed_items, parser.errors_by_row)

    @classmethod
    def _get_columns(cls, fields: list[DtoField]) -> typing.List[Column]:
        columns = []
        for field in fields:
            columns.append(
                Column(
                    name=field.name,
                    index=field.index,
                    processor=field.processor,
                    header=field.header,
                    validate_header=field.validate_header,
                    required=field.required,
                    unique=field.unique,
                ),
            )
        return columns

    @classmethod
    def _construct_parser(
        cls,
        fields: typing.List[DtoField],
        file_path: typing.Union[pathlib.Path, str, None] = None,
        file_contents: typing.Optional[typing.IO] = None,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> BaseParser:
        class DtoParser(cls.parser_base):
            columns = cls._get_columns(fields)

        for key, value in cls.ParserMeta.__dict__.items():
            if not key.startswith('__'):
                setattr(DtoParser, key, value)
        return DtoParser(file_path, file_contents, *args, **kwargs)

    @classmethod
    def _serialize_cleaned_data(
        cls: T, parser: BaseParser, fields: typing.List[DtoField],
    ) -> typing.List[T]:
        defaults = {field.name: field.default for field in fields}
        parsed_items: typing.List[T] = []
        for row in parser.cleaned_data:
            dto_kwargs = {}
            for key, value in row.items():
                if value is not None:
                    dto_kwargs[key] = value
                else:
                    default_value = defaults.get(key)
                    if default_value is not _NOT_SPECIFIED:
                        dto_kwargs[key] = default_value
            try:
                parsed_items.append(cls(**dto_kwargs))
            except Exception as e:
                parser.add_errors(
                    str(e),
                    row_index=row.get('row_index'),
                    worksheet_title=row.get('worksheet'),
                )
        return parsed_items


class PydanticImportableDtoMixin(BaseImportableDtoMixin):
    fields_getter = get_pydantic_fields


class DataclassImportableDtoMixin(BaseImportableDtoMixin):
    fields_getter = get_dataclass_fields
