all:
	python setup.py sdist bdist_wheel
install:
	pip install -e .
format:
	black . -l 79
test:
	black . -l 79 --check
	pytest tests