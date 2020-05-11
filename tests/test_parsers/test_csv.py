from import_me.columns import Column
from import_me.parsers.csv import BaseCSVParser


def test_base_csv_parser(csv_file_factory):
    class CSVParser(BaseCSVParser):
        columns = [
            Column('first_name', index=0, header='First Name'),
            Column('last_name', index=1, header='Last Name'),
        ]

    csv_file = csv_file_factory(
        header=['First Name', 'Last Name'],
        data=[
            ['Ivan', 'Ivanov'],
            ['Petr', 'Petrov'],
        ],
    )
    parser = CSVParser(file_path=csv_file.name)
    parser()

    assert parser.cleaned_data == [
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


def test_base_csv_parser_additional_params(csv_file_factory):
    class CSVParser(BaseCSVParser):
        columns = [
            Column('first_name', index=0, header='First Name'),
            Column('last_name', index=1, header='Last Name'),
        ]

    csv_file = csv_file_factory(
        header=['First Name', 'Last Name'],
        data=[
            ['Ivan', 'Ivanov'],
            ['Petr', 'Petrov'],
        ],
        file_kwargs={'encoding': 'cp1251'},
        writer_kwargs={'delimiter': ';'},
    )
    parser = CSVParser(file_path=csv_file.name, encoding='cp1251', delimiter=';')
    parser()

    assert parser.cleaned_data == [
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


def test_parser_unique_column(csv_file_factory):
    class Parser(BaseCSVParser):
        columns = [
            Column('id', index=0, unique=True),
        ]

    csv_file = csv_file_factory(
        header=['id'],
        data=[
            ['1'],
            ['2'],
            ['1'],
        ],
    )
    parser = Parser(file_path=csv_file.name)

    parser()

    assert parser.has_errors is True
    assert parser.errors == ['row: 3, column: 0, value 1 is a duplicate of row 1']
    assert parser.cleaned_data == [
        {'id': '1', 'row_index': 1},
        {'id': '2', 'row_index': 2},
    ]


def test_parser_unique_together_column(csv_file_factory):
    class Parser(BaseCSVParser):
        columns = [
            Column('first_name', index=0),
            Column('last_name', index=1),
            Column('middle_name', index=2),
        ]
        unique_together = [
            ['first_name', 'last_name'],
            ['last_name', 'middle_name'],
        ]

    csv_file = csv_file_factory(
        header=['first_name', 'last_name', 'middle_name'],
        data=[
            ['Ivan', 'Ivanov', 'Ivanovich'],
            ['Ivan', 'Ivanov', 'Petrovich'],
            ['Petr', 'Ivanov', 'Ivanovich'],
            ['Petr', 'Petrov', 'Petrovich'],
        ],
    )
    parser = Parser(file_path=csv_file.name)

    parser()

    assert parser.has_errors is True
    assert parser.errors == [
        'row: 2, first_name (Ivan), last_name (Ivanov) is a duplicate of row 1',
        'row: 3, last_name (Ivanov), middle_name (Ivanovich) is a duplicate of row 1',
    ]
    assert parser.cleaned_data == [
        {'first_name': 'Ivan', 'last_name': 'Ivanov', 'middle_name': 'Ivanovich', 'row_index': 1},
        {'first_name': 'Petr', 'last_name': 'Petrov', 'middle_name': 'Petrovich', 'row_index': 4},
    ]
