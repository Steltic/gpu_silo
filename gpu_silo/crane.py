"""One crawler crane for the whole job.

After the tandem cage lift the south crawler stays. It hangs the cooler frames,
lowers the power modules and the lid, and comes back for the cooler service
during the pod exchange. This module joins those lifts into one continuous path.
"""
import math

from . import cooler_frames as fr
from . import maintenance as care
from . import plant
from . import service
from . import silo_model as s


def _transit(f,start,end,a,b):
    """Track from one working position to the next with the hook carried high."""
    q=s.step(start,end,f)
    (ax,ay,_),ahook,_=a;(bx,by,_),bhook,_=b
    r0,r1=math.hypot(ax,ay),math.hypot(bx,by)
    t0=math.atan2(ay,ax);turn=(math.atan2(by,bx)-t0+math.pi)%(2*math.pi)-math.pi
    foot=s.polar(r0+(r1-r0)*q,t0+turn*q,0)
    hook=tuple(u+(v-u)*q for u,v in zip(ahook,bhook))
    hook=(hook[0],hook[1],hook[2]+5*math.sin(math.pi*q))
    return foot,hook,math.atan2(foot[1],foot[0])+math.pi/2


def poses(p):
    """Foot, hook and heading of the retained crawler for every frame from the pod delivery to its departure."""
    def frames(f):
        foot,hook,_,heading=fr.crane(f)
        return foot,hook,heading
    def power(f):
        base=plant.CRANE_BASE
        return base,plant.hook_position(p.CROWN,f-p.FILLED),math.atan2(base[1],base[0])+math.pi/2
    def cooler(f):
        return service.crane(f-p.FILLED-care.REPAIR)
    picks=p.FILLED+plant.PICK_STARTS[0]-2
    lidded=p.FILLED+plant.LID[1]+30
    parked=lidded+150
    serving=p.FILLED+care.REPAIR+service.ARRIVE
    result={}
    for f in range(fr.START,p.FRAMES):
        if f<=fr.END:pose=frames(f)
        elif f<picks:pose=_transit(f,fr.END,picks,frames(fr.END),power(picks))
        elif f<=lidded:pose=power(f)
        elif f<serving:pose=_transit(f,lidded,parked,power(lidded),cooler(serving))
        else:pose=cooler(f)
        result[f]=pose
    return result,p.FILLED+care.REPAIR+service.GONE
