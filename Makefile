test:
	python -m pytest --cov=import_me --cov-report=xml

types:
	mypy .

style:
	flake8 .
	mdl README.md

check:
	make style
	make types
	make test
