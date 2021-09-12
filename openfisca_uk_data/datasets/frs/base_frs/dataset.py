from openfisca_uk_data.datasets.frs.base_frs.model_input_variables import (
    from_BaseFRS,
)
from openfisca_uk_data.utils import dataset, UK
import pandas as pd
import numpy as np
import warnings
from openfisca_uk_data.datasets.frs.raw_frs import RawFRS
import h5py
from tqdm import tqdm


@dataset
class BaseFRS:
    name = "base_frs"
    model = UK
    input_reform_from_year = from_BaseFRS

    def generate(year):
        raw_frs_files = RawFRS.load(year)
        tables = (
            "adult",
            "child",
            "accounts",
            "benefits",
            "job",
            "benunit",
            "househol",
            "chldcare",
            "pension",
        )
        (
            frs_adult,
            frs_child,
            frs_accounts,
            frs_benefits,
            frs_job,
            frs_benunit,
            frs_household,
            frs_childcare,
            frs_pension,
        ) = [raw_frs_files[table] for table in tables]
        person = frs_adult.drop(["AGE"], axis=1)
        person["role"] = "adult"

        get_new_columns = lambda df: list(
            df.columns.difference(person.columns)
        ) + ["person_id"]
        person = pd.merge(
            person,
            frs_child[get_new_columns(frs_child)],
            how="outer",
            on="person_id",
        ).sort_values("person_id")

        person["role"].fillna("child", inplace=True)

        # link capital income sources (amounts summed by account type)

        accounts = (
            frs_accounts[get_new_columns(frs_accounts)]
            .groupby(["person_id", "ACCOUNT"])
            .sum()
            .reset_index()
        )
        accounts = accounts.pivot(index="person_id", columns="ACCOUNT")[
            ["ACCINT"]
        ].reset_index()
        accounts.columns = accounts.columns.get_level_values(1)
        accounts = accounts.add_prefix("ACCINT_ACCOUNT_CODE_").reset_index()
        person = pd.merge(
            person,
            accounts,
            how="outer",
            left_on="person_id",
            right_on="ACCINT_ACCOUNT_CODE_",
        )

        # link benefit income sources (amounts summed by benefit program)

        bens = frs_benefits[get_new_columns(frs_benefits)]

        # distinguish income-related JSA and ESA from contribution-based variants

        bonus_to_IB_benefits = 1000 * (
            bens.VAR2.isin((2, 4)) & bens.BENEFIT.isin((14, 16))
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bens["BENEFIT"] += bonus_to_IB_benefits
        benefits = bens.groupby(["person_id", "BENEFIT"]).sum().reset_index()
        benefits = benefits.pivot(index="person_id", columns="BENEFIT")[
            ["BENAMT"]
        ].reset_index()
        benefits.columns = benefits.columns.get_level_values(1)
        benefits = benefits.add_prefix("BENAMT_BENEFIT_CODE_").reset_index()
        person = pd.merge(
            person,
            benefits,
            how="outer",
            left_on="person_id",
            right_on="BENAMT_BENEFIT_CODE_",
        )

        # link job-level data (all fields summed across all jobs)

        job = (
            frs_job[get_new_columns(frs_job)]
            .groupby("person_id")
            .sum()
            .reset_index()
        )
        person = pd.merge(person, job, how="outer", on="person_id").fillna(0)

        person["benunit_id"] = person["person_id"] // 1e1
        person["household_id"] = person["person_id"] // 1e2

        childcare = (
            frs_childcare[get_new_columns(frs_childcare)]
            .groupby("person_id")
            .sum()
            .reset_index()
        )
        person = pd.merge(
            person, childcare, how="outer", on="person_id"
        ).fillna(0)
        childcare_cost = (
            frs_childcare[frs_childcare.COST == 1][frs_childcare.REGISTRD == 1]
            .groupby("person_id")
            .CHAMT.sum()
            * 52
        )
        person = person.add_prefix("P_")
        person = pd.merge(
            person,
            childcare_cost.to_frame(name="childcare_cost")
            .reset_index()
            .rename(columns={"person_id": "P_person_id"}),
            how="outer",
            on="P_person_id",
        ).fillna(0)

        # generate benefit unit and household datasets

        benunit = frs_benunit.fillna(0).add_prefix("B_")

        # attach pension income (many pensions to one person)

        def add_pension_income(df):
            # following UKMOD DRD
            return (
                df.PENPAY[df.PENPAY > 0].sum()
                + df.PTAMT[(df.PTINC == 2) & (df.PTAMT > 0)].sum()
                + df.POAMT[
                    ((df.POINC == 2) | (df.PENOTH == 1)) & (df.POAMT > 0)
                ].sum()
            ) * 52

        pension_income_df = (
            pd.DataFrame(
                dict(
                    pension_income=frs_pension[
                        [
                            "person_id",
                            "PENPAY",
                            "PTAMT",
                            "PTINC",
                            "PENOTH",
                            "POAMT",
                            "POINC",
                        ]
                    ]
                    .groupby("person_id")
                    .apply(add_pension_income)
                )
            )
            .reset_index()
            .rename(columns={"person_id": "P_person_id"})
        )

        person = pd.merge(
            person, pension_income_df, how="outer", on="P_person_id"
        ).fillna(0)

        # Council Tax is severely under-reported in the micro-data - find
        # mean & std for each (region, CT band) pair and sample from distribution.
        # rows with missing regions or CT bands are sampled from the same distributions, respectively

        CT_mean = frs_household.groupby(
            ["GVTREGNO", "CTBAND"], dropna=False
        ).CTANNUAL.mean()
        CT_std = frs_household.groupby(
            ["GVTREGNO", "CTBAND"], dropna=False
        ).CTANNUAL.std()
        pairs = frs_household.set_index(["GVTREGNO", "CTBAND"])
        hh_CT_mean = CT_mean[pairs.index].values
        hh_CT_std = CT_std[pairs.index].values
        ct = np.random.randn(len(pairs)) * hh_CT_std + hh_CT_mean
        household = frs_household.fillna(0).add_prefix("H_")
        household.H_CTANNUAL = np.where(
            household.H_CTANNUAL == 0, ct, household.H_CTANNUAL
        )
        average_CT = household.H_CTANNUAL.dropna().mean()
        household.fillna(average_CT, inplace=True)

        raw_frs_files.close()

        # store dataset for future use
        year = int(year)

        with h5py.File(BaseFRS.file(year), mode="w") as f:
            for entity in (person, benunit, household):
                for variable in entity.columns:
                    try:
                        f[f"{variable}/{year}"] = entity[variable].values
                    except:
                        f[f"{variable}/{year}"] = entity[
                            variable
                        ].values.astype("S")
