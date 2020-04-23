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
