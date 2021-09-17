all:
	pip install wheel
	python setup.py sdist bdist_wheel
reset:
	rm -rf openfisca_uk_data/microdata/**/*.h5
install:
	conda install -c anaconda hdf5
	pip install git+https://github.com/PolicyEngine/openfisca-uk
	pip install git+https://github.com/PSLmodels/synthimpute
	pip install -e .
format:
	black . -l 79
test:
	pytest openfisca_uk_data/tests -vv
	jb clean docs/book
	jb build docs/book
