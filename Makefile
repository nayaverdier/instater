.DEFAULT_GOAL := all

black = black instater tests
flake8 = flake8 instater tests
isort = isort instater tests
mypy = mypy instater tests --ignore-missing-imports --scripts-are-modules --check-untyped-defs --no-implicit-optional
install-pip = python -m pip install -U setuptools pip wheel
test = pytest --cov=instater --cov-report term-missing tests/

.PHONY: install
install:
	$(install-pip)
	pip install -e .

.PHONY: install-dev
install-dev:
	$(install-pip)
	pip install -e ".[dev]"

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: check
check:
	$(isort) --check-only --df
	$(black) --check --diff
	$(flake8)
	$(mypy)

.PHONY: test
test:
	$(test)

.PHONY: coverage
coverage:
	coverage xml

.PHONY: build
build:
	python setup.py sdist bdist_wheel
	twine check dist/*

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -f coverage.xml
