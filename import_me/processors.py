import datetime
from decimal import Decimal, InvalidOperation
from typing import Callable, Any, Iterable, Optional, Sequence

from email_validator import validate_email, EmailNotValidError

from import_me.exceptions import ColumnError, StopParsing


def strip(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
    return value


def lower(value: Any) -> Any:
    if isinstance(value, str):
        value = value.lower()
    return value


class BaseProcessor:
    raise_error = True
    none_if_error = False

    def __init__(self, raise_error: bool = None, none_if_error: bool = None, **kwargs: Any):
        if raise_error is not None:
            self.raise_error = raise_error
        if none_if_error is not None:
            self.none_if_error = none_if_error

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
        if value is None or (isinstance(value, str) and not value):
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
    def process_value(self, value: Any) -> Optional[str]:
        if not isinstance(value, str):
            value = str(value)

        value = value.strip()

        if value:
            return value


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
            raise ColumnError(f'{value} не является целым числом')

        return int_value


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
                raise ColumnError(f'{value} не является числом с плавающей точкой')

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
                raise ColumnError(f'{value} не является числом с плавающей точкой')

        return decimal_value


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

        raise ColumnError('Ожидается одно из значений: {0}'.format(list(self.true_values) + list(self.false_values)))


class DateTimeProcessor(BaseProcessor):
    def __init__(self, formats: Iterable[str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.formats = formats

    def process_value(self, value: Any) -> Any:
        if isinstance(value, str):
            value = self._get_datetime_from_string(value.strip())
        elif isinstance(value, datetime.datetime):
            pass
        elif isinstance(value, datetime.date):
            value = datetime.datetime.combine(value, datetime.time.min)
        else:
            raise ColumnError(f'Невозможно преобразовать в дату {value}')
        return value

    def _get_datetime_from_string(self, value: str) -> datetime.datetime:
        for date_format in self.formats:
            try:
                return datetime.datetime.strptime(value, date_format)
            except ValueError:
                pass
        raise ColumnError(f'Значение "{value}" не соответствует форматам {self.formats}')


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
                raise ColumnError(f'{value} не является корректным почтовым адресом')
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
