test:
	python -m pytest --cov=import_me --cov-report=xml

types:
	mypy .

style:
	flake8 .
	mdl README.md

requirements:
	safety check -r requirements.txt

check:
	make style
	make types
	make test
	make requirements
