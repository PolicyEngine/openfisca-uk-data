from openfisca_uk_data import VERSION
from setuptools import setup, find_packages

setup(
    name="OpenFisca-UK-Data",
    version=VERSION,
    description=(
        "A Python package to manage OpenFisca-UK-compatible microdata"
    ),
    url="http://github.com/PolicyEngine/OpenFisca-UK-Data",
    author="Nikhil Woodruff",
    author_email="nikhil@policyengine.org",
    packages=find_packages(exclude="microdata"),
    install_requires=[
        "pandas",
        "pathlib",
        "tqdm",
        "h5py",
        "tables",
        "google-cloud-storage",
        "jupyter-book>=0.11.1",
        "sphinxcontrib-bibtex>=1.0.0",
        "synthimpute>=0.1.0",
        "OpenFisca-Tools>=0.1.3",
    ],
    entry_points={
        "console_scripts": ["openfisca-uk-data=openfisca_uk_data.cli:main"],
    },
)
