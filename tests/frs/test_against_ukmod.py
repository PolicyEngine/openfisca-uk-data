"""
This module tests the FRS dataset produced by openfisca-uk-data against UKMOD - checking that the distributions are similar.
"""

import numpy as np
import pandas as pd
from openfisca_uk_data import FRS, UKMODInput, RawFRS, REPO
from openfisca_uk import Microsimulation, BASELINE_VARIABLES
import pytest
from microdf import MicroDataFrame
from itertools import product
from functools import partial
import yaml

TEST_YEAR = 2018
# Variable pairs to check for similarity
with open(REPO.parent / "tests" / "frs" / "variable_ukmod_map.yml") as f:
    metadata = yaml.load(f)

MAX_REL_ERROR = 0.05
MAX_QUANTILE_REL_ERROR = 0.05
MIN_QUANTILE_ABS_ERROR = 25
MAX_MEAN_REL_ERROR = 0.05
MIN_NONZERO_AGREEMENT = 0.99

if TEST_YEAR not in UKMODInput.years:
    raise FileNotFoundError("UKMOD FRS needed to run tests against.")
if TEST_YEAR not in RawFRS.years:
    raise FileNotFoundError("Raw FRS needed to construct datasets.")

# Run the dataset generation and load test data

FRS.generate(TEST_YEAR)
baseline = Microsimulation(dataset=FRS)
ukmod = UKMODInput.load(TEST_YEAR, "person")
ukmod_hh = ukmod.groupby("household_id").sum()
ukmod = MicroDataFrame(ukmod, weights=ukmod.person_weight)

# For each variable pair and metric, check that the error is within absolute and relative thresholds


@pytest.mark.parametrize(
    "variable,quantile",
    product(metadata.keys(), np.linspace(0.1, 0.9, 9).round(1)),
)
def test_quantile(variable, quantile):
    result = baseline.calc(variable, period=TEST_YEAR)
    target = ukmod[metadata[variable]]
    result_quantile = result[result > 0].quantile(quantile)
    target_quantile = target[target > 0].quantile(quantile)

    assert (
        abs(result_quantile - target_quantile) < MIN_QUANTILE_ABS_ERROR
        or abs(result_quantile / target_quantile - 1) < MAX_QUANTILE_REL_ERROR
    )


@pytest.mark.parametrize("variable", metadata.keys())
def test_aggregate(variable):
    result = baseline.calc(variable, period=TEST_YEAR).sum()
    target = ukmod[metadata[variable]].sum()

    assert abs(result / target - 1) < MAX_REL_ERROR


@pytest.mark.parametrize("variable", metadata.keys())
def test_nonzero_count(variable):
    result = (baseline.calc(variable, period=TEST_YEAR) > 0).sum()
    target = (ukmod[metadata[variable]] > 0).sum()

    assert abs(result / target - 1) < MAX_REL_ERROR


@pytest.mark.parametrize("variable", metadata.keys())
def test_average_error_among_nonzero(variable):
    result = pd.Series(
        baseline.calc(variable, period=TEST_YEAR, map_to="household").values,
        index=baseline.calc("household_id", period=TEST_YEAR).values,
    )
    target = ukmod_hh[metadata[variable]]
    error = (result / target - 1)[target > 0].abs()

    assert error.mean() < MAX_MEAN_REL_ERROR


@pytest.mark.parametrize("variable", metadata.keys())
def test_ukmod_nonzero_agreement(variable):
    result = pd.Series(
        baseline.calc(variable, period=TEST_YEAR, map_to="household").values,
        index=baseline.calc("household_id", period=TEST_YEAR).values,
    )
    target = ukmod_hh[metadata[variable]]
    error = (result > 0) == (target == 0)

    assert error.mean() < MIN_NONZERO_AGREEMENT


# Debugging utilities


def compare_datasets(
    openfisca_uk_variables: list, ukmod_variables: list, entity: str = "person"
):
    if entity == "person":
        ukmod_df = ukmod
    elif entity == "benunit":
        ukmod_df = ukmod.groupby("benunit_id").sum()
    else:
        ukmod_df = ukmod_hh
    return pd.concat(
        [
            baseline.df(
                openfisca_uk_variables
                + ["person_id", "benunit_id", "household_id"]
            ).set_index(f"{entity}_id"),
            ukmod_df[ukmod_variables],
        ]
    )
