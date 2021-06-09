import datetime
import string
import pytz.exceptions
from decimal import Decimal, InvalidOperation
from pytz import timezone as check_timezone
from typing import Callable, Collection, Any, Optional, Sequence, Dict, List, Union

from dateutil.parser import parse
from email_validator import validate_email, EmailNotValidError

from import_me.constants import WHITESPACES
from import_me.exceptions import ColumnError, StopParsing


def strip(value: Any, strip_chars: str = string.whitespace) -> Any:
    if isinstance(value, str):
        value = value.strip(strip_chars)
    return value


def lower(value: Any) -> Any:
    if isinstance(value, str):
        value = value.lower()
    return value


class BaseProcessor:
    raise_error = True
    none_if_error = False

    def __init__(
        self, raise_error: bool = None, none_if_error: bool = None,
        strip_chars: str = None, strip_whitespace: bool = True,
        **kwargs: Any,
    ):
        if raise_error is not None:
            self.raise_error = raise_error
        if none_if_error is not None:
            self.none_if_error = none_if_error

        self.strip_chars = WHITESPACES if strip_whitespace else ''
        if strip_chars:
            self.strip_chars += strip_chars

    def process_value(self, value: Any) -> Any:
        return value

    def process_value_error(self, value: Any, exc_info: Exception) -> Any:
        if self.raise_error:
            if isinstance(exc_info, ColumnError):
                raise exc_info
            raise ColumnError(str(exc_info)) from exc_info
        if self.none_if_error:
            value = None
        return value

    def __call__(self, value: Any) -> Any:
        if value is None or (isinstance(value, str) and not value.strip(self.strip_chars)):
            return None

        try:
            return self.process_value(value)
        except StopParsing as e:
            raise e
        except Exception as e:
            return self.process_value_error(value, e)


