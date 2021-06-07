import datetime
import string
from decimal import Decimal

import pytest

from import_me.exceptions import StopParsing, ColumnError
from import_me.processors import (
    strip, lower, BaseProcessor, MultipleProcessor, DateTimeProcessor, DateProcessor,
    StringProcessor, StringIsNoneProcessor, BooleanProcessor, IntegerProcessor,
    DecimalProcessor, FloatProcessor, EmailProcessor, ChoiceProcessor, ClassifierProcessor,
)
from conftest import (
    raise_, choices_classifier_datetime_processor, choices_classifier_integer_processor,
    choices_classifier_no_processor,
)


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
    'value, strip_chars, expected_value',
    (
        (' * | test string | * ', string.whitespace, '* | test string | *'),
        (' * | test string | * ', ' *', '| test string |'),
        (' * | test string | * ', ' *|', 'test string'),
        (1, ' *1', 1),
        (None, ' *1', None),
    ),
)
def test_strip_chars(value, strip_chars, expected_value):
    assert strip(value, strip_chars=strip_chars) == expected_value


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
    'formats, parser, value, expected_value',
    (
        (['%d.%m.%Y'], None, '20.07.2019', datetime.datetime(2019, 7, 20)),
        (['%d.%m.%Y'], None, '  20.07.2019  ', datetime.datetime(2019, 7, 20)),
        (['%Y-%m-%d', '%d.%m.%Y'], None, '20.07.2019', datetime.datetime(2019, 7, 20)),
        (['%d.%m.%Y'], None, None, None),
        (['%d.%m.%Y %H:%M:%S'], None, '20.07.2019 12:43:52', datetime.datetime(2019, 7, 20, 12, 43, 52)),
        (None, None, '20.07.2019', datetime.datetime(2019, 7, 20)),
        (None, None, '  20.07.2019  ', datetime.datetime(2019, 7, 20)),
        (None, None, None, None),
        (None, None, '20.07.2019 12:43:52', datetime.datetime(2019, 7, 20, 12, 43, 52)),
        ([], None, '20.07.2019 12:43:52', datetime.datetime(2019, 7, 20, 12, 43, 52)),
        ('', None, '20.07.2019 12:43:52', datetime.datetime(2019, 7, 20, 12, 43, 52)),
        (None, lambda x: datetime.datetime(2020, 1, 1), '20.07.2019 12:43:52', datetime.datetime(2020, 1, 1)),
    ),
)
def test_datetime_processor(formats, parser, value, expected_value):
    processor = DateTimeProcessor(formats=formats, parser=parser)

    assert processor(value) == expected_value


def test_datetime_processor_error_value():
    processor = DateTimeProcessor(formats=['%d.%m.%Y'])

    with pytest.raises(ColumnError):
        assert processor('2019-01-01')


def test_datetime_processor_error_date_value():
    processor = DateTimeProcessor(formats=[])

    with pytest.raises(ColumnError):
        assert processor('2019_01_01')


@pytest.mark.parametrize(
    'formats, parser, value, expected_value',
    (
        (['%d.%m.%Y'], None, '20.07.2019', datetime.date(2019, 7, 20)),
        (['%d.%m.%Y'], None, '  20.07.2019  ', datetime.date(2019, 7, 20)),
        (['%Y-%m-%d', '%d.%m.%Y'], None, '20.07.2019', datetime.date(2019, 7, 20)),
        (['%d.%m.%Y'], None, None, None),
        (['%d.%m.%Y %H:%M:%S'], None, '20.07.2019 12:43:52', datetime.date(2019, 7, 20)),
        (None, None, '20.07.2019', datetime.date(2019, 7, 20)),
        (None, None, '  20.07.2019  ', datetime.date(2019, 7, 20)),
        (None, None, None, None),
        (None, None, '20.07.2019 12:43:52', datetime.date(2019, 7, 20)),
        ([], None, '20.07.2019 12:43:52', datetime.date(2019, 7, 20)),
        ('', None, '20.07.2019 12:43:52', datetime.date(2019, 7, 20)),
        (None, lambda x: datetime.datetime(2020, 1, 1), '20.07.2019 12:43:52', datetime.date(2020, 1, 1)),
    ),
)
def test_date_processor(formats, parser, value, expected_value):
    processor = DateProcessor(formats=formats, parser=parser)

    assert processor(value) == expected_value


def test_date_processor_error_value():
    processor = DateProcessor(formats=['%d.%m.%Y'])

    with pytest.raises(ColumnError):
        assert processor('2019-01-01')


def test_date_processor_error_date_value():
    processor = DateProcessor(formats=None)

    with pytest.raises(ColumnError):
        assert processor('2019_01_01')


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (None, None),
        (' Test string  ', 'Test string'),
        (123, '123'),
        ('123.0', '123.0'),
        (123.1, '123.1'),
        (datetime.datetime(2019, 1, 1, 1, 1, 1), '2019-01-01 01:01:01'),
        (datetime.date(2019, 1, 1), '2019-01-01'),
        (None, None),
        ('       ', None),
    ),
)
@pytest.mark.parametrize('float_fix', (True, False))
def test_string_processor(value, float_fix, expected_value):
    processor = StringProcessor(float_fix=float_fix)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, float_fix, expected_value', (
        (123.0, False, '123.0'),
        (123.0, True, '123'),
    ),
)
def test_string_processor_float_fix(value, float_fix, expected_value):
    processor = StringProcessor(float_fix=float_fix)

    assert processor.process_value(value) == expected_value


@pytest.mark.parametrize(
    'value, strip_chars, strip_whitespace, expected_value',
    (
        (None, None, True, None),
        (None, None, False, None),
        (' * | Test string | *  \t\n ', None, True, '* | Test string | *'),
        (' * | Test string | *  \t\n ', '*', True, '| Test string |'),
        (' * | Test string | *  \t\n ', '*|', True, 'Test string'),
        ('\xa0* | Test string | *\xa0\r\n', '*|', True, 'Test string'),
        ('\ufeff * | Test string | *\n\xa0', '*|', True, 'Test string'),
        ('\u180e\u180e * | Test string | *\u2008 ', '*|', True, 'Test string'),
        ('** \t\n Test string \t\n **', '*', False, ' \t\n Test string \t\n '),
        ('** \t\n Test string \t\n **', ' *\n', False, '\t\n Test string \t'),
    ),
)
def test_string_processor_strip(value, strip_chars, strip_whitespace, expected_value):
    processor = StringProcessor(strip_chars=strip_chars, strip_whitespace=strip_whitespace)

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
        ('True', True),
        ('False', False),
    ),
)
def test_boolean_processor_custom_values(value, expected_value):
    processor = BooleanProcessor(true_values=['True'], false_values=['False'])

    assert processor(value) is expected_value


