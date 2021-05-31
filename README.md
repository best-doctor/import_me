# import me

[![Build Status](https://travis-ci.org/best-doctor/import_me.svg?branch=master)](https://travis-ci.org/best-doctor/import_me)
[![Maintainability](https://api.codeclimate.com/v1/badges/5e6923f90968e21955e4/maintainability)](https://codeclimate.com/github/best-doctor/import_me/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/5e6923f90968e21955e4/test_coverage)](https://codeclimate.com/github/best-doctor/import_me/test_coverage)
[![PyPI version](https://badge.fury.io/py/import-me.svg)](https://badge.fury.io/py/import-me)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/import-me)](https://pypi.org/project/import-me/)

Python tool for importing and validating data from xlsx/xls/csv files.

## Example

```jupyter
from import_me import BaseXLSXParser, Column
from import_me.processors import StringProcessor, IntegerProcessor

>>> class XLSXParser(BaseXLSXParser):
...     columns = [
...         Column('first_name', index=0, header='First Name', processor=StringProcessor()),
...         Column('last_name', index=1, header='Last Name', processor=StringProcessor()),
...         Column('age', index=2, header='Age', processor=IntegerProcessor()),
...     ]

>>> parser = XLSXParser(file_path=xlsx_filepath)
>>> parser()
>>> print(parser.has_errors)  # False
>>> pprint(parser.cleaned_data)
[
    {
        'first_name': 'Ivan',
        'last_name': 'Ivanov',
        'age': 25,
        'row_index': 1,
    },
    {
        'first_name': 'Petr',
        'last_name': 'Petrov',
        'age': 33,
        'row_index': 2,
    },
]
```

## Installation

```bash
pip install import_me
```

## Contributing

We would love you to contribute to our project. It's simple:

- Create an issue with bug you found or proposal you have.
  Wait for approve from maintainer.
- Create a pull request. Make sure all checks are green.
- Fix review comments if any.
- Be awesome.

Here are useful tips:

- You can run all checks and tests with `make check`. Please do it
  before TravisCI does.
- We use
  [BestDoctor python styleguide](https://github.com/best-doctor/guides/blob/master/guides/en/python_styleguide.md).
- We respect [Django CoC](https://www.djangoproject.com/conduct/).
  Make soft, not bullshit.
