#! /usr/bin/make -f

NOSETESTS = nosetests3 test -v --stop
nosetests_cmd = $(NOSETESTS) ${NOSETESTS_OPTS}

.PHONY: tests
tests:
	$(nosetests_cmd)

# run tests not requiring network
.PHONY: quicktests
quicktests: NOSETESTS_OPTS += --processes=4 --attr='!network'
quicktests:
	$(nosetests_cmd)

coverage: NOSETESTS_OPTS += --with-coverage --cover-package=reportbug
coverage:
	$(nosetests_cmd)

coverhtml: NOSETESTS_OPTS += --cover-html
coverhtml: coverage

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
