from openfisca_uk_data.datasets.was.raw_was import RawWAS
from openfisca_uk_data.utils import dataset, UK
from openfisca_uk_data.datasets.frs.frs import FRS
from openfisca_uk_data.datasets.frs.frs_enhanced.was_imputation import (
    impute_land,
)
from openfisca_uk_data.datasets.frs.frs_enhanced.lcf_imputation import (
    impute_carbon,
)
import h5py
import numpy as np
from time import time


@dataset
class FRSEnhanced:
    name = "frs_enhanced"
    model = UK

    def generate(year: int) -> None:
        print("Imputing FRS land value exposure...", end="", flush=True)
        t = time()
        pred_land = impute_land(year)
        print(
            f" (completed in {round(time() - t, 1)}s)\nImputing FRS carbon consumption...",
            end="",
            flush=True,
        )
        t = time()
        pred_carbon = impute_carbon(year)
        print(
            f" (completed in {round(time() - t, 1)}s)\nGenerating default FRS...",
            end="",
            flush=True,
        )
        t = time()
        frs_enhanced = h5py.File(FRSEnhanced.file(year), mode="w")
        FRS.generate(year)
        frs = FRS.load(year)
        for variable in tuple(frs.keys()):
            frs_enhanced[variable] = np.array(frs[variable][...])
        frs_enhanced["land_value"] = pred_land
        frs_enhanced["carbon_consumption"] = pred_carbon
        frs_enhanced.close()
        frs.close()
        print(f" (completed in {round(time() - t, 1)}s)\nDone", flush=True)
