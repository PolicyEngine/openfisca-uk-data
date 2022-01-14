from openfisca_uk_data.datasets import *
from pathlib import Path
from openfisca_uk_data.utils import VERSION

REPO = Path(__file__).parent


DATASETS = (
    FRS,
    SynthFRS,
    FRS_SPI_Adjusted,
    FRS_WAS_Imputation,
    FRSEnhanced,
    SPI,
    RawLCF,
)
