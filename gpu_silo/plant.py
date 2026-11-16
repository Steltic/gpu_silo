"""Power-module picks through the open silo top, their stubs and exhaust risers.

Coordinates are metres and Z is up.
"""
from . import design as cfg

import math

from . import services
from . import silo_model as s
from . import maintenance as care


RADIAL_CLEARANCE = .05
WIDTH, HEIGHT = cfg.POWER["width_m"], cfg.POWER["height_m"]
LENGTH = math.floor(200*math.sqrt((s.RI-RADIAL_CLEARANCE)**2-(WIDTH/2)**2))/100
BASE_STUB, ROOF_STUB = .27, .22
STACK_X, STACK_R = LENGTH/2-.69, .47
POWER_YAW = math.radians(cfg.POWER["first_heading_degrees"])
PICK_STARTS = (20, 260)
PICK_LENGTH = 151
VENT_START, VENT_END, END = 435, 506, care.END
PICK_SITES = ((-21.5,-8.0),(-21.5,4.0))
CRANE_BASE = (-20.,-23.,0.)
TRANSIT = 35.
GROUND = .36
APEX = HEIGHT+3.9
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


def power_mesh(index):
    m=mesh("Closed corrugated power module "+str(index+1)+" | frame, end plenums and docking collars")
    l,w=LENGTH/2,WIDTH/2
    paint=("748d83","9e927a")[index]
    rib=("9cada1","bbad94")[index]
    closed(m,-l+.08,-w+.105,l-.08,w-.105,.07,HEIGHT-.08,paint)
    # Folded corrugations have a raised ridge with two sloping flanks.
    for sign in (-1,1):
        for k in range(41):
            x=-l+.29+k*(LENGTH-.58)/40
            profile=[(x-.074,sign*(w-.102)),(x-.038,sign*(w-.042)),
                     (x+.035,sign*(w-.042)),(x+.073,sign*(w-.102))]
            for a,b in zip(profile,profile[1:]):
                face=[(*a,.15),(*b,.15),(*b,HEIGHT-.15),(*a,HEIGHT-.15)]
                m.face(face if sign<0 else face[::-1],rib if a==profile[1] else paint)
        closed(m,-l,sign*w-(.13 if sign>0 else 0),l,sign*w+(.13 if sign<0 else 0),0,.15,STRUCT)
        closed(m,-l,sign*w-(.13 if sign>0 else 0),l,sign*w+(.13 if sign<0 else 0),HEIGHT-.15,HEIGHT,SILVER)
        for xx in (-l,l-.16):
            y=w-.16 if sign>0 else -w
            closed(m,xx,y,xx+.16,y+.16,0,HEIGHT,STRUCT)
        x=l-.11 if sign>0 else -l+.11
        for j in range(8):
            y=-.99+j*.28
            closed(m,x-.075,y-.035,x+.075,y+.035,.22,HEIGHT-.22,rib)
        closed(m,l-.15 if sign>0 else -l,-w,l if sign>0 else -l+.15,w,0,.16,STRUCT)
        closed(m,l-.15 if sign>0 else -l,-w,l if sign>0 else -l+.15,w,HEIGHT-.15,HEIGHT,SILVER)
    # Each end plenum turns the exhaust upward inside the body's corner envelope.
    for x in (-STACK_X,STACK_X):
        closed(m,x-.60,-.61,x+.60,.61,HEIGHT-.082,HEIGHT-.018,DARK)
        services.pipe(m,(x,0,HEIGHT-.02),(x,0,HEIGHT+.115),STACK_R+.08,SILVER,STACK_R-.025,n=20)
        services.pipe(m,(x,0,HEIGHT-.017),(x,0,HEIGHT-.009),STACK_R-.027,DARK,n=20)
    services.pipe(m,(0,0,-BASE_STUB),(0,0,-.19),.57,AMBER,.40,n=24)
    services.pipe(m,(0,0,-.19),(0,0,.01),.51,STRUCT,.40,n=24)
    services.pipe(m,(0,0,HEIGHT-.005),(0,0,HEIGHT+.08),.61,STRUCT,n=24)
    services.pipe(m,(0,0,HEIGHT+.08),(0,0,HEIGHT+ROOF_STUB),.53,AMBER,n=24)
    return m


def bridle():
    m=mesh("Four-leg power-unit lifting bridle")
    for x in (-LENGTH/2+.52,LENGTH/2-.52):
        for y in (-1.14,1.14):
            s.bar(m,(x,y,HEIGHT-.07),(0,0,APEX),.064,"726952")
    return m


def power_base(crown,idx):
    return crown+BASE_STUB+idx*(HEIGHT+ROOF_STUB+BASE_STUB)


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
    away=s.step(end+22,end+55,t)
    offered=(x-16*away,y-4*away,z+APEX+(TRANSIT+APEX-z-APEX)*s.step(end+3,end+22,t))
    return offered


