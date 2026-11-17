"""Frame clock for the closing scenes: propane storage, the plan-view cooling loop, the section,
and the pod and cooler replacement that ends the film.

Times are frames after the pod store is full. The plan-view scene is as long as its narration.
"""
import json
import math
from pathlib import Path

from . import design as cfg
from . import clock

FPS=24
FUEL=clock.ORBIT_DONE+24
TANKS=FUEL+56
# One tank truck arrives every TANK_STEP frames. Each tank is on its saddles TANK_STEP frames after its truck stops.
TANK_STEP=36
LINE=TANKS+cfg.PROJECT["fuel"]["tanks"]*TANK_STEP+8
HEADER=(LINE,LINE+20)
RUN=(LINE+20,LINE+62)
RISER=(LINE+62,LINE+104)
ROOF=(LINE+104,LINE+128)
DROP=(LINE+128,LINE+150)
FUEL_END=DROP[1]+64
FADE=18

NARRATION=Path(__file__).resolve().parents[1]/"audio"/"plan_view.json"
VOICE_LEAD,VOICE_TAIL=1.2,2.0
if NARRATION.is_file():
    VOICE=json.loads(NARRATION.read_text(encoding="utf-8"))
else:
    VOICE={"duration":26.0,"lines":[]}
PLAN=FUEL_END
PLAN_FRAMES=math.ceil((VOICE_LEAD+VOICE["duration"]+VOICE_TAIL)*FPS)
SECTION=PLAN+PLAN_FRAMES
SECTION_FRAMES=624
# The replacement scene is a cutaway again. The concrete returns for the last shot.
REPAIR=SECTION+SECTION_FRAMES
REPAIR_FRAMES=1212
FINAL=(REPAIR+REPAIR_FRAMES,REPAIR+REPAIR_FRAMES+39)
END=FINAL[1]+110


def captions():
    """Narration lines as (first frame, last frame, text), in frames after the store is full."""
    start=PLAN+round(VOICE_LEAD*FPS)
    return [(start+round(line["start"]*FPS),start+round(line["end"]*FPS),line["text"]) for line in VOICE["lines"]]
