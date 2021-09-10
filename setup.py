from setuptools import setup, find_packages

setup(
    name="openfisca-uk-data",
    version="0.1.2",
    description=(
        "A Python package to manage OpenFisca-UK-compatible microdata"
    ),
    url="http://github.com/ubicenter/openfisca-uk-data",
    author="Nikhil Woodruff",
    author_email="nikhil.woodruff@outlook.com",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "pathlib",
        "tqdm",
        "tables",
        "h5py",
        "OpenFisca-UK @ git+https://github.com/PSLmodels/openfisca-uk",
        "synthimpute @ git+https://github.com/PSLmodels/synthimpute",
    ],
    entry_points={
        "console_scripts": ["openfisca-uk-data=openfisca_uk_data.cli:main"],
    },
)
