from openfisca_uk_data.datasets import *
from pathlib import Path
from openfisca_uk_data.utils import VERSION

REPO = Path(__file__).parent


DATASETS = (
    RawFRS,
    FRS,
    SynthFRS,
    RawSPI,
    SPI,
    RawWAS,
    RawLCF,
    FRSEnhanced,
)
