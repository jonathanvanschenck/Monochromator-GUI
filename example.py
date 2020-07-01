#%%
from monochromator.monochromator import Monochromator
from monochromator.calibrate import Calibrate

# Instantiate monochromator instance
try:
    mono.close()
except:
    pass
mono = Monochromator()

# Launch calibration GUI
Calibrate(mono)
