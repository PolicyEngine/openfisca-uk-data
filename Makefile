all:
	pip install wheel
	python setup.py sdist bdist_wheel
install:
	pip install -e .
	pip install git+https://github.com/PSLmodels/openfisca-uk
format:
	black . -l 79
test:
	pytest tests