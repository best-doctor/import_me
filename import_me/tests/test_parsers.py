import pytest

from import_me.base import BaseParser, Column
from import_me.exceptions import SkipRow, StopParsing, ColumnError
from import_me.tests.conftest import raise_


@pytest.mark.parametrize(
    'header_row_index, first_data_row_index, expected_result',
    (
        (None, None, None),
        (10, None, 10),
        (None, 20, 19),
    ),
)
def test_base_parser_header_row_offset(header_row_index, first_data_row_index, expected_result):
    parser = BaseParser(file_path=None)
    parser.header_row_index = header_row_index
    parser.first_data_row_index = first_data_row_index

    assert parser.header_row_offset == expected_result


def test_base_parser_clean_column():
    class Parser(BaseParser):
        columns = [
            Column('last_name', index=0),
            Column('first_name', index=1),
        ]

        def clean_column_last_name(self, value):
            return f'Modified {value}'

    parser = Parser(file_path=None)

    assert parser.clean_column(parser.columns[0], 'Test Last Name') == 'Modified Test Last Name'
    assert parser.clean_column(parser.columns[1], 'Test First Name') == 'Test First Name'


def test_clean_row_skip_row(my_parser):
    row_data, row, row_index = {'test': 'test'}, ('test',), 1

    with pytest.raises(SkipRow):
        my_parser.clean_row(row_data, row, row_index)


def test_clean_row(my_parser):
    row_data, row, row_index = {'test': 'test'}, ('test',), 1
    my_parser.skip_empty_rows = False

    result = my_parser.clean_row(row_data, row, row_index)

    assert result.get('file_path') == 'test_file_path'
    assert result.get('row_index') == row_index


@pytest.mark.parametrize(
    'column, row_values, expected_value',
    (
        (Column('column_name', index=0), [0], 0),
        (Column('column_name', index=10), [], None),
        (Column('column_name', index=0, processor=lambda x: str(x)), [0], '0'),
        (Column('column_name', index=0, processor=lambda x: int(x)), ['1'], 1),
    ),
)
def test_parse_column(column, row_values, expected_value, row_factory):
    class Parser(BaseParser):
        columns = [column]

    parser = Parser(None)
    row = row_factory(row_values)

    assert parser.parse_column(row, column, row_index=0) == expected_value


def test_parse_row(row_factory):
    class Parser(BaseParser):
        columns = [
            Column('first_name', index=0),
            Column('last_name', index=1),
            Column('age', index=2, processor=lambda x: x if isinstance(x, int) else raise_(ColumnError())),
        ]

    parser = Parser(None)

    with pytest.raises(SkipRow) as exc_info:
        parser.parse_row(row_factory(('Василий', 'Теркин', 'не возраст')), 1)
    result = parser.parse_row(row_factory(('Василий', 'Теркин', 34)), 1)

    assert exc_info.value.messages == ['Не обработана т.к. содержит ошибки']
    assert result == {
        'first_name': 'Василий',
        'last_name': 'Теркин',
        'age': 34,
        'file_path': None,
        'row_index': 1,
    }


@pytest.mark.parametrize(
    'column_processor, expected_exception',
    (
        (lambda x: raise_(StopParsing, 'invalid_column_value'), StopParsing),
        (lambda x: raise_(ColumnError, 'invalid_column_value'), ColumnError),
        (lambda x: raise_(ValueError), ColumnError),
        (lambda x: raise_(TypeError), ColumnError),
        (lambda x: raise_(Exception), ColumnError),
    ),
)
def test_parse_column_exceptions(column_processor, expected_exception, row_factory):
    class Parser(BaseParser):
        columns = [Column('column_name', index=0, processor=column_processor)]

    parser = Parser(None)
    row = row_factory([0])

    with pytest.raises(expected_exception):
        parser.parse_column(row, parser.columns[0], row_index=0)


def test_clean_row_required_columns():
    class Parser(BaseParser):
        columns = [
            Column('column1', index=0, required=False),
            Column('column2', index=1, required=True),
            Column('column3', index=2, header='Колонка1', required=True),
        ]

    parser = Parser()
    row_data = {
        'column1': 'test_data',
        'column2': 'test_data',
        'column3': 'test_data',
    }

    result = parser.clean_row_required_columns(row_data=row_data, row=tuple(row_data.values()), row_index=1)

    assert result == row_data
    assert len(parser.errors) == 0


