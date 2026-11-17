"""Frame clock for the closing scenes: propane storage, the plan-view cooling loop, the section,
and the pod and cooler replacement that ends the film.

Times are frames after the pod store is full. The plan-view scene is as long as its narration.
"""
import json
import math
from pathlib import Path

from . import design as cfg
from . import clock
from . import film

FPS=24
FADE=18
NARRATION=Path(__file__).resolve().parents[1]/"audio"/"plan_view.json"
VOICE_LEAD,VOICE_TAIL=1.2,2.0
if NARRATION.is_file() and not film.SHORT:
    VOICE=json.loads(NARRATION.read_text(encoding="utf-8"))
else:
    VOICE={"duration":26.0,"lines":[]}
COUNT=cfg.PROJECT["fuel"]["tanks"]
if film.SHORT:
    # The tanks arrive on day 8, while the pods are loading. The lines follow once the lid is on.
    FUEL=film.FUEL_CUT[0]-film.LOADING
    TANKS=FUEL+24
    TANK_STEP=24
    TANK_SETTLE=44
    FUEL_CUT_END=film.FUEL_CUT[1]-film.LOADING
    LINE=clock.LINES
else:
    FUEL=clock.ORBIT_DONE+24
    TANKS=FUEL+56
    # One tank truck arrives every TANK_STEP frames. Each tank is on its saddles TANK_SETTLE frames after its truck stops.
    TANK_STEP=36
    TANK_SETTLE=TANK_STEP-2
    LINE=TANKS+COUNT*TANK_STEP+8
HEADER=(LINE,LINE+20)
RUN=(LINE+20,LINE+62)
RISER=(LINE+62,LINE+104)
ROOF=(LINE+104,LINE+128)
DROP=(LINE+128,LINE+150)
FUEL_END=DROP[1]+(36 if film.SHORT else 64)
if film.SHORT:
    # The closing scene: plan and section side by side, with no voice-over.
    PLAN=clock.ORBIT_DONE+20
    PLAN_FRAMES=456
    SECTION=PLAN+PLAN_FRAMES
    SECTION_FRAMES=0
    END=SECTION
    # There is no replacement scene and no second cutaway.
    REPAIR=END+10**5
    REPAIR_FRAMES=0
    FINAL=(REPAIR+10**5,REPAIR+10**5+39)
else:
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