class MultipleProcessor(BaseProcessor):
    def __init__(self, *processors: Callable, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.processors = processors

    def process_value(self, value: Any) -> Any:
        for processor in self.processors:
            try:
                value = processor(value)
            except StopParsing as e:
                raise e
            except (TypeError, ValueError, ColumnError) as e:
                value = self.process_value_error(value, e)
        return value


class StringProcessor(BaseProcessor):
    def __init__(
        self, strip_chars: str = None,
        strip_whitespace: bool = True,
        float_fix: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.strip_chars = WHITESPACES if strip_whitespace else ''
        if strip_chars:
            self.strip_chars += strip_chars
        self.float_fix = float_fix

    def process_value(self, value: Any) -> Optional[str]:
        if self.float_fix and isinstance(value, float) and str(value).endswith('.0'):
            value = str(value)[:-2]
        if not isinstance(value, str):
            value = str(value)

        value = value.strip(self.strip_chars)

        if value:
            return value


class LimitedStringProcessor(StringProcessor):
    def __init__(self, max_length: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.max_length = max_length

    def process_value(self, value: Any) -> Any:
        str_value = super().process_value(value)
        if str_value and len(str_value) > self.max_length:
            raise ColumnError(f'"{value}" exceeds max length {self.max_length}')

        return str_value


class IntegerProcessor(BaseProcessor):
    @staticmethod
    def _process_float_value(value: float) -> Optional[int]:
        if value.is_integer():
            return int(value)

    @staticmethod
    def _process_str_value(value: str) -> Optional[int]:
        str_value = value.strip()
        if str_value and str_value.isdigit():
            return int(str_value)

    def process_value(self, value: Any) -> Any:
        int_value = value
        if isinstance(value, float):
            int_value = self._process_float_value(value)
        elif isinstance(value, str):
            int_value = self._process_str_value(value)

        if not isinstance(int_value, int):
            raise ColumnError(f'{value} is not an integer.')

        return int_value


class IntegerRangeProcessor(IntegerProcessor):
    def __init__(self, min_value: int, max_value: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.min_value = min_value
        self.max_value = max_value

    def process_value(self, value: Any) -> Any:
        value = super().process_value(value)
        if not (self.min_value < value <= self.max_value):
            raise ColumnError(f'{value} is not in range ({self.min_value}..{self.max_value}].')

        return value


class FloatProcessor(BaseProcessor):
    def process_value(self, value: Any) -> Any:
        if isinstance(value, float):
            float_value = value
        elif isinstance(value, int):
            float_value = float(value)
        else:
            try:
                float_value = float(str(value).strip().replace(',', '.'))
            except (ValueError, TypeError):
                raise ColumnError(f'{value} is not a floating point number.')

        return float_value


class DecimalProcessor(BaseProcessor):
    def process_value(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            decimal_value = value
        elif isinstance(value, (int, float)):
            decimal_value = Decimal(value)
        else:
            try:
                decimal_value = Decimal(str(value).strip().replace(',', '.'))
            except InvalidOperation:
                raise ColumnError(f'{value} is not a floating point number.')

        return decimal_value


class DecimalRangeProcessor(DecimalProcessor):
    def __init__(
        self, min_value: Decimal, max_value: Decimal, **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self.min_value = min_value
        self.max_value = max_value

    def process_value(self, value: Any) -> Any:
        value = super().process_value(value)
        if not (self.min_value < value <= self.max_value):
            raise ColumnError(f'{value} is not in range ({self.min_value}..{self.max_value}].')

        return value


class BooleanProcessor(BaseProcessor):
    def __init__(self, true_values: Sequence = None, false_values: Sequence = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        default_true_values = {True, 'True', 'true', '1', 'Да'}
        default_false_values = {False, 'False', 'false', '0', 'Нет'}
        self.true_values = set(true_values) if true_values else default_true_values
        self.false_values = set(false_values) if false_values else default_false_values

    def process_value(self, value: Any) -> Any:
        raw_value = value
        if isinstance(raw_value, str):
            raw_value = raw_value.strip()
        if raw_value in self.true_values:
            return True
        elif raw_value in self.false_values:
            return False

        raise ColumnError('It is expected one of values: {0}'.format(list(self.true_values) + list(self.false_values)))


class DateTimeProcessor(BaseProcessor):
    def __init__(self, formats: Collection[str] = None,
                 parser: Callable = None, timezone: Union[str, None] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.formats = formats
        self.parser = parser or parse
        self.user_timezone = None
        if timezone:
            try:
                self.user_timezone = check_timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                self.user_timezone = None
                raise ValueError(f'Unknown time zone.')

    def process_value(self, value: Any) -> Any:
        if isinstance(value, str):
            value = self._get_datetime_from_string(value.strip())
        elif isinstance(value, datetime.datetime):
            pass
        elif isinstance(value, datetime.date):
            value = datetime.datetime.combine(value, datetime.time.min)
        else:
            raise ColumnError(f'Unable to convert to date {value}.')
        if self.user_timezone:
            value = value.astimezone(self.user_timezone)
        return value

    def _get_datetime_from_string(self, value: str) -> datetime.datetime:
        if not self.formats:
            try:
                return self.parser(value)
            except ValueError:
                raise ColumnError(f'Unable to convert "{value}" to date.')
        for date_format in self.formats:
            try:
                return datetime.datetime.strptime(value, date_format)
            except ValueError:
                pass
        raise ColumnError(f'Value "{value}" is not accordance with the format {self.formats}.')


class DateProcessor(DateTimeProcessor):
    def process_value(self, value: Any) -> Any:
        value = super().process_value(value)
        return value.date()


class EmailProcessor(StringProcessor):
    def process_value(self, value: Any) -> Optional[str]:
        email_value = super().process_value(value)
        if email_value:
            email_value = lower(email_value)
            try:
                validate_email(email_value)
            except EmailNotValidError:
                raise ColumnError(f'{value} is not a valid postal address.')
            return email_value


class StringIsNoneProcessor(BaseProcessor):
    def __init__(self, none_symbols: Sequence = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.none_symbols = set(none_symbols) if none_symbols else None

    def process_value(self, value: Any) -> Any:
        if isinstance(value, str) and self.none_symbols:
            symbols = {symbol for word in value.split() for symbol in word}
            if symbols.issubset(self.none_symbols):
                return None
        return value


class StringsArrayProcessor(BaseProcessor):
    def process_value(self, value: Any) -> Optional[List[str]]:
        values = super().process_value(value)
        if values is None:
            return None

        result_values = []
        for value in values.split(','):
            result_values.append(value.strip(self.strip_chars))

        return result_values

    def __call__(self, value: Any) -> List[str]:
        result = super().__call__(value)
        if result is None:
            result = []

        return result


class ChoiceProcessor(BaseProcessor):
    def __init__(self, choices: Dict[Any, Any], raw_value_processor: BaseProcessor = None, **kwargs: Any) -> None:
        self.choices = choices
        self.raw_value_processor = raw_value_processor or StringProcessor(**kwargs)
        super().__init__(**kwargs)

    def process_value(self, value: Any) -> Any:
        value = self.raw_value_processor(value)
        try:
            return self.choices[value]
        except KeyError:
            raise ColumnError(f'Unknown value {value}.')


class ClassifierProcessor(BaseProcessor):
    def __init__(self, choices: List[Any], raw_value_processor: BaseProcessor = None, **kwargs: Any) -> None:
        self.choices = choices
        self.raw_value_processor = raw_value_processor or (lambda raw_value: raw_value)
        super().__init__(**kwargs)

    def process_value(self, value: Any) -> Any:
        value: Any = self.raw_value_processor(value)
        for item, choice_function in self.choices:
            if not callable(choice_function) and choice_function == value:
                return item
            try:
                if choice_function(value):
                    return item
            except TypeError:
                pass
        raise ColumnError('Unknown value.')
