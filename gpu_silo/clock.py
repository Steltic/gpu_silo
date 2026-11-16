"""Frame clock for the scenes between the cage lift and the first pod. 24 frames per second."""
from . import silo_model as s

CAGE_END=s.FRAMES+352
STORE_FILL=(CAGE_END+16,CAGE_END+126)
STORE_END=CAGE_END+168
DELIVERY_AT=STORE_END
DELIVERY_FRAMES=336
FIRST_POD=DELIVERY_AT+DELIVERY_FRAMES+8
# The cooler frames are hung while the pods are loaded. The first pick follows the first pod's dock.
FRAMES_FIRST=FIRST_POD+190
