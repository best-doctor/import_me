import pytest

from bdata_parser.exceptions import ParserError


@pytest.mark.parametrize(
    'messages, expected_messages',
    (
        ('Ошибка', ['Ошибка']),
        (['Ошибка1', 'Ошибка2'], ['Ошибка1', 'Ошибка2']),
    ),
)
def test_parser_error_messages(messages, expected_messages):
    exc_info = ParserError(messages)

    assert exc_info.messages == expected_messages


def test_parser_error_str():
    exc_info = ParserError(['Ошибка1', 'Ошибка2'])

    assert str(exc_info) == 'Ошибка1\nОшибка2'
