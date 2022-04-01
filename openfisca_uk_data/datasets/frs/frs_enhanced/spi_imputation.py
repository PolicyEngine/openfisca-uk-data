import logging
import pandas as pd
from typing import Dict, List
import h5py
import numpy as np
from numpy.typing import ArrayLike

from openfisca_uk_data.datasets.frs.frs import FRS

def impute_incomes(dataset: type = FRS, year: int = 2019) -> Dict[str, ArrayLike]:
    """Imputation of high incomes from the SPI.

    Args:
        dataset (type): The dataset to clone.
        year (int): The year to clone.

    Returns:
        Dict[str, ArrayLike]: The mapping from the original dataset to the cloned dataset.
    """
    from openfisca_uk import Microsimulation
    sim = Microsimulation(dataset=FRS, year=year)

    return 0

