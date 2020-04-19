import pytest

from import_me.columns import Column
from import_me.exceptions import StopParsing
from import_me.parsers.xlsx import BaseXLSXParser


def test_base_xlsx_parser_clean_column():
    class Parser(BaseXLSXParser):
        columns = [
            Column('last_name', index=0),
            Column('first_name', index=1),
        ]

        def clean_column_last_name(self, value):
            return f'Modified {value}'

    parser = Parser(file_path=None)

    assert parser.clean_column(parser.columns[0], 'Test Last Name') == 'Modified Test Last Name'
    assert parser.clean_column(parser.columns[1], 'Test First Name') == 'Test First Name'


@pytest.mark.parametrize(
    'header_row_index, first_data_row_index, expected_result',
    (
        (None, None, None),
        (10, None, 10),
        (None, 20, 19),
    ),
)
def test_base_xlsx_parser_header_row_offset(header_row_index, first_data_row_index, expected_result):
    parser = BaseXLSXParser(file_path=None)
    parser.header_row_index = header_row_index
    parser.first_data_row_index = first_data_row_index

    assert parser.header_row_offset == expected_result


@pytest.mark.parametrize(
    'header_row_idx',
    (0, 1, 2),
)
def test_validate_worksheet_headers(header_row_idx, workbook_factory):
    class Parser(BaseXLSXParser):
        header_row_index = header_row_idx + 1
        columns = [
            Column('column1', index=0, header='колонка1'),
            Column('column2', index=1, header='колонка2', validate_header=False),
            Column('column3', index=2),
            Column('column4', index=3, header='колонка4', validate_header=True),
            Column('column5', index=4, header='Колонка5'),
            Column('column6', index=5, header='колонка6'),
        ]

    parser = Parser()
    workbook = workbook_factory(
        header=['колонка1', 'test', 'test', 'колонка4', '   колонка5   ', 'КоЛоНка6'],
        data=[],
        header_row_index=header_row_idx,
    )

    parser.validate_worksheet_headers(worksheet=workbook.active)


@pytest.mark.parametrize(
    'column_header, column_index, wb_headers',
    (
        ('колонка1', 0, ['не колонка1']),
        ('колонка1', 1, ['колонка1']),
        ('колонка1', 0, ['', 'колонка1']),
        ('колонка1', 0, [None]),
    ),
)
def test_validate_worksheet_headers_errors(
    column_header, column_index, wb_headers, workbook_factory,
):
    class Parser(BaseXLSXParser):
        columns = [
            Column('column1', index=column_index, header=column_header),
        ]

    parser = Parser()
    workbook = workbook_factory(header=wb_headers, data=[])

    with pytest.raises(StopParsing):
        parser.validate_worksheet_headers(worksheet=workbook.active)


@pytest.mark.parametrize(
    'parser_skip_empty_rows, file_data, expected_data',
    (
        (True, [[None], ['column1_data']], [{'column1': 'column1_data'}]),
        (False, [[None], ['column1_data']], [{'column1': None}, {'column1': 'column1_data'}]),
    ),
)
def test_parser_skip_empty_row(parser_skip_empty_rows, file_data, expected_data, workbook_factory):
    class Parser(BaseXLSXParser):
        skip_empty_rows = parser_skip_empty_rows
        add_file_path = False
        add_row_index = False
        columns = [
            Column('column1', index=0),
        ]

    workbook = workbook_factory(header=['column1'], data=file_data, save_to_io=True)
    parser = Parser(file_path=workbook.file)

    parser()

    assert parser.has_errors is False
    assert parser.cleaned_data == expected_data
