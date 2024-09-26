from typing import List, Union, Optional


class ParserError(Exception):
    def __init__(self, messages: Optional[Union[List, str]] = None) -> None:
        super().__init__(messages)
        if messages is None:
            messages = []
        elif not isinstance(messages, list):
            messages = [messages]
        self.messages = messages

    def __str__(self) -> str:
        return '\n'.join(self.messages)


class ColumnError(ParserError):
    pass


class SkipRow(ParserError):
    pass


class StopParsing(ParserError):
    pass
