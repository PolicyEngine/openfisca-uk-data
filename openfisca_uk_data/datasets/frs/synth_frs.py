from openfisca_uk_data.utils import *
from openfisca_uk_data.datasets.frs.frs import FRS
import shutil
import pandas as pd
import numpy as np
import h5py
import requests
from tqdm import tqdm

DEFAULT_SYNTH_FILE = "https://github.com/PolicyEngine/openfisca-uk-data/releases/download/synth-frs-2019/synth_frs_2019.h5"


@dataset
class SynthFRS:
    name = "synth_frs"
    model = UK

    def generate(year):
        ID_COLS = (
            "person_id",
            "person_benunit_id",
            "person_benunit_role",
            "person_household_id",
            "person_household_role",
            "person_state_id",
            "person_state_role",
            "benunit_id",
            "household_id",
            "state_id",
        )

        def anonymise(arr: np.array, name: str) -> pd.DataFrame:
            result = pd.Series(arr)
            if name not in ID_COLS:
                # don't change identity columns, this breaks structures
                if len(result.unique()) < 16:
                    # shuffle categorical columns
                    result = result.sample(frac=1).values
                else:
                    # shuffle + add noise to numeric columns
                    # noise = between -3% and +3% added to each row
                    noise = np.random.rand() * 3e-2 + 1.0
                    result = result.sample(frac=1).values * noise
            return result

        data = FRS.load(year)
        year = int(year)

        with h5py.File(SynthFRS.file(year), mode="w") as f:
            for variable in data.keys():
                try:
                    f[variable] = anonymise(data[variable], variable)
                except:
                    f[variable] = anonymise(data[variable], variable).astype(
                        "S"
                    )

    def save(data_file: str = DEFAULT_SYNTH_FILE, year: int = 2019):
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
