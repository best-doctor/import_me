import dataclasses

import pydantic

from import_me.columns import Column
from import_me.dto import (
    DataclassImportableDtoMixin,
    ParsingResult,
    META_UNIQUE,
    META_HEADER,
    PydanticImportableDtoMixin,
)
from import_me.parsers.xlsx import BaseXLSXParser

DEFAULT_WORKBOOK_DATA = {
    'header': ['First Name', 'Last Name'],
    'data': [['Ivan', 'Ivanov'], ['Petr', 'Petrov']],
}

DEFAULT_PARSER_COLUMNS = [
    Column('first_name', index=0, header='First Name'),
    Column('last_name', index=1, header='Last Name'),
]


def test_dataclass_dto_xlsx_parser(xlsx_file_factory):

    @dataclasses.dataclass
    class PersonDto(DataclassImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = dataclasses.field(metadata={META_HEADER: 'First Name'})
        last_name: str = dataclasses.field(metadata={META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(**DEFAULT_WORKBOOK_DATA)
    persons = PersonDto.parse_from_file(file_path=xlsx_file.name)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
        PersonDto(
            first_name='Petr',
            last_name='Petrov',
            row_index=2,
        ),
    ]


def test_dataclass_dto_xlsx_parser_accepts_file_object(xlsx_file_factory):
    @dataclasses.dataclass
    class PersonDto(DataclassImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = dataclasses.field(metadata={META_HEADER: 'First Name'})
        last_name: str = dataclasses.field(metadata={META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(**DEFAULT_WORKBOOK_DATA)
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
        PersonDto(
            first_name='Petr',
            last_name='Petrov',
            row_index=2,
        ),
    ]


def test_dataclass_dto_xlsx_parser_without_header(xlsx_file_factory):

    @dataclasses.dataclass
    class PersonDto(DataclassImportableDtoMixin):
        class ParserMeta:
            first_data_row_index = 0

        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = dataclasses.field(metadata={META_HEADER: 'First Name'})
        last_name: str = dataclasses.field(metadata={META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(
        data=[
            ['Ivan', 'Ivanov'],
            ['Petr', 'Petrov'],
        ],
        data_row_index=0,
    )
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=0,
        ),
        PersonDto(
            first_name='Petr',
            last_name='Petrov',
            row_index=1,
        ),
    ]


def test_dataclass_dto_xlsx_parser_clean_column(xlsx_file_factory):
    @dataclasses.dataclass
    class PersonDto(DataclassImportableDtoMixin):
        class ParserMeta:
            def clean_column_last_name(self, value):
                return f'Modified {value}'

        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = dataclasses.field(metadata={META_HEADER: 'First Name'})
        last_name: str = dataclasses.field(metadata={META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(**DEFAULT_WORKBOOK_DATA)
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert persons.parsed_items[0].last_name == 'Modified Ivanov'
    assert persons.parsed_items[0].first_name == 'Ivan'
    assert persons.parsed_items[1].last_name == 'Modified Petrov'
    assert persons.parsed_items[1].first_name == 'Petr'


def test_dataclass_dto_xlsx_parser_unique_column(xlsx_file_factory):
    @dataclasses.dataclass
    class IdDto(DataclassImportableDtoMixin):
        row_index: int
        id_: int = dataclasses.field(metadata={META_UNIQUE: True})

    xlsx_file = xlsx_file_factory(
        header=['id'],
        data=[
            ['1'],
            ['2'],
            ['1'],
        ],
    )
    parsing_result = IdDto.parse_from_file(file_path=xlsx_file.file)

    assert parsing_result.errors
    assert parsing_result.errors == {3: ['row: 3, column: 0, value 1 is a duplicate of row 1']}
    assert parsing_result.parsed_items == [
        IdDto(**{'id_': 1, 'row_index': 1}),
        IdDto(**{'id_': 2, 'row_index': 2}),
    ]


def test_dataclass_dto_xlsx_parser_default_value(xlsx_file_factory):
    @dataclasses.dataclass
    class PersonDto(DataclassImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = dataclasses.field(metadata={META_HEADER: 'First Name'})
        last_name: str = dataclasses.field(default='', metadata={META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(
        data=[
            ['First Name', 'Last Name'],
            ['Ivan', 'Ivanov'],
            ['Petr', None],
        ],
    )
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
        PersonDto(
            first_name='Petr',
            last_name='',
            row_index=2,
        ),
    ]
    assert persons.errors == {}


def test_dataclass_dto_xlsx_parser_no_default_value(xlsx_file_factory):
    @dataclasses.dataclass
    class PersonDto(DataclassImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = dataclasses.field(metadata={META_HEADER: 'First Name'})
        last_name: str = dataclasses.field(metadata={META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(
        data=[
            ['First Name', 'Last Name'],
            ['Ivan', 'Ivanov'],
            ['Petr', None],
        ],
    )
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
    ]
    assert persons.errors == {2: ['row: 2, column: 1, Column Last Name is required.']}


def test_pydantic_dto_xlsx_parser(xlsx_file_factory):
    class PersonDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = pydantic.Field(**{META_HEADER: 'First Name'})
        last_name: str = pydantic.Field(**{META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(**DEFAULT_WORKBOOK_DATA)
    persons = PersonDto.parse_from_file(file_path=xlsx_file.name)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
        PersonDto(
            first_name='Petr',
            last_name='Petrov',
            row_index=2,
        ),
    ]


def test_pydantic_dto_xlsx_parser_accepts_file_object(xlsx_file_factory):
    class PersonDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = pydantic.Field(**{META_HEADER: 'First Name'})
        last_name: str = pydantic.Field(**{META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(**DEFAULT_WORKBOOK_DATA)
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
        PersonDto(
            first_name='Petr',
            last_name='Petrov',
            row_index=2,
        ),
    ]


def test_pydantic_dto_xlsx_parser_without_header(xlsx_file_factory):
    class PersonDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        class ParserMeta:
            first_data_row_index = 0

        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = pydantic.Field(**{META_HEADER: 'First Name'})
        last_name: str = pydantic.Field(**{META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(
        data=[
            ['Ivan', 'Ivanov'],
            ['Petr', 'Petrov'],
        ],
        data_row_index=0,
    )
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=0,
        ),
        PersonDto(
            first_name='Petr',
            last_name='Petrov',
            row_index=1,
        ),
    ]


def test_pydantic_dto_xlsx_parser_clean_column(xlsx_file_factory):
    class PersonDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        class ParserMeta:
            def clean_column_last_name(self, value):
                return f'Modified {value}'

        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = pydantic.Field(**{META_HEADER: 'First Name'})
        last_name: str = pydantic.Field(**{META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(**DEFAULT_WORKBOOK_DATA)
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert persons.parsed_items[0].last_name == 'Modified Ivanov'
    assert persons.parsed_items[0].first_name == 'Ivan'
    assert persons.parsed_items[1].last_name == 'Modified Petrov'
    assert persons.parsed_items[1].first_name == 'Petr'


def test_pydantic_dto_xlsx_parser_unique_column(xlsx_file_factory):
    class IdDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        row_index: int
        id_: int = pydantic.Field(**{META_UNIQUE: True})

    xlsx_file = xlsx_file_factory(
        header=['id'],
        data=[
            ['1'],
            ['2'],
            ['1'],
        ],
    )
    parsing_result = IdDto.parse_from_file(file_path=xlsx_file.file)

    assert parsing_result.errors
    assert parsing_result.errors == {3: ['row: 3, column: 0, value 1 is a duplicate of row 1']}
    assert parsing_result.parsed_items == [
        IdDto(**{'id_': 1, 'row_index': 1}),
        IdDto(**{'id_': 2, 'row_index': 2}),
    ]


def test_pydantic_dto_xlsx_parser_default_value(xlsx_file_factory):
    class PersonDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = pydantic.Field(**{META_HEADER: 'First Name'})
        last_name: str = pydantic.Field(default='', **{META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(
        data=[
            ['First Name', 'Last Name'],
            ['Ivan', 'Ivanov'],
            ['Petr', None],
        ],
    )
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
        PersonDto(
            first_name='Petr',
            last_name='',
            row_index=2,
        ),
    ]
    assert persons.errors == {}


def test_pydantic_dto_xlsx_parser_no_default_value(xlsx_file_factory):
    class PersonDto(pydantic.BaseModel, PydanticImportableDtoMixin):
        parser_base = BaseXLSXParser
        row_index: int
        first_name: str = pydantic.Field(**{META_HEADER: 'First Name'})
        last_name: str = pydantic.Field(**{META_HEADER: 'Last Name'})

    xlsx_file = xlsx_file_factory(
        data=[
            ['First Name', 'Last Name'],
            ['Ivan', 'Ivanov'],
            ['Petr', None],
        ],
    )
    persons = PersonDto.parse_from_file(file_contents=xlsx_file)

    assert isinstance(persons, ParsingResult)
    assert persons.parsed_items == [
        PersonDto(
            first_name='Ivan',
            last_name='Ivanov',
            row_index=1,
        ),
    ]
    assert persons.errors == {2: ['row: 2, column: 1, Column Last Name is required.']}
