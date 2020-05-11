import csv
import io
from contextlib import contextmanager

from typing import Optional, Iterator, Tuple, List, Any, Dict

from import_me.exceptions import StopParsing
from import_me.parsers.base import BaseParser


class BaseCSVParser(BaseParser):
    header_row_index: Optional[int] = None
    first_data_row_index: int = 1
    last_data_row_index: Optional[int] = None

    @property
    def header_row_offset(self) -> Optional[int]:
        index = None
        if self.header_row_index is not None:
            index = self.header_row_index
        elif self.first_data_row_index:
            index = self.first_data_row_index - 1
        if index is not None and index < 0:
            raise StopParsing('Invalid row index.')
        return index

    @property
    def _open_file_params(self) -> Dict[str, Any]:
        return {
            key: self._params[key]
            for key in ['encoding', 'buffering', 'newline', 'errors']
            if key in self._params
        }

    @property
    def _reader_params(self) -> Dict[str, Any]:
        reader_params = [i for i in dir(csv.Dialect) if not i.startswith('_')]
        reader_params.append('dialect')
        return {key: self._params[key] for key in reader_params if key in self._params}

    @contextmanager
    def open_file(self) -> Iterator:
        if self.file_path:
            try:
                file_obj = open(self.file_path, 'r', **self._open_file_params)
                try:
                    yield file_obj
                finally:
                    file_obj.close()
            except (TypeError, IOError) as e:
                raise e
        elif self.file_contents:
            data = self.file_contents.read()
            if isinstance(data, bytes):
                yield io.StringIO(data.decode())
            else:
                yield data

    def iterate_file_rows(self) -> Iterator[Tuple[int, List[Any]]]:
        with self.open_file() as csv_file:
            reader = csv.reader(csv_file, **self._reader_params)

            self.validate_headers(reader)
            csv_file.seek(0)

            for row_index, row in enumerate(reader):
                if row_index < self.first_data_row_index:
                    continue
                if self.last_data_row_index is not None and row_index >= self.last_data_row_index:
                    break

                yield row_index, row

    def validate_headers(self, reader: Iterator[List[str]]) -> None:
        expected_headers = {
            column.index: column.header.lower()
            for column in self.columns
            if column.header and column.validate_header
        }
        if expected_headers and self.header_row_offset is not None:
            for row_index, row in enumerate(reader):
                if row_index >= self.header_row_offset:
                    columns = {
                        idx: col.strip().lower()
                        if isinstance(col, str) else col
                        for idx, col in enumerate(row) if idx in expected_headers
                    }

                    if columns != expected_headers:
                        file_path = self.file_path or 'file'
                        raise StopParsing((
                            f'Incorrect column names in the file: {file_path}. '
                            f'Columns in file: {columns}. '
                            f'Expected columns: {expected_headers}.'))
                    break
