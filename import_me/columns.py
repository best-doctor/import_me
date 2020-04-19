from typing import Callable


class Column:
    def __init__(
        self, name: str, index: int, processor: Callable = None,
        header: str = None, validate_header: bool = True, required: bool = False,
    ):
        self.name = name
        self.index = index
        if processor:
            self.processor = processor
        else:
            self.processor = lambda x: x
        self.header = header
        self.validate_header = validate_header
        self.required = required
