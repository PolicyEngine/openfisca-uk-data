from typing import Dict
import h5py
from numpy.typing import ArrayLike
import numpy as np

def clone_and_replace_half(dataset: type, year: int, f: h5py.File, mapping: Dict[str, ArrayLike], weighting: float = 0.5):
    """Clones a dataset and replaces half of the values with the values in the mapping.

    Args:
        dataset (type): The dataset to clone.
        year (int): The year to clone.
        f (h5py.File): The file stream to which to write the cloned dataset.
        mapping (Dict[str, ArrayLike]): The mapping from the original dataset to the cloned dataset.
        weighting (float): The weighting to apply to the cloned dataset. The original dataset has
                            (1 - weighting) weight.
    """
    data = dataset.load(year)
    for field in data.keys():
        if "_id" in field:
            values = np.concatenate([data[field][...] * 10, mapping[field] * weighting * 10 + 1])
        elif "_weight" in field:
            values = np.concatenate([data[field][...] * (1 - weighting), mapping[field] * weighting])
        elif field in mapping:
            values = np.concatenate([data[field][...], mapping[field]])
        else:
            values = np.concatenate([data[field][...], data[field][...]])
        try:
            f[field] = values
        except TypeError:
            f[field] = values.astype("S")
