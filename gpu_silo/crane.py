"""One crawler crane for the whole job.

After the tandem cage lift the south crawler stays. It hangs the cooler frames,
lowers the power modules and the lid, drives off, and comes back for the cooler
service during the pod exchange at the end. This module joins those lifts into one continuous path.
"""
import math

from . import clock
from . import cooler_frames as fr
from . import film
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


AWAY=96.


def _clear(pose,radius=AWAY):
    """The same crawler with its hook carried, moved straight out to a given radius."""
    (x,y,_),(hx,hy,hz),heading=pose
    r=math.hypot(x,y);k=radius/r
    return (x*k,y*k,0),(hx+x*(k-1),hy+y*(k-1),max(hz,24.)),heading


def poses(p,cage_release):
    """Foot, hook and heading of the crawler, and the two spans of frames in which it is on site.

    It stays from the cage lift until the lid is on, drives off, and comes back for the cooler service.
    """
    def frames(f):
        foot,hook,_,heading=fr.crane(f)
        return foot,hook,heading
    def power(f):
        base=plant.CRANE_BASE
        return base,plant.hook_position(p.CROWN,f-p.FILLED),math.atan2(base[1],base[0])+math.pi/2
    def support(f):
        base=plant.CRANE_BASE
        x,y,z=plant.rig_position(p.CROWN,f)
        return base,(x,y,z+plant.APEX),math.atan2(base[1],base[0])+math.pi/2
    def cooler(f):
        return service.crane(f-p.FILLED-care.REPAIR)
    picks=p.FILLED+plant.PICK_STARTS[0]-2
    lidded=p.FILLED+plant.LID[1]+12
    gone=lidded+110
    serving=p.FILLED+care.REPAIR+service.ARRIVE
    back=serving-120
    if film.SHORT:back=serving=p.FRAMES+10    # the short film ends before any service visit
    result={}
    release=clock.RIG_PICK+plant.PICK_LENGTH+3
    for f in range(clock.CAGE_END,p.FRAMES):
        if f<clock.RIG_PICK:pose=_transit(f,clock.CAGE_END,clock.RIG_PICK,cage_release,support(clock.RIG_PICK))
        elif f<=release:pose=support(f)
        elif f<fr.START:
            a,b=support(release),frames(fr.START)
            foot,_,heading=_transit(f,release,fr.START,a,b)
            pose=foot,plant.empty_hook(a[1],b[1],(f-release)/(fr.START-release)),heading
        elif f<=fr.END:pose=frames(f)
        elif f<picks:pose=_transit(f,fr.END,picks,frames(fr.END),power(picks))
        elif f<=lidded:pose=power(f)
        elif f<back:
            q=s.step(lidded,gone,f);a=power(lidded);b=_clear(a)
            pose=(tuple(u+(v-u)*q for u,v in zip(a[0],b[0])),tuple(u+(v-u)*q for u,v in zip(a[1],b[1])),a[2])
        elif f<serving:
            q=s.step(back,serving-8,f);b=cooler(serving);a=_clear(b)
            pose=(tuple(u+(v-u)*q for u,v in zip(a[0],b[0])),tuple(u+(v-u)*q for u,v in zip(a[1],b[1])),b[2])
        else:pose=cooler(f)
        result[f]=pose
    return result,(gone,back,p.FILLED+care.REPAIR+service.GONE)
