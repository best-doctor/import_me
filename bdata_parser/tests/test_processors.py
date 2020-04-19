import datetime

import pytest

from bdata_parser.exceptions import StopParsing, ColumnError
from bdata_parser.processors import (
    strip, lower, BaseProcessor, MultipleProcessor, DateTimeProcessor, DateProcessor,
    StringProcessor, StringIsNoneProcessor, BooleanProcessor, IntegerProcessor,
)
from bdata_parser.tests.conftest import raise_


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (' test string  ', 'test string'),
        (1, 1),
        (None, None),
    ),
)
def test_strip(value, expected_value):
    assert strip(value) == expected_value


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (' Test strIng  ', ' test string  '),
        (1, 1),
        (None, None),
    ),
)
def test_lower(value, expected_value):
    assert lower(value) == expected_value


@pytest.mark.parametrize(
    'exception_class, expected_exception_class',
    (
        (StopParsing, StopParsing),
        (ColumnError, ColumnError),
        (ValueError, ColumnError),
        (TypeError, ColumnError),
    ),
)
def test_base_processor_error(exception_class, expected_exception_class):
    class TestProcessor(BaseProcessor):
        def process_value(self, value):
            raise exception_class('invalid value')

    processor = TestProcessor()

    with pytest.raises(expected_exception_class):
        processor('test_value')


def test_base_processor_without_error():
    class WithoutErrorProcessor(BaseProcessor):
        raise_error = False

        def process_value(self, value):
            raise ValueError

    processor = WithoutErrorProcessor()

    assert processor('test_value') == 'test_value'


def test_base_processor_none_if_error():
    class NoneIfErrorProcessor(BaseProcessor):
        raise_error = False
        none_if_error = True

        def process_value(self, value):
            raise ValueError

    processor = NoneIfErrorProcessor()

    assert processor('test_value') is None


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (' Test strIng  ', 'test string'),
        (None, None),
    ),
)
def test_multiple_processor(value, expected_value):
    processor = MultipleProcessor(strip, lower)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'exception_class, expected_exception_class',
    (
        (StopParsing, StopParsing),
        (ColumnError, ColumnError),
        (ValueError, ColumnError),
        (TypeError, ColumnError),
    ),
)
def test_multiple_processor_error(exception_class, expected_exception_class):
    processor = MultipleProcessor(lambda x: raise_(exception_class, 'invalid_value'), lambda x: x.lower())

    with pytest.raises(expected_exception_class):
        processor('value')


def test_multiple_processor_without_error():
    processor = MultipleProcessor(lambda x: x.strip(), lambda x: x.lower())
    processor.raise_error = False

    assert processor(100) == 100


def test_multiple_processor_none_if_error():
    processor = MultipleProcessor(lambda x: x.strip(), lambda x: x.lower())
    processor.raise_error = False
    processor.none_if_error = True

    assert processor(100) is None


@pytest.mark.parametrize(
    'formats, value, expected_value',
    (
        (['%d.%m.%Y'], '20.07.2019', datetime.datetime(2019, 7, 20)),
        (['%d.%m.%Y'], '  20.07.2019  ', datetime.datetime(2019, 7, 20)),
        (['%Y-%m-%d', '%d.%m.%Y'], '20.07.2019', datetime.datetime(2019, 7, 20)),
        (['%d.%m.%Y'], None, None),
        (['%d.%m.%Y %H:%M:%S'], '20.07.2019 12:43:52', datetime.datetime(2019, 7, 20, 12, 43, 52)),
    ),
)
def test_datetime_processor(formats, value, expected_value):
    processor = DateTimeProcessor(formats=formats)

    assert processor(value) == expected_value


def test_datetime_processor_error_value():
    processor = DateTimeProcessor(formats=['%d.%m.%Y'])

    with pytest.raises(ColumnError):
        assert processor('2019-01-01')


@pytest.mark.parametrize(
    'formats, value, expected_value',
    (
        (['%d.%m.%Y'], '20.07.2019', datetime.date(2019, 7, 20)),
        (['%d.%m.%Y'], '  20.07.2019  ', datetime.date(2019, 7, 20)),
        (['%Y-%m-%d', '%d.%m.%Y'], '20.07.2019', datetime.date(2019, 7, 20)),
        (['%d.%m.%Y'], None, None),
        (['%d.%m.%Y %H:%M:%S'], '20.07.2019 12:43:52', datetime.date(2019, 7, 20)),
    ),
)
def test_date_processor(formats, value, expected_value):
    processor = DateProcessor(formats=formats)

    assert processor(value) == expected_value


def test_date_processor_error_value():
    processor = DateProcessor(formats=['%d.%m.%Y'])

    with pytest.raises(ColumnError):
        assert processor('2019-01-01')


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (' Test string  ', 'Test string'),
        (123, '123'),
        (123.1, '123.1'),
        (datetime.datetime(2019, 1, 1, 1, 1, 1), '2019-01-01 01:01:01'),
        (datetime.date(2019, 1, 1), '2019-01-01'),
        (None, None),
        ('       ', None),
    ),
)
def test_string_processor(value, expected_value):
    processor = StringProcessor()

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'none_symbols, value, expected_value',
    (
        (None, ' Test string  ', ' Test string  '),
        (['_'], '_', None),
        (['_'], '_A', '_A'),
        (['_'], '  _    A ', '  _    A '),
        (['_', ',', '.'], ' _  .  , ', None),
        (['_'], 123, 123),
        (['_'], 123.1, 123.1),
        (['_'], datetime.datetime(2019, 1, 1, 1, 1, 1), datetime.datetime(2019, 1, 1, 1, 1, 1)),
        (['_'], datetime.date(2019, 1, 1), datetime.date(2019, 1, 1)),
        (['_'], None, None),
    ),
)
def test_string_is_none_processor(none_symbols, value, expected_value):
    processor = StringIsNoneProcessor(none_symbols=none_symbols)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (None, None),
        (True, True),
        ('True', True),
        ('true', True),
        (1, True),
        ('Да', True),
        (False, False),
        ('False', False),
        ('false', False),
        (0, False),
        ('Нет', False),
    ),
)
def test_boolean_processor(value, expected_value):
    processor = BooleanProcessor()

    assert processor(value) is expected_value


@pytest.mark.parametrize(
    'value, expected_value',
    (
        ('Истина', True),
        ('Ложь', False),
    ),
)
def test_boolean_processor_custom_values(value, expected_value):
    processor = BooleanProcessor(true_values=['Истина'], false_values=['Ложь'])

    assert processor(value) is expected_value


def test_boolean_processor_exception():
    processor = BooleanProcessor(true_values=['Да'], false_values=['Нет'])

    with pytest.raises(ColumnError) as exc_info:
        processor('Не знаю')
    assert exc_info.value.messages == ["Ожидается одно из значений: ['Да', 'Нет']"]


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (None, None),
        (10, 10),
        (10.0, 10),
        ('  10  ', 10),
    ),
)
def test_integer_processor(value, expected_value):
    processor = IntegerProcessor()

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, expected_error_message',
    (
        (10.1, '10.1 не является целым числом'),
        ('Не число', 'Не число не является целым числом'),
    ),
)
def test_integer_processor_exception(value, expected_error_message):
    processor = IntegerProcessor()

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]
