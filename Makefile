#! /usr/bin/make -f

.PHONY: tests
tests:
	pytest-3

# run tests not requiring network
.PHONY: quicktests
quicktests:
	pytest-3 -m 'not network'

.PHONY: lint
lint:
	flake8 . bin/*

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf build
	rm -rf reportbug.egg-info
