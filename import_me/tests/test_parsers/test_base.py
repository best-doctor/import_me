import pytest

from import_me.columns import Column
from import_me.exceptions import SkipRow, StopParsing, ColumnError
from import_me.parsers.base import BaseParser
from import_me.tests.conftest import raise_


def test_clean_row_skip_row(base_parser):
    row_data, row, row_index = {'test': 'test'}, ('test',), 1

    with pytest.raises(SkipRow):
        base_parser.clean_row(row_data, row, row_index)


def test_clean_row(base_parser):
    row_data, row, row_index = {'first_name': 'test'}, ('test',), 1

    result = base_parser.clean_row(row_data, row, row_index)

    assert result == {
        'first_name': 'test',
        'file_path': 'test_file_path',
        'row_index': row_index,
    }


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

    parser = Parser()

    with pytest.raises(SkipRow) as exc_info:
        parser.parse_row(row_factory(('Ivan', 'Ivanov', 'fail age')), 1)
    result = parser.parse_row(row_factory(('Ivan', 'Ivanov', 34)), 1)

    assert exc_info.value.messages == ['Не обработана т.к. содержит ошибки']
    assert result == {
        'first_name': 'Ivan',
        'last_name': 'Ivanov',
        'age': 34,
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
            Column('column3', index=2, header='column3 name', required=True),
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
            Column('column3', index=2, header='Custom Name', required=True),
        ]

    parser = Parser()
    row_data = {
        'column1': None,
        'column2': None,
        'column3': None,
    }

    with pytest.raises(SkipRow) as exc_info:
        parser.clean_row_required_columns(row_data=row_data, row=list(row_data.values()), row_index=0)

    assert exc_info.value.messages == ['В строке 0 есть незаполненные колонки.']
    assert parser.errors == [
        'строка: 0, колонка: 1, Колонка column2 обязательна к заполнению.',
        'строка: 0, колонка: 2, Колонка Custom Name обязательна к заполнению.',
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


def test_parser_has_errors():
    class Parser(BaseParser):
        pass

    parser = Parser()

    assert parser.has_errors is False

    parser.add_errors('Ошибка', 0, 0)

    assert parser.has_errors is True


def test_parser_custom_column_clean_method(workbook_factory):
    class Parser(BaseParser):
        add_file_path = False
        add_row_index = False
        columns = [
            Column('column1', index=0),
        ]

        def clean_column_column1(self, value):
            return 'any value'

    parser = Parser(file_path='file')

    result = parser.parse_row(row=['column1_data'], row_index=1)

    assert result == {'column1': 'any value'}
