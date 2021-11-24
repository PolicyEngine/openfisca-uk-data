from typing import Tuple
import pandas as pd
from pathlib import Path
from openfisca_uk_data.datasets.frs.frs import FRS
from openfisca_uk_data.datasets.lcf import RawLCF
from microdf import MicroDataFrame
import synthimpute as si

CATEGORY_NAMES = {
    1: "Food and non-alcoholic beverages",
    2: "Alcohol and tobacco",
    3: "Clothing and footwear",
    4: "Housing, water and electricity",
    5: "Household furnishings",
    6: "Health",
    7: "Transport",
    8: "Communication",
    9: "Recreation",
    10: "Education",
    11: "Restaurants and hotels",
    12: "Miscellaneous",
}

HOUSEHOLD_LCF_RENAMES = {
    "G018": "is_adult",
    "G019": "is_child",
    "Gorx": "region",
}
PERSON_LCF_RENAMES = {
    "B303p": "employment_income",
    "B3262p": "self_employment_income",
    "B3381": "state_pension",
    "P049p": "pension_income",
}
REGIONS = {
    1: "NORTH_EAST",
    2: "NORTH_WEST",
    3: "YORKSHIRE",
    4: "EAST_MIDLANDS",
    5: "WEST_MIDLANDS",
    6: "EAST_OF_ENGLAND",
    7: "LONDON",
    8: "SOUTH_EAST",
    9: "SOUTH_WEST",
    10: "WALES",
    11: "SCOTLAND",
    12: "NORTHERN_IRELAND",
}


def impute_carbon(year: int) -> pd.Series:
    """Impute carbon consumption by fitting a random forest model.

    Args:
        year (int): The year of LCFS to use.

    Returns:
        pd.Series: The imputed carbon consumption.
    """

    # Load the LCF data with carbon consumption
    lcf = load_lcfs_with_carbon(year)

    # Impute LCF carbon consumption to FRS households
    return impute_carbon_to_FRS(lcf, year)


def impute_carbon_to_FRS(lcf: MicroDataFrame, year: int) -> pd.Series:
    """Impute carbon consumption to the FRS.

    Args:
        lcf (MicroDataFrame): The LCF data.
        year (int): The year of the FRS to use.

    Returns:
        pd.Series: The imputed carbon consumption.
    """

    from openfisca_uk import Microsimulation

    sim = Microsimulation(dataset=FRS, year=year)

    frs = sim.df(
        [
            "is_adult",
            "is_child",
            "region",
            "employment_income",
            "self_employment_income",
            "state_pension",
            "pension_income",
        ],
        map_to="household",
    )

    frs.region = frs.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )
    lcf.region = lcf.region.map(
        {name: float(i) for i, name in REGIONS.items()}
    )

    return si.rf_impute(
        x_train=lcf.drop(["carbon_tonnes"], axis=1),
        y_train=lcf.carbon_tonnes,
        x_new=frs,
    )


def load_lcfs_with_carbon(year: int) -> MicroDataFrame:
    """Load LCF data with carbon consumption.

    Args:
        year (int): The year of LCFS to use.

    Returns:
        MicroDataFrame: The LCF data with carbon consumption.
    """
    households, people = load_and_process_lcf(year)

    emissions = pd.read_csv(
        Path(__file__).parent / "ncfs_emissions_2019.csv"
    ).set_index("code_start")

    # Manipulate LCF and NCFS data to get expenditure on the same categories
    # Both datasets use the COICOP classification
    # Documentation: https://unstats.un.org/unsd/classifications/unsdclassifications/COICOP_2018_-_pre-edited_white_cover_version_-_2018-12-26.pdf

    index_to_col = {i: f"P6{i:02}" for i in CATEGORY_NAMES}
    spending = (
        households[list(index_to_col.values())]
        .rename(columns={y: x for x, y in index_to_col.items()})
        .unstack()
        .reset_index()
    )
    spending.columns = "category", "household", "spending"
    spending["household"] = households.case[spending.household].values
    households = households.set_index("case")
    spending.category = spending.category.map(CATEGORY_NAMES)
    spending.spending *= 52
    spending["weight"] = households.weighta[spending.household].values * 1000
    spending = MicroDataFrame(spending, weights=spending.weight)
    emissions.index = emissions.index.astype(str)
    spending_by_category = spending.groupby("category").spending.sum()

    grouped_ncfs = pd.DataFrame(
        {
            code: {
                "category": CATEGORY_NAMES[code],
                "carbon_tonnes": emissions[
                    emissions.index.str.startswith(str(code))
                ].carbon_tonnes.sum(),
            }
            for code in CATEGORY_NAMES.keys()
        }
    ).T.set_index("category")

    # For each category, calculate spending from the LCFS and carbon emissions
    # from the NCFS. Then, divide to find the carbon emissions per pound spent

    carbon_by_category = pd.DataFrame(
        {
            category: {
                "carbon_tonnes": grouped_ncfs.carbon_tonnes[category],
                "spending": spending_by_category[category],
            }
            for category in spending.category.unique()
        }
    ).T

    carbon_by_category["carbon_per_pound"] = (
        carbon_by_category.carbon_tonnes / carbon_by_category.spending
    )

    # Multiple spending by carbon intensity to calculate LCF households' carbon footprints
    spending["carbon_tonnes"] = (
        carbon_by_category.carbon_per_pound[spending.category].values
        * spending.spending
    )
    lcf_with_carbon = (
        pd.DataFrame(spending[["household", "carbon_tonnes", "weight"]])
        .groupby("household")
        .sum()
    )

    # Add in LCF variables that also appear in the FRS-based microsimulation model

    lcf_household_vars = households[list(HOUSEHOLD_LCF_RENAMES.keys())].rename(
        columns=HOUSEHOLD_LCF_RENAMES
    )
    lcf_person_vars = (
        people[list(PERSON_LCF_RENAMES) + ["case"]]
        .rename(columns=PERSON_LCF_RENAMES)
        .groupby("case")
        .sum()
    )

    lcf_with_carbon = pd.concat(
        [
            lcf_with_carbon,
            lcf_household_vars,
            lcf_person_vars,
        ],
        axis=1,
    )

    # LCF incomes are weekly - convert to annual
    for variable in PERSON_LCF_RENAMES.values():
        lcf_with_carbon[variable] *= 52

    lcf_with_carbon.region = lcf_with_carbon.region.map(REGIONS)
    lcf = lcf_with_carbon.sort_index()

    # Return household-level LCF dataset with carbon consumption
    # and FRS-shared columns
    return MicroDataFrame(lcf, weights=households.weighta[lcf.index] * 1000)


def load_and_process_lcf(
    year: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and process the LCF and NCFS summary data.

    Args:
        year (int): The year of LCFS to use.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: The LCF household and person tables.
    """
    households = RawLCF.load(2019, "lcfs_2019_dvhh_ukanon")
    people = RawLCF.load(2019, "lcfs_2019_dvper_ukanon201920")

    return households, people
