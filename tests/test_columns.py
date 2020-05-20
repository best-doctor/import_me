import pytest

from import_me import Column
from import_me.constants import COLUMN_NAME_PATTERN
from import_me.exceptions import ParserError


@pytest.mark.parametrize(
    'column_name',
    ('a', 'name', 'column_name', 'column_name1'),
)
def test_column_valid_name(column_name):
    Column(name=column_name, index=0)


@pytest.mark.parametrize(
    'column_name',
    ('', '1', '_name', 'NaMe', 'na-me'),
)
def test_column_invalid_name(column_name):
    with pytest.raises(ParserError) as exc_info:
        Column(name=column_name, index=0)

    assert exc_info.value.messages == [
        f'Column name {column_name} does not match the pattern {COLUMN_NAME_PATTERN}.']
