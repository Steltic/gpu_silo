"""Cooler service during the pod exchange.

The retained crawler lowers one cooler frame to the ground, a cooler is drawn
out and replaced, and the frame is hung back on its seats. Times are frames
after the start of the pod exchange. Station coordinates are X from the silo
axis along the frame's bearing, Y along the wall and Z up.
"""
import math

from . import cooler_frames as fr
from . import design as cfg
from . import maintenance as care
from . import silo_model as s

K=cfg.SERVICE["cooler_service_frame"]-1
ROW=cfg.SERVICE["cooler_service_row"]-1
THETA=fr.BEARINGS[K]
BASE=fr.base(K)
REST=ROW*fr.ROW+.15
ARRIVE=290
RIG=(330,348)
LIFT=(366,382)
OUT=(382,420)
DOWN=(420,472)
FREE=478
SLIDE=(482,504)
TAKE=(506,524)
SET=(524,566)
DROP=572
FETCH=(574,606)
RAISE=(612,662)
BRING=(662,694)
INSERT=(698,726)
RETURN=(728,752)
HOIST=(758,816)
IN=(816,852)
SEAT=(852,868)
RELEASE=874
DONE=904
LEAVE=(906,1036)
GONE=1040
PULL,PARK_OLD,PARK_NEW=3.3,6.15,9.25
FLOOR=.30
CENTRE=(fr.COOL_X0+fr.COOL_X1)/2
SLING=1.9
AWAY=82.
# The crawler stands back from its track so the coolers on the ground stay outside its minimum radius.
STAND=fr.TRACK_R+7.
OFF,ON=(0,0,0),(1,1,1)


def world(x,y,z):
    co,si=math.cos(THETA),math.sin(THETA)
    return (x*co-y*si,x*si+y*co,z)


def frame(w):
    """Radius of the frame's back plane and elevation of its base."""
    radius=fr.BACK+(fr.LAY_R-fr.BACK)*(s.step(*OUT,w)-s.step(*IN,w))
    z=BASE+fr.OVER*s.step(*LIFT,w)+(fr.GROUND-BASE-fr.OVER)*s.step(*DOWN,w)
    z+=(BASE+fr.OVER-fr.GROUND)*s.step(*HOIST,w)-fr.OVER*s.step(*SEAT,w)
    return radius,z


def old_cooler(w):
    """Offset of the withdrawn cooler from its bay: outward and up."""
    out=PULL*s.step(*SLIDE,w)+(PARK_OLD-PULL)*s.step(*TAKE,w)
    up=.4*s.step(TAKE[0],TAKE[0]+8,w)+(FLOOR-fr.GROUND-REST-.4)*s.step(*SET,w)
    return out,up


def new_cooler(w):
    down=FLOOR-fr.GROUND-REST
    out=PARK_NEW+(PULL-PARK_NEW)*s.step(*BRING,w)-PULL*s.step(INSERT[0]+6,INSERT[1],w)
    up=down+(.4-down)*s.step(*RAISE,w)-.4*s.step(INSERT[0],INSERT[0]+6,w)
    return out,up


def lugs(w):
    radius,z=frame(w)
    return (radius+fr.DEPTH/2,0,z+fr.HEIGHT+fr.SLING)


def cooler_pick(offset):
    out,up=offset
    return (fr.LAY_R+out+CENTRE,fr.COOL_Y,fr.GROUND+REST+up+fr.COOL_H+SLING)


def glide(w,start,end,a,b,rise=1.6):
    q=s.step(start,end,w)
    return tuple(p+(v-p)*q for p,v in zip(a,b))[:2]+(a[2]+(b[2]-a[2])*q+rise*math.sin(math.pi*q),)


def hook(w):
    """Hook in station coordinates."""
    if w<RIG[1]:
        x,y,z=lugs(w)
        return x,y,z+6*(1-s.step(*RIG,w))
    if w<FREE:return lugs(w)
    if w<TAKE[0]:return glide(w,FREE,TAKE[0]-2,lugs(w),cooler_pick(old_cooler(TAKE[0])))
    if w<DROP:return cooler_pick(old_cooler(w))
    if w<RAISE[0]:return glide(w,DROP,FETCH[1],cooler_pick(old_cooler(DROP)),cooler_pick(new_cooler(RAISE[0])))
    if w<INSERT[0]+8:return cooler_pick(new_cooler(w))
    if w<RETURN[1]+4:return glide(w,INSERT[0]+8,RETURN[1],cooler_pick(new_cooler(INSERT[0]+8)),lugs(RETURN[1]))
    if w<RELEASE:return lugs(w)
    x,y,z=lugs(w)
    return x,y,z+6*s.step(RELEASE,DONE,w)


