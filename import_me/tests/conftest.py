import tempfile
from typing import List, ValuesView, Optional, Union, IO, Any

import pytest
from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet

from import_me.base import BaseParser, Column


def virtual_workbook(
    data: List[ValuesView],
    header: Optional[List[str]] = None,
    n_preallocated_columns: int = 20,
    save_to_io: bool = True,
    suffix: str = '.xlsx',
) -> Union[IO[Any], Workbook]:
    if not header:
        header = []
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    for row in data:
        workbook_row = list(row)
        n_columns_to_allocate = n_preallocated_columns - len(workbook_row)
        ws.append(workbook_row + [None for _ in range(n_columns_to_allocate)])

    if save_to_io:
        virtual_workbook = tempfile.NamedTemporaryFile(suffix='.xlsx')
        wb.save(virtual_workbook.name)
        return virtual_workbook
    else:
        return wb


@pytest.fixture
def my_parser():
    class Parser(BaseParser):
        add_file_path = True
        add_row_index = True
        skip_empty_rows = True
        columns = [Column('first_name', index=1)]

    return Parser(file_path='test_file_path')


@pytest.fixture
def cell_factory():
    def cell(value):
        return Cell(Worksheet(Workbook()), value=value)

    return cell


@pytest.fixture
def row_factory(cell_factory):
    def row(values):
        return [cell_factory(value) for value in values]

    return row


@pytest.fixture
def workbook_factory():
    def workbook(header, data, header_row_index=0, save_to_io=False):
        wb_header = []
        wb_data = []

        if header_row_index > 0:
            wb_data = [[]] * (header_row_index - 1)
            wb_data.append(header)
        else:
            wb_header = header

        wb_data += data
        return virtual_workbook(wb_data, wb_header, suffix='.xls', save_to_io=save_to_io)
    return workbook


def raise_(ex, *args, **kwargs):
    raise ex(*args, **kwargs)
