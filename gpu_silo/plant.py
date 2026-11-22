"""The two power levels above the pods and the lid that closes the silo.

The lower level carries the backup diesel sets and their day tanks. The upper level carries two in-line
gas turbine generator sets side by side. Each level is lowered through the open top as one assembly.
One turbine enclosure has a side that folds down to a work floor. The lid arrives with the exhaust
stacks, air inlet houses and diesel vents already on it.

Coordinates are metres and Z is up.
"""
from . import design as cfg
from . import film

import math

from . import services
from . import silo_model as s
from . import clock
from . import closing
from . import maintenance as care
from . import crew


P, D = cfg.POWER, cfg.PROJECT["diesel"]
# One in-line turbine generator set, and the names the rest of the model uses for it.
SET_L, SET_W, SET_H = P["set_length_m"], P["set_width_m"], P["set_height_m"]
LENGTH, WIDTH, HEIGHT = SET_L, SET_W, SET_H
AISLE = P["aisle_m"]
SET_Y = AISLE/2+SET_W/2
GEN_L, GEN_W, GEN_H = D["set_length_m"], D["set_width_m"], D["set_height_m"]
DECK = P["floor_structure_m"]
LEVEL = (GEN_H+DECK, SET_H+DECK)
# Level coordinates: X along the turbine sets, Y toward the crew wedge that reaches the turbine level.
# The diesel sets leave that wedge clear so its work deck can pass.
GEN_AT = ((0.,-.6,0),(-5.65,-.4,90),(0.,-4.9,0),(5.65,-.4,90))[:D["sets"]]
DAY_TANKS = ((3.2,3.2),(-3.2,3.2))[:D["day_tanks"]]
ACCESS_HALF = math.radians(26)
EXHAUST_R, EXHAUST_H = P["exhaust_stack_diameter_m"]/2, P["exhaust_stack_height_m"]
EXHAUST_AT = ((.6,SET_Y),(.6,-SET_Y))
INLET_HOUSE = tuple(P["inlet_house_m"])
INLET_AT = ((-5.9,SET_Y),(-5.9,-SET_Y))
DIESEL_STACK_R, DIESEL_STACK_H = D["exhaust_stack_diameter_m"]/2, D["exhaust_stack_height_m"]
DIESEL_STACKS = ((-5.65,-4.6),(5.65,-4.6),(2.9,-5.3),(-2.9,0.))[:D["sets"]]
ROOM_VENT = tuple(D["room_vent_m"])
ROOM_VENTS = ((4.6,5.6),(-6.0,5.0))[:D["room_vents"]]
STACK_X, STACK_R = EXHAUST_AT[0][0], EXHAUST_R
POWER_YAW = math.radians(P["first_heading_degrees"])
PICK_STARTS = (50, 290)
PICK_LENGTH = 151
# After the second level is seated the crane goes for the lid.
VENT_START, VENT_END, END = PICK_STARTS[1]+PICK_LENGTH+4, care.POWER_DONE, closing.END
LID_THICK = .22
VENT_RISE = .03+LID_THICK+EXHAUST_H
LID = care.LID
LID_SITE = (-46.,-30.)
LID_R = s.RO+.14
LID_Z = s.WALL_HEIGHT+.03
LID_GROUND, LID_TRANSIT, LID_APEX = .30, s.WALL_HEIGHT+4.5, EXHAUST_H+3.6
PICK_SITES = ((-26.,-12.),(-26.,8.))
CRANE_BASE = (-20.,-23.,0.)
TRANSIT = 35.
GROUND = .36
APEX = SET_H+5.5
ON, OFF = (1.,1.,1.), (0.,0.,0.)
STRUCT, SILVER = "4c6266", "c4c9be"
AMBER, DARK = "db9955", "32484e"


def mesh(name):
    item=s.Mesh(name)
    item.material=3
    return item


def closed(m,x0,y0,x1,y1,z0,z1,color):
    s.box(m,x0,y0,x1,y1,z0,z1,color)
    m.face([(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0)],color)


def both(m,points,color):
    m.face(points,color)
    m.face(points[::-1],color)


PAINT=("748d83","9e927a")
RIB=("9cada1","bbad94")
# The outer side of turbine set A is hinged at floor level over part of its length.
PANEL_X=(-4.9,.5)
HINGE_Y,HINGE_Z=SET_Y+SET_W/2-.06,.14
PANEL_HEIGHT=2.5
PANEL_POSES=13


def turned(x,y,z=0.):
    """Level coordinates to silo coordinates."""
    c,q=math.cos(POWER_YAW),math.sin(POWER_YAW)
    return (x*c-y*q,x*q+y*c,z)


