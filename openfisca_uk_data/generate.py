from openfisca_uk_data import (
    RawFRS,
    RawWAS,
    FRS,
    FRS_WAS_Imputation,
    FRSEnhanced,
)
from openfisca_uk_data.datasets.lcf.raw_lcf import RawLCF

print("Downloading WAS (2016)")
RawWAS.download(2016)
print("Downloading WAS (2019)")
RawLCF.download(2019)

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

print(f"Generating enhanced FRS (2019)")
FRSEnhanced.generate(2019)
print(f"Uploading enhanced FRS (2019)")
FRSEnhanced.upload(2019)
