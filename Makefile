#! /usr/bin/make -f

.PHONY: tests
tests:
	pytest-3

# run tests not requiring network
.PHONY: quicktests
quicktests:
	pytest-3 -m 'not network'

codechecks: pep8 pyflakes pylint

pep8:
	pep8 --verbose --repeat --show-source --filename=*.py,reportbug,querybts . --statistics --ignore=E501

pyflakes:
	pyflakes . bin/*

pylint:
	pylint --output-format=colorized  bin/* reportbug/ checks/* test/ setup.py

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build
	rm -rf reportbug.egg-info
