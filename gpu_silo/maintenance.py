"""Crew access, the pod exchange and the closing exterior orbit. Timing is relative to the full store."""
from . import design as cfg

import math

from . import clock
from . import closing
from . import crew
from . import cargo
from . import services
from . import silo_model as s


POWER_DONE,LID,CREW=clock.POWER_DONE,clock.LID,clock.CREW
SOLID_BEGIN,SOLID_END=clock.SOLID_BEGIN,clock.SOLID_END
ORBIT,ORBIT_DONE=clock.ORBIT,clock.ORBIT_DONE
# The exchange is the last scene. The concrete is see-through again from REPAIR to FINAL.
REPAIR=closing.REPAIR
REPAIR_LENGTH=closing.END-REPAIR
FINAL=closing.FINAL
END=closing.END
# Level selected by the storyboard. Retain the last approved circumferential bay.
LEVEL,BAY=cfg.SERVICE["fault_level"],cfg.SERVICE["fault_bay"]
BAD=(cfg.LEVELS-LEVEL)*cfg.BAYS+BAY-1
PORT=services.PORT_ANGLES[BAY-1]
REGISTER=(s.ENTRY-PORT+math.pi)%(2*math.pi)-math.pi
OFF,ON=(0.,0.,0.),(1.,1.,1.)
DECK_STOW=crew.STOW
# The wide shot of the exchange also takes in the cooler frame being serviced on the ground.
WIDE=(322,918)
WIDE_TARGET=(-4.,-16.,10.)
WIDE_AZIMUTH=-80
def step(a,b,w):
    return s.step(a,b,w)

def bunched(w):
    return step(112,150,w)*(1-step(1103,1142,w))


def registration(w):
    return REGISTER*step(204,299,w)*(1-step(1002,1097,w))


