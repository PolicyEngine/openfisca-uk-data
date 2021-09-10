from openfisca_uk_data import BaseFRS, FRS
from openfisca_uk import Microsimulation

# Assumes that the RawFRS dataset is available, and runs tests
# on the FRS dataset generated.

BaseFRS.generate(2018)
FRS.generate(2018)

baseline = Microsimulation(dataset=FRS)