def crane(w):
    """World position of the crawler and its hook, and the crawler heading."""
    gone=s.step(*LEAVE,w)
    radius=STAND+(AWAY-STAND)*gone
    x,y,z=hook(min(w,DONE))
    return s.polar(radius,THETA,0),world(x+(AWAY-STAND)*gone,y,z),THETA+math.pi/2


def phase(w):
    if w<RIG[1]:return "Rig the frame"
    if w<DOWN[1]:return "Lower the frame to the ground"
    if w<DROP:return "Withdraw the cooler"
    if w<INSERT[1]:return "Fit the replacement"
    if w<RELEASE:return "Hang the frame back"
    return "Frame back in service"


def install(scene,node,p):
    begin=p.FILLED+care.REPAIR
    info=scene.cooler_frames[K];label=f"Cooler frame {K+1:02}"
    def window(start,end=None):
        keys=[(begin+start-.02,OFF),(begin+start,ON)]
        if end is not None:keys.extend([(begin+end-.02,ON),(begin+end,OFF)])
        return keys
    def curve(start,end,fn):
        values=[fn(w) for w in range(start,end+1)]
        return [(begin+start+k,v) for k,v in p.flat_keys(values)]
    root=scene.nodes[info["root"]]
    def seat(w):
        radius,z=frame(w)
        return s.polar(radius,THETA,z)
    root["tracks"]["translation"]=root["tracks"]["translation"]+curve(LIFT[0],SEAT[1],seat)
    scene.nodes[info["slings"]]["tracks"]["scale"]+=window(RIG[1],FREE)+window(RETURN[1],RELEASE)
    reach=info["reach"]
    scene.nodes[info["spools"]]["tracks"]["scale"]+=[(begin+RIG[0],(reach,1,1)),(begin+RIG[1],(.001,1,1)),(begin+RIG[1]+.02,OFF),
        (begin+RELEASE-.02,OFF),(begin+RELEASE,(.001,1,1)),(begin+DONE-4,(reach,1,1))]
    node(label+" | service dunnage",scene.mesh(fr.dunnage_mesh()),"Frame laydown",ang=THETA,t=s.polar(fr.LAY_R,THETA,0),
         tracks={"scale":[(0,OFF)]+window(ARRIVE,GONE)})
    old=scene.nodes[info["coolers"][ROW]];mesh_id=old["mesh"]
    def drawn(w):
        out,up=old_cooler(w)
        return (out,fr.COOL_Y,REST+up)
    old["tracks"]["translation"]=[(0,(0,fr.COOL_Y,REST))]+curve(SLIDE[0],SET[1],drawn)
    old["tracks"]["scale"]=[(0,ON),(begin+DROP-.02,ON),(begin+DROP,OFF)]
    rig=p.newsteel("Cooler pick | two-leg sling")
    top=fr.COOL_H+SLING
    for y in (-fr.COOL_L*.3,fr.COOL_L*.3):
        s.bar(rig,(CENTRE,y,fr.COOL_H),(CENTRE,0,top),.05,"80765c")
    rig_id=scene.mesh(rig)
    node(label+f" | cooler {ROW+1} | withdrawal sling",rig_id,"Frame rigging",info["coolers"][ROW],
         tracks={"scale":[(0,OFF)]+window(TAKE[0]-2,DROP)})
    out,up=old_cooler(DROP)
    node(label+f" | cooler {ROW+1} | withdrawn unit on the ground",mesh_id,"Service coolers",ang=THETA,
         t=world(fr.LAY_R+out,fr.COOL_Y,fr.GROUND+REST+up),tracks={"scale":[(0,OFF)]+window(DROP,GONE)})
    def carried(w):
        out,up=new_cooler(w)
        return world(fr.LAY_R+out,fr.COOL_Y,fr.GROUND+REST+up)
    fresh=node(label+f" | replacement cooler {ROW+1}",mesh_id,"Service coolers",ang=THETA,
               tracks={"translation":[(0,carried(0))]+curve(RAISE[0],INSERT[1],carried),"scale":[(0,OFF)]+window(ARRIVE,INSERT[1])})
    node(label+f" | replacement cooler {ROW+1} | sling",rig_id,"Frame rigging",fresh,
         tracks={"scale":[(0,OFF)]+window(FETCH[1],INSERT[0]+8)})
    node(label+f" | cooler {ROW+1} | replacement in its bay",mesh_id,"Dry coolers",info["root"],t=(0,fr.COOL_Y,REST),
         tracks={"scale":[(0,OFF)]+window(INSERT[1])})
    scene.project_info.update(coolerServiceFrame=K+1,coolerServiceRow=ROW+1,
        coolerServiceStart_s=(begin+ARRIVE)/p.FPS,coolerServiceEnd_s=(begin+DONE)/p.FPS)
