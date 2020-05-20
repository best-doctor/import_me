import re
from typing import Callable

from import_me.constants import COLUMN_NAME_PATTERN
from import_me.exceptions import ParserError


class Column:
    def __init__(
        self, name: str, index: int, processor: Callable = None,
        header: str = None, validate_header: bool = True,
        required: bool = False, unique: bool = False,
    ):
        self.name = name
        self.index = index
        if processor:  # noqa: IFSTMT001 (this is for mypy)
            self.processor = processor
        else:
            self.processor = lambda x: x
        self.header = header
        self.validate_header = validate_header
        self.required = required
        self.unique = unique

        self._check_name()

    def _check_name(self) -> None:
        if not re.match(COLUMN_NAME_PATTERN, self.name):
            raise ParserError(
                f'Column name {self.name} does not match the pattern {COLUMN_NAME_PATTERN}.')
