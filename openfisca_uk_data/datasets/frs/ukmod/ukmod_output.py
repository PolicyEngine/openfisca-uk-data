from pathlib import Path
import pandas as pd
from openfisca_uk_data.utils import dataset

NON_MONTHLY_VARIABLES = (
    "person_id",
    "benunit_id",
    "household_id",
    "person_weight",
)


@dataset
class UKMODOutput:
    name = "ukmod_output"

    def generate(tabfile: str, year: int):
        tabfile = Path(tabfile)
        # Read the input dataset and construct a weighted DataFrame
        df = pd.read_csv(tabfile, delimiter="\t")
        # Add IDs to match against OpenFisca-UK
        df["person_id"] = (
            df.idorighh * 1e2 + df.idorigbenunit * 1e1 + df.idorigperson
        )
        df["benunit_id"] = df.idorighh * 1e2 + df.idorigbenunit * 1e1
        df["household_id"] = df.idorighh * 1e2
        df["person_weight"] = df.dwt
        df.set_index("person_id", inplace=True)
        for variable in df.columns:
            if variable not in NON_MONTHLY_VARIABLES:
                df[variable] *= 12
        with pd.HDFStore(UKMODOutput.file(year)) as f:
            f["person"] = pd.DataFrame(df)
