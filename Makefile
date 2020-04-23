test:
	python -m pytest

types:
	mypy .

style:
	flake8 .
	mdl README.md

check:
	make style
	make types
	make test
