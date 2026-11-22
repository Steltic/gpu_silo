"""Frame clock for the scenes between the cage lift and the first pod. 24 frames per second."""
from . import film
from . import silo_model as s

CAGE_END=s.FRAMES+352
RIG_PICK=CAGE_END+34
RIG_END=CAGE_END+204
if film.SHORT:
    # The dock follows the rig. The short film fills the store at the end of the build.
    STORE_FILL=(RIG_END+16,RIG_END+17)
    STORE_END=RIG_END+44
else:
    STORE_FILL=(RIG_END+16,RIG_END+126)
    STORE_END=RIG_END+168
DELIVERY_AT=STORE_END
DELIVERY_FRAMES=336
FIRST_POD=DELIVERY_AT+DELIVERY_FRAMES+8
# The cooler frames are hung while the pods are loaded. The first pick follows the first pod's dock.
FRAMES_FIRST=FIRST_POD+190

# After the store is full. These are frames after FILLED, the frame on which the last pod is docked.
POWER_DONE=470
LID=(POWER_DONE+10,POWER_DONE+128)
if film.SHORT:
    # Fuel lines after the lid, then the dock is enclosed as the control office, then the finished silo.
    LINES=LID[1]+24
    OFFICE=(LINES+196,LINES+330)
    CREW=OFFICE[1]+12
    NEVER=10**6
    ENCLOSURE_OPEN=(NEVER,NEVER+1)
    TURBINE_WORK=(NEVER,NEVER,NEVER,NEVER)
    ENCLOSURE_CLOSE=(NEVER,NEVER+1)
    SOLID_BEGIN,SOLID_END=CREW,CREW+39
    # Water tankers run from the last pod to the end of the closing orbit.
    WATER=(0,SOLID_END+24+456)
else:
    CREW=LID[1]+38
    # The enclosure of turbine set A opens and closes during the crew scene.
    ENCLOSURE_OPEN=(CREW+408,CREW+440)
    TURBINE_WORK=(CREW+444,CREW+470,CREW+574,CREW+598)
    ENCLOSURE_CLOSE=(CREW+606,CREW+640)
    SOLID_BEGIN,SOLID_END=CREW+746,CREW+785
ORBIT=SOLID_END+24
ORBIT_DONE=ORBIT+456
