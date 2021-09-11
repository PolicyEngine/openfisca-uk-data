from pathlib import Path
import pandas as pd
import numpy as np
from microdf import MicroDataFrame
from openfisca_uk_data.utils import dataset


@dataset
class UKMODAggregates:
    name = "ukmod_agg"

    def generate(tabfile: str, year: int):
        tabfile = Path(tabfile)
        # Read the input dataset and construct a weighted DataFrame
        UKMOD_inp = pd.read_csv(tabfile, delimiter="\t")
        df = MicroDataFrame(UKMOD_inp, weights=UKMOD_inp.dwt)
        agg_df = pd.DataFrame()
        QUANTILES = np.linspace(0, 1, 11)

        for var in df.columns:
            # For each possible variable, save the deciles, total and non-zero counts
            try:
                data = {
                    f"q{round(q * 100)}": result * 12
                    for q, result in zip(
                        QUANTILES, df[var].quantile(QUANTILES)
                    )
                }
                data["sum"] = df[var].sum() * 12
                data["nonzero"] = (df[var] != 0).sum()
                agg_df[var] = pd.Series(data)
            except:
                pass

        with pd.HDFStore(UKMODAggregates.file(year)) as f:
            f["aggregates"] = agg_df
