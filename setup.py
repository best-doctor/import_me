from typing import Optional

from setuptools import setup, find_packages


package_name = 'import_me'


def get_version() -> Optional[str]:
    with open('import_me/__init__.py', 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('__version__'):
            return line.split('=')[-1].strip().strip("'")


def get_long_description() -> str:
    with open('README.md', encoding='utf8') as f:
        return f.read()


setup(
    name=package_name,
    description='Python tool for importing and validating data from xlsx/xls/csv files.',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(),
    include_package_data=True,
    keywords='xlsx csv import',
    version=get_version(),
    author='Ilya Lebedev',
    author_email='melevir@gmail.com',
    install_requires=[
        'setuptools',
        'openpyxl>=3.0.1',
        'xlrd>=1.2.0',
        'email-validator>=1.0.5',
    ],
    url='https://github.com/best-doctor/import_me',
    license='MIT',
    py_modules=[package_name],
    zip_safe=False,
)
