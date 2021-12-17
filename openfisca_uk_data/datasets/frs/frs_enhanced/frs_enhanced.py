from pathlib import Path
from openfisca_uk_data.utils import dataset, UK, PACKAGE_DIR
from openfisca_uk_data.datasets.frs.frs import FRS
from openfisca_uk_data.datasets.frs.frs_enhanced.was_imputation import (
    impute_wealth,
)
from openfisca_uk_data.datasets.frs.frs_enhanced.lcf_imputation import (
    impute_consumption,
)
import h5py
import numpy as np
from time import time
import pandas as pd


@dataset
class FRSEnhanced:
    name = "frs_enhanced"
    model = UK

    def generate(year: int) -> None:
        folder = Path(__file__).parent
        print(
            "Imputing FRS property, corporate and land wealth...",
            end="",
            flush=True,
        )
        t = time()
        pred_wealth = impute_wealth(year)
        print(
            f" (completed in {round(time() - t, 1)}s)\nImputing FRS consumption categories...",
            end="",
            flush=True,
        )
        t = time()
        pred_consumption = impute_consumption(year)
        print(
            f" (completed in {round(time() - t, 1)}s)\nGenerating default FRS...",
            end="",
            flush=True,
        )
        t = time()
        frs_enhanced = h5py.File(FRSEnhanced.file(year), mode="w")
        FRS.generate(year)
        frs = FRS.load(year)
        results = pd.DataFrame(
            {
                "household_id": np.array(frs["household_id"][...]),
            }
        )
        pd.concat(
            [
                results,
                pred_wealth,
                pred_consumption,
            ],
            axis=1,
        ).to_csv(PACKAGE_DIR / "imputations" / f"imputations_{year}.csv")
        for variable in tuple(frs.keys()):
            frs_enhanced[variable] = np.array(frs[variable][...])
        for wealth_category in pred_wealth.columns:
            frs_enhanced[wealth_category] = pred_wealth[wealth_category].values
        for consumption_category in pred_consumption.columns:
            frs_enhanced[consumption_category] = pred_consumption[
                consumption_category
            ].values
        frs_enhanced.close()
        frs.close()
        print(f" (completed in {round(time() - t, 1)}s)\nDone", flush=True)
