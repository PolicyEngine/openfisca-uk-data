from openfisca_uk_data.utils import *
from openfisca_uk_data.datasets.frs.frs import FRS
import shutil
import pandas as pd
import numpy as np
import h5py
import requests
from tqdm import tqdm

DEFAULT_SYNTH_URL = "https://github.com/UBICenter/openfisca-uk-data/releases/download/synth-frs/synth_frs_2018.h5"


@dataset
class SynthFRS:
    name = "synth_frs"
    model = UK
    input_reform_from_year = FRS.input_reform_from_year

    def generate(year):
        from openfisca_uk import CountryTaxBenefitSystem

        ID_COLS = (
            "person_person_id",
            "person_benunit_id",
            "person_household_id",
            "benunit_id",
            "household_id",
        )

        def anonymise(df: pd.DataFrame) -> pd.DataFrame:
            result = df.copy()
            for col in result.columns:
                if col not in ID_COLS:
                    # don't change identity columns, this breaks structures
                    if result[col].unique().size < 16:
                        # shuffle categorical columns
                        result[col] = result[col].sample(frac=1).values
                    else:
                        # shuffle + add noise to numeric columns
                        # noise = between -3% and +3% added to each row
                        noise = np.random.rand() * 3e-2 + 1.0
                        result[col] = result[col].sample(frac=1).values * noise
            return result

        year = 2018
        system = CountryTaxBenefitSystem()
        data = FRS.load(year)
        entities = ("person", "benunit", "household")
        entity_dfs = {key: {} for key in entities}
        for entity in entities:
            for variable in data.keys():
                if system.variables[variable].entity.key == entity:
                    entity_dfs[entity][variable] = data[variable]
        person, benunit, household = map(
            lambda x: anonymise(pd.DataFrame(x)), entity_dfs.values()
        )

        year = int(year)

        with h5py.File(SynthFRS.file(year), mode="w") as f:
            for df in (person, benunit, household):
                for variable in df.columns:
                    try:
                        f[variable] = df[variable].values
                    except:
                        f[variable] = df[variable].values.astype("S")

    def save(data_file: str = DEFAULT_SYNTH_URL, year: int = 2018):
        if "https://" in data_file:
            response = requests.get(data_file, stream=True)
            total_size_in_bytes = int(
                response.headers.get("content-length", 0)
            )
            block_size = 1024  # 1 Kibibyte
            progress_bar = tqdm(
                total=total_size_in_bytes, unit="iB", unit_scale=True
            )
            with open(SynthFRS.file(year), "wb") as file:
                for data in response.iter_content(block_size):
                    progress_bar.update(len(data))
                    file.write(data)
            progress_bar.close()
        else:
            shutil.copyfile(data_file, SynthFRS.file(year))
