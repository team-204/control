init:
	pipenv install --dev

test:
	pipenv run python -m unittest discover tests/