def offset(level,bay):
    rank=(bay-(BAY-1))%cfg.BAYS
    if level==LEVEL:
        signed=(rank+cfg.BAYS//2)%cfg.BAYS-cfg.BAYS//2
        deg=-(360/cfg.BAYS-cfg.STORE["packed_pitch_degrees"])*.8*signed
    elif level%2==0:
        deg=(cfg.BAYS-rank)*(360/cfg.BAYS-cfg.STORE["packed_pitch_degrees"])
    else:
        deg=-(cfg.BAYS if rank==0 else rank)*(360/cfg.BAYS-cfg.STORE["packed_pitch_degrees"])
    # Seven 40-degree spaces and one 80-degree space. The wide opening
    # straddles the transfer ray and accepts an entire 600 mm wide case.
    return math.radians(deg)


def extent(w,index,replacement=False):
    if index==BAD and replacement:return step(1151,1194,w)
    if index==BAD:return 1-step(65,106,w)
    a,b=(65,106) if index%cfg.BAYS==BAY-1 else (73,108)
    return 1-step(a,b,w)+step(1151,1194,w)


def pod_shoe(w,level,bay):
    if level!=LEVEL or bay!=BAY-1:return 1.
    return 1-step(448,458,w)+step(930,943,w)


def old_pose(w):
    seat=cfg.STORE["lowest_berth_m"]+(LEVEL-1)*cfg.STORE["pitch_m"]
    z=seat+.074*step(434,447,w)
    z*=1-step(466,502,w)
    return (14.5*step(509,581,w),4.5*step(588,642,w),z)


def new_pose(w):
    seat=cfg.STORE["lowest_berth_m"]+(LEVEL-1)*cfg.STORE["pitch_m"]
    x=14.5*(1-step(711,790,w))
    y=-4.5*(1-step(649,708,w))
    z=(seat+.074)*step(805,930,w)-.074*step(946,963,w)
    return x,y,z


def hook_z(w,p):
    seat=p.level_z(LEVEL);h=cargo.FRAME_HEIGHT
    v=p.EMPTY_HOOK+(seat+h-p.EMPTY_HOOK)*step(308,433,w)+.074*step(434,447,w)
    v-=(seat+.074)*step(466,502,w)
    v+=.46*step(503,509,w)-.46*step(792,803,w)
    v+=(seat+.074)*step(805,930,w)-.074*step(946,963,w)
    v+=(p.EMPTY_HOOK-seat-h)*step(967,994,w)
    return v


def hook_angle(w):
    aim=(PORT-s.ENTRY)*step(158,194,w)
    # Parked over the ground inlet until the rings are ready, and above the
    # storage crown whenever the empty bridge slews independently.
    az=s.ENTRY+aim+registration(w)
    return az-(PORT-s.ENTRY)*step(1103,1142,w)


def gate_z(w):
    return -.245*step(377,418,w)*(1-step(833,868,w))


def fault_view(cam):
    return cam(s.polar(3.0,PORT,services.port_height(LEVEL)+.55),145,17,19)


def orbit_fraction(t):
    # Two short acceleration ramps leave a constant angular rate for most of the sweep.
    duration=ORBIT_DONE-ORBIT
    x=max(0,min(t-ORBIT,duration))
    ramp=20.
    if x<ramp:distance=x*x/(2*ramp)
    elif x>duration-ramp:distance=duration-ramp-(duration-x)**2/(2*ramp)
    else:distance=x-ramp/2
    return distance/(duration-ramp)


def service_camera(t,section,cam,blend):
    """Camera from the end of the power installation to the last frame."""
    u=orbit_fraction(t)
    ext=cam(EXTERIOR,-62+360*u,15+6*math.sin(math.pi*u)**2,92.0)
    start=cam(EXTERIOR,-62,15,92.0)
    if t<CREW:return section
    if t<SOLID_BEGIN+8:return crew_camera(t-CREW,cam,blend,section)
    if t<ORBIT:return vent_camera(t,cam,blend,start)
    if t<REPAIR:return ext
    return repair_camera(t-REPAIR,cam,blend,start)


EXTERIOR=(0,0,14.6)


def door_view(cam):
    return cam(s.polar(s.RO+.4,s.ENTRY,1.5),math.degrees(s.ENTRY)+38,9,13.5)


def vent_camera(t,cam,blend,start):
    """Close on the door plug, rise to the roof vents, then pull back for the orbit."""
    door=door_view(cam)
    roof=cam((0,0,s.WALL_HEIGHT+.6),math.degrees(s.ENTRY)+20,36,31)
    if t<clock.DOOR[1]+26:return door
    if t<clock.ROOF[1]+4:return blend(door,roof,step(clock.DOOR[1]+26,clock.ROOF[0]-6,t))
    return blend(roof,start,step(clock.ROOF[1]+4,ORBIT-2,t))


def crew_camera(w,cam,blend,section):
    entry=cam(s.polar(3.10,s.ENTRY,.92),-48,31,13.6)
    lift=cam((.55,-.7,10.7),-70,17,47)
    pod=cam(s.polar(3.64,s.ENTRY,8.57),-46,10,12.6)
    power=cam(s.polar(2.3,s.ENTRY+crew.POWER_BAY*2*math.pi/cfg.BAYS,crew.POWER_FLOOR+1.05),math.degrees(s.ENTRY)+crew.POWER_BAY*360/cfg.BAYS-34,9,13.4)
    down=cam((0,0,10.1),-58,18,48)
    if w<62:return blend(section,entry,step(0,53,w))
    if w<225:return blend(entry,lift,step(106,205,w))
    if w<352:return blend(lift,pod,step(248,295,w))
    if w<clock.ENCLOSURE_CLOSE[0]-CREW+6:return blend(pod,power,step(352,404,w))
    return blend(power,door_view(cam),step(clock.ENCLOSURE_CLOSE[0]-CREW+6,SOLID_BEGIN-CREW+4,w))


def repair_camera(w,cam,blend,exterior):
    target=fault_view(cam)
    tower=cam((0,0,10.4),146,20,48)
    side=cam((.7,-1.2,9.7),-75,15,45)
    door=cam(s.polar(s.RO-.10,s.ENTRY,1.35),-100,20,31)
    yard=cam(s.polar(12.,s.ENTRY,1.4),-102,27,35)
    final=cam(s.polar(3.3,PORT,services.port_height(LEVEL)+.40),149,17,21)
    if w<60:return target
    if w<190:return blend(target,tower,step(70,125,w))
    if w<300:
        u=step(198,299,w)
        return cam((.7*u,-1.2*u,10.4-.7*u),146+139*u,20-5*u,48-3*u)
    # Zoom out. The pod exchange at the door and the cooler service beside it share one shot.
    wide=cam(WIDE_TARGET,WIDE_AZIMUTH,19,134)
    if w<WIDE[1]:return blend(side,wide,step(WIDE[0],WIDE[0]+62,w))
    if w<999:return blend(wide,side,step(WIDE[1],WIDE[1]+70,w))
    if w<1105:
        u=step(1002,1097,w)
        return cam((.7*(1-u),-1.2*(1-u),9.7+.7*u),285-139*u,15+5*u,45+3*u)
    if w<1200:return blend(tower,final,step(1121,1189,w))
    return blend(final,exterior,step(1203,FINAL[1]-REPAIR-2,w))


def yard_station(p):
    m=p.newsteel("Flush external transfer table and transverse guides")
    for y in (-4.5,0,4.5):
        for x in (15.1,20.7):
            p.end_box(m,x-.085,y-.92,x+.085,y+.92,-.16,-.018,"768681")
        for sy in (-.32,.32):
            p.end_box(m,14.75,y+sy-.032,20.93,y+sy+.032,-.12,-.015,"888d80")
    for x in (15.35,20.15):
        p.end_box(m,x-.065,-5.1,x+.065,5.1,-.095,-.013,"9b937d")
    for x in (14.85,20.75):
        for y in (-4.5,4.5):
            p.end_box(m,x-.055,y-.67,x+.055,y+.67,.006,.027,"d2ac77")
    return m


def install(scene,node,p):
    begin=p.FILLED+REPAIR
    duration=REPAIR_LENGTH
    def later(fn):
        vals=[fn(w) for w in range(duration)]
        return [(begin+w,v) for w,v in p.flat_keys(vals)]
    lookup={v["name"]:i for i,v in enumerate(scene.nodes)}
    def overwrite_after(i,prop,fn,initial):
        item=scene.nodes[i]
        keys=item["tracks"].get(prop,[(0,initial)])
        before=[(t,v) for t,v in keys if t<begin]
        at=s.at(keys,begin) if keys else initial
        after=later(fn)
        assert all(abs(x-y)<.001 for x,y in zip(at,after[0][1])),(item["name"],prop,at,after[0][1])
        item["tracks"][prop]=before+after
    def initial_curve(fn):
        curve=later(fn)
        return [(0,curve[0][1])]+curve
    def appear(f):return [(0,OFF),(f-.01,OFF),(f,ON)]
    def case_name(index):return f"Pod {index+1:03}"
    node("Swap | ground transfer tracks",scene.mesh(yard_station(p)),"Replacement handling",ang=p.ENTRY,
         tracks={"scale":appear(begin-12)})
    for level in range(1,cfg.LEVELS+1):
        level_node=lookup[f"Level {level:02} | independently indexed carrier"]
        rest=p.ENTRY+p.UNIFORM*.5-p.TAU
        overwrite_after(level_node,"yaw",lambda w:(rest+registration(w),),(rest,))
        for bay in range(cfg.BAYS):
            idx=(cfg.LEVELS-level)*cfg.BAYS+bay
            slot=lookup[f"L{level:02} / bay {bay+1:02} | angular carriage"]
            right=bay*p.UNIFORM
            overwrite_after(slot,"yaw",lambda w:(right+offset(level,bay)*bunched(w),),(right,))
            label=case_name(idx)
            plug=lookup[label+" | retractable service plug"]
            lamp=lookup[label+" | fluid and power online"]
            overwrite_after(plug,"scale",lambda w:(extent(w,idx),1,1),ON)
            overwrite_after(lamp,"scale",lambda w:ON if extent(w,idx)>.995 else OFF,ON)
            if idx!=BAD:continue
            shoe=lookup[f"L{level:02}B{bay+1:02} shaft root lock"]
            overwrite_after(shoe,"scale",lambda w:(pod_shoe(w,level,bay),1,1),ON)
            old=lookup[label+f" | L{level:02} B{bay+1:02}"]
            # The defective pod retains its original object and complete construction
            # history. Its final stop is a separate quarantine track outside the silo.
            # After withdrawal and side transfer, counter-rotate its root relative to
            # the returning store. Hold both the case and its position fixed on site.
            def yard_position(w):
                if w<=1002:return old_pose(w)
                a=-(registration(w)-REGISTER)
                x,y,z=old_pose(w)
                return (x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),z)
            overwrite_after(old,"translation",yard_position,(0,0,p.level_z(level)))
            overwrite_after(old,"yaw",lambda w:(-(registration(w)-REGISTER) if w>1002 else 0.,),(0.,))
            node("Swap | amber fault case",scene.mesh(cargo.mesh("fault",cfg.extension(BAD+1))),"Swap markings",old,
                 tracks={"scale":appear(begin+34)})
            # The fault changes the end tabs on the same full-size frame.
            node(f"Original pod {BAD+1:03} | bronze before fault",scene.nodes[old]["mesh"],"Pod finish",old,
                 tracks={"scale":[(0,ON),(begin+33.99,ON),(begin+34,OFF)]})
            scene.nodes[old]["mesh"]=-1
            fresh=node(f"Replacement {cfg.TOTAL+1:03} | L{LEVEL:02} B{BAY:02}",scene.mesh(cargo.mesh("spare",cfg.extension(cfg.TOTAL+1))),"Replacement pod",slot,
                       tracks={"scale":appear(begin+300)})
            def fresh_loc(w):
                # Stage on a fixed world-space siding until the store reaches the
                # portal. The case remains stationary throughout its visible wait.
                if w>=299:return new_pose(w)
                a=REGISTER-registration(w);x,y,z=new_pose(w)
                return (x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),z)
            scene.nodes[fresh]["tracks"]["translation"]=initial_curve(fresh_loc)
            new_tip=cargo.OUTER+cfg.extension(cfg.TOTAL+1)
            new_parts=[scene.mesh(m) for m in services.moving_parts(new_tip)]
            node(f"Replacement {cfg.TOTAL+1:03} | flush service socket",new_parts[0],"Replacement services",fresh,
                 t=(0,0,p.POD_H/2))
            node(f"Replacement {cfg.TOTAL+1:03} | retractable service plug",new_parts[1],"Replacement services",fresh,
                 t=(new_tip,0,p.POD_H/2),tracks={"scale":initial_curve(lambda w:(extent(w,BAD,True),1,1))})
            node(f"Replacement {cfg.TOTAL+1:03} | fluid and power online",new_parts[2],"Replacement services",fresh,
                 t=(0,0,p.POD_H/2),tracks={"scale":initial_curve(lambda w:ON if extent(w,BAD,True)>.995 else OFF)})
    hoist=lookup["Slewing two-point hoist bridge"]
    overwrite_after(hoist,"yaw",lambda w:(hook_angle(w),),(p.ENTRY,))
    hooks=lookup["Twin self-releasing pickup heads"]
    line=lookup["Twin suspension ropes"]
    for i in (line,hooks):overwrite_after(i,"translation",lambda w:(0,0,hook_z(w,p)),(0,0,p.EMPTY_HOOK))
    overwrite_after(line,"scale",lambda w:(1,1,p.HEAD-hook_z(w,p)),(1,1,p.HEAD-p.EMPTY_HOOK))
    overwrite_after(lookup["Portal rail insert"],"translation",lambda w:(0,0,gate_z(w)),(0,0,0))
    scene.inspection_windows=((p.FILLED+CREW,p.FILLED+(SOLID_BEGIN+SOLID_END)//2),(p.FILLED+REPAIR,p.FILLED+sum(FINAL)//2))
    scene.power_detail=(p.FILLED+CREW+384,p.FILLED+clock.ENCLOSURE_CLOSE[1]+30)
    scene.project_info.update(servicePlatforms=cfg.BAYS,serviceCrewCount=sum(crew.SIZES),crewByWedge=list(crew.SIZES),
        crewDestinations=["Lower power unit" if n==0 else f"Level {n}" for n in crew.LEVELS],
        powerServiceDeckElevation_m=crew.POWER_DECK,crewSceneStart_s=(p.FILLED+CREW)/p.FPS,
        replacementSceneStart_s=(p.FILLED+REPAIR)/p.FPS,
        finalExteriorSweep_deg=360,exteriorSweepStart_s=(p.FILLED+ORBIT)/p.FPS,defectivePod=BAD+1,serviceLevel=LEVEL,
        serviceBay=BAY,neighboursAbove=cfg.LEVELS-LEVEL,neighboursBelow=LEVEL-1,replacementPod=cfg.TOTAL+1,
        serviceRegister_deg=math.degrees(REGISTER),finalLivePods=cfg.TOTAL)
