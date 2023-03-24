install-dev:
	pip install --editable .[dev]

check-types:
	mypy seqmail
