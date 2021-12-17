from openfisca_uk_data.datasets import *
from pathlib import Path

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
