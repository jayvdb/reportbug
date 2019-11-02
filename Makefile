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

.PHONY: lint
lint:
	flake8 . bin/*

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build
	rm -rf reportbug.egg-info
