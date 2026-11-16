"""Power-module picks through the open silo top, their stubs and exhaust vents, the gas turbine inside
the lower module with its fold-down side, and the lid that closes the silo.

Coordinates are metres and Z is up.
"""
from . import design as cfg

import math

from . import services
from . import silo_model as s
from . import clock
from . import closing
from . import maintenance as care
from . import crew


RADIAL_CLEARANCE = .05
WIDTH, HEIGHT = cfg.POWER["width_m"], cfg.POWER["height_m"]
LENGTH = math.floor(200*math.sqrt((s.RI-RADIAL_CLEARANCE)**2-(WIDTH/2)**2))/100
BASE_STUB, ROOF_STUB = .27, .22
STACK_X, STACK_R = LENGTH/2-.69, .47
POWER_YAW = math.radians(cfg.POWER["first_heading_degrees"])
PICK_STARTS = (50, 290)
PICK_LENGTH = 151
VENT_START, VENT_END, END = 465, care.POWER_DONE, closing.END
VENT_RISE = .90
LID = care.LID
LID_SITE = (-40.,-4.)
LID_R, LID_THICK = s.RO+.14, .22
LID_Z = s.WALL_HEIGHT+.03
LID_GROUND, LID_TRANSIT, LID_APEX = .30, s.WALL_HEIGHT+VENT_RISE+3.6, 7.0
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


PAINT=("748d83","9e927a")
RIB=("9cada1","bbad94")
# The lower module's side toward the crew wedge is a separate panel hinged at floor level.
HINGE_Y,HINGE_Z=-(WIDTH/2-.105),.15
PANEL_HEIGHT=HEIGHT-.30
PANEL_POSES=13


def power_mesh(index):
    m=mesh("Closed corrugated power module "+str(index+1)+" | frame, end plenums and docking collars")
    l,w=LENGTH/2,WIDTH/2
    paint=PAINT[index]
    rib=RIB[index]
    if index:
        closed(m,-l+.08,-w+.105,l-.08,w-.105,.07,HEIGHT-.08,paint)
    else:
        # An open shell: floor, roof, far wall and end bulkheads. The near side is the hinged panel.
        inside="5f6f6a"
        closed(m,-l+.08,-w+.105,l-.08,w-.105,.07,.13,inside)
        closed(m,-l+.08,-w+.105,l-.08,w-.105,HEIGHT-.14,HEIGHT-.08,paint)
        closed(m,-l+.08,w-.165,l-.08,w-.105,.13,HEIGHT-.14,paint)
        for x0,x1 in ((-l+.08,-l+.14),(l-.14,l-.08)):
            closed(m,x0,-w+.105,x1,w-.165,.13,HEIGHT-.14,paint)
    # Folded corrugations have a raised ridge with two sloping flanks.
    for sign in (-1,1):
        for k in range(41):
            if index==0 and sign<0:break
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


def enclosure_angle(t):
    """Angle of the hinged side in radians, at frames after the store is full. 0 is closed."""
    return math.pi/2*(s.step(*clock.ENCLOSURE_OPEN,t)-s.step(*clock.ENCLOSURE_CLOSE,t))


def panel_mesh(theta):
    """The hinged side of the lower module, turned down by theta about its bottom edge.

    Closed it is the corrugated wall. Fully open it lies flat at floor level and is the work floor.
    """
    m=mesh(f"Power module 1 | hinged side at {math.degrees(theta):.1f} degrees")
    l=LENGTH/2;co,si=math.cos(theta),math.sin(theta)
    def at(x,v,n):
        return (x,HINGE_Y-(v*si+n*co),HINGE_Z+v*co-n*si)
    x0,x1=-l+.17,l-.17
    both(m,[at(x0,0,0),at(x1,0,0),at(x1,PANEL_HEIGHT,0),at(x0,PANEL_HEIGHT,0)],"c9ccc3")
    for k in range(41):
        x=-l+.29+k*(LENGTH-.58)/40
        profile=[(x-.074,.003),(x-.038,.063),(x+.035,.063),(x+.073,.003)]
        for a,b in zip(profile,profile[1:]):
            m.face([at(a[0],0,a[1]),at(b[0],0,b[1]),at(b[0],PANEL_HEIGHT,b[1]),at(a[0],PANEL_HEIGHT,a[1])],
                   RIB[0] if a==profile[1] else PAINT[0])
    for v in (0,PANEL_HEIGHT):
        s.bar(m,at(x0,v,.03),at(x1,v,.03),.07,STRUCT)
    if theta>.02:
        # Two stays hold the free edge from the roof rail.
        for x in (-l*.62,l*.62):
            s.bar(m,(x,HINGE_Y,HEIGHT-.16),at(x,PANEL_HEIGHT-.05,0),.035,"80765c")
    return m


def turbine_mesh():
    """A 25 MW class aeroderivative gas turbine and its generator on one skid, in module coordinates."""
    m=mesh("Power module 1 | aeroderivative gas turbine, exhaust collector and generator")
    y,z=.18,1.20
    def drum(x0,x1,r,col,n=20):
        services.pipe(m,(x0,y,z),(x1,y,z),r,col,n=n)
    closed(m,-5.45,-.80,5.45,1.02,.13,.26,DARK)
    # Inlet filter house and bellmouth
    closed(m,-5.35,-.74,-3.95,.98,.26,2.22,"d5d8cf")
    for k in range(6):
        zz=.50+k*.29
        both(m,[(-5.25,-.745,zz),(-4.05,-.745,zz),(-4.05,-.745,zz+.13),(-5.25,-.745,zz+.13)],"8d9690")
    drum(-3.95,-3.74,.92,"aab4b2");drum(-3.74,-3.52,.78,"9aa6a5")
    # Compressor with flanges
    drum(-3.52,-1.36,.60,"8fa3a8")
    for k in range(7):
        x=-3.42+k*.33
        drum(x,x+.05,.67,"6c7f86")
    # Combustor, fuel manifold and nozzles
    drum(-1.36,-.52,.80,"c98a4b")
    drum(-1.10,-1.02,.90,"d9b13c");drum(-.82,-.74,.90,"d9b13c")
    # Turbines
    drum(-.52,.06,.70,"8a8f8c")
    for k,r in enumerate((.76,.86,.96)):
        drum(.06+k*.42,.48+k*.42,r,"7d8a8a")
    # Exhaust collector rising to the roof
    closed(m,1.32,-.78,2.52,1.00,.26,2.28,"9aa09a")
    both(m,[(1.40,-.785,.50),(2.44,-.785,.50),(2.44,-.785,2.05),(1.40,-.785,2.05)],"868c86")
    # Coupling and generator
    drum(2.52,3.12,.13,"5c6468",12);drum(2.66,2.98,.25,"d6a23a",14)
    closed(m,3.12,-.70,5.30,.96,.30,2.02,"5f7f9a")
    for k in range(5):
        x=3.36+k*.42
        closed(m,x,-.72,x+.16,.98,2.02,2.12,"4d6a84")
    closed(m,3.9,-.86,4.6,-.70,.9,1.6,"c9cdc8")
    # Gas supply to the manifold
    services.pipe(m,(-2.6,-.70,.46),(-1.06,-.70,.46),.055,"d9b13c",n=8)
    services.pipe(m,(-1.06,-.70,.46),(-1.06,-.70,z-.2),.055,"d9b13c",n=8)
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
    m=mesh("Silo lid | steel deck over the bore and the liquid, with four vent openings")
    s.sector(m,0,LID_R,0,LID_THICK,0,s.TAU,48,["9aa39f","9aa39f","b9beb8","9aa39f"],caps=False)
    s.sector(m,LID_R-.16,LID_R,LID_THICK,LID_THICK+.10,0,s.TAU,48,["8b9591","8b9591","a7aeaa","8b9591"],caps=False)
    for k in range(8):
        a=k*s.TAU/8+.2
        s.bar(m,s.polar(1.2,a,LID_THICK+.05),s.polar(LID_R-.3,a,LID_THICK+.05),.16,"a3aaa5",.10)
    for j in (0,1):
        yaw=POWER_YAW+j*math.pi/2
        for sign in (-1,1):
            x,y,_=s.polar(sign*STACK_X,yaw,0)
            services.pipe(m,(x,y,LID_THICK),(x,y,LID_THICK+.16),STACK_R+.16,"7f8a86",STACK_R+.03,n=16)
    return m


def lid_bridle():
    m=mesh("Lid pick | four-leg bridle")
    for k in range(4):
        s.bar(m,s.polar(LID_R*.62,k*s.TAU/4+.4,LID_THICK),(0,0,LID_APEX),.07,"726952")
    return m


def camera_power(p,frame,old,cam,blend):
    t=frame-p.FILLED
    # Start at the same eye as the preceding shot. Follow the lift vertically,
    # then move to a steeper view to expose the central bearing and both roof ducts.
    wide=cam((-7,-2,22),-60,15,108)
    first=cam((-.5,0,24.8),-52,33,49)
    second=cam((0,0,24.7),-45,40,43)
    finished=cam((0,0,24.5),-39,53,41)
    if t<75:return blend(old,wide,s.step(0,44,t))
    if t<177:return blend(wide,first,s.step(123,173,t))
    if t<260:return blend(first,wide,s.step(220,258,t))
    if t<421:return blend(wide,second,s.step(360,421,t))
    if t<VENT_END:return blend(second,finished,s.step(447,VENT_END-1,t))
    # Pull back for the lid, then look down on it as it closes the silo.
    lift=cam((-9,-1,24),-64,22,104)
    closed_view=cam((0,0,28.5),-52,38,66)
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
        if j==0:
            # Bake the hinged side at a set of angles and show the one nearest the current angle.
            poses=[round(enclosure_angle(t)/(math.pi/2)*(PANEL_POSES-1)) for t in range(END)]
            for k in range(PANEL_POSES):
                keys=[(0,ON if poses[0]==k else OFF)]
                for t in range(1,END):
                    if (poses[t-1]==k)!=(poses[t]==k):
                        keys.extend([(p.FILLED+t-.02,ON if poses[t-1]==k else OFF),(p.FILLED+t,ON if poses[t]==k else OFF)])
                node(label+f" | hinged side, pose {k+1:02}",addmesh(panel_mesh(k/(PANEL_POSES-1)*math.pi/2)),"Power modules",base,
                     tracks={"scale":keys})
            node(label+" | gas turbine and generator",addmesh(turbine_mesh()),"Power modules",base,
                 tracks={"scale":hide_after(p.FILLED+clock.ENCLOSURE_OPEN[0]-2,p.FILLED+clock.ENCLOSURE_CLOSE[1]+2)})
        node(label+" | four-leg rigging",rig,"Power picks",base,
             tracks={"scale":hide_after(p.FILLED+PICK_STARTS[j],p.FILLED+PICK_STARTS[j]+PICK_LENGTH+3)})
        roof=power_base(p.CROWN,j)+HEIGHT
        for sign in (-1,1):
            dx=sign*STACK_X
            run=s.WALL_HEIGHT+VENT_RISE-roof
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
    # The lid is the retained crawler's last lift of the build.
    cover=node("Silo lid | crane placement",addmesh(lid_mesh()),"Silo lid",tracks={
        "translation":compact_relative(lid_position),
        "scale":show(p.FILLED+1)+[(p.FILLED+care.CREW+14.98,ON),(p.FILLED+care.CREW+15,OFF),
                                  (p.RESTORE-.02,OFF),(p.RESTORE,ON),
                                  (p.REGHOST-.02,ON),(p.REGHOST,OFF),(p.RESTORE2-.02,OFF),(p.RESTORE2,ON)]})
    node("Silo lid | lifting bridle",addmesh(lid_bridle()),"Lid pick",cover,
         tracks={"scale":hide_after(p.FILLED+LID[0]-4,p.FILLED+LID[1]+5)})
    timber=mesh("Silo lid | ground dunnage")
    for k in range(3):
        a=k*s.TAU/3
        s.bar(timber,s.polar(1.5,a,LID_GROUND/2),s.polar(LID_R-.5,a,LID_GROUND/2),.40,"8f8064",LID_GROUND)
    node(timber.name,addmesh(timber),"Power laydown",t=(*LID_SITE,0),tracks={"scale":hide_after(p.FILLED+1,p.FILLED+LID[1]+10)})
    scene.project_info.update(powerBodies_m=[LENGTH,WIDTH,HEIGHT],powerCornerAllowance_m=RADIAL_CLEARANCE,
        powerBodyBaseElevations_m=[power_base(p.CROWN,j) for j in (0,1)],powerYawDifference_deg=90,
        exhaustStacks=4,exhaustVentElevation_m=s.WALL_HEIGHT+VENT_RISE,lidElevation_m=LID_Z,lidRadius_m=LID_R,
        lidSeatedAt_s=(p.FILLED+LID[1])/p.FPS,firstLiquidAfter_s=p.C/p.FPS,
        powerModuleOutput_MW=cfg.POWER["module_output_mw"],primeMover=cfg.POWER["prime_mover"],
        turbineEnclosureOpens_s=(p.FILLED+clock.ENCLOSURE_OPEN[0])/p.FPS,turbineWorkFloor_m=power_base(p.CROWN,0)+HINGE_Z,
        powerScope="Each module is drawn as a container holding one aeroderivative gas turbine and generator. The package is not sized.")
    assert abs(crew.POWER_FLOOR-power_base(p.CROWN,0)-HINGE_Z)<1e-9
