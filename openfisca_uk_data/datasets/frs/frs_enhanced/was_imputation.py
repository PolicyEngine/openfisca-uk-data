from microdf.generic import MicroDataFrame
from openfisca_uk_data.datasets.was.raw_was import RawWAS
from openfisca_uk_data.datasets.frs.frs import FRS
import pandas as pd
import microdf as mdf
import synthimpute as si


def impute_wealth(year: int) -> pd.Series:
    """Impute wealth by fitting a random forest model.

    Args:
            year (int): The year of simulation.

    Returns:
            pd.Series: The predicted wealth values.
    """

    was = load_and_process_was()

    from openfisca_uk import Microsimulation

    sim = Microsimulation(dataset=FRS, year=year)

    TRAIN_COLS = [
        "gross_income",
        "num_adults",
        "num_children",
        "pension_income",
        "employment_income",
        "self_employment_income",
        "investment_income",
        "num_bedrooms",
        "council_tax",
        "is_renting",
    ]

    IMPUTE_COLS = [
        "owned_land_value",
        "property_wealth",
        "corporate_wealth",
        "gross_financial_wealth",
        "net_financial_wealth",
        "main_residence_value",
        "other_residential_property_value",
        "non_residential_property_value",
    ]

    # FRS has investment income split between dividend and savings interest.
    frs_cols = [i for i in TRAIN_COLS if i != "investment_income"]
    frs_cols += [
        "dividend_income",
        "savings_interest_income",
        "people",
        "net_income",
        "household_weight",
    ]

    frs = sim.df(frs_cols, map_to="household", period=year)
    frs["investment_income"] = (
        frs.savings_interest_income + frs.dividend_income
    )

    return si.rf_impute(
        x_train=was[TRAIN_COLS],
        y_train=was[IMPUTE_COLS],
        x_new=frs[TRAIN_COLS],
        verbose=True,
    )


def load_and_process_was() -> pd.DataFrame:
    """Process the Wealth and Assets Survey household wealth file.

    Returns:
            pd.DataFrame: The processed dataframe.
    """
    RENAMES = {
        "R6xshhwgt": "weight",
        # Components for estimating land holdings.
        "DVLUKValR6_sum": "owned_land_value",  # In the UK.
        "DVPropertyR6": "property_wealth",
        "DVFESHARESR6_aggr": "emp_shares_options",
        "DVFShUKVR6_aggr": "uk_shares",
        "DVIISAVR6_aggr": "investment_isas",
        "DVFCollVR6_aggr": "unit_investment_trusts",
        "TotpenR6_aggr": "pensions",
        "DvvalDBTR6_aggr": "db_pensions",
        # Predictors for fusing to FRS.
        "dvtotgirR6": "gross_income",
        "NumAdultW6": "num_adults",
        "NumCh18W6": "num_children",
        # Household Gross Annual income from occupational or private pensions
        "DVGIPPENR6_AGGR": "pension_income",
        "DVGISER6_AGGR": "self_employment_income",
        # Household Gross annual income from investments
        "DVGIINVR6_aggr": "investment_income",
        # Household Total Annual Gross employee income
        "DVGIEMPR6_AGGR": "employment_income",
        "HBedrmW6": "num_bedrooms",
        "GORR6": "region",
        "DVPriRntW6": "is_renter",  # {1, 2} TODO: Get codebook values.
        "CTAmtW6": "council_tax",
        # Other columns for reference.
        "DVLOSValR6_sum": "non_uk_land",
        "HFINWNTR6_Sum": "net_financial_wealth",
        "DVLUKDebtR6_sum": "uk_land_debt",
        "HFINWR6_Sum": "gross_financial_wealth",
        "TotWlthR6": "wealth",
        "DVhvalueR6": "main_residence_value",
        "DVHseValR6_sum": "other_residential_property_value",
        "DVBlDValR6_sum": "non_residential_property_value",
    }

    # TODO: Handle different WAS releases

    was = (
        RawWAS.load(2016, "was_round_6_hhold_eul_mar_20")[list(RENAMES.keys())]
        .rename(columns=RENAMES)
        .fillna(0)
    )

    was["is_renting"] = was["is_renter"] == 1

    was["non_db_pensions"] = was.pensions - was.db_pensions
    was["corporate_wealth"] = was[
        [
            "non_db_pensions",
            "emp_shares_options",
            "uk_shares",
            "investment_isas",
            "unit_investment_trusts",
        ]
    ].sum(axis=1)
    return MicroDataFrame(was, weights=was.weight)
