from openfisca_uk_data.datasets.spi.raw_spi import RawSPI
from openfisca_core.model_api import *
from openfisca_uk_data.utils import *
import pandas as pd
from pandas import DataFrame
import h5py

max_ = np.maximum
where = np.where


@dataset
class SPI:
    name = "spi"
    model = UK

    def generate(year: int) -> None:
        """Generates the SPI-based input dataset for OpenFisca-UK.

        Args:
                year (int): The year to generate for (uses the raw SPI from this year)
        """

        main = RawSPI.load(year, "main").fillna(0)
        spi = h5py.File(SPI.file(year), mode="w")

        add_id_variables(spi, main)
        add_age(spi, main)
        add_incomes(spi, main)

        # Generate OpenFisca-UK variables and save
        spi.close()


def add_id_variables(spi: h5py.File, main: DataFrame):
    spi["person_id"] = main.index
    spi["person_benunit_id"] = main.index
    spi["person_household_id"] = main.index
    spi["benunit_id"] = main.index
    spi["household_id"] = main.index
    spi["role"] = np.array(["adult"] * len(main)).astype("S")


def add_age(spi: h5py.File, main: DataFrame):
    LOWER = np.array([16, 25, 35, 45, 55, 65, 75])
    UPPER = np.array([25, 35, 45, 55, 65, 75, 80])
    age_range = main.AGERANGE - 1
    spi["age"] = LOWER[age_range] + np.random.rand(len(main)) * (
        UPPER[age_range] - LOWER[age_range]
    )


def add_incomes(spi: h5py.File, main: DataFrame):
    RENAMES = dict(
        pension_income="PENSION",
        self_employment_income="PROFITS",
        property_income="INCPROP",
        savings_interest_income="INCBBS",
        dividend_income="DIVIDENDS",
        blind_persons_allowance="BPADUE",
        married_couples_allowance="MCAS",
        gift_aid="GIFTAID",
        capital_allowances="CAPALL",
        deficiency_relief="DEFICIEN",
        covenanted_payments="COVNTS",
        charitable_investment_gifts="GIFTINV",
        employment_expenses="EPB",
        other_deductions="MOTHDED",
        pension_contributions="PENSRLF",
        person_weight="FACT",
        benunit_weight="FACT",
        household_weight="FACT",
    )
    spi["pays_scottish_income_tax"] = main.SCOT_TXP == 1
    spi["employment_income"] = main[["PAY", "EPB", "TAXTERM"]].sum(axis=1)
    spi["social_security_income"] = main[
        ["SRP", "INCPBEN", "UBISJA", "OSSBEN"]
    ].sum(axis=1)
    spi["miscellaneous_income"] = main[
        ["OTHERINV", "OTHERINC", "MOTHINC"]
    ].sum(axis=1)
    for var, key in RENAMES.items():
        spi[var] = main[key]
