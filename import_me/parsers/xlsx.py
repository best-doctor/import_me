import datetime
from typing import Optional, Iterator, Tuple, Any, List

import xlrd
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet.worksheet import Worksheet

from import_me.parsers.base import BaseParser, ParserMixin
from import_me.exceptions import StopParsing


class BaseXLSXParser(BaseParser):
    ws_index: int = 0
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
        return index

    def iterate_file_rows(self) -> Iterator[Tuple[int, List[Any]]]:
        wb = self.load_workbook()
        self.validate_workbook(wb)

        ws = wb[wb.sheetnames[self.ws_index]]
        self.validate_worksheet(ws)

        row_index = self.first_data_row_index
        min_row = self.first_data_row_index + 1 if self.first_data_row_index is not None else None
        max_row = self.last_data_row_index + 1 if self.last_data_row_index is not None else None
        for row in ws.iter_rows(min_row=min_row, max_row=max_row):
            yield row_index, [cell.value for cell in row]
            row_index += 1

    def load_workbook(self) -> Workbook:
        """Загрузка openpyxl Workbook из файла.

        Пробуем загрузить сначала через openpyxl,
        если он не умеет работать с данным типом файлов,
        то читаем файл с помощью xlrd.

        """
        try:
            wb = self._load_workbook_from_xlsx()
        except InvalidFileException:
            wb = self._load_workbook_from_xls()
        return wb

    def validate_workbook(self, workbook: Workbook) -> None:
        pass

    def validate_worksheet(self, worksheet: Worksheet) -> None:
        self.validate_worksheet_headers(worksheet)

    def validate_worksheet_headers(self, worksheet: Worksheet) -> None:
        expected_headers = {
            column.index: column.header.lower()
            for column in self.columns
            if column.header and column.validate_header
        }
        if expected_headers and self.header_row_offset is not None:
            for row in worksheet.iter_rows(min_row=self.header_row_offset + 1):
                columns = {
                    idx: col.value.strip().lower()
                    if isinstance(col.value, str) else col.value
                    for idx, col in enumerate(row) if idx in expected_headers
                }

                if columns != expected_headers:
                    file_path = self.file_path or 'file'
                    raise StopParsing((
                        f'Incorrect column names in the file: {file_path}. '
                        f'Columns in file: {columns}. '
                        f'Expected columns: {expected_headers}.'))
                break

    def _load_workbook_from_xlsx(self) -> Workbook:
        return load_workbook(filename=self.file_path or self.file_contents, read_only=True, data_only=True)

    def _load_workbook_from_xls(self) -> Workbook:
        xls_workbook = xlrd.open_workbook(filename=self.file_path, file_contents=self.file_contents)
        xls_sheet = xls_workbook.sheet_by_index(0)
        nrows = xls_sheet.nrows
        ncols = xls_sheet.ncols

        wb = Workbook()
        ws = wb[wb.sheetnames[0]]

        for row in range(nrows):
            for col in range(ncols):
                cell = xls_sheet.cell(row, col)
                value = cell.value
                if value and cell.ctype == 3:
                    value = datetime.datetime(*xlrd.xldate_as_tuple(value, xls_workbook.datemode))
                ws.cell(row=row + 1, column=col + 1).value = value

        return wb


class BaseMultipleXLSXFileParser(ParserMixin):
    filename_patterns: List[str] = ['*.xls', '*.xlsx']
