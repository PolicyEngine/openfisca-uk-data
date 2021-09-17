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
<<<<<<< HEAD
        "google-cloud-storage",
=======
>>>>>>> 162c2e5842d8cfa9db7ff8bd4f7e8ff8e7c7e55c
    ],
    entry_points={
        "console_scripts": ["openfisca-uk-data=openfisca_uk_data.cli:main"],
    },
)
