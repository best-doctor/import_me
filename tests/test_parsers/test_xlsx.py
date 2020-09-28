import pytest

from import_me.columns import Column
from import_me.exceptions import StopParsing
from import_me.parsers.xlsx import BaseXLSXParser


def test_base_xlsx_parser(xlsx_file_factory):
    class XLSXParser(BaseXLSXParser):
        columns = [
            Column('first_name', index=0, header='First Name'),
            Column('last_name', index=1, header='Last Name'),
        ]

    xlsx_file = xlsx_file_factory(
        header=['First Name', 'Last Name'],
        data=[
            ['Ivan', 'Ivanov'],
            ['Petr', 'Petrov'],
        ],
    )
    parser = XLSXParser(file_path=xlsx_file.name)

    parser()

    assert parser.has_errors is False
    assert parser.cleaned_data == [
        {
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
            'row_index': 1,
        },
        {
            'first_name': 'Petr',
            'last_name': 'Petrov',
            'row_index': 2,
        },
    ]


def test_base_xlsx_parser_without_header(xlsx_file_factory):
    class XLSXParser(BaseXLSXParser):
        columns = [
            Column('first_name', index=0),
            Column('last_name', index=1),
        ]
        first_data_row_index = 0

    xlsx_file = xlsx_file_factory(
        data=[
            ['Ivan', 'Ivanov'],
            ['Petr', 'Petrov'],
        ],
        data_row_index=0,
    )
    parser = XLSXParser(file_path=xlsx_file.name)

    parser()

    assert parser.has_errors is False
    assert parser.cleaned_data == [
        {
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
            'row_index': 0,
        },
        {
            'first_name': 'Petr',
            'last_name': 'Petrov',
            'row_index': 1,
        },
    ]


def test_base_xlsx_parser_clean_column():
    class Parser(BaseXLSXParser):
        columns = [
            Column('last_name', index=0),
            Column('first_name', index=1),
        ]

        def clean_column_last_name(self, value):
            return f'Modified {value}'

    parser = Parser()

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
    parser = BaseXLSXParser()
    parser.header_row_index = header_row_index
    parser.first_data_row_index = first_data_row_index

    assert parser.header_row_offset == expected_result


@pytest.mark.parametrize(
    'header_row_idx',
    (0, 1, 2),
)
def test_validate_worksheet_headers(header_row_idx, workbook_factory):
    class Parser(BaseXLSXParser):
        header_row_index = header_row_idx
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
def test_parser_skip_empty_row(parser_skip_empty_rows, file_data, expected_data, xlsx_file_factory):
    class Parser(BaseXLSXParser):
        skip_empty_rows = parser_skip_empty_rows
        # add_file_path = False  # TODO: удалить, если clean_row не должен возвращать путь к файлу
        add_row_index = False
        columns = [
            Column('column1', index=0),
        ]

    xlsx_file = xlsx_file_factory(header=['column1'], data=file_data)
    parser = Parser(file_path=xlsx_file.file)

    parser()

    assert parser.has_errors is False
    assert parser.cleaned_data == expected_data


def test_parser_unique_column(xlsx_file_factory):
    class Parser(BaseXLSXParser):
        columns = [
            Column('id', index=0, unique=True),
        ]

    xlsx_file = xlsx_file_factory(
        header=['id'],
        data=[
            ['1'],
            ['2'],
            ['1'],
        ],
    )
    parser = Parser(file_path=xlsx_file.file)

    parser()

    assert parser.has_errors is True
    assert parser.errors == ['row: 3, column: 0, value 1 is a duplicate of row 1']
    assert parser.cleaned_data == [
        {'id': '1', 'row_index': 1},
        {'id': '2', 'row_index': 2},
    ]


def test_parser_unique_together_column(xlsx_file_factory):
    class Parser(BaseXLSXParser):
        columns = [
            Column('first_name', index=0),
            Column('last_name', index=1),
            Column('middle_name', index=2),
        ]
        unique_together = [
            ['first_name', 'last_name'],
            ['last_name', 'middle_name'],
        ]

    xlsx_file = xlsx_file_factory(
        header=['first_name', 'last_name', 'middle_name'],
        data=[
            ['Ivan', 'Ivanov', 'Ivanovich'],
            ['Ivan', 'Ivanov', 'Petrovich'],
            ['Petr', 'Ivanov', 'Ivanovich'],
            ['Petr', 'Petrov', 'Petrovich'],
        ],
    )
    parser = Parser(file_path=xlsx_file.file)

    parser()

    assert parser.has_errors is True
    assert parser.errors == [
        'row: 2, first_name (Ivan), last_name (Ivanov) is a duplicate of row 1',
        'row: 3, last_name (Ivanov), middle_name (Ivanovich) is a duplicate of row 1',
    ]
    assert parser.cleaned_data == [
        {'first_name': 'Ivan', 'last_name': 'Ivanov', 'middle_name': 'Ivanovich', 'row_index': 1},
        {'first_name': 'Petr', 'last_name': 'Petrov', 'middle_name': 'Petrovich', 'row_index': 4},
    ]
