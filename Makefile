all:
	pip install wheel
	python setup.py sdist bdist_wheel
install:
	pip install git+https://github.com/nikhilwoodruff/openfisca-uk
	pip install git+https://github.com/PSLmodels/synthimpute
	pip install -e .
format:
	black . -l 79
test:
	pytest tests