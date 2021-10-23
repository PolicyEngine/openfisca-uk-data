from openfisca_uk_data import RawFRS, RawWAS, FRS, FRS_WAS_Imputation

for year in (2018, 2019):
    print(f"Downloading raw FRS ({year})")
    RawFRS.download(year)
    print(f"Generating FRS ({year})")
    FRS.generate(year)
    print(f"Uploading FRS ({year})")
    FRS.upload(year)

print(f"Generating WAS-adjusted FRS (2019)")
FRS_WAS_Imputation.generate(2019)
print(f"Uploading WAS-adjusted FRS (2019)")
FRS_WAS_Imputation.upload(2019)
