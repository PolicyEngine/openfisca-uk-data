from openfisca_uk.tools.simulation import Microsimulation
from openfisca_uk_data import FRS
import h5py
import pytest

TEST_YEAR = 2018

FRS.generate(2018)

with h5py.File(FRS.file(TEST_YEAR)) as f:
    VARIABLES = list(f.keys())

baseline = Microsimulation(dataset=FRS)


@pytest.mark.parametrize("variable", VARIABLES)
def test_not_nan(variable):
    assert baseline.calc(variable, period=TEST_YEAR).isna().mean() == 0
