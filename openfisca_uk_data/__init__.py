from openfisca_uk_data.datasets import *
from pathlib import Path
from openfisca_uk_data.utils import VERSION

REPO = Path(__file__).parent


DATASETS = (
    RawFRS,
    UKMODInput,
    UKMODOutput,
    FRS,
    SynthFRS,
    RawSPI,
    SPI,
    FRS_SPI_Adjusted,
    FRS_WAS_Imputation,
    RawWAS,
    RawLCF,
    FRSEnhanced,
)