def test_boolean_processor_exception():
    processor = BooleanProcessor(true_values=['Yes'], false_values=['No'])

    with pytest.raises(ColumnError) as exc_info:
        processor('I do not know.')
    assert exc_info.value.messages == ["It is expected one of values: ['Yes', 'No']"]


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
        (10.1, '10.1 is not an integer.'),
        ('Not integer', 'Not integer is not an integer.'),
        (
            datetime.datetime(2020, 1, 1),
            '2020-01-01 00:00:00 is not an integer.',
        ),
    ),
)
def test_integer_processor_exception(value, expected_error_message):
    processor = IntegerProcessor()

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (None, None),
        (0, Decimal(0)),
        (10, Decimal('10')),
        (10.1, Decimal(10.1)),
        ('10.123', Decimal('10.123')),
        ('    123,22  \n', Decimal('123.22')),
    ),
)
def test_decimal_processor(value, expected_value):
    processor = DecimalProcessor()

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, expected_error_message',
    (
        ('String', 'String is not a floating point number.'),
        ('10.1.1', '10.1.1 is not a floating point number.'),
        (
            datetime.datetime(2020, 1, 1),
            '2020-01-01 00:00:00 is not a floating point number.',
        ),
    ),
)
def test_decimal_processor_exception(value, expected_error_message):
    processor = DecimalProcessor()

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (None, None),
        (0, float(0)),
        (10, float(10)),
        (10.1, float(10.1)),
        ('10.123', float('10.123')),
        ('    123,22  \n', float('123.22')),
    ),
)
def test_float_processor(value, expected_value):
    processor = FloatProcessor()

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, expected_error_message',
    (
        ('String', 'String is not a floating point number.'),
        ('10.1.1', '10.1.1 is not a floating point number.'),
        (
            datetime.datetime(2020, 1, 1),
            '2020-01-01 00:00:00 is not a floating point number.',
        ),
    ),
)
def test_float_processor_exception(value, expected_error_message):
    processor = FloatProcessor()

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, expected_value',
    (
        (None, None),
        ('', None),
        ('user@example.com', 'user@example.com'),
        ('User@eXample.cOm', 'user@example.com'),
        ('ivan.ivanov@example.com', 'ivan.ivanov@example.com'),
    ),
)
def test_email_processor(value, expected_value):
    processor = EmailProcessor()

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, expected_error_message',
    (
        ('String', 'String is not a valid postal address.'),
        (1, '1 is not a valid postal address.'),
        (
            datetime.datetime(2020, 1, 1),
            '2020-01-01 00:00:00 is not a valid postal address.',
        ),
        ('example.com', 'example.com is not a valid postal address.'),
        ('@example.com', '@example.com is not a valid postal address.'),
        ('user@', 'user@ is not a valid postal address.'),
        ('user@example', 'user@example is not a valid postal address.'),
        ('user@example.doesnotexists', 'user@example.doesnotexists is not a valid postal address.'),
    ),
)
def test_email_processor_exception(value, expected_error_message):
    processor = EmailProcessor()

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_value',
    (
        (None, None, None, None),
        ('2', {'1': 'First', '2': 'Second'}, None, 'Second'),
        (2, {'1': 'First', '2': 'Second'}, None, 'Second'),
        (' 2 ', {'1': 'First', '2': 'Second'}, None, 'Second'),
        (' 2 ', {1: 'First', 2: 'Second'}, IntegerProcessor(), 'Second'),
        (
            ' 31.12.2020 ',
            {
                datetime.date(2020, 12, 31): 'New Year',
                datetime.date(2020, 11, 11): 'typical day',
            },
            DateProcessor(formats=['%d.%m.%Y']),
            'New Year',
        ),
        ('True', {True: 'ok', False: 'fail'}, BooleanProcessor(), 'ok'),
    ),
)
def test_choice_processor(value, choices, raw_value_processor, expected_value):
    processor = ChoiceProcessor(choices=choices, raw_value_processor=raw_value_processor)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_error_message',
    (
        ('3', {'1': 'First', '2': 'Second'}, None, 'Unknown value 3.'),
        ('Not integer', {1: 'First', 2: 'Second'}, IntegerProcessor(), 'Not integer is not an integer.'),
    ),
)
def test_choice_processor_exception(value, choices, raw_value_processor, expected_error_message):
    processor = ChoiceProcessor(choices=choices, raw_value_processor=raw_value_processor)

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_value',
    [
        (
            3, choices_classifier_no_processor, None, 'a',
        ),
        (
            12, choices_classifier_no_processor, None, 'b',
        ),
        (
            'test', choices_classifier_no_processor, None, 'd',
        ),
        (
            'text', choices_classifier_no_processor, None, 'c',
        ),
        (
            'A', choices_classifier_no_processor, None, 'e',
        ),
    ],
)
def test_classifier_processor(value, choices, raw_value_processor, expected_value):
    processor = ClassifierProcessor(choices=choices, raw_value_processor=raw_value_processor)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_error_message',
    [
        (
            -10, choices_classifier_no_processor, None, 'Unknown value.',
        ),
    ],
)
def test_classifier_processor_exception(value, choices, raw_value_processor, expected_error_message):
    processor = ClassifierProcessor(choices=choices, raw_value_processor=raw_value_processor)

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_value',
    [
        (
            3, choices_classifier_integer_processor, IntegerProcessor(), 'a',
        ),
        (
            '12', choices_classifier_integer_processor, IntegerProcessor(), 'b',
        ),
    ],
)
def test_classifier_integer_processor(value, choices, raw_value_processor, expected_value):
    processor = ClassifierProcessor(choices=choices, raw_value_processor=raw_value_processor)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_error_message',
    [
        (
            '-10', choices_classifier_integer_processor, IntegerProcessor(), '-10 is not an integer.',
        ),
        (
            -10, choices_classifier_integer_processor, IntegerProcessor(), 'Unknown value.',
        ),

    ],
)
def test_classifier_integer_processor_exception(value, choices, raw_value_processor, expected_error_message):
    processor = ClassifierProcessor(choices=choices, raw_value_processor=raw_value_processor)

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_value',
    [
        (
            '2020-02-01', choices_classifier_datetime_processor, DateProcessor(), 'a',
        ),
        (
            '2021-01-01', choices_classifier_datetime_processor, DateProcessor(), 'b',
        ),
    ],
)
def test_classifier_datetime_processor(value, choices, raw_value_processor, expected_value):
    processor = ClassifierProcessor(choices=choices, raw_value_processor=raw_value_processor)

    assert processor(value) == expected_value


@pytest.mark.parametrize(
    'value, choices, raw_value_processor, expected_error_message',
    [
        (
            '2022-01-01', choices_classifier_datetime_processor, DateProcessor(), 'Unknown value.',
        ),
    ],
)
def test_classifier_datetime_processor_exception(value, choices, raw_value_processor, expected_error_message):
    processor = ClassifierProcessor(choices=choices, raw_value_processor=raw_value_processor)

    with pytest.raises(ColumnError) as exc_info:
        processor(value)
    assert exc_info.value.messages == [expected_error_message]
