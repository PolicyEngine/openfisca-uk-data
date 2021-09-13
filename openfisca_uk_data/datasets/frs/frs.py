from openfisca_uk_data.datasets.frs.raw_frs import RawFRS
from openfisca_core.model_api import *
from openfisca_uk_data.utils import *
import pandas as pd
from pandas import DataFrame
import h5py

max_ = np.maximum
where = np.where


@dataset
class FRS:
    name = "frs"
    model = UK

    def generate(year: int) -> None:
        """Generates the FRS-based input dataset for OpenFisca-UK.

        Args:
            year (int): The year to generate for (uses the raw FRS from this year)
        """

        # Load raw FRS tables
        raw_frs_files = RawFRS.load(year)
        frs = h5py.File(FRS.file(year), mode="w")
        tables = (
            "adult",
            "child",
            "accounts",
            "benefits",
            "job",
            "oddjob",
            "benunit",
            "househol",
            "chldcare",
            "pension",
            "maint",
            "mortgage",
            "penprov",
        )
        (
            adult,
            child,
            accounts,
            benefits,
            job,
            oddjob,
            benunit,
            household,
            childcare,
            pension,
            maintenance,
            mortgage,
            pen_prov,
        ) = [raw_frs_files[table] for table in tables]
        raw_frs_files.close()

        person = pd.concat([adult, child]).sort_index().fillna(0)

        # Generate OpenFisca-UK variables and save

        add_id_variables(frs, person, benunit, household)
        add_personal_variables(frs, person)
        add_benunit_variables(frs, benunit)
        add_household_variables(frs, household)
        add_market_income(
            frs, person, pension, job, accounts, household, oddjob, year
        )
        add_benefit_income(frs, person, benefits, household)
        add_expenses(
            frs,
            person,
            household,
            maintenance,
            mortgage,
            childcare,
            pen_prov,
        )
        frs.close()


def add_id_variables(
    frs: h5py.File, person: DataFrame, benunit: DataFrame, household: DataFrame
):
    """Adds ID variables and weights.

    Args:
        frs (h5py.File)
        person (DataFrame)
        benunit (DataFrame)
        household (DataFrame)
    """
    # Add primary and foreign keys
    frs["person_id"] = person.index
    frs["person_benunit_id"] = person.benunit_id
    frs["person_household_id"] = person.household_id
    frs["benunit_id"] = person.benunit_id.sort_values().unique()
    frs["household_id"] = person.household_id.sort_values().unique()

    # Add grossing weights
    frs["person_weight"] = pd.Series(
        household.GROSS4[person.household_id].values, index=person.index
    )
    frs["benunit_weight"] = benunit.GROSS4
    frs["household_weight"] = household.GROSS4


def add_personal_variables(frs: h5py.File, person: DataFrame):
    """Adds personal variables (age, gender, education).

    Args:
        frs (h5py.File)
        person (DataFrame)
    """
    # Add basic personal variables
    age = person.AGE80 + person.AGE
    frs["age"] = age
    frs["role"] = np.where(person.AGE80 == 0, "adult", "child").astype("S")
    frs["gender"] = np.where(person.SEX == 1, "MALE", "FEMALE").astype("S")
    frs["is_household_head"] = person.HRPID == 1
    frs["is_benunit_head"] = person.UPERSON == 1
    frs["marital_status"] = (
        person.MARITAL.fillna(2)
        .map(
            {
                i: status
                for i, status in zip(
                    range(1, 7),
                    [
                        "MARRIED",
                        "SINGLE",
                        "SINGLE",
                        "WIDOWED",
                        "SEPARATED",
                        "DIVORCED",
                    ],
                )
            }
        )
        .astype("S")
    )

    # Add education levels
    fted = person.FTED
    typeed2 = person.TYPEED2
    frs["dec"] = np.select(
        [
            fted.isin((2, -1, 0)),
            typeed2 == 1,
            typeed2.isin((2, 4))
            | (typeed2.isin((3, 8)) & (age < 11))
            | ((typeed2 == 0) & (fted == 1) & (age > 5) & (age < 11)),
            typeed2.isin((5, 6))
            | (typeed2.isin((3, 8)) & (age >= 11) & (age <= 16))
            | ((typeed2 == 0) & (fted == 1) & (age <= 16)),
            typeed2
            == 7
            | (typeed2.isin((3, 8)) & (age > 16))
            | ((typeed2 == 0) & (fted == 1) & (age > 16)),
            typeed2.isin((7, 8)) & (age >= 19),
            typeed2 == 9 | ((typeed2 == 0) & (fted == 1) & (age >= 19)),
        ],
        [
            "NOT_IN_EDUCATION",
            "PRE_PRIMARY",
            "PRIMARY",
            "LOWER_SECONDARY",
            "UPPER_SECONDARY",
            "POST_SECONDARY",
            "TERTIARY",
        ],
    ).astype("S")

    # Add employment status
    frs["employment_status"] = person.EMPSTATI.map(
        {
            i: status
            for i, status in zip(
                range(12),
                [
                    "CHILD",
                    "FT_EMPLOYED",
                    "PT_EMPLOYED",
                    "FT_SELF_EMPLOYED",
                    "PT_SELF_EMPLOYED",
                    "UNEMPLOYED",
                    "RETIRED",
                    "STUDENT",
                    "CARER",
                    "LONG_TERM_DISABLED",
                    "SHORT_TERM_DISABLED",
                ],
            )
        }
    ).astype("S")


def add_household_variables(frs: h5py.File, household: DataFrame):
    """Adds household variables (region, tenure, council tax imputation).

    Args:
        frs (h5py.File)
        household (DataFrame)
    """
    # Add region
    from openfisca_uk.variables.demographic.household import Region

    frs["region"] = household.GVTREGNO.map(
        {
            i: region
            for i, region in zip(
                range(1, 13),
                [
                    "NORTH_EAST",
                    "NORTH_WEST",
                    "YORKSHIRE",
                    "EAST_MIDLANDS",
                    "WEST_MIDLANDS",
                    "EAST_OF_ENGLAND",
                    "LONDON",
                    "SOUTH_EAST",
                    "SOUTH_WEST",
                    "SCOTLAND",
                    "WALES",
                    "NORTHERN_IRELAND",
                ],
            )
        }
    ).astype("S")

    frs["tenure_type"] = household.PTENTYP2.map(
        {
            i: tenure
            for i, tenure in zip(
                range(1, 7),
                [
                    "RENT_FROM_COUNCIL",
                    "RENT_FROM_HA",
                    "RENT_PRIVATELY",
                    "RENT_PRIVATELY",
                    "OWNED_OUTRIGHT",
                    "OWNED_WITH_MORTGAGE",
                ],
            )
        }
    ).astype("S")

    frs["num_bedrooms"] = household.BEDROOM6

    frs["accommodation_type"] = household.TYPEACC.map(
        {
            i: accommodation
            for i, accommodation in zip(
                range(1, 8),
                [
                    "HOUSE_DETACHED",
                    "HOUSE_SEMI_DETACHED",
                    "HOUSE_TERRACED",
                    "FLAT",
                    "CONVERTED_HOUSE",
                    "MOBILE",
                    "OTHER",
                ],
            )
        }
    ).astype("S")

    # Impute Council Tax

    CT_mean = household.groupby(
        ["GVTREGNO", "CTBAND"], dropna=False
    ).CTANNUAL.mean()
    pairs = household.set_index(["GVTREGNO", "CTBAND"])
    hh_CT_mean = CT_mean[pairs.index].values
    CT_imputed = hh_CT_mean
    council_tax = pd.Series(
        np.where(
            household.CTANNUAL.isna(), max_(CT_imputed, 0), household.CTANNUAL
        )
    )
    average_CT = council_tax.dropna().mean()
    council_tax.fillna(average_CT, inplace=True)
    frs["council_tax"] = council_tax

    # Add housing costs


def add_market_income(
    frs: h5py.File,
    person: DataFrame,
    pension: DataFrame,
    job: DataFrame,
    account: DataFrame,
    household: DataFrame,
    oddjob: DataFrame,
    year: DataFrame,
):
    """Adds income variables (non-benefit).

    Args:
        frs (h5py.File)
        person (DataFrame)
        pension (DataFrame)
        job (DataFrame)
        account (DataFrame)
        household (DataFrame)
        oddjob (DataFrame)
        year (DataFrame)
    """
    frs["employment_income"] = person.INEARNS * 52

    frs["pension_income"] = (
        pension.PENPAY[pension.PENPAY > 0].groupby(pension.person_id).sum()
        + pension.PTAMT[pension.PTINC == 2][pension.PTAMT > 0]
        .groupby(pension.person_id)
        .sum()
        + pension.POAMT[(pension.POINC == 2) | (pension.PENOTH == 1)][
            pension.POAMT > 0
        ]
    ).reindex(index=person.index).fillna(0) * 52

    # Add self-employed income (correcting one person in 2018)
    seincamt = (
        (job.SEINCAMT.groupby(job.person_id).sum())
        .reindex(person.index)
        .fillna(0)
    )
    frs["self_employment_income"] = (
        np.where(
            (year == 2018) & (person.index == 806911),
            seincamt,
            person.SEINCAM2,
        )
        * 52
    )

    DIVIDEND_ACCOUNTS = (7, 8, 9, 13, 22, 23, 24)
    TAX_FREE_SAVINGS_ACCOUNTS = (6, 14, 21)
    frs["tax_free_savings_income"] = (
        account.ACCINT[account.ACCOUNT.isin(TAX_FREE_SAVINGS_ACCOUNTS)]
        .groupby(account.person_id)
        .sum()
        .reindex(index=person.index)
        .fillna(0)
        * 52
    )
    dividend_tax_paid = (
        account.ACCINT[account.INVTAX == 1]
        .groupby(account.person_id)
        .sum()
        .reindex(index=person.index)
        .fillna(0)
        * 52
        * 0.25
    )
    frs["dividend_income"] = (
        account.ACCINT[account.ACCOUNT.isin(DIVIDEND_ACCOUNTS)]
        .groupby(account.person_id)
        .sum()
        .reindex(index=person.index)
        .fillna(0)
        * 52
        + dividend_tax_paid
    )
    savings_interest_tax_paid = (
        account.ACCINT[account.ACCTAX == 1]
        .groupby(account.person_id)
        .sum()
        .reindex(index=person.index)
        .fillna(0)
        * 52
        * 0.25
    )
    frs["savings_interest_income"] = (
        account.ACCINT.groupby(account.person_id)
        .sum()
        .reindex(index=person.index)
        .fillna(0)
        * 52
        + savings_interest_tax_paid
        - frs["dividend_income"]
    )
    is_head = person.HRPID == 1
    frs["property_income"] = (
        is_head
        * (
            pd.Series(
                (household.TENTYP2.isin((5, 6)) * household.SUBRENT)[
                    person.household_id
                ].values,
                index=person.index,
            ).fillna(0)
        )
        + person.CVPAY
        + person.ROYYR1
    ) * 52

    frs["maintenance_income"] = (
        max_(where(person.MNTUS1 == 2, person.MNTUSAM1, person.MNTAMT1), 0)
        + max_(where(person.MNTUS2 == 2, person.MNTUSAM2, person.MNTAMT2), 0)
    ) * 52

    frs["miscellaneous_income"] = (
        oddjob.OJAMT[oddjob.OJNOW == 1]
        .groupby(oddjob.person_id)
        .sum()
        .reindex(person.index)
        .fillna(0)
        + person.ALLPAY2
        + person.ROYYR2
        + person.ROYYR3
        + person.ROYYR4
        + person.CHAMTERN
        + person.CHAMTTST
    ) * 52

    frs["private_transfer_income"] = (
        person[
            ["APAMT", "APDAMT", "PAREAMT", "ALLPAY1", "ALLPAY3", "ALLPAY4"]
        ].sum(axis=1)
    ) * 52

    frs["lump_sum_income"] = person.REDAMT


def add_benefit_income(
    frs: h5py.File,
    person: DataFrame,
    benefits: DataFrame,
    household: DataFrame,
):
    """Adds benefit variables.

    Args:
        frs (h5py.File)
        person (DataFrame)
        benefits (DataFrame)
        household (DataFrame)
    """
    BENEFIT_CODES = dict(
        child_benefit=3,
        income_support=19,
        housing_benefit=94,
        AA=12,
        DLA_SC=1,
        DLA_M=2,
        IIDB=15,
        carers_allowance=13,
        SDA=10,
        AFCS=8,
        maternity_allowance=21,
        pension_credit=4,
        child_tax_credit=91,
        working_tax_credit=90,
        state_pension=5,
        winter_fuel_allowance=62,
        incapacity_benefit=17,
        universal_credit=95,
        PIP_M=97,
        PIP_DL=96,
    )

    for benefit, code in BENEFIT_CODES.items():
        frs[benefit + "_reported"] = (
            benefits.BENAMT[benefits.BENEFIT == code]
            .groupby(benefits.person_id)
            .sum()
            .reindex(index=person.index)
            .fillna(0)
            .values
            * 52
        )

    frs["BSP_reported"] = (
        benefits.BENAMT[benefits.BENEFIT.isin((6, 9))]
        .groupby(benefits.person_id)
        .sum()
        .reindex(index=person.index)
        .fillna(0)
        .values
        * 52
    )

    frs["winter_fuel_allowance_reported"][...] = (
        np.array(frs["winter_fuel_allowance_reported"]) / 52
    )

    frs["SSP_reported"] = person.SSPADJ * 52

    frs["student_loans"] = person.TUBORR

    frs["student_payments"] = person[["ADEMAAMT", "CHEMAAMT", "ACCSSAMT"]].sum(
        axis=1
    ) * 52 + person[["GRTDIR1", "GRTDIR2"]].sum(axis=1)

    frs["council_tax_benefit_reported"] = (
        (person.HRPID == 1)
        * pd.Series(
            household.CTREBAMT[person.household_id].values, index=person.index
        ).fillna(0)
        * 52
    )


def add_expenses(
    frs: h5py.File,
    person: DataFrame,
    household: DataFrame,
    maintenance: DataFrame,
    mortgage: DataFrame,
    childcare: DataFrame,
    pen_prov: DataFrame,
):
    """Adds expense variables

    Args:
        frs (h5py.File)
        person (DataFrame)
        household (DataFrame)
        maintenance (DataFrame)
        mortgage (DataFrame)
        childcare (DataFrame)
        pen_prov (DataFrame)
    """
    frs["maintenance_expenses"] = (
        pd.Series(
            np.where(
                maintenance.MRUS == 2, maintenance.MRUAMT, maintenance.MRAMT
            )
        )
        .groupby(maintenance.person_id)
        .sum()
        .reindex(person.index)
        .fillna(0)
        * 52
    )

    frs["housing_costs"] = (
        np.where(
            household.GVTREGNO != 13, household.GBHSCOST, household.NIHSCOST
        )
        * 52
    )
    frs["rent"] = household.HHRENT * 52
    frs["mortgage_interest_repayment"] = household.MORTINT * 52
    mortgage_capital = np.where(
        mortgage.RMORT == 1, mortgage.RMAMT, mortgage.BORRAMT
    )
    mortgage_capital_repayment = (
        (mortgage_capital / mortgage.MORTEND)
        .groupby(mortgage.household_id)
        .sum()
        .reindex(household.index)
        .fillna(0)
    )
    frs["mortgage_capital_repayment"] = mortgage_capital_repayment

    frs["childcare_expenses"] = (
        childcare.CHAMT[childcare.COST == 1][childcare.REGISTRD == 1]
        .groupby(childcare.person_id)
        .sum()
        .reindex(person.index)
        .fillna(0)
    ) * 52

    frs["private_pension_contributions"] = (
        pen_prov.PENAMT[pen_prov.STEMPPEN.isin((5, 6))]
        .groupby(pen_prov.person_id)
        .sum()
        .reindex(person.index)
        .fillna(0)
        .clip(0, pen_prov.PENAMT.quantile(0.95))
        * 52
    )
    frs["employer_pension_contributions"] = (
        pen_prov.PENAMT[pen_prov.STEMPPEN.isin((1, 2, 3, 4))]
        .groupby(pen_prov.person_id)
        .sum()
        .reindex(person.index)
        .fillna(0)
        * 52
    )

    frs["housing_service_charges"] = (
        pd.DataFrame(
            [
                household[f"CHRGAMT{i}"] * (household[f"CHRGAMT{i}"] > 0)
                for i in range(1, 10)
            ]
        ).sum()
        * 52
    )
    frs["water_and_sewerage_charges"] = (
        np.where(
            household.GVTREGNO == 12,
            household.CSEWAMT + household.CWATAMTD,
            household.WATSEWRT,
        )
        * 52
    )


def add_benunit_variables(frs: h5py.File, benunit: DataFrame):
    frs["benunit_rent"] = benunit.BURENT
