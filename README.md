# import me

Python tool for importing and validating data from xlsx/xls/csv files.

## Example

```jupyter
>>> class XLSXParser(BaseXLSXParser):
...     columns = [
...         Column('first_name', index=0, header='First Name'),
...         Column('last_name', index=1, header='Last Name'),
...     ]

>>> parser = XLSXParser(file_path=xlsx_filepath)
>>> parser()
>>> print(parser.has_errors)  # False
>>> pprint(parser.cleaned_data)
[
    {
        'first_name': 'Ivan',
        'last_name': 'Ivanov',
        'row_index': 1,
    },
    {
        'first_name': 'Petr',
        'last_name': 'Petrov',
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
  [BestDoctor python styleguide](https://github.com/best-doctor/guides/blob/master/guides/python_styleguide.md).
  Sorry, styleguide is available only in Russian for now.
- We respect [Django CoC](https://www.djangoproject.com/conduct/).
  Make soft, not bullshit.