def camera_power(p,frame,old,cam,blend):
    t=frame-p.FILLED
    # Start at the same eye as the preceding shot. Follow the lift vertically,
    # then move to a steeper view to expose the central bearing and both roof ducts.
    wide=cam((-7,-2,22),-60,15,108)
    first=cam((-.5,0,24.8),-52,33,49)
    second=cam((0,0,24.7),-45,40,43)
    finished=cam((0,0,24.5),-39,53,41)
    if t<45:return blend(old,wide,s.step(0,38,t))
    if t<147:return blend(wide,first,s.step(93,143,t))
    if t<230:return blend(first,wide,s.step(190,228,t))
    if t<391:return blend(wide,second,s.step(330,391,t))
    power_end=blend(second,finished,s.step(417,505,t))
    return care.service_camera(t,power_end,cam,blend) if t>=VENT_END else power_end


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
    crib=mesh("Power-unit ground crib | bearing strips")
    for x in (-4.35,4.35):
        closed(crib,x-.19,-1.22,x+.19,1.22,0,GROUND,"93846b")
    crib_id=addmesh(crib)
    for j in (0,1):
        y=POWER_YAW+j*math.pi/2
        label=f"Power unit {j+1:02}"
        node(label+" | ground crib",crib_id,"Power laydown",ang=y,t=(*PICK_SITES[j],0),
             tracks={"scale":hide_after(p.FILLED+1,p.FILLED+VENT_END+12)})
        base=node(label+" | closed container body",addmesh(power_mesh(j)),"Power modules",ang=y,
             tracks={"translation":compact_relative(lambda t:body_position(p.CROWN,j,t)),"scale":show(p.FILLED+1)})
        node(label+" | four-leg rigging",rig,"Power picks",base,
             tracks={"scale":hide_after(p.FILLED+PICK_STARTS[j],p.FILLED+PICK_STARTS[j]+PICK_LENGTH+3)})
        roof=power_base(p.CROWN,j)+HEIGHT
        for sign in (-1,1):
            dx=sign*STACK_X
            run=s.WALL_HEIGHT-roof
            joint=.12
            # Nested stainless tubes extend from both end plenums after crane release.
            # The socket lips overlap axially at each telescoping joint.
            for k in range(3):
                rr=STACK_R-.038*k
                item=mesh(label+f" | exhaust sleeve {k+1}")
                services.pipe(item,(0,0,0),(0,0,1),rr,"a8b8b5" if k%2==0 else "91aaa9",rr-.038,n=16)
                extension=lambda t:s.step(VENT_START+3*j,VENT_END-3+3*j,t)
                def origin(t,k=k):
                    e=extension(t)
                    return (dx,0,HEIGHT+.065+k*(.018+(run/3-.018)*e))
                def length(t,k=k):
                    e=extension(t)
                    final=run/3+(.025 if k<2 else -.065)
                    return (1,1,joint+(final-joint)*e)
                name=label+(" | negative" if sign<0 else " | positive")+f" end stack {k+1}"
                node(name,addmesh(item),"End exhausts",base,tracks={"translation":compact_relative(origin),
                                                                  "scale":compact_relative(length)})
                lip=mesh("Rolled exhaust collar")
                services.pipe(lip,(0,0,-.068),(0,0,0),rr+.025,SILVER,rr-.038,n=16)
                node(name+" lip",addmesh(lip),"End exhausts",base,tracks={"translation":compact_relative(
                    lambda t:(dx,0,origin(t)[2]+length(t)[2]))})
    car=node("Power pick | crawler",addmesh(p.crane_lower()),"Power crane",t=CRANE_BASE,
             tracks={"scale":hide_after(p.FILLED+1,p.FILLED+VENT_END+18)})
    hooks=[hook_position(p.CROWN,t) for t in range(END)]
    dx=[v[0]-CRANE_BASE[0] for v in hooks]
    dy=[v[1]-CRANE_BASE[1] for v in hooks]
    reach=[math.hypot(x,y) for x,y in zip(dx,dy)]
    tip=[2.45+math.sqrt(p.BOOM_LENGTH**2-d*d) for d in reach]
    deck=node("Power pick | slewing deck",addmesh(p.crane_upper()),"Power crane",car,
              tracks={"yaw":compact_relative(lambda t:(math.atan2(dy[t],dx[t]),))})
    node("Power pick | lattice boom",addmesh(p.boom_mesh()),"Power crane",deck,t=(0,0,2.45),
         tracks={"scale":compact_relative(lambda t:(reach[t]/17,1,(tip[t]-2.45)/math.sqrt(p.BOOM_LENGTH**2-17**2)))})
    fall=mesh("Power crane main hoist line")
    closed(fall,-.045,-.045,.045,.045,0,1,DARK)
    node("Power pick | hoist rope",addmesh(fall),"Power crane",car,tracks={
        "translation":compact_relative(lambda t:(dx[t],dy[t],hooks[t][2])),
        "scale":compact_relative(lambda t:(1,1,tip[t]-hooks[t][2]))})
    block=mesh("Power crane hook block")
    closed(block,-.20,-.16,.20,.16,0,.42,AMBER)
    node("Power pick | hook block",addmesh(block),"Power crane",car,tracks={
        "translation":compact_relative(lambda t:(dx[t],dy[t],hooks[t][2]))})
    scene.project_info.update(powerBodies_m=[LENGTH,WIDTH,HEIGHT],powerCornerAllowance_m=RADIAL_CLEARANCE,
        powerBodyBaseElevations_m=[power_base(p.CROWN,j) for j in (0,1)],powerYawDifference_deg=90,
        exhaustStacks=4,exhaustRimElevation_m=s.WALL_HEIGHT,firstLiquidAfter_s=p.C/p.FPS,
        powerScope="Placeholder power modules. The electrical supply is not yet sized.")
