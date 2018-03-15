.PHONY: test test-component test-all init clean all

test:
	pipenv run pytest tests/unit

test-component:
	pipenv run pytest tests/component

test-all:
	pipenv run pytest tests

init:
	pipenv install --dev

clean:
	rm -rf control.egg-info .pytest_cache */*.pyc */__pycache__
