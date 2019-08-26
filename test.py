#%%
from monochromator import Monochromator
#%
try:
    mono.close()
except:
    pass
mono = Monochromator()

#%%
from calibrate import Calibrate
Calibrate(mono)