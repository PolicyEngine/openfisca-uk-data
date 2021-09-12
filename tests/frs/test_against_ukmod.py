"""
This module tests the FRS dataset produced by openfisca-uk-data against UKMOD - checking that the distributions are similar.
"""

import numpy as np
from openfisca_uk_data import BaseFRS, FRS, UKMODFRS
from openfisca_uk_data.datasets.frs.base_frs.model_input_variables import (
    get_input_variables,
)
from openfisca_uk import Microsimulation
import pytest
from microdf import MicroDataFrame
from itertools import product
from functools import partial

# Assumes that the RawFRS dataset is available, and runs tests
# on the FRS dataset generated.

TEST_YEAR = 2018
PAIRS = dict(
    employment_income="yem",
    pension_income="ypp",
    self_employment_income="yse",
    property_income="ypr",
    pension_contributions="tpcpe",
    rent="xhcrt",
    mortgage="xhcmomi",
    housing_costs="xhc",
    childcare_cost="xcc",
    weekly_hours="lhw",
)
MIN_ABS_ERROR = 1.0
REL_ERROR_TOLERANCE = dict(
    employment_income=0.01,
    pension_income=0.01,
    self_employment_income=0.02,
    property_income=0.025,
    pension_contributions=0.01,
    rent=0.01,
    mortgage=0.01,
    housing_costs=0.01,
    childcare_cost=0.01,
    weekly_hours=0.02,
)


variables = get_input_variables()
BaseFRS.generate(TEST_YEAR)
FRS.generate(TEST_YEAR)
baseline = Microsimulation(dataset=FRS)
ukmod = UKMODFRS.load(TEST_YEAR, "person")
ukmod = MicroDataFrame(ukmod, weights=ukmod.person_weight)
metrics = list(map(lambda n: f"q{n}", range(0, 110, 10))) + ["sum", "nonzero"]
get_quantile = lambda values, q: values[values > 0].quantile(q)
calc_functions = [
    partial(get_quantile, q=q) for q in np.linspace(0, 1, 11)
] + [lambda values: values.sum(), lambda values: (values > 0).sum()]
metric_to_func = {m: f for m, f in zip(metrics, calc_functions)}


@pytest.mark.parametrize(
    "variable,UKMOD_variable,metric",
    map(lambda x: (*x[0], x[1]), product(PAIRS.items(), metrics)),
)
def test_distribution_parameter_close_to_UKMOD(
    variable, UKMOD_variable, metric
):
    result = metric_to_func[metric](baseline.calc(variable, period=TEST_YEAR))
    target = metric_to_func[metric](ukmod[UKMOD_variable])
    rel_err = result / target - 1
    abs_err = result - target
    max_err = REL_ERROR_TOLERANCE[variable]
    # assert OpenFisca-UK distribution parameters are within relative error thresholds

    assert (
        result == target
        or (-MIN_ABS_ERROR < abs_err < MIN_ABS_ERROR)
        or (-max_err < rel_err < max_err)
    )
