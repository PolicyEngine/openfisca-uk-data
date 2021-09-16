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
import h5py

TEST_YEAR = 2018
# Variable pairs to check for similarity
with open(REPO / "tests" / "frs" / "variable_ukmod_map.yml") as f:
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


def get_test_params(variable):
    test_params = dict(
        ukmod=metadata[variable],
        min_quantile_abs_error=MIN_QUANTILE_ABS_ERROR,
        max_quantile_rel_error=MAX_QUANTILE_REL_ERROR,
        max_rel_error=MAX_MEAN_REL_ERROR,
        max_mean_rel_error=MAX_MEAN_REL_ERROR,
        min_nonzero_agreement=MIN_NONZERO_AGREEMENT,
    )
    if isinstance(metadata[variable], dict):
        test_params.update(**metadata[variable])
    else:
        test_params["ukmod"] = metadata[variable]
    return test_params


# For each variable pair and metric, check that the error is within absolute and relative thresholds


@pytest.mark.parametrize(
    "variable,quantile",
    product(metadata.keys(), np.linspace(0.1, 0.9, 9).round(1)),
)
def test_quantile(variable, quantile):
    test_params = get_test_params(variable)
    result = baseline.calc(variable, period=TEST_YEAR)
    target = ukmod[test_params["ukmod"]]
    result_quantile = result[result > 0].quantile(quantile)
    target_quantile = target[target > 0].quantile(quantile)

    abs_error = abs(result_quantile - target_quantile)
    rel_error = abs(result_quantile / target_quantile - 1)

    assert (
        abs_error < test_params["min_quantile_abs_error"]
        or rel_error < test_params["max_quantile_rel_error"]
    )

    return result_quantile, target_quantile


@pytest.mark.parametrize("variable", metadata.keys())
def test_aggregate(variable):
    test_params = get_test_params(variable)
    result = baseline.calc(variable, period=TEST_YEAR).sum()
    target = ukmod[test_params["ukmod"]].sum()

    assert abs(result / target - 1) < test_params["max_rel_error"]

    return result, target


@pytest.mark.parametrize("variable", metadata.keys())
def test_nonzero_count(variable):
    test_params = get_test_params(variable)
    result = (baseline.calc(variable, period=TEST_YEAR) > 0).sum()
    target = (ukmod[test_params["ukmod"]] > 0).sum()

    assert abs(result / target - 1) < test_params["max_rel_error"]

    return result, target


@pytest.mark.parametrize("variable", metadata.keys())
def test_average_error_among_nonzero(variable):
    test_params = get_test_params(variable)
    result = pd.Series(
        baseline.calc(variable, period=TEST_YEAR, map_to="household").values,
        index=baseline.calc("household_id", period=TEST_YEAR).values,
    )
    target = ukmod_hh[test_params["ukmod"]]
    mean_error = (result / target - 1)[target > 0].abs().mean()

    assert mean_error < test_params["max_mean_rel_error"]

    return mean_error


@pytest.mark.parametrize("variable", metadata.keys())
def test_ukmod_nonzero_agreement(variable):
    test_params = get_test_params(variable)
    result = pd.Series(
        baseline.calc(variable, period=TEST_YEAR, map_to="household").values,
        index=baseline.calc("household_id", period=TEST_YEAR).values,
    )
    target = ukmod_hh[test_params["ukmod"]]
    mean_error = ((result > 0) == (target == 0)).mean()

    assert mean_error < test_params["min_nonzero_agreement"]

    return mean_error
