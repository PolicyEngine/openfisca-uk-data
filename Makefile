all: install
	pip install wheel
	python setup.py sdist bdist_wheel
reset:
	rm -rf openfisca_uk_data/microdata/**/*.h5
install:
	pip install openfisca-uk
	pip install synthimpute
	pip install git+git://github.com/PSLmodels/microdf
	pip install -e .
format:
	black . -l 79
test:
	pytest openfisca_uk_data/tests -vv
	jb clean docs/book
	jb build docs/book
generate:
	python openfisca_uk_data/generate.py