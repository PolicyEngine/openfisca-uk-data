all:
	pip install wheel
	python setup.py sdist bdist_wheel
reset:
	rm -rf openfisca_uk_data/microdata/**/*.h5
install:
	pip install git+https://github.com/PolicyEngine/openfisca-uk
	pip install git+https://github.com/PSLmodels/synthimpute
	pip install git+https://github.com/PSLmodels/microdf
	pip install -e .
format:
	black . -l 79
test:
	pytest openfisca_uk_data/tests -vv
	jb clean docs/book
	jb build docs/book
generate:
	openfisca-uk-data raw_frs download 2018
	openfisca-uk-data raw_frs download 2019
	openfisca-uk-data raw_was download 2016
	openfisca-uk-data frs generate 2018
	openfisca-uk-data frs upload 2018
	openfisca-uk-data frs generate 2019
	openfisca-uk-data frs upload 2019
	openfisca-uk-data frs_was_imp generate 2019
	openfisca-uk-data frs_was_imp upload 2019
