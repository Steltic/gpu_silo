"""Receiving dock for the pods: two back-in truck lanes, a gantry over both and the rail to the ground opening.

Every pod arrives on a truck carrying the heaviest legal load, is lifted by the gantry onto a cradle
on the rail and is fed through the opening when the hoist is ready for it. The dock keeps pace with
the hoist: the cradles hold the next pods, and a second lane lets one truck back in while another unloads.
Dock coordinates are X out from the silo axis along the entry, Y to its left, Z up.
"""
from . import design as cfg

import math

from . import cargo
from . import clock
from . import film
from . import logistics
from . import site
from . import traffic
from . import silo_model as s

INSERT_AT=clock.DELIVERY_AT
DELIVERY_FRAMES=clock.DELIVERY_FRAMES
LG=logistics.C
PER=LG["pods_per_truck"]
CRADLES=cfg.PROJECT["logistics"]["pods"]["buffer_cradles"]
LANES=cfg.PROJECT["logistics"]["pods"]["dock_lanes"]
RAIL_OFFSET=22.
LOAD_OFFSETS=tuple(RAIL_OFFSET+j*(cfg.length(1)+.85) for j in range(CRADLES))
LANE_Y=tuple(site.DOCK_Y*(1 if j%2==0 else -1)*(1+j//2) for j in range(LANES))
DECK=site.DECK
SPAN=max(abs(y) for y in LANE_Y)+2.3
RUNWAY=(21.2,LOAD_OFFSETS[-1]+cargo.INNER+cfg.length(1)/2+2.4)
PARK_Z=4.62
HOVER=.45
ON=(1.,1.,1.);OFF=(0.,0.,0.)
IRON="44565a";EDGE="8d9a95";AMBER="ba843f";CONCRETE="b6bcab"


def box(m,x0,y0,x1,y1,z0,z1,c):
    s.box(m,x0,y0,x1,y1,z0,z1,c)
    m.face([(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0)],c)


def steel(name):
    m=s.Mesh(name);m.material=3
    return m


def coords(a,xyz):
    x,y,z=xyz;c=math.cos(a);d=math.sin(a)
    return (x*c-y*d,x*d+y*c,z)


def camera(target,az,el,distance):
    az=math.radians(az);el=math.radians(el)
    move=(math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el))
    return {"target":target,"eye":s.plus(target,s.times(move,distance)),"fov":33.}


def blend(a,b,q):
    return {k:s.plus(s.times(a[k],1-q),s.times(b[k],q)) for k in ("eye","target")}|{"fov":33.}


def deck_slots():
    """Where each pod's origin sits on the trailer, from the rear of the deck forward."""
    length=cfg.length(1);gap=cfg.PROJECT["logistics"]["pods"]["load_gap_m"]
    rows=min(PER,LG["deck_rows"]);across=math.ceil(PER/rows)
    run=rows*length+(rows-1)*gap
    mid=site.DECK_FRONT-site.DECK_L/2
    slots=[]
    for n in range(PER):
        row,col=n%rows,n//rows
        x=mid-run/2+row*(length+gap)-cargo.INNER
        slots.append((x,(col-(across-1)/2)*(cargo.FRAME_WIDTH+gap)))
    return slots


def terminal():
    m=steel(f"Receiving dock | {CRADLES} cradles on the rail, {LANES} truck lanes and gantry rails")
    far=RUNWAY[1]+.6
    box(m,14.62,-SPAN-.6,far,SPAN+.6,-.16,-.055,"acae96")
    for y in LANE_Y:
        s.quad_xy(m,18.2,y-2.0,site.R_RUN-site.HALF,y+2.0,-.010,"b8b49d")
    for y in (-.27,.27):
        box(m,15.32,y-.039,far-.9,y+.039,-.064,-.008,EDGE)
    for x in range(15,int(far-1)):
        box(m,x,-.38,x+.055,.38,-.049,-.014,"747e76")
    for offset in LOAD_OFFSETS:
        for xx in (offset+1.47,offset+5.27):
            box(m,xx-.16,-.46,xx+.16,.46,-.055,-.002,"839390")
            for y in (-1,1):box(m,xx-.15,y*.51-.046,xx+.15,y*.51+.046,0,.13,"bd9255")
    posts=[RUNWAY[0]+.45,(RUNWAY[0]+RUNWAY[1])/2,RUNWAY[1]-.45]
    for y in (-SPAN,SPAN):
        for x in posts:
            box(m,x-.105,y-.105,x+.105,y+.105,0,4.94,IRON)
            box(m,x-.24,y-.24,x+.24,y+.24,0,.12,EDGE)
        box(m,RUNWAY[0],y-.11,RUNWAY[1],y+.11,4.83,5.10,EDGE)
    # Wheel stops at the back of each lane.
    for y in LANE_Y:
        box(m,18.6,y-1.25,18.9,y+1.25,0,.35,"d4af6b")
    return m


def bridge_mesh():
    m=steel("Dock gantry | cross girder over both lanes and twin end trucks")
    for x in (-.37,.37):box(m,x-.063,-SPAN-.08,x+.063,SPAN+.08,5.02,5.30,"b18c56")
    for y in (-SPAN,SPAN):box(m,-.52,y-.15,.52,y+.15,4.98,5.21,IRON)
    return m


def dock_clock(p):
    """Dock time for a film frame. It follows the hoist, which runs faster for the lower levels."""
    def at(frame):
        if frame<=p.SPEED_FRAME:return float(frame)
        if frame<=p.FILLED:return p.SPEED_FRAME+p.FAST_RATE*(frame-p.SPEED_FRAME)
        return p.SPEED_FRAME+p.FAST_RATE*(p.FILLED-p.SPEED_FRAME)+frame-p.FILLED
    return at


def plan(p):
    """Dock timetable in dock time: when each pod is picked off its truck and landed on the rail, and each truck's visit."""
    starts=p.SOURCE_STARTS;n=p.TOTAL
    advance=[0]+[min(12,starts[i]-starts[i-1]-4) for i in range(1,n)]
    land,carry,cradle=[],[],[]
    for i in range(n):
        if i<CRADLES:
            land.append(INSERT_AT+106+75*i);carry.append(44);cradle.append(i)
        else:
            land.append(starts[i-CRADLES]+advance[i-CRADLES+1]+3)
            carry.append(max(12,min(40,land[i]-land[i-1]-6)));cradle.append(CRADLES-1)
        if land[i]>starts[i]-2 or (i and land[i]-carry[i]<land[i-1]+3):
            raise ValueError(f"The gantry cannot land pod {i+1} in time for the hoist.")
    pick=[a-b for a,b in zip(land,carry)]
    visits=[];free=[-1e9]*LANES
    for k in range(math.ceil(n/PER)):
        pods=list(range(k*PER,min(n,(k+1)*PER)))
        ready=INSERT_AT+49 if k==0 else pick[pods[0]]-5
        leaves=pick[pods[-1]]+math.ceil(.3*carry[pods[-1]])+2
        lane=next((j for j in range(LANES) if free[j]<=ready-18),None)
        if lane is None:
            raise ValueError(f"No dock lane is free for truck {k+1}. Add a lane or a cradle.")
        reverse=int(max(14,min(60,ready-free[lane]-4)))
        visits.append(dict(pods=pods,lane=lane,ready=ready,leaves=leaves,reverse=reverse))
        free[lane]=leaves+14
    return dict(pick=pick,land=land,carry=carry,cradle=cradle,advance=advance,visits=visits)


def pod_origin(index,visit):
    """Dock coordinates of a pod's origin on its parked truck."""
    x,y=deck_slots()[visit["pods"].index(index)]
    pin=site.DOCK_FRONT-site.STEER
    return pin+x,LANE_Y[visit["lane"]]+y


def install_terminal(scene,node,p):
    start=INSERT_AT
    timetable=plan(p);scene.dock=timetable
    at=dock_clock(p)
    total=p.FRAMES
    def frame_at(time):
        """First film frame at or after a dock time."""
        f=int(min(total-1,max(0,math.floor(time if time<=p.SPEED_FRAME else p.SPEED_FRAME+(time-p.SPEED_FRAME)/p.FAST_RATE))))
        while f<total-1 and at(f)<time-1e-9:f+=1
        return f
    def show(t0,t1=None):
        k=[(0,OFF),(t0-.02,OFF),(t0,ON)]
        if t1 is not None:k.extend([(t1-.02,ON),(t1,OFF)])
        return k
    yard=node("Receiving dock, rail and truck lanes",scene.mesh(terminal()),"Terminal infrastructure",ang=p.ENTRY,
              tracks={"scale":show(start)})
    fleet=scene.fleet
    flat=fleet.mesh("flatbed",site.flatbed)
    lanes=[traffic.dock_lane(y,site.DOCK_FRONT) for y in LANE_Y]
    pick,land,carry,cradle=(timetable[k] for k in ("pick","land","carry","cradle"))
    length=cfg.length(1)
    centre=cargo.INNER+length/2
    last_frame=p.FILLED+60
    trucks=[]
    for k,visit in enumerate(timetable["visits"]):
        lane,parked,bearing=lanes[visit["lane"]]
        trip=site.Trip()
        traffic.back_in(trip,lane,parked,bearing,traffic.RIG_BEHIND,visit["ready"],holding=k%site.HOLDING,
                        waits=visit["ready"]-330-37*(k%5),reverse=visit["reverse"])
        traffic.leave(trip,lane,parked,visit["leaves"])
        towed,(first,last),pose=fleet.rig(f"Pod truck {k+1:02}",trip,flat,site.FLAT_AXLE,clock=at,group="Pod delivery")
        trucks.append((first,frame_at(visit["ready"]),frame_at(visit["leaves"]),last))
        for index in visit["pods"]:
            label=f"Pod {index+1:03} | L{p.LEVELS-index//p.BAYS:02} B{index%p.BAYS+1:02}"
            body=next(n for n in scene.nodes if n["name"]==label)
            mesh_id=body["mesh"] if body["mesh"]>=0 else next(n["mesh"] for n in scene.nodes if n["name"]==f"Original pod {index+1:03} | bronze before fault")
            x,y=deck_slots()[visit["pods"].index(index)]
            lifted=frame_at(pick[index]);handed=p.STARTS[index]
            node(f"Pod {index+1:03} | on its truck",mesh_id,"Pod delivery",towed,t=(x,y,DECK),tracks={"scale":site.window(0,lifted)})
            # From the truck to the cradle on the gantry, then along the rail to the opening.
            (px,py,_),yaw=pose(lifted)
            c,d=math.cos(yaw),math.sin(yaw)
            wx,wy=px+x*c-y*d,py+x*d+y*c
            ce,se=math.cos(p.ENTRY),math.sin(p.ENTRY)
            x0,y0=wx*ce+wy*se,-wx*se+wy*ce
            turn0=yaw-p.ENTRY;turn0-=s.TAU*round(turn0/s.TAU)
            rest=LOAD_OFFSETS[cradle[index]]
            moves=timetable["advance"][index];begins=p.SOURCE_STARTS[index-1] if index else 0
            values,turns=[],[]
            for f in range(lifted,handed+1):
                t=at(f);u=s.clamp((t-pick[index])/carry[index]);q=s.step(.16,.74,u)
                z=DECK+HOVER*s.step(0,.18,u)-(DECK+HOVER)*s.step(.72,.95,u)
                along=rest+(RAIL_OFFSET-rest)*(s.step(begins,begins+moves,t) if index and rest!=RAIL_OFFSET else 0)
                values.append((x0+(along-x0)*q,y0*(1-q),z));turns.append((turn0*(1-q),))
            values[-1]=(RAIL_OFFSET,0.,0.)
            node(f"Pod {index+1:03} | on the gantry and rail",mesh_id,"Terminal cargo",yard,
                 tracks={"translation":fleet.curve(lifted,values),"yaw":fleet.curve(lifted,turns),"scale":show(lifted,handed)})
    # The gantry follows whichever pod it is carrying and parks high between lifts.
    def hook(t):
        """Spreader position in dock coordinates at a dock time: along the rail, across it and its height."""
        i=0
        while i<p.TOTAL-1 and t>land[i]+1.5:i+=1
        visit=timetable["visits"][i//PER]
        x0,y0=pod_origin(i,visit);rest=LOAD_OFFSETS[cradle[i]]
        u=(t-pick[i])/carry[i]
        if u<0:
            # Travel from the last landing to the next pick.
            if i==0:return x0+centre,y0,PARK_Z
            before=land[i-1]+1.5;q=s.step(before,pick[i]-.5,t) if pick[i]-.5>before else 1.
            px=LOAD_OFFSETS[cradle[i-1]]+centre
            lift=min(1.,(pick[i]-before)/14.)
            z=cargo.FRAME_HEIGHT*(1-q)+(DECK+cargo.FRAME_HEIGHT)*q+(PARK_Z-DECK-cargo.FRAME_HEIGHT)*lift*math.sin(math.pi*q)
            return px+(x0+centre-px)*q,y0*q,z
        u=min(1.,u);q=s.step(.16,.74,u)
        z=DECK+HOVER*s.step(0,.18,u)-(DECK+HOVER)*s.step(.72,.95,u)
        return x0+centre+(rest-x0)*q,y0*(1-q),z+cargo.FRAME_HEIGHT
    hooks=[hook(at(f)) for f in range(start,last_frame+1)]
    def keyed(values):
        return [(0,values[0])]+[(start+k,v) for k,v in p.flat_keys(values,1e-4)]
    trolley=steel("Dock trolley | powered hoist drums")
    box(trolley,-.61,-.34,.61,.34,4.94,5.34,"8c998a")
    carrier=steel("Dock lifting spreader | two pickup points")
    box(carrier,-1.83,-.12,1.83,.12,0,.092,"c59d63")
    rope=steel("Dock hoist | two falls")
    for r in (-1.65,1.65):box(rope,r-.018,-.02,r+.018,.02,0,1,"56534b")
    node("Dock | powered bridge",scene.mesh(bridge_mesh()),"Terminal infrastructure",yard,
         tracks={"translation":keyed([(x,0,0) for x,_,_ in hooks])})
    node("Dock | traversing trolley",scene.mesh(trolley),"Terminal infrastructure",yard,
         tracks={"translation":keyed([(x,y,0) for x,y,_ in hooks])})
    node("Dock | twin lift cables",scene.mesh(rope),"Terminal infrastructure",yard,
         tracks={"translation":keyed(hooks),"scale":keyed([(1.,1.,4.96-z) for _,_,z in hooks])})
    node("Dock | lifting spreader",scene.mesh(carrier),"Terminal infrastructure",yard,tracks={"translation":keyed(hooks)})
    # Counters for the panels: trucks unloaded and pods landed on the rail.
    gone=sorted(frame_at(v["leaves"]) for v in timetable["visits"])
    landed=sorted(frame_at(t) for t in land)
    scene.counts["pod_trucks"]=[sum(1 for g in gone if f>=g) for f in range(total)]
    scene.counts["pods_landed"]=[sum(1 for g in landed if f>=g) for f in range(total)]
    if film.SHORT:office(scene,node,yard,p)
    scene.project_info.update(podsPerTruck=PER,podTrucks=len(timetable["visits"]),dockLanes=LANES,dockCradles=CRADLES,terminalToIntake_m=RAIL_OFFSET)


OFFICE_H=6.2
OFFICE_X=(RUNWAY[0]-1.0,RUNWAY[1]+1.0)
OFFICE_Y=SPAN+1.0
ROOF_PANELS=6


def office_walls():
    """Walls round the dock: doors for the two truck lanes and the rail, and a band of windows."""
    m=steel("Control office | wall panels round the receiving dock")
    x0,x1=OFFICE_X;y=OFFICE_Y;wall="d9d6c6";glass="4b6971"
    def panel(xa,ya,xb,yb,z0=0,z1=OFFICE_H,colour=wall):
        box(m,min(xa,xb),min(ya,yb),max(xa,xb),max(ya,yb),z0,z1,colour)
    for side in (-1,1):
        panel(x0,side*y,x1,side*(y-.2))
        panel(x0+1.5,side*(y+.02),x1-1.5,side*(y-.22),3.3,4.4,glass)
    door=2.3;top=4.7
    # Outer end: a door for each lane. Inner end: an opening for the rail.
    spans=[-y]+[v for lane in sorted(LANE_Y) for v in (lane-door,lane+door)]+[y]
    for a,b in zip(spans[::2],spans[1::2]):panel(x1-.2,a,x1,b)
    panel(x1-.2,-y,x1,y,top,OFFICE_H)
    panel(x1-.22,-1.6,x1+.02,1.6,3.3,4.4,glass)
    for a,b in ((-y,-1.0),(1.0,y)):panel(x0,a,x0+.2,b)
    panel(x0,-y,x0+.2,y,3.1,OFFICE_H)
    return m


def office_roof():
    m=steel("Control office | one flat roof panel")
    width=(OFFICE_X[1]-OFFICE_X[0])/ROOF_PANELS
    box(m,0,-OFFICE_Y-.25,width+.02,OFFICE_Y+.25,OFFICE_H,OFFICE_H+.26,"b9beb6")
    box(m,.1,-OFFICE_Y-.3,width-.08,-OFFICE_Y-.22,OFFICE_H+.26,OFFICE_H+.5,"8d9a95")
    box(m,.1,OFFICE_Y+.22,width-.08,OFFICE_Y+.3,OFFICE_H+.26,OFFICE_H+.5,"8d9a95")
    return m


def office(scene,node,dock,p):
    """Near the end of the build the dock is walled and roofed and becomes the control office."""
    begin=p.FILLED+clock.OFFICE[0];stand=64
    node("Control office | walls",scene.mesh(office_walls()),"Control office",dock,
         tracks={"scale":[(0,OFF),(begin-.02,OFF)]+[(begin+k,(1.,1.,max(.01,s.step(0,stand,k)))) for k in range(stand+1)]})
    roof=scene.mesh(office_roof());width=(OFFICE_X[1]-OFFICE_X[0])/ROOF_PANELS
    for k in range(ROOF_PANELS):
        at=begin+stand+6+8*k
        node(f"Control office | roof panel {k+1}",roof,"Control office",dock,
             tracks={"scale":[(0,OFF),(at-.02,OFF),(at,ON)],"translation":[(0,(OFFICE_X[0]+k*width,0,2.4)),(at,(OFFICE_X[0]+k*width,0,2.4)),(at+8,(OFFICE_X[0]+k*width,0,0))]})
    scene.project_info.update(controlOffice="The receiving dock is roofed and walled at the end of the build",controlOfficeHeight_m=OFFICE_H)


def delivery_camera(frame,p):
    """Look in along the rail from beyond the ring, a little to one side so both lanes and the rail can be seen."""
    t=frame-INSERT_AT
    entry=math.degrees(p.ENTRY)
    wide=camera(coords(p.ENTRY,(27.0,0.,2.0)),entry-25,24,42.)
    close=camera(coords(p.ENTRY,(27.0,2.0,2.4)),entry-20,17,23.)
    rail=camera(coords(p.ENTRY,(27.0,1.25,1.8)),entry-14,30,31.)
    if t<62:return wide
    if t<141:return blend(wide,close,s.step(62,90,t))
    if t<278:return blend(close,rail,s.step(141,180,t))
    return blend(rail,camera(coords(p.ENTRY,(19.0,.5,1.65)),entry-10,19,32.),s.step(278,335,t))