def test_clean_row_required_columns_exception():
    class Parser(BaseParser):
        columns = [
            Column('column1', index=0, required=False),
            Column('column2', index=1, required=True),
            Column('column3', index=2, header='Колонка1', required=True),
        ]

    parser = Parser()
    row_data = {
        'column1': None,
        'column2': None,
        'column3': None,
    }

    with pytest.raises(SkipRow) as exc_info:
        parser.clean_row_required_columns(row_data=row_data, row=tuple(row_data.values()), row_index=1)

    assert exc_info.value.messages == ['В строке 1 есть незаполненные колонки.']
    assert parser.errors == [
        'строка: 1, колонка: 1, Колонка column2 обязательна к заполнению.',
        'строка: 1, колонка: 2, Колонка Колонка1 обязательна к заполнению.',
    ]


@pytest.mark.parametrize(
    'messages, row_index, col_index, expected_parser_errors',
    (
        ('Текст ошибки', None, None, ['Текст ошибки']),
        ('Текст ошибки', 1, None, ['строка: 1, Текст ошибки']),
        ('Текст ошибки', None, 1, ['колонка: 1, Текст ошибки']),
        ('Текст ошибки', 2, 1, ['строка: 2, колонка: 1, Текст ошибки']),
        (['Текст ошибки1', 'Текст ошибки2'], None, None, ['Текст ошибки1', 'Текст ошибки2']),
        (['Текст ошибки1', 'Текст ошибки2'], 1, None, ['строка: 1, Текст ошибки1', 'строка: 1, Текст ошибки2']),
        (['Текст ошибки1', 'Текст ошибки2'], None, 1, ['колонка: 1, Текст ошибки1', 'колонка: 1, Текст ошибки2']),
        (
            ['Текст ошибки1', 'Текст ошибки2'],
            2,
            1,
            ['строка: 2, колонка: 1, Текст ошибки1', 'строка: 2, колонка: 1, Текст ошибки2'],
        ),
    ),
)
def test_add_errors(messages, row_index, col_index, expected_parser_errors):
    class Parser(BaseParser):
        pass

    parser = Parser()

    parser.add_errors(messages=messages, row_index=row_index, col_index=col_index)

    assert parser.errors == expected_parser_errors


@pytest.mark.parametrize(
    'header_row_idx',
    (0, 1, 2),
)
def test_validate_worksheet_headers(header_row_idx, workbook_factory):
    class Parser(BaseParser):
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
    class Parser(BaseParser):
        columns = [
            Column('column1', index=column_index, header=column_header),
        ]

    parser = Parser()
    workbook = workbook_factory(header=wb_headers, data=[])

    with pytest.raises(StopParsing):
        parser.validate_worksheet_headers(worksheet=workbook.active)


def test_parser_has_errors():
    class Parser(BaseParser):
        pass

    parser = Parser()

    assert parser.has_errors is False

    parser.add_errors('Ошибка', 0, 0)

    assert parser.has_errors is True


@pytest.mark.parametrize(
    'parser_skip_empty_rows, file_data, expected_data',
    (
        (True, [[None], ['column1_data']], [{'column1': 'column1_data'}]),
        (False, [[None], ['column1_data']], [{'column1': None}, {'column1': 'column1_data'}]),
    ),
)
def test_parser_skip_empty_row(parser_skip_empty_rows, file_data, expected_data, workbook_factory):
    class Parser(BaseParser):
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


def test_parser_custom_column_clean_method(workbook_factory):
    class Parser(BaseParser):
        add_file_path = False
        add_row_index = False
        columns = [
            Column('column1', index=0),
        ]

        def clean_column_column1(self, value):
            return 'any value'

    workbook = workbook_factory(header=['column1'], data=['column1_data'], save_to_io=True)
    parser = Parser(file_path=workbook.file)

    parser()

    assert parser.has_errors is False
    assert parser.cleaned_data == [{'column1': 'any value'}]