def deck_steel(m,lines):
    """Girders under the machines and a ring beam at the wall, open at the access wedge."""
    for a,b in lines:
        s.bar(m,(*a,-DECK/2),(*b,-DECK/2),.28,STRUCT,DECK-.10)
    r=s.RI-.22
    s.sector(m,r-.14,r+.14,-DECK+.05,-.05,math.pi/2+ACCESS_HALF,math.pi/2+s.TAU-ACCESS_HALF,40,[STRUCT]*4,caps=True)


# The load path that holds the top of the shaft is drawn in one colour: connector, seats and cast-in plates.
HOLD="c8862e"
RIG=cfg.PROJECT["structure"]["top_rig"]
SHAFT_R=cfg.STORE["shaft_radius_m"]
COLLAR=SHAFT_R+.24
SEAT_Z=-DECK+.05
PLATE_W,PLATE_H=RIG["mount_plate_m"]


def mount_angles():
    """Bearings of the wall mounts in the frame of the power level: evenly round the ring beam, clear of the access wedge."""
    n=RIG["wall_mounts"]
    start=math.pi/2+ACCESS_HALF+math.radians(5);arc=s.TAU-2*(ACCESS_HALF+math.radians(5))
    return [start+k*arc/(n-1) for k in range(n)]


def shaft_connector(m):
    """Collar round the top of the shaft with arms out to the ring beam. It passes sideways force only: the shaft can slide in it."""
    s.sector(m,SHAFT_R+.03,COLLAR,-DECK+.04,-.04,0,s.TAU,32,[HOLD]*4,caps=True)
    for k in range(RIG["arms"]):
        a=math.pi/4+k*s.TAU/RIG["arms"]
        s.bar(m,s.polar(COLLAR-.04,a,-DECK/2),s.polar(s.RI-.34,a,-DECK/2),.26,HOLD,DECK-.18)
    # A shoe under the ring beam at every mount, welded to the plate cast into the wall once the rig is down.
    for a in mount_angles():
        s.bar(m,s.polar(s.RI-.46,a,SEAT_Z-.07),s.polar(s.RI-.056,a,SEAT_Z-.07),.40,HOLD,.14)
        s.bar(m,s.polar(s.RI-.085,a,SEAT_Z+.22),s.polar(s.RI-.056,a,SEAT_Z+.22),.50,HOLD,.44)


def mount_plate():
    """A plate cast into the inner wall, flush with the bore, with studs back into the concrete. Local x points out through the wall."""
    m=mesh("Top rig | cast-in wall plate and studs")
    closed(m,-.014,-PLATE_W/2,.02,PLATE_W/2,-.45,PLATE_H-.45,HOLD)
    for y in (-PLATE_W/2+.1,PLATE_W/2-.1):
        for z in (-.33,-.05,.22,.38):
            closed(m,.02,y-.02,.21,y+.02,z-.02,z+.02,"5d6468")
    return m


def chord(y,r=None):
    r=r or s.RI-.3
    half=math.sqrt(r*r-y*y)
    return (-half,y),(half,y)


def diesel_set(m,cx,cy,deg):
    """One backup diesel generator set: skid, engine, alternator, cooler and exhaust riser."""
    def box(x0,y0,x1,y1,z0,z1,col):
        if deg:x0,y0,x1,y1=-y1,x0,-y0,x1
        closed(m,cx+x0,cy+y0,cx+x1,cy+y1,z0,z1,col)
    l,w=GEN_L/2,GEN_W/2
    box(-l,-w+.35,l,w-.35,0,.32,DARK)
    box(-l+.55,-.82,.75,.82,.32,2.35,"c2a548")
    box(-l+.75,-.60,.55,.60,2.35,2.75,"8d7a3c")
    box(.95,-.78,l-.55,.78,.32,2.05,"7d8c96")
    box(l-.55,-.5,l-.05,.5,.5,1.7,"c9cdc8")
    box(-l+.05,-w+.2,-l+.5,w-.2,.32,GEN_H-.35,"9aa39f")
    x,y=(-l+1.4,0) if not deg else (0,-l+1.4)
    services.pipe(m,(cx+x,cy+y,2.75),(cx+x,cy+y,LEVEL[0]-DECK),DIESEL_STACK_R,"8b9591",DIESEL_STACK_R-.04,n=12)


