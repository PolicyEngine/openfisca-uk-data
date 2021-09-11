"""
This module tests the FRS dataset produced by openfisca-uk-data against UKMOD - checking that the distributions are similar.
"""

import numpy as np
from openfisca_uk_data import BaseFRS, FRS, UKMODAggregates
from openfisca_uk_data.datasets.frs.base_frs.model_input_variables import (
    get_input_variables,
)
from openfisca_uk import Microsimulation
import pytest
import pandas as pd
from itertools import product
from functools import partial

# Assumes that the RawFRS dataset is available, and runs tests
# on the FRS dataset generated.

TEST_YEAR = 2018
MAX_RELATIVE_ERROR = 0.02
PAIRS = dict(employment_income="yem")

variables = get_input_variables()


BaseFRS.generate(TEST_YEAR)
FRS.generate(TEST_YEAR)

baseline = Microsimulation(dataset=FRS)
agg_df = UKMODAggregates.load(TEST_YEAR, "aggregates")


metrics = list(map(lambda n: f"q{n}", range(0, 110, 10))) + ["sum", "nonzero"]
get_quantile = lambda values, q: values.quantile(q)
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
    target = agg_df[UKMOD_variable][metric]

    # assert OpenFisca-UK distribution parameters are within relative error thresholds

    assert (
        result == target
        or -MAX_RELATIVE_ERROR < result / target - 1 < MAX_RELATIVE_ERROR
    )
