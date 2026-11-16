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

# After the store is full. These are frames after FILLED, the frame on which the last pod is docked.
POWER_DONE=536
LID=(POWER_DONE+10,POWER_DONE+128)
CREW=LID[1]+38
# The turbine enclosure on the lower power module opens and closes during the crew scene.
ENCLOSURE_OPEN=(CREW+408,CREW+440)
TURBINE_WORK=(CREW+444,CREW+470,CREW+574,CREW+598)
ENCLOSURE_CLOSE=(CREW+606,CREW+640)
SOLID_BEGIN,SOLID_END=CREW+746,CREW+785
DOOR=(SOLID_END+34,SOLID_END+82)
ROOF=(SOLID_END+124,SOLID_END+180)
ORBIT=SOLID_END+204
ORBIT_DONE=ORBIT+456