def power_mesh(index):
    if index==0:
        m=mesh(f"Power level 1 | {len(GEN_AT)} backup diesel sets, {len(DAY_TANKS)} day tanks and deck steel")
        # The girder over the axis stops at the collar that holds the top of the shaft.
        (x0,y0),(x1,y1)=chord(.3)
        deck_steel(m,[((x0,y0),(-COLLAR+.03,y0)),((COLLAR-.03,y1),(x1,y1))]+[chord(y) for y in (-1.5,-4.0,-5.8)]+[((x,-4.4),(x,3.0)) for x in (-6.55,-4.75,4.75,6.55)])
        shaft_connector(m)
        for cx,cy,deg in GEN_AT:
            diesel_set(m,cx,cy,deg)
        r,l=D["day_tank_diameter_m"]/2,D["day_tank_length_m"]
        for x,y in DAY_TANKS:
            services.pipe(m,(x,y-l/2,r+.45),(x,y+l/2,r+.45),r,"b5553c",n=16)
            for yy in (y-l/2+.3,y+l/2-.3):
                closed(m,x-r*.8,yy-.08,x+r*.8,yy+.08,0,.5,DARK)
        return m
    m=mesh("Power level 2 | two in-line gas turbine generator sets and deck steel")
    l,w=SET_L/2,SET_W/2
    deck_steel(m,[chord(y) for y in (1.2,3.4,-1.2,-3.4)])
    if film.SHORT:
        # The short film leaves the enclosures off so both turbine sets can be seen.
        return m
    # Set B is closed. Set A is an open shell so the turbine can be seen when its side is down.
    closed(m,-l,-SET_Y-w,l,-SET_Y+w,0,SET_H,PAINT[1])
    y0,y1=SET_Y-w,SET_Y+w
    closed(m,-l,y0,l,y1,0,.14,DARK)
    closed(m,-l,y0,l,y1,SET_H-.08,SET_H,PAINT[1])
    closed(m,-l,y0,l,y0+.06,.14,SET_H-.08,PAINT[1])
    closed(m,-l,y0+.06,-l+.06,y1,.14,SET_H-.08,PAINT[1])
    closed(m,l-.06,y0+.06,l,y1,.14,SET_H-.08,PAINT[1])
    closed(m,-l+.06,y1-.06,PANEL_X[0],y1,.14,SET_H-.08,PAINT[1])
    closed(m,PANEL_X[1],y1-.06,l-.06,y1,.14,SET_H-.08,PAINT[1])
    closed(m,PANEL_X[0],y1-.06,PANEL_X[1],y1,HINGE_Z+PANEL_HEIGHT,SET_H-.08,PAINT[1])
    for sign in (-1,1):
        yc=sign*SET_Y
        for k in range(24):
            x=-l+.3+k*(SET_L-.6)/23
            closed(m,x-.05,yc-w+.2,x+.05,yc+w-.2,SET_H,SET_H+.05,RIB[1])
    for k in range(36):
        x=-l+.25+k*(SET_L-.5)/35
        both(m,[(x-.07,-SET_Y-w-.004,.2),(x+.07,-SET_Y-w-.004,.2),(x+.07,-SET_Y-w-.004,SET_H-.2),(x-.07,-SET_Y-w-.004,SET_H-.2)],RIB[1])
    return m


def enclosure_angle(t):
    """Angle of the hinged side in radians, at frames after the store is full. 0 is closed."""
    return math.pi/2*(s.step(*clock.ENCLOSURE_OPEN,t)-s.step(*clock.ENCLOSURE_CLOSE,t))


def panel_mesh(theta):
    """The hinged side of turbine set A, turned down by theta about its bottom edge.

    Closed it is part of the enclosure wall. Fully open it lies flat at floor level and is the work floor.
    """
    m=mesh(f"Turbine set A | hinged side at {math.degrees(theta):.1f} degrees")
    co,si=math.cos(theta),math.sin(theta)
    def at(x,v,n):
        return (x,HINGE_Y+v*si+n*co,HINGE_Z+v*co-n*si)
    x0,x1=PANEL_X[0]+.03,PANEL_X[1]-.03
    both(m,[at(x0,0,0),at(x1,0,0),at(x1,PANEL_HEIGHT,0),at(x0,PANEL_HEIGHT,0)],"c9ccc3")
    both(m,[at(x0,0,.06),at(x1,0,.06),at(x1,PANEL_HEIGHT,.06),at(x0,PANEL_HEIGHT,.06)],PAINT[1])
    for k in range(14):
        x=x0+.2+k*(x1-x0-.4)/13
        both(m,[at(x-.07,.05,.064),at(x+.07,.05,.064),at(x+.07,PANEL_HEIGHT-.05,.064),at(x-.07,PANEL_HEIGHT-.05,.064)],RIB[1])
    for v in (0,PANEL_HEIGHT):
        s.bar(m,at(x0,v,.03),at(x1,v,.03),.07,STRUCT)
    if theta>.02:
        for x in (x0+.4,x1-.4):
            s.bar(m,(x,HINGE_Y,HINGE_Z+PANEL_HEIGHT+.5),at(x,PANEL_HEIGHT-.05,0),.035,"80765c")
    return m


def turbine_mesh(side=1):
    """A 25 MW class aeroderivative gas turbine and its generator in line. Set A is at +Y and set B at -Y."""
    m=mesh(f"Turbine set {'A' if side>0 else 'B'} | aeroderivative gas turbine, exhaust collector and generator")
    k=1.22;y=side*(SET_Y-.08);z=.14+1.07*k
    def box(x0,ya,x1,yb,z0,z1,col):
        closed(m,x0,y+ya*k,x1,y+yb*k,.14+z0*k,.14+z1*k,col)
    def drum(x0,x1,r,col,n=20):
        services.pipe(m,(x0,y,z),(x1,y,z),r*k,col,n=n)
    box(-6.9,-.98,6.9,.84,0,.13,DARK)
    # Inlet plenum and bellmouth
    box(-6.75,-.92,-5.35,.80,.13,2.09,"d5d8cf")
    for j in range(6):
        zz=.14+(.37+j*.29)*k
        both(m,[(-6.65,y+.81*k,zz),(-5.45,y+.81*k,zz),(-5.45,y+.81*k,zz+.16),(-6.65,y+.81*k,zz+.16)],"8d9690")
    drum(-5.35,-5.10,.92,"aab4b2");drum(-5.10,-4.85,.78,"9aa6a5")
    # Compressor with flanges
    drum(-4.85,-2.66,.60,"8fa3a8")
    for j in range(7):
        x=-4.75+j*.33
        drum(x,x+.05,.67,"6c7f86")
    # Combustor and fuel manifolds
    drum(-2.66,-1.82,.80,"c98a4b")
    drum(-2.40,-2.32,.90,"d9b13c");drum(-2.12,-2.04,.90,"d9b13c")
    # Turbines
    drum(-1.82,-1.24,.70,"8a8f8c")
    for j,r in enumerate((.76,.86,.96)):
        drum(-1.24+j*.42,-.82+j*.42,r,"7d8a8a")
    # Exhaust collector rising to the roof
    box(.02,-.90,1.22,.78,.13,2.9,"9aa09a")
    both(m,[(.10,y+.79*k,.6),(1.14,y+.79*k,.6),(1.14,y+.79*k,3.4),(.10,y+.79*k,3.4)],"868c86")
    # Coupling and generator
    drum(1.22,1.82,.13,"5c6468",12);drum(1.36,1.68,.25,"d6a23a",14)
    box(1.82,-.88,6.6,.74,.17,1.89,"5f7f9a")
    for j in range(9):
        x=2.1+j*.5
        box(x,-.90,x+.18,.76,1.89,1.99,"4d6a84")
    # Gas supply to the manifold
    services.pipe(m,(-3.9,y+.72*k,.6),(-2.36,y+.72*k,.6),.06,"d9b13c",n=8)
    services.pipe(m,(-2.36,y+.72*k,.6),(-2.36,y+.72*k,z-.2),.06,"d9b13c",n=8)
    return m


def bridle():
    m=mesh("Four-leg power-unit lifting bridle")
    for x in (-5.6,5.6):
        for y in (-4.2,4.2):
            s.bar(m,(x,y,-DECK/2),(0,0,APEX),.07,"726952")
    return m


def power_base(crown,idx):
    return crown+DECK+idx*LEVEL[0]


def body_position(crown,idx,t):
    start=PICK_STARTS[idx]
    q=t-start
    x,y=PICK_SITES[idx]
    across=s.step(55,89,q)
    z=GROUND+(TRANSIT-GROUND)*s.step(5,54,q)
    z+=(power_base(crown,idx)-TRANSIT)*s.step(91,PICK_LENGTH,q)
    return (x*(1-across),y*(1-across),z)


def hook_position(crown,t):
    if t<PICK_STARTS[0]+PICK_LENGTH:
        x,y,z=body_position(crown,0,t)
        return x,y,z+APEX
    if t<PICK_STARTS[1]:
        a=PICK_STARTS[0]+PICK_LENGTH
        x,y=PICK_SITES[1]
        move=s.step(a+28,a+62,t)
        z=power_base(crown,0)+APEX
        high=TRANSIT+APEX
        return (x*move,y*move,z+(high-z)*s.step(a+4,a+27,t)
                +(GROUND+APEX-high)*s.step(a+63,PICK_STARTS[1]-1,t))
    x,y,z=body_position(crown,1,t)
    end=PICK_STARTS[1]+PICK_LENGTH
    if t<=end+3:return x,y,z+APEX
    a,b=LID
    lx,ly,lz=lid_position(t)
    if t<a:
        # Leave the upper unit, travel high and come down onto the lid's bridle.
        up=TRANSIT+APEX;go=s.step(end+25,a-22,t)
        height=z+APEX+(up-z-APEX)*s.step(end+3,end+24,t)+(lz+LID_APEX-up)*s.step(a-22,a-2,t)
        return lx*go,ly*go,height
    return lx,ly,lz+LID_APEX+8*s.step(b+6,b+30,t)


def lid_position(t):
    """The lid waits on the ground, is carried over the vents and lowered onto the rim."""
    a,b=LID;x,y=LID_SITE
    across=s.step(a+45,a+80,t)
    z=LID_GROUND+(LID_TRANSIT-LID_GROUND)*s.step(a+8,a+45,t)+(LID_Z-LID_TRANSIT)*s.step(a+80,b,t)
    return (x*(1-across),y*(1-across),z)


def lid_mesh():
    m=mesh("Silo lid | steel deck with turbine exhaust stacks, air inlet houses and diesel vents")
    s.sector(m,0,LID_R,0,LID_THICK,0,s.TAU,48,["9aa39f","9aa39f","b9beb8","9aa39f"],caps=False)
    s.sector(m,LID_R-.16,LID_R,LID_THICK,LID_THICK+.10,0,s.TAU,48,["8b9591","8b9591","a7aeaa","8b9591"],caps=False)
    for k in range(8):
        a=k*s.TAU/8+.2
        s.bar(m,s.polar(1.2,a,LID_THICK+.05),s.polar(LID_R-.3,a,LID_THICK+.05),.16,"a3aaa5",.10)
    top=LID_THICK
    # Turbine exhaust: one stack over each exhaust collector.
    for x,y in EXHAUST_AT:
        a=turned(x,y)
        services.pipe(m,(a[0],a[1],top),(a[0],a[1],top+EXHAUST_H),EXHAUST_R,"a8b8b5",EXHAUST_R-.08,n=24)
        for z in (top,top+EXHAUST_H*.5,top+EXHAUST_H-.14):
            services.pipe(m,(a[0],a[1],z),(a[0],a[1],z+.14),EXHAUST_R+.07,"7f8a86",EXHAUST_R-.08,n=24)
    # Turbine air: a filter house over each inlet plenum, lower than the exhaust and away from it.
    hl,hw,hh=INLET_HOUSE
    for x,y in INLET_AT:
        s.bar(m,turned(x-hl/2,y,top+hh/2),turned(x+hl/2,y,top+hh/2),hw,"d5d8cf",hh)
        s.bar(m,turned(x-hl/2-.1,y,top+hh+.06),turned(x+hl/2+.1,y,top+hh+.06),hw+.2,"8e9690",.12)
        for side in (-1,1):
            for j in range(5):
                z=top+.35+j*.42
                s.bar(m,turned(x-hl/2+.15,y+side*(hw/2+.012),z),turned(x+hl/2-.15,y+side*(hw/2+.012),z),.03,"6f7c7a",.22)
    # Diesel exhausts and the diesel room air vents.
    for x,y in DIESEL_STACKS:
        a=turned(x,y)
        services.pipe(m,(a[0],a[1],top),(a[0],a[1],top+DIESEL_STACK_H),DIESEL_STACK_R,"8b9591",DIESEL_STACK_R-.04,n=14)
        services.pipe(m,(a[0],a[1],top+DIESEL_STACK_H-.1),(a[0],a[1],top+DIESEL_STACK_H),DIESEL_STACK_R+.06,"6f7c7a",DIESEL_STACK_R-.04,n=14)
    vl,vw,vh=ROOM_VENT
    for x,y in ROOM_VENTS:
        s.bar(m,turned(x-vl/2,y,top+vh/2),turned(x+vl/2,y,top+vh/2),vw,"c2c6c0",vh)
        s.bar(m,turned(x-vl/2-.1,y,top+vh+.05),turned(x+vl/2+.1,y,top+vh+.05),vw+.2,"8e9690",.10)
    return m


def lid_bridle():
    m=mesh("Lid pick | four-leg bridle")
    for k in range(4):
        s.bar(m,s.polar(LID_R*.62,k*s.TAU/4+.4,LID_THICK),(0,0,LID_APEX),.07,"726952")
    return m


# Fabrication of the two power levels on the ground, in frames after the store is full. Short film only.
FAB=tuple(f-film.LOADING for f in film.FABRICATE_CUT)
FAB_DONE=FAB[0]+222
STRIPS=6
DECK_AT=(FAB[0]+6,FAB[0]+14)
STRIP_STEP=7
WELD=((FAB[0]+10,FAB[0]+72),(FAB[0]+18,FAB[0]+86))
GENSETS_AT=FAB[0]+84
GENSET_STEP=14
TANKS_AT=FAB[0]+146
TURBINES_AT=(FAB[0]+152,FAB[0]+184)
DROP=10


def fabrication_parts(index):
    """A power level in the pieces it is built from: strips of deck steel, then each machine."""
    whole=power_mesh(index)
    strips=[mesh(f"Power level {index+1} | deck steel, strip {k+1}") for k in range(STRIPS)]
    machines={}
    reach=s.RI
    for a,b,c,colour in whole.tris:
        x=(a[0]+b[0]+c[0])/3;y=(a[1]+b[1]+c[1])/3
        if max(a[2],b[2],c[2])<=.001:
            strips[max(0,min(STRIPS-1,int((x+reach)/(2*reach)*STRIPS)))].tris.append((a,b,c,colour));continue
        near=min(range(len(GEN_AT)),key=lambda n:math.hypot(x-GEN_AT[n][0],y-GEN_AT[n][1]))
        key=near if math.hypot(x-GEN_AT[near][0],y-GEN_AT[near][1])<4.3 else "tanks"
        if key not in machines:machines[key]=mesh(f"Power level {index+1} | "+("day tanks" if key=="tanks" else f"diesel set {key+1}"))
        machines[key].tris.append((a,b,c,colour))
    return strips,machines


def fabricate(scene,node,p):
    """Deck steel is laid and welded on the ground, then the sets are landed on it from their trucks."""
    from . import cagebuild
    from . import site
    from . import traffic
    base=p.FILLED;fleet=scene.fleet
    def show(at):
        return [(0,OFF),(at-.02,OFF),(at,ON)]
    arcs=fleet.mesh("spark",cagebuild.spark_mesh)
    flat=fleet.mesh("flatbed",site.flatbed);hauler=fleet.mesh("haul trailer",site.haul_trailer)
    def landing(at):
        return [(0,(0,0,2.6)),(base+at,(0,0,2.6)),(base+at+DROP,(0,0,0))]
    def crate(name,length,width,height,colour):
        m=mesh(name);closed(m,-length/2,-width/2,length/2,width/2,0,height,colour)
        for x in (-length/2+.4,0,length/2-.4):closed(m,x-.06,-width/2-.03,x+.06,width/2+.03,0,height+.04,"59646a")
        return scene.mesh(m)
    loads=(crate("Diesel set on its truck",GEN_L,GEN_W,GEN_H-.4,"c2a548"),crate("Turbine set on its trailer",SET_L,SET_W,SET_H-.5,"d5d8cf"))
    people={}
    for j in (0,1):
        x,y=PICK_SITES[j];label=f"Power level {j+1:02}"
        holder=node(label+" | being fabricated",-1,"Power fabrication",ang=POWER_YAW,t=(x,y,GROUND),
                    tracks={"scale":[(0,ON),(base+FAB_DONE-.02,ON),(base+FAB_DONE,OFF)]})
        strips,machines=fabrication_parts(j)
        for k,strip in enumerate(strips):
            node(strip.name,scene.mesh(strip),"Power fabrication",holder,tracks={"scale":show(base+DECK_AT[j]+k*STRIP_STEP)})
        bearing=math.degrees(math.atan2(y,x))%360
        route,stop=traffic.stop_route(traffic.normal(math.radians(bearing)))
        arrivals=[]
        if j==0:
            for key,machine in machines.items():
                at=TANKS_AT if key=="tanks" else GENSETS_AT+key*GENSET_STEP
                node(machine.name,scene.mesh(machine),"Power fabrication",holder,tracks={"scale":show(base+at),"translation":landing(at)})
                if key!="tanks":arrivals.append((at,flat,site.FLAT_AXLE,traffic.DECK_MID,site.DECK,loads[0],f"Diesel set {key+1}"))
        else:
            for n,(side,name) in enumerate(((1,"A"),(-1,"B"))):
                at=TURBINES_AT[n]
                node(f"Turbine set {name} | landed on the deck",scene.mesh(turbine_mesh(side)),"Power fabrication",holder,
                     tracks={"scale":show(base+at),"translation":landing(at)})
                arrivals.append((at,hauler,site.HAUL_AXLE,-9.6,.98,loads[1],f"Turbine set {name}"))
        for at,trailer,axle,seat,deck,load,name in arrivals:
            trip=site.Trip()
            front=stop+traffic.DECK_MID-seat
            traffic.come(trip,route,front,base+at-6);traffic.go(trip,route,front,base+at+8)
            towed,_,_=fleet.rig(name+" | delivery",trip,trailer,axle,group="Power fabrication")
            node(name+" | on its truck",load,"Power fabrication",towed,t=(seat,0,deck),tracks={"scale":site.window(0,base+at)})
        # Welders and their arcs on the deck steel.
        first,last=base+WELD[j][0],base+WELD[j][1]
        for n,(wx,wy) in enumerate(((-4.75,-2.),(4.75,-2.),(0,-1.5),(-2.5,-5.6),(3.,1.))):
            node(f"{label} | deck weld {n+1}",arcs,"Welding",holder,t=(wx,wy,.02),tracks={"scale":cagebuild.flicker([(first+3*n,last)],n+j)})
        for n in range(cfg.PROJECT["logistics"]["power_fabrication"]["welders"]):
            a=n*s.TAU/4+.9
            actor=node(f"{label} | welder {n+1}",-1,"Fabrication crew",holder,ang=a+math.pi,t=s.polar(s.RI+.5,a,-GROUND+.02),
                       tracks={"scale":site.window(first-8,last+10)})
            count=crew.MODES["inspect"]
            for index in range(count):
                key=(n%3,"inspect",index)
                if key not in people:people[key]=scene.mesh(crew.technician(*key))
                keys=[(0,ON if index==0 else OFF)]
                for f in range(first-8,last+11):
                    was,now=((f-1)//3+n)%count==index,(f//3+n)%count==index
                    if was!=now:keys+=[(f-.025,ON if was else OFF),(f,ON if now else OFF)]
                node(f"{label} | welder {n+1} | pose {index+1}",people[key],"Fabrication crew poses",actor,tracks={"scale":keys})


def camera_power(p,frame,old,cam,blend):
    t=frame-p.FILLED
    # Start at the same eye as the preceding shot. Follow the lift vertically,
    # then move to a steeper view to expose the central bearing and both roof ducts.
    wide=cam((-7,-2,22),-60,15,108)
    first=cam((-.5,0,26.5),-52,33,58)
    second=cam((0,0,28.5),-45,40,52)
    finished=cam((0,0,27.5),-39,53,50)
    if t<75:return blend(old,wide,s.step(0,44,t))
    if t<177:return blend(wide,first,s.step(123,173,t))
    if t<260:return blend(first,wide,s.step(220,258,t))
    if t<421:return blend(wide,second,s.step(360,421,t))
    if t<VENT_END:return blend(second,finished,s.step(VENT_START,VENT_END-1,t))
    # Pull back for the lid, then look down on it as it closes the silo.
    lift=cam((-9,-1,24),-64,22,104)
    closed_view=cam((0,0,31.5),-52,38,74)
    if t<LID[0]+60:lid_view=blend(finished,lift,s.step(VENT_END,LID[0]+18,t))
    else:lid_view=blend(lift,closed_view,s.step(LID[0]+62,LID[1]-8,t))
    return care.service_camera(t,lid_view,cam,blend)


def add(scene,node,p):
    def addmesh(m): return scene.mesh(m)
    def show(t):
        return [(0,OFF),(max(0,t-.02),OFF),(t,ON)]
    def hide_after(t0,t1):
        return show(t0)+[(t1-.02,ON),(t1,OFF)]
    def compact_relative(fn):
        vals=[fn(i) for i in range(END)]
        return [(0,vals[0])]+[(p.FILLED+f,v) for f,v in p.flat_keys(vals)] if len(set(vals))>1 else [(0,vals[0])]
    rig=addmesh(bridle())
    # Plates for the support rig are set in the forms of the wall lift that holds them, like the cooler fixings.
    from . import cooler_frames
    plate=addmesh(mount_plate())
    seat=power_base(p.CROWN,0)+SEAT_Z
    start,cast=cooler_frames.pour_frames(seat,-.45)
    for k,a in enumerate(mount_angles()):
        x,y,_=s.polar(s.RI,POWER_YAW+a,0)
        node(f"Top rig mount {k+1:02} | cast-in wall plate",plate,"Rig mounts",ang=POWER_YAW+a,
             tracks={"scale":show(start),"translation":[(0,(x,y,seat+.46)),(start,(x,y,seat+.46)),(cast,(x,y,seat))]})
    crib=mesh("Power-unit ground crib | bearing strips")
    for x in (-5.2,0,5.2):
        closed(crib,x-.25,-6.0,x+.25,6.0,0,GROUND-DECK+.05,"93846b")
    crib_id=addmesh(crib)
    for j in (0,1):
        y=POWER_YAW
        label=f"Power level {j+1:02}"
        node(label+" | ground crib",crib_id,"Power laydown",ang=y,t=(*PICK_SITES[j],0),
             tracks={"scale":hide_after(p.FILLED+(FAB[0]-12 if film.SHORT else 1),p.FILLED+VENT_END+12)})
        ready=p.FILLED+(FAB_DONE if film.SHORT else 1)
        base=node(label+(" | diesel deck assembly" if j==0 else " | turbine deck assembly"),addmesh(power_mesh(j)),"Power modules",ang=y,
             tracks={"translation":compact_relative(lambda t:body_position(p.CROWN,j,t)),"scale":show(ready)})
        if j==1 and film.SHORT:
            for side,name in ((1,"A"),(-1,"B")):
                node(f"Turbine set {name} | gas turbine and generator",addmesh(turbine_mesh(side)),"Power modules",base)
        elif j==1:
            # Bake the hinged side at a set of angles and show the one nearest the current angle.
            poses=[round(enclosure_angle(t)/(math.pi/2)*(PANEL_POSES-1)) for t in range(END)]
            for k in range(PANEL_POSES):
                keys=[(0,ON if poses[0]==k else OFF)]
                for t in range(1,END):
                    if (poses[t-1]==k)!=(poses[t]==k):
                        keys.extend([(p.FILLED+t-.02,ON if poses[t-1]==k else OFF),(p.FILLED+t,ON if poses[t]==k else OFF)])
                node(f"Turbine set A | hinged side, pose {k+1:02}",addmesh(panel_mesh(k/(PANEL_POSES-1)*math.pi/2)),"Power modules",base,
                     tracks={"scale":keys})
            node("Turbine set A | gas turbine and generator",addmesh(turbine_mesh()),"Power modules",base)
        node(label+" | four-leg rigging",rig,"Power picks",base,
             tracks={"scale":hide_after(p.FILLED+PICK_STARTS[j],p.FILLED+PICK_STARTS[j]+PICK_LENGTH+3)})
    # The lid is the retained crawler's last lift of the build.
    cover=node("Silo lid | crane placement",addmesh(lid_mesh()),"Silo lid",tracks={
        "translation":compact_relative(lid_position),
        "scale":show(p.FILLED+1)+([] if film.SHORT else [(p.FILLED+care.CREW+14.98,ON),(p.FILLED+care.CREW+15,OFF),
                                  (p.RESTORE-.02,OFF),(p.RESTORE,ON),
                                  (p.REGHOST-.02,ON),(p.REGHOST,OFF),(p.RESTORE2-.02,OFF),(p.RESTORE2,ON)])})
    node("Silo lid | lifting bridle",addmesh(lid_bridle()),"Lid pick",cover,
         tracks={"scale":hide_after(p.FILLED+LID[0]-4,p.FILLED+LID[1]+5)})
    timber=mesh("Silo lid | ground dunnage")
    for k in range(3):
        a=k*s.TAU/3
        s.bar(timber,s.polar(1.5,a,LID_GROUND/2),s.polar(LID_R-.5,a,LID_GROUND/2),.40,"8f8064",LID_GROUND)
    node(timber.name,addmesh(timber),"Power laydown",t=(*LID_SITE,0),tracks={"scale":hide_after(p.FILLED+1,p.FILLED+LID[1]+10)})
    if film.SHORT:fabricate(scene,node,p)
    scene.project_info.update(turbineSet_m=[SET_L,SET_W,SET_H],dieselSet_m=[GEN_L,GEN_W,GEN_H],dieselSets=len(GEN_AT),
        powerLevelFloors_m=[power_base(p.CROWN,j) for j in (0,1)],
        exhaustStacks=len(EXHAUST_AT),exhaustStackTop_m=s.WALL_HEIGHT+VENT_RISE,lidElevation_m=LID_Z,lidRadius_m=LID_R,
        lidSeatedAt_s=(p.FILLED+LID[1])/p.FPS,firstLiquidAfter_s=p.C/p.FPS,
        powerModuleOutput_MW=cfg.POWER["module_output_mw"],primeMover=cfg.POWER["prime_mover"],
        turbineEnclosureOpens_s=(p.FILLED+clock.ENCLOSURE_OPEN[0])/p.FPS,turbineWorkFloor_m=power_base(p.CROWN,1)+HINGE_Z,
        powerScope="Each level is lowered as one assembly. Real lifts would be made machine by machine.")
    assert abs(crew.POWER_FLOOR-power_base(p.CROWN,1)-HINGE_Z)<1e-9
