import logging
from pathlib import Path
from openfisca_uk_data.datasets.frs.frs_enhanced.spi_imputation import impute_incomes
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
        logging.info(f"Generating FRSEnhanced for year {year}")
        logging.info("Loading FRS")
        FRS.generate(year)
        frs_enhanced = h5py.File(FRSEnhanced.file(year), mode="w")
        logging.info("Adding high incomes imputed from the SPI")
        impute_incomes(frs_enhanced)
        frs_enhanced.close()
        logging.info("Adding wealth imputed from the WAS")
        pred_wealth = impute_wealth(year, dataset=FRSEnhanced)
        frs_enhanced = h5py.File(FRSEnhanced.file(year), mode="a")
        for wealth_category in pred_wealth.columns:
            frs_enhanced[wealth_category] = pred_wealth[wealth_category].values
        frs_enhanced.close()
        logging.info("Adding consumption imputed from the LCFS")
        pred_consumption = impute_consumption(year)
        frs_enhanced = h5py.File(FRSEnhanced.file(year), mode="a")
        for consumption_category in pred_consumption.columns:
            frs_enhanced[consumption_category] = pred_consumption[
                consumption_category
            ].values
        frs_enhanced.close()

        # Save imputed variables to a CSV file

        logging.info("Saving imputed variables to CSV")

        from openfisca_uk import Microsimulation
        sim = Microsimulation(dataset=FRSEnhanced)
        hnet = sim.calc("household_net_income")
        hnet.weights *= sim.calc("people", map_to="household").values
        pd.concat(
            [
                sim.df(["household_net_income", "household_market_income", "household_id", "income_decile", "wealth_decile"]),
                pred_wealth,
                pred_consumption,
                pd.DataFrame({
                    "decile": hnet.decile_rank(),
                })
            ],
            axis=1,
        ).to_csv(PACKAGE_DIR / "imputations" / f"imputations_{year}.csv")
