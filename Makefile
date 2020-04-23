test:
	python -m pytest

types:
	mypy .

style:
	flake8 .

check:
	make style
	make types
	make test
