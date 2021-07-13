from __future__ import annotations

import collections
import pathlib
from typing import TYPE_CHECKING

from import_me.columns import Column
from import_me.exceptions import ColumnError, ParserError, SkipRow, StopParsing

if TYPE_CHECKING:
    from typing import List, Dict, Tuple, Any, Type, Union, IO, Iterator, DefaultDict


class ParserMixin:
    skip_empty_rows: bool = True
    add_file_path: bool = False
    add_row_index: bool = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.cleaned_data: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def __call__(self, raise_errors: bool = False, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError


class BaseParser(ParserMixin):
    columns: List[Column]
    unique_together: List[List[str]]

    def __init__(
        self, file_path: Union[pathlib.Path, str] = None, file_contents: IO = None, *args: Any, **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self.file_contents = file_contents
        self._params = kwargs
        self._unique_column_values: DefaultDict[str, Dict[Any, int]] = collections.defaultdict(dict)
        self._unique_together_values: DefaultDict[
            Tuple[str, ...], Dict[Tuple[Any, ...], int],
        ] = collections.defaultdict(dict)

    @property
    def _unique_together(self) -> Tuple[Tuple[str, ...], ...]:
        if '_unique_together' not in self.__dict__:
            if hasattr(self, 'unique_together'):
                value = tuple((tuple(unique_together_columns) for unique_together_columns in self.unique_together))
            else:
                value = ()
            self.__dict__['_unique_together'] = value
        return self.__dict__['_unique_together']

    def iterate_file_rows(self) -> Iterator[Tuple[int, List[Any]]]:
        raise NotImplementedError

    def parse(self) -> None:
        data = []

        for row_index, row in self.iterate_file_rows():
            try:
                row_data = self.parse_row(row, row_index)
            except SkipRow:
                pass
            else:
                data.append(row_data)

        self.cleaned_data = self.clean(data)

    def parse_row(self, row: List[Any], row_index: int, worksheet_title: str = None) -> Dict:
        row_data = {}
        if worksheet_title:
            row_data['worksheet'] = worksheet_title
        row_has_errors = False

        for column in self.columns:
            try:
                row_data[column.name] = self.parse_column(row, column, row_index)
            except ColumnError as e:
                row_has_errors = True
                self.add_errors(
                    e.messages,
                    row_index=row_index,
                    col_index=column.index,
                    worksheet_title=worksheet_title,
                )

        if row_has_errors:
            raise SkipRow('Not processed because the string contains errors.')

        return self.clean_row(row_data, row, row_index, worksheet_title=worksheet_title)

    def parse_column(self, row: List[Any], column: Column, row_index: int) -> Any:
        try:
            value = row[column.index]
        except IndexError:
            value = None

        try:
            value = column.processor(value)
            value = self.clean_column(column, value)
            value = self.clean_unique_value(column, value, row_index)
        except StopParsing as e:
            raise e
        except Exception as e:
            raise ColumnError(getattr(e, 'messages', str(e))) from e

        return value

    def clean_row(self, row_data: Dict, row: List[Any], row_index: int, worksheet_title: str = None) -> Dict:
        if self.skip_empty_rows and all((row_data.get(column.name) is None for column in self.columns)):
            raise SkipRow

        row_data = self.clean_row_required_columns(row_data, row, row_index, worksheet_title=worksheet_title)
        row_data = self.clean_unique_together_values(row_data, row, row_index, worksheet_title=worksheet_title)

        if self.add_file_path:
            row_data['file_path'] = self.file_path
        if self.add_row_index:
            row_data['row_index'] = row_index

        return row_data

    def clean_row_required_columns(
        self, row_data: Dict, row: List[Any], row_index: int, worksheet_title: str = None,
    ) -> Dict:
        has_empty_required_columns = False

        for column in self.columns:
            if column.required and row_data.get(column.name) is None:
                self.add_errors(
                    f'Column {column.header or column.name} is required.',
                    row_index=row_index, col_index=column.index, worksheet_title=worksheet_title,
                )
                has_empty_required_columns = True

        if has_empty_required_columns:
            raise SkipRow(f'Row {row_index} contains blank columns.')

        return row_data

    def clean_unique_together_values(
        self, row_data: Dict, row: List[Any], row_index: int, worksheet_title: str = None,
    ) -> Dict:
        is_not_unique_row = False

        if not self._unique_together:
            return row_data

        for unique_together_columns in self._unique_together:
            values = tuple((
                row_data[column_name]
                for column_name in unique_together_columns
                if row_data[column_name] is not None
            ))
            if len(values) == len(unique_together_columns):
                duplicate_row = self._unique_together_values[unique_together_columns].get(values, None)
                if duplicate_row:
                    error = ', '.join((
                        f'{column_name} ({column_value})'
                        for column_name, column_value in zip(unique_together_columns, values)
                    ))
                    self.add_errors(
                        f'{error} is a duplicate of row {duplicate_row}',
                        row_index=row_index, worksheet_title=worksheet_title,
                    )
                    is_not_unique_row = True
                else:
                    self._unique_together_values[unique_together_columns][values] = row_index

        if is_not_unique_row:
            raise SkipRow(f'Row {row_index} is not unique.')

        return row_data

    def clean_column(self, column: Column, value: Any) -> Any:
        column_clean_func = getattr(self, f'clean_column_{column.name}', None)
        if column_clean_func:
            value = column_clean_func(value)
        return value

    def clean_unique_value(self, column: Column, value: Any, row_index: int) -> Any:
        if value is not None and column.unique:
            duplicate_row = self._unique_column_values[column.name].get(value, None)
            if duplicate_row is not None:
                raise ColumnError(f'value {value} is a duplicate of row {duplicate_row}')
            else:
                self._unique_column_values[column.name][value] = row_index
        return value

    def clean(self, data: List) -> List:
        return data

    def add_errors(
        self,
        messages: Union[str, List],
        row_index: int = None,
        col_index: int = None,
        worksheet_title: str = None,
    ) -> None:
        if not isinstance(messages, list):
            messages = [messages]
        for message in messages:
            error = []
            if worksheet_title is not None:
                error.append(f'worksheet: {worksheet_title}')
            if row_index is not None:
                error.append(f'row: {row_index}')
            if col_index is not None:
                error.append(f'column: {col_index}')
            error.append(message)
            self.errors.append(', '.join(error))

    def __call__(self, raise_errors: bool = False, *args: Any, **kwargs: Any) -> None:
        try:
            self.parse()
        except Exception as e:
            messages = getattr(e, 'messages', str(e))
            self.add_errors(messages)

        if raise_errors and self.has_errors:
            raise ParserError(self.errors)


class BaseMultipleFileParser(ParserMixin):
    parser_class: Type[BaseParser]
    dir_path: pathlib.Path
    filename_patterns: List[str]

    def __init__(self, dir_path: pathlib.Path = None, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if dir_path:
            self.dir_path = dir_path

    def get_file_paths(self) -> List[pathlib.Path]:
        paths = []
        for filename_pattern in self.filename_patterns:
            for file_path in self.dir_path.glob(filename_pattern):
                paths.append(file_path)
        return sorted(paths)

    def add_errors(self, messages: Union[List, str], file_path: pathlib.Path) -> None:
        if not isinstance(messages, list):
            messages = [messages]
        for message in messages:
            self.errors.append(f'{file_path}, {message}')

    def __call__(self, raise_errors: bool = False, *args: Any, **kwargs: Any) -> None:
        for file_path in self.get_file_paths():
            try:
                parser = self.parser_class(file_path)
                parser(raise_errors=raise_errors)
            except Exception as e:
                messages = getattr(e, 'messages', str(e))
                self.add_errors(messages, file_path)
            else:
                if parser.has_errors:
                    self.add_errors(parser.errors, file_path)
                self.cleaned_data.extend(parser.cleaned_data)

        if raise_errors and self.has_errors:
            raise ParserError(self.errors)
