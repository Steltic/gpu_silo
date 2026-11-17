"""Jumpforming, a tandem crane pick, the dry cooler frames and a ground-fed rotating pod store. Metres, Z up."""
from . import design as cfg

import argparse
import bisect
import math
import struct
from pathlib import Path

from . import silo_model as s
from . import services
from . import plant
from . import cooler_frames as frames
from . import calcs
from . import clock
from . import closing
from . import crane
from . import fuel
from . import service
from . import crew
from . import cargo
from . import yard
from . import site
from . import jumpform
from . import logistics
from . import programme
from . import traffic
from . import maintenance as care
import sys


FPS, C = s.FPS, s.FRAMES
TAU, ENTRY = s.TAU, s.ENTRY
POD_L, POD_W, POD_H = cargo.LENGTH, cargo.BODY_WIDTH, cargo.BODY_HEIGHT
LEVELS, BAYS, PITCH = cfg.LEVELS, cfg.BAYS, cfg.STORE["pitch_m"]
TOTAL = LEVELS*BAYS
INNER, OUTER = cargo.INNER, cargo.OUTER
PICKUPS = (INNER+.158*POD_L, INNER+.838*POD_L)
RIM = s.RI-.052
BASE = cfg.STORE["lowest_berth_m"]
SHAFT, HEAD = cfg.STORE["shaft_radius_m"], cfg.CROWN-1.16
EMPTY_HOOK = HEAD-.12
HEAD_BEAM = cfg.CROWN-.82
CROWN = cfg.CROWN
UNIFORM, PACKED = TAU/BAYS, math.radians(cfg.STORE['packed_pitch_degrees'])
SWEEP = 2.5*UNIFORM
FAST_RATE=cfg.MOVIE['lower_tier_speed']
PICK_X = -23.0
STEEL_START, STEEL_END = C+8, C+337
FIRST_POD = yard.INSERT_AT+yard.DELIVERY_FRAMES+8
PORTAL_VIEW = C+48
LOAD_TIP = 33.0
ON, OFF = (1.,1.,1.), (0.,0.,0.)
STEEL = "466460"
DARK = "344d50"
MINT = "819a87"
OCHRE = "d69751"
CABLE = "5d5445"


def normal_motion(i):
    if i==0: return 151
    if i==1: return 44
    if i==BAYS: return 111
    if i==TOTAL-1: return 82
    if i%BAYS==0: return 46
    if i%BAYS==BAYS-1: return 35
    return 24


def dock_frames(i):
    return 32 if i==0 else 8 if i==BAYS else 3


def playback_frame(source):
    return int(source) if source<=SWITCH_SOURCE else SWITCH_SOURCE+math.ceil((source-SWITCH_SOURCE)/FAST_RATE)


SOURCE_STARTS=[FIRST_POD]
for index in range(TOTAL):
    pause=12 if index%BAYS==BAYS-1 and index!=TOTAL-1 else 0
    # Borrow time from the accelerated approach of the first two tiers. Only
    # their first example adds a full new hold to the original storyboard.
    motion=normal_motion(index)-(dock_frames(index) if 0<index<2*BAYS else 0)
    SOURCE_STARTS.append(SOURCE_STARTS[-1]+motion+dock_frames(index)+pause)
SWITCH_SOURCE=SOURCE_STARTS[2*BAYS]
STARTS=[playback_frame(v) for v in SOURCE_STARTS]
SPEED_FRAME=STARTS[2*BAYS]
FILLED=STARTS[-1]
FRAMES=FILLED+closing.END
RESTORE=FILLED+(care.SOLID_BEGIN+care.SOLID_END)//2
# The concrete is see-through a second time for the replacement scene that ends the film.
REGHOST=FILLED+care.REPAIR
RESTORE2=FILLED+sum(care.FINAL)//2
CUTAWAY=[(RESTORE-.01,0),(RESTORE,1),(REGHOST-.01,1),(REGHOST,0),(RESTORE2-.01,0),(RESTORE2,1)]
if frames.END>FILLED-8:
    raise ValueError("The cooler frames finish after the pods. Shorten installation.repeat_cycle_frames.")
SOURCE_END=SOURCE_STARTS[-1]


def source_time(frame):
    return min(SOURCE_END,frame if frame<SPEED_FRAME else round(SPEED_FRAME+FAST_RATE*(frame-SPEED_FRAME),7))


def motion_ticks(i):
    return normal_motion(i)-(dock_frames(i) if 0<i<2*BAYS else 0)


def smooth(u,a,b):
    return s.step(a,b,u)


def mix(a,b,t):
    return a+(b-a)*t


def level_z(level):
    return BASE+(level-1)*PITCH


def lift_state(frame):
    src=source_time(frame)
    i=min(TOTAL-1,max(0,bisect.bisect_right(SOURCE_STARTS,src)-1))
    ticks=motion_ticks(i)
    local=max(0,src-SOURCE_STARTS[i])
    before=.91*ticks
    dock=s.clamp((local-before)/dock_frames(i))
    after=s.clamp((local-before-dock_frames(i))/(ticks-before))
    u=s.clamp(local/ticks,0,.91) if local<=before else .91+.09*after
    level=LEVELS-i//BAYS
    seat=level_z(level)
    # The return is delayed until the hooks have cleared every occupied storey.
    travel=smooth(u,.30,.69)
    release=smooth(u,.91,.966)
    angle=SWEEP*travel*(1-release)
    bunch=smooth(u,.115,.245)*(1-smooth(u,.925,.964))
    incoming=smooth(u,0,.225)
    carried_z=(seat+.062)*travel-.062*smooth(u,.745,.805)
    hook_z=mix(EMPTY_HOOK,cargo.FRAME_HEIGHT,smooth(u,.025,.28))
    if u>=.28: hook_z=cargo.FRAME_HEIGHT+carried_z
    hook_z=mix(hook_z,EMPTY_HOOK,smooth(u,.811,.891))
    if u<.225: label="Feed through portal"
    elif u<.30: label="Engage twin pickups"
    elif u<.695: label="Spiral to level"
    elif u<.807: label="Engage the shaft lock"
    elif u<.902: label="Release and retract"
    elif local<before+dock_frames(i): label="Connect the pod"
    else: label="Index the next bay"
    return dict(i=i,j=i%BAYS,level=level,u=u,theta=angle,bunch=bunch,feed=incoming,
                pod_z=carried_z,hook_z=hook_z,phase=label,
                count=i+int(u>=.807),new_shoe=smooth(u,.692,.751),dock=dock,
                mobility=1-smooth(u,.91,.966),reindex=release,source=src)


def arriving_link(st):
    return smooth(st['dock'],.03,.33)


def dock_extension(frame,st,index):
    if frame<FIRST_POD or index>st['i']: return 0.
    if frame>=FILLED:return 1.
    # All occupied higher tiers and all occupied bays on this tier move;
    # every connection is stowed before their first angular displacement.
    if .907<=st['u']<=.91 and (index==st['i'] or index//BAYS==st['i']//BAYS):
        return arriving_link(st)*(1-smooth(st['dock'],.76,1.0))
    if index==st['i']: return smooth(st['u'],.970,.996)
    return 1-smooth(st['u'],.002,.098) if st['u']<.5 else smooth(st['u'],.970,.996)


def carrier_yaw(st,level,frame):
    if frame<FIRST_POD or st['level']>level: return ENTRY+UNIFORM*.5
    if frame>=FILLED or st['level']<level:
        return ENTRY+UNIFORM*.5+(0 if frame>=FILLED else st['theta'])-TAU
    j=st['j']
    left_park=smooth(st['u'],.115,.245)
    return (ENTRY+UNIFORM*.5-j*UNIFORM+st['theta']
            -UNIFORM*.5*left_park*st['mobility']-UNIFORM*st['reindex'])


def rack_pose(frame):
    t=frame-C
    x=mix(PICK_X,0,smooth(t,118,189))
    z=LOAD_TIP*smooth(t,39,111)*(1-smooth(t,195,298))
    return (x,0,z)


def liquid_level(frame):
    """Water-glycol rises behind the cage lift and reaches the rim before the pods arrive."""
    rising=.55*smooth(frame,C,clock.CAGE_END)+.45*smooth(frame,*clock.STORE_FILL)
    return cfg.LIQUID_TOP*rising


def camera(center,az,el,d):
    a,b=map(math.radians,(az,el))
    v=(math.cos(a)*math.cos(b),math.sin(a)*math.cos(b),math.sin(b))
    return {"target":center,"eye":s.plus(center,s.times(v,d)),"fov":33.}


def blend(a,b,x):
    return {k:tuple(mix(p,q,x) for p,q in zip(a[k],b[k])) for k in ("eye","target")}|{"fov":33.}


def frames_camera(frame):
    """Follow the crawler round the silo while the pods load, with a close look at the first seat."""
    bearing=math.degrees(frames.crane_bearing(min(frame,frames.END)))
    follow=camera((0,0,15.5),bearing+54*frames.SIDE,18,112)
    a,b,c,d,e,r,g,end=frames.times(0)
    k=frames.ORDER[0];theta=frames.THETA[0]
    near=frames.side(0)
    seat=camera(s.polar(frames.BACK+1.0,theta+.16*near,frames.base(k)+4.2),math.degrees(theta)+42*near,5,62)
    near=smooth(frame,d-22,e+2)*(1-smooth(frame,g-4,end+14))
    return blend(follow,seat,near)


def construction_camera(frame):
    if frame<C: return s.camera_at(frame)
    t=frame-C
    cam=camera
    if frame>=FILLED+care.REPAIR:
        return plant.camera_power(sys.modules[__name__],frame,None,cam,blend)
    if frame>=FILLED+closing.FUEL:
        orbit_end=plant.camera_power(sys.modules[__name__],FILLED+care.ORBIT_DONE,None,cam,blend)
        return fuel.camera(min(frame-FILLED,closing.FUEL_END),orbit_end,cam,blend)
    # Wide view includes both picks, their hooks and the entire receiving shell.
    w=cam((-10,0,26.0),-65,11.8,130)
    if t<58: return blend(s.camera_at(C-1),w,smooth(t,0,54))
    if t<188: return w
    install=cam((-.8,0,17),-59,19,85)
    if frame<clock.CAGE_END: return blend(w,install,smooth(t,185,307))
    store=cam((0,0,24.5),-59,31,60)
    if frame<yard.INSERT_AT: return blend(install,store,smooth(frame,clock.CAGE_END,clock.CAGE_END+64))
    close=cam((3.4,-2.1,3.5),-110,16,36)
    if frame<yard.INSERT_AT+yard.DELIVERY_FRAMES:
        return yard.delivery_camera(frame,sys.modules[__name__])
    if frame<FIRST_POD:
        return yard.delivery_camera(yard.INSERT_AT+yard.DELIVERY_FRAMES-1,sys.modules[__name__])
    elapsed=frame-FIRST_POD
    if elapsed<40:
        terminal=yard.delivery_camera(yard.INSERT_AT+yard.DELIVERY_FRAMES-1,sys.modules[__name__])
        return blend(terminal,close,smooth(elapsed,0,28))
    middle=cam((0,0,14.3),-55,24,62)
    if elapsed<151:
        return blend(close,middle,smooth(elapsed,44,106))
    follow=frames_camera(frame)
    if frame>=FILLED:
        return plant.camera_power(sys.modules[__name__],frame,follow,cam,blend)
    # Pull back to take in the crawler and the cooler frames while the pods keep loading.
    return blend(middle,follow,smooth(elapsed,151,188))


def annulus(m,ri,ro,z0,z1,color,start=0,end=TAU,n=36):
    s.sector(m,ri,ro,z0,z1,start,end,n,[color,color,color,color],caps=end-start<TAU-.0001)


def end_box(m,x0,y0,x1,y1,z0,z1,col):
    s.box(m,x0,y0,x1,y1,z0,z1,col)
    m.face([(x0,y1,z0),(x1,y1,z0),(x1,y0,z0),(x0,y0,z0)],col)


def newsteel(name):
    m=s.Mesh(name);m.material=3;return m


def cage_mesh():
    m=newsteel("Steel module | shaft, bearings, rim girders and braced columns")
    annulus(m,0,SHAFT,-.08,CROWN,"617b79",n=28)
    annulus(m,0,.78,-.08,.18,DARK,n=24)
    for a in [j*TAU/12 for j in range(12)]:
        x,y,_=s.polar(.69,a,0)
        end_box(m,x-.036,y-.036,x+.036,y+.036,.18,.235,"b69b70")
    # A recessed base grille and overhead crown connect the inner and outer structures.
    for j in range(BAYS):
        a=ENTRY+(j+.5)*UNIFORM
        for z in (-.22,CROWN-.18):
            s.bar(m,s.polar(.48,a,z),s.polar(RIM,a,z),.20,STEEL,.25)
    perimeter_posts=24
    for j in range(perimeter_posts):
        a=ENTRY+(j+.5)*TAU/perimeter_posts
        p=s.polar((s.RI-0.065),a,0)
        s.bar(m,p,s.polar((s.RI-0.065),a,CROWN),.078,STEEL)
        x,y,z=p
        end_box(m,x-.039,y-.039,x+.039,y+.039,-.05,.13,DARK)
    for level in range(1,LEVELS+1):
        z=level_z(level)
        # A walkway ring between the shaft and the pod roots lets people pass from sector to sector.
        # It sits just under the pods, with a gangway out to each wedge deck.
        annulus(m,SHAFT+.22,INNER-.10,z-.13,z-.09,"cfd3c8",n=40)
        annulus(m,INNER-.12,INNER-.04,z-.20,z-.06,STEEL,n=40)
        annulus(m,INNER-.12,INNER-.08,z+.95,z+1.0,"ddb477",n=40)
        for j in range(BAYS):
            a=ENTRY+j*UNIFORM
            if level>1 or j:
                s.bar(m,s.polar(INNER-.1,a,z-.11),s.polar(crew.PLATE_IN-.06,a,z-.11),.80,"cfd3c8",.04)
            s.bar(m,s.polar(.78,a+UNIFORM/2,z-.17),s.polar(INNER-.08,a+UNIFORM/2,z-.17),.12,STEEL,.10)
        annulus(m,.48,.792,z+cargo.FRAME_HEIGHT-.125,z+cargo.FRAME_HEIGHT-.03,STEEL,n=28)
        annulus(m,.46,.77,z-.18,z-.045,STEEL,n=28)
        annulus(m,.685,.79,z-.11,z-.025,MINT,n=28)
        gap=math.radians(5.0) if level==1 else 0
        annulus(m,(s.RI-0.085),(s.RI-0.030),z-.17,z-.035,STEEL,ENTRY+gap,ENTRY+TAU-gap)
        annulus(m,(s.RI-0.100),(s.RI-0.040),z-.06,z-.01,MINT,ENTRY+gap,ENTRY+TAU-gap)
        for j in range(BAYS):
            a=j*UNIFORM
            s.bar(m,s.polar(.48,a,z-.14),s.polar(.74,a,z-.14),.14,STEEL,.16)
        for j in range(perimeter_posts):
            if j%4 not in (0,2) or j%3==1: continue
            a=ENTRY+(j+.5)*TAU/perimeter_posts
            # Frame a service window at the middle of every 45-degree bay.
            b=a+TAU/perimeter_posts*(1 if j%3==2 else -1)
            if level==1 and max(abs(math.sin((a-ENTRY)/2)),abs(math.sin((b-ENTRY)/2)))<.18: continue
            # The narrow radial allowance requires a curved brace laid against
            # the envelope. Short faceted segments follow the ring between posts.
            for segment in range(5):
                t=segment/5;u=(segment+1)/5
                s.bar(m,s.polar((s.RI-0.045),mix(a,b,t),z+.01+t*(PITCH-.27)),
                        s.polar((s.RI-0.045),mix(a,b,u),z+.01+u*(PITCH-.27)),.048,"678078")
    annulus(m,(s.RI-.105),(s.RI-.026),HEAD_BEAM-.19,HEAD_BEAM-.03,MINT)
    annulus(m,(s.RI-0.110),(s.RI-.024),CROWN-.32,CROWN-.10,STEEL)
    annulus(m,.48,.88,HEAD_BEAM-.12,HEAD_BEAM+.07,DARK,n=28)
    annulus(m,.45,.74,CROWN-.31,CROWN-.02,STEEL,n=24)
    return m


def bridge_mesh():
    m=newsteel("Slewing two-point hoist bridge")
    for y in (-.20,.20):
        end_box(m,.55,y-.045,(s.RI-0.053),y+.045,HEAD_BEAM,HEAD_BEAM+.13,"b47942")
        end_box(m,.62,y-.036,(s.RI-0.100),y+.036,HEAD_BEAM+.41,HEAD_BEAM+.48,"d6a362")
        for j in range(8):
            step=(s.RI-.80)/8
            x=.62+j*step
            s.bar(m,(x,y,HEAD_BEAM+.10),(x+step-.01,y,HEAD_BEAM+.43),.047,OCHRE)
    for r in PICKUPS:
        end_box(m,r-.19,-.23,r+.19,.23,HEAD-.015,HEAD_BEAM+.23,"966b41")
    return m


def loading_dock():
    m=newsteel("Flush portal and intake roller bed")
    for rr in (s.RO+.055,s.RI-.035):
        for w in (-(s.OPENING_WIDTH/2+.063),s.OPENING_WIDTH/2+.063):
            end_box(m,rr-.087,w-.056,rr+.087,w+.056,0,s.OPENING_HEIGHT+.14,STEEL)
        end_box(m,rr-.087,-s.OPENING_WIDTH/2-.119,rr+.087,s.OPENING_WIDTH/2+.119,s.OPENING_HEIGHT,s.OPENING_HEIGHT+.14,STEEL)
    for y in (-.30,.30):
        end_box(m,s.RO+.10,y-.038,s.RO+8.0,y+.038,-.095,-.008,DARK)
    for j in range(21):
        x=s.RO+.10+j*.385
        end_box(m,x-.06,-.32,x+.06,.32,-.064,.0,"9a9d92")
    for y in (-.56,.56):
        end_box(m,s.RO+.12,y-.035,s.RO+8.05,y+.035,.012,.044,"c58c4f")
    return m


def casing(lite=False):
    m=s.Mesh("Ghosted concrete | "+("rim, joints and door" if lite else "surfaces"))
    m.material=2 if lite else 1
    for ri,ro in [(s.RI,s.RO_INNER),(s.RI_OUTER,s.RO)]:
        if lite:
            for z in [3,9,15,21,27,30]:
                annulus(m,ro-.051,ro+.021,z-.033,z+.021,"87a9b0")
            for y in (-(s.OPENING_WIDTH/2+.015),s.OPENING_WIDTH/2+.015):
                cs,sn=math.cos(ENTRY),math.sin(ENTRY)
                x=math.sqrt(ro*ro-y*y)
                a=(x*cs-y*sn,x*sn+y*cs,0)
                s.bar(m,a,(a[0],a[1],s.OPENING_HEIGHT),.03,"81bbc0")
            continue
        partial=s.Mesh("Portal skin")
        annulus(partial,ri,ro,0,3,"b6cdcb",n=64)
        m.tris.extend(s.door_cut(partial,ri,ro,True).tris)
        annulus(m,ri,ro,3,s.WALL_HEIGHT,"bfd1cc",n=64)
    return m


def crane_lower():
    m=newsteel("Crawler undercarriage")
    for yy in (-1.37,1.37):
        end_box(m,-2.85,yy-.34,2.85,yy+.34,.0,.66,"46504b")
        for j in range(10):
            x=-2.58+j*.55
            end_box(m,x-.11,yy-.355,x+.11,yy+.355,.11,.50,"6d7265")
    end_box(m,-2.17,-1.20,1.84,1.20,.59,1.28,"8b7651")
    annulus(m,0,1.20,1.18,1.53,"6a6d5c",n=12)
    return m


def crane_upper():
    m=newsteel("Crawler counterweight and cab")
    end_box(m,-2.65,-1.14,1.46,1.14,1.45,2.42,"c18b49")
    for j in range(4): end_box(m,-3.20,-1.28,-1.87,1.28,1.42+j*.28,1.66+j*.28,"a1895e")
    end_box(m,-.18,-1.53,1.54,-.71,1.78,3.41,"c4965d")
    end_box(m,.19,-1.55,1.41,-1.52,2.41,3.18,"658886")
    return m


BOOM_LENGTH=62.


def boom_mesh():
    m=newsteel("Tapered lattice crane boom")
    rows=[]
    for k in range(19):
        u=k/18
        x,z=17*u,math.sqrt(BOOM_LENGTH**2-17**2)*u
        w=.82*(1-.66*u)
        rows.append([(x+dx*w,y*w,z-dx*w*.282) for dx,y in [(-1,-1),(1,-1),(1,1),(-1,1)]])
    for j,(low,high) in enumerate(zip(rows,rows[1:])):
        for k in range(4):
            n=(k+1)%4
            s.bar(m,low[k],high[k],.13,"b2834a")
            s.bar(m,low[k],high[n],.077,"cfaa6a")
            if j%2==0: s.bar(m,low[k],low[n],.10,"a9824d")
    end_box(m,16.64,-.38,17.36,.38,59.26,59.75,"876e4f")
    return m


def sling_mesh(sign):
    m=newsteel("Two-leg pick bridle and mast sling")
    apex=(0,sign*3.65,CROWN+4.0)
    for x,y in [(-3.30,sign*4.92),(3.30,sign*4.92),(0,sign*.56)]:
        s.bar(m,apex,(x,y,CROWN-.07),.079,"766953")
    end_box(m,-.21,sign*3.65-.16,.21,sign*3.65+.16,CROWN+3.74,CROWN+4.12,"a87b44")
    return m


def flat_keys(values,tol=.000015):
    """Reduce sampled transform curves while retaining pauses, stops and reversals."""
    if not values: return []
    res=[(0,values[0])]
    for i in range(1,len(values)-1):
        a,b,c=values[i-1],values[i],values[i+1]
        if any(abs(x+z-2*y)>tol for x,y,z in zip(a,b,c)): res.append((i,b))
    if len(values)>1: res.append((len(values)-1,values[-1]))
    if all(v==res[0][1] for _,v in res): return [res[0]]
    return res


def build():
    scene=s.build()
    site.ground(scene)
    services.perforate_concrete(scene)
    scene.project_info=dict(clearBore_m=2*s.RI,podLength_m=POD_L,podWidth_m=POD_W,podHeight_m=POD_H,
        storageLevels=LEVELS,podsPerLevel=BAYS,levelPitch_m=PITCH,storageZone_m=LEVELS*PITCH,
        shaftDiameter_m=2*SHAFT,baySpacing_deg=math.degrees(UNIFORM),bunchedPitch_deg=math.degrees(PACKED),
        groundAperture_m=[s.OPENING_WIDTH,s.OPENING_HEIGHT],
        framedPodWidth_m=cargo.FRAME_WIDTH,sideTrussDepth_m=cargo.FRAME_HEIGHT,
        nominalDoorSideClearance_m=cfg.POD["intake_clearance_each_side_m"],nominalDoorHeadClearance_m=cfg.POD["intake_clearance_overhead_m"],
        unitName=cfg.NAME,rackHousingLength_m=cfg.BODY_LENGTH,cduPumpSection_m=cfg.SECTION,cduPumpSectionByUnit_m=cfg.SECTIONS,
        application=cfg.PROJECT["project"]["application"],rackModel=cfg.CLUSTER["rack_model"],gpuRacks=cfg.RACKS,
        liquidHeatLoad_MW=calcs.C["heat_mw"],thermalStore_m3=calcs.C["tank_m3"],thermalStore_USgal=calcs.C["tank_gal"],
        heatRejection_MW=calcs.C["reject_mw"],
        technicalScope="Geometric concept animation; no load or tolerance design.")
    crew.recess_floor(scene)
    scene.camera=[construction_camera(i) for i in range(FRAMES)]
    scene.states=[lift_state(i) for i in range(FRAMES)]
    # Retain every docking and retraction key in the editor, including the
    # subframes between video samples in the 3x section.
    tail=[SPEED_FRAME+(v-SWITCH_SOURCE)/FAST_RATE for v in range(SWITCH_SOURCE+1,SOURCE_END+1)]
    scene.motion_frames=list(range(SPEED_FRAME+1))+tail+([FILLED] if tail[-1]<FILLED else [])+[FRAMES-1]
    scene.motion_states=[lift_state(f) for f in scene.motion_frames]
    def motion_keys(vals):
        compact={i:v for i,v in flat_keys(vals)}
        if len(compact)>1:
            for i in (SPEED_FRAME,len(scene.motion_frames)-2):
                compact[i]=vals[i]
        return [(scene.motion_frames[i],v) for i,v in sorted(compact.items())]
    scene.project_info.update(servicesPerTier=BAYS,totalServiceConduits=TOTAL,
        lowestStationCentre_m=services.PORT_Z,highestStationCentre_m=services.port_height(LEVELS),
        podSleeveTankEnd_m=services.TANK_END,liquidGap_m=s.CLEAR_GAP,
        liquidTarget_m=cfg.LIQUID_TOP,speedChange_s=SPEED_FRAME/FPS,lowerTierPlaybackRate=FAST_RATE,
        serviceConcept="Each pod's CDU pump draws from and returns to the water-glycol store through a self-sealing coupling in the inner wall. Power and data reach each pod through the steel shaft and its root lock.")
    for item in scene.nodes:
        if "concrete wall" in item['group']:
            tr=item['tracks']['scale']
            tr.extend([(PORTAL_VIEW+16,tr[-1][1]),(PORTAL_VIEW+17,OFF)]+[(f,ON if v else OFF) for f,v in CUTAWAY])
    def mesh(m): return scene.mesh(m)
    def node(name,mid,group,parent=-1,ang=0,t=(0,0,0),tracks=None):
        scene.node(name,mid,group,ang,t,tracks)
        scene.nodes[-1]['parent']=parent
        return len(scene.nodes)-1
    show=lambda a:[(0,OFF),(a-1,OFF),(a,ON)]
    scene.fleet=site.Fleet(scene,node,flat_keys,FRAMES);scene.counts={}
    def interval(start,end):
        return show(start)+[(end-1,ON),(end,OFF)]
    jumpform.install(scene,node,sys.modules[__name__])
    scene.liquid=services.add_fixed(scene,node,flat_keys,[liquid_level(f) for f in range(FRAMES)])
    for lite in (False,True):
        m=casing(lite)
        if not lite:m=services.bore_rows(m,0,[services.port_height(l) for l in range(1,LEVELS+1)])
        node(m.name,mesh(m),"Translucent silo",tracks={'scale':show(PORTAL_VIEW+17)+[(f,OFF if v else ON) for f,v in CUTAWAY]})
    dock=loading_dock()
    node(dock.name,mesh(dock),"Intake",ang=ENTRY,tracks={'scale':show(PORTAL_VIEW+17)})
    # This single parent carries the entire empty module during both crane picks.
    rack=node("Preassembled steel store",-1,"Rotating pod store",tracks={
        'translation':flat_keys([rack_pose(f) for f in range(FRAMES)]),'scale':show(STEEL_START)})
    m=cage_mesh();node(m.name,mesh(m),"Structure",rack)
    for sign in (-1,1):
        base=(-11.5,sign*19.3,0)
        tr=[rack_pose(f) for f in range(FRAMES)]
        jog=[smooth(f,C+300,C+344) for f in range(FRAMES)]
        hx=[v[0]-6*j for v,j in zip(tr,jog)]
        hy=[sign*(3.65+7.0*j) for j in jog]
        hook=[CROWN+4+v[2]+29*j for v,j in zip(tr,jog)]
        foot=[base]*FRAMES;heading=[0.]*FRAMES;leaves=C+349
        if sign<0:
            # The south crawler stays for every later lift: cooler frames, power modules, lid and cooler service.
            path,(leaves,returns,departs)=crane.poses(sys.modules[__name__])
            for f,(place,(x,y,z),facing) in path.items():
                foot[f]=place;hx[f],hy[f],hook[f]=x,y,z;heading[f]=facing
        a=[math.atan2(y-b[1],x-b[0])-h for x,y,b,h in zip(hx,hy,foot,heading)]
        for f in range(1,FRAMES):
            a[f]-=TAU*round((a[f]-a[f-1])/TAU)
        dist=[math.hypot(x-b[0],y-b[1]) for x,y,b in zip(hx,hy,foot)]
        tip=[2.45+math.sqrt(BOOM_LENGTH**2-d*d) for d in dist]
        side="North" if sign>0 else "South"
        lower=crane_lower()
        seen=interval(STEEL_START,leaves)
        if sign<0:seen=seen+[(returns-1,OFF),(returns,ON),(departs-1,ON),(departs,OFF)]
        tracks={'scale':seen}
        if sign<0:tracks.update(translation=flat_keys(foot),yaw=flat_keys([(h,) for h in heading]))
        car=node(side+" crawler",mesh(lower),"Tandem crane lift",t=base,tracks=tracks)
        upper=crane_upper()
        cab=node(side+" revolving deck",mesh(upper),"Cranes",car,tracks={'yaw':flat_keys([(v,) for v in a])})
        boom=boom_mesh()
        node(side+" crane boom",mesh(boom),"Cranes",cab,t=(0,0,2.45),
             tracks={'scale':flat_keys([(d/17,1,(v-2.45)/math.sqrt(BOOM_LENGTH**2-17**2)) for d,v in zip(dist,tip)])})
        # The fall and hook block are kept in site coordinates so the travelling crawler can turn beneath them.
        fall=node(side+" crane fall and hook",-1,"Cranes",tracks={'scale':seen})
        rope=newsteel("Crane hoist rope");end_box(rope,-.032,-.032,.032,.032,0,1,CABLE)
        node(side+" crane fall",mesh(rope),"Cranes",fall,
             tracks={'translation':flat_keys(list(zip(hx,hy,hook))),
                     'scale':flat_keys([(1,1,t-z) for t,z in zip(tip,hook)])})
        if sign<0:
            block=newsteel("Retained crawler | hook block")
            end_box(block,-.22,-.17,.22,.17,-.07,.37,OCHRE)
            node("South crawler | retained hook block",mesh(block),"Cranes",fall,
                 tracks={"translation":flat_keys(list(zip(hx,hy,hook))),"scale":show(C+302)})
        m=sling_mesh(sign)
        node(side+" lift slings",mesh(m),"Rigging",rack,tracks={'scale':interval(STEEL_START,C+302)})
    state=scene.motion_states
    def angs(fn):
        return motion_keys([(fn(f,st),) for f,st in zip(scene.motion_frames,state)])
    def arm_angle(i,st):
        return ENTRY + (st['theta'] if i>=FIRST_POD else 0)
    arm=bridge_mesh()
    hoist=node(arm.name,mesh(arm),"Hoist",rack,tracks={'yaw':angs(arm_angle)})
    line=newsteel("Twin suspension ropes")
    for r in PICKUPS:
        end_box(line,r-.027,-.027,r+.027,.027,0,1,"956b3d")
    blocks=newsteel("Twin self-releasing pickup heads")
    for r in PICKUPS:
        end_box(blocks,r-.082,-.084,r+.082,.084,0,.115,"d1a063")
    hs=[EMPTY_HOOK if f<FIRST_POD else st['hook_z'] for f,st in zip(scene.motion_frames,state)]
    trans=motion_keys([(0,0,v) for v in hs])
    node(line.name,mesh(line),"Hoist",hoist,tracks={'translation':trans,'scale':motion_keys([(1,1,HEAD-v) for v in hs])})
    node(blocks.name,mesh(blocks),"Hoist",hoist,tracks={'translation':trans})
    # A sliding segment closes the interruption in the lowest outer race after each entry.
    gate=newsteel("Portal rail insert")
    ga=math.radians(5.)
    annulus(gate,s.RI-.10,s.RI-.03,BASE-.16,BASE-.02,MINT,ENTRY-ga,ENTRY+ga,n=4)
    node(gate.name,mesh(gate),"Intake",rack,tracks={'translation':motion_keys([
        (0,0,-.24*(1-smooth(st['u'],.23,.31))-.24*smooth(st['u'],.90,1)*int(st['i']<TOTAL-1))
        if FIRST_POD<=f<FILLED else (0,0,0) for f,st in zip(scene.motion_frames,state)])})
    cases={}
    mi=mesh(cargo.root_dock())
    levels={}
    for level in range(LEVELS,0,-1):
        levels[level]=node(f"Level {level:02} | independently indexed carrier",-1,"Levels",rack,
            tracks={'yaw':angs(lambda f,st:carrier_yaw(st,level,f))})

    for idx in range(TOTAL):
        level,j=LEVELS-idx//BAYS,idx%BAYS
        start=SOURCE_STARTS[idx] if idx<2*BAYS else SPEED_FRAME+(SOURCE_STARTS[idx]-SWITCH_SOURCE)/FAST_RATE
        extra=cfg.extension(idx+1)
        if extra not in cases:
            cases[extra]=(mesh(cargo.mesh(extra=extra)),[mesh(m) for m in services.moving_parts(OUTER+extra)])
        pod_id,service_meshes=cases[extra]
        seat=level_z(level)
        # Pods share the carrier after seating. Each has its own ground approach
        # and its own vertical track, even during the accelerated middle section.
        local=[]; rot=[]; extension=[]
        for f,st in zip(scene.motion_frames,state):
            if f<start:
                d,z=22.,0
            elif st['i']==idx:
                d,z=22.*(1-st['feed']),st['pod_z']
            else: d,z=0,seat
            local.append((d,0,z))
            packed=st['bunch'] if (st['level']<level and f<FILLED) else 0
            at_gate=-UNIFORM*.5*(1-smooth(st['u'],.115,.245)) if st['i']==idx else 0
            rot.append((j*UNIFORM+at_gate+(j-(BAYS-1)/2)*(PACKED-UNIFORM)*packed,))
            extension.append((0.001 if f<start else st['new_shoe'] if st['i']==idx else 1,1,1))
        slot=node(f"L{level:02} / bay {j+1:02} | angular carriage",-1,"Carriages",levels[level],
                  tracks={'yaw':motion_keys(rot)})
        # Use a slide in the carriage coordinates of the radial pod, with
        # translation applied at the pod node after the parent has rotated.
        body=node(f"Pod {idx+1:03} | L{level:02} B{j+1:02}",pod_id,"Pods",slot,tracks={
            'scale':show(start),'translation':motion_keys(local)})
        node(f"Pod {idx+1:03} | flush service socket",service_meshes[0],"Pod services",body,t=(0,0,POD_H/2))
        ext=[dock_extension(f,st,idx) for f,st in zip(scene.motion_frames,state)]
        node(f"Pod {idx+1:03} | retractable service plug",service_meshes[1],"Pod services",body,
             t=(OUTER+extra,0,POD_H/2),tracks={'scale':motion_keys([(v,1,1) for v in ext])})
        node(f"Pod {idx+1:03} | fluid and power online",service_meshes[2],"Service indicators",body,
             t=(0,0,POD_H/2),tracks={'scale':motion_keys([ON if v>.995 else OFF for v in ext])})
        seat_ext=motion_keys(extension)
        node(f"L{level:02}B{j+1:02} shaft root lock",mi,"Steel shoes",slot,t=(0,0,seat),tracks={'scale':seat_ext})
    frames.add(scene,node,sys.modules[__name__])
    plant.add(scene,node,sys.modules[__name__])
    crew.install(scene,node,sys.modules[__name__],FILLED+care.CREW)
    care.install(scene,node,sys.modules[__name__])
    service.install(scene,node,sys.modules[__name__])
    fuel.install(scene,node,sys.modules[__name__])
    scene.storage_inspection=(FIRST_POD,FILLED+plant.VENT_END)
    traffic.install(scene,node,sys.modules[__name__])
    yard.install_terminal(scene,node,sys.modules[__name__])
    return scene


def render_data(scene,path):
    with open(path,"wb") as file:
        def ints(*v): file.write(struct.pack("<"+"i"*len(v),*v))
        def floats(*v): file.write(struct.pack("<"+"f"*len(v),*v))
        def string(txt):
            b=txt.encode("utf8");ints(len(b));file.write(b)
        file.write(b"GSILO05\0")
        ints(len(scene.meshes),len(scene.nodes),FRAMES,FPS)
        floats(s.RO,s.RI_OUTER,s.RO_INNER,s.RI,s.WALL_HEIGHT,s.LIFT)
        ints(s.COUNT,s.LAST_POUR,s.LAST_POUR+s.REVEAL//2,s.LAST_POUR+s.REVEAL,
             C,PORTAL_VIEW,FIRST_POD,FILLED,SPEED_FRAME)
        ints(*plant.PICK_STARTS,plant.PICK_LENGTH,plant.VENT_START,plant.VENT_END,*plant.LID)
        ints(care.SOLID_BEGIN,care.SOLID_END,care.ORBIT,care.ORBIT_DONE)
        floats(CROWN,cfg.LIQUID_TOP)
        ints(care.CREW,care.REPAIR,care.BAD,care.LEVEL,care.BAY)
        ints(LEVELS,BAYS,TOTAL)
        floats(PITCH,BASE,cfg.BODY_LENGTH,cargo.FRAME_WIDTH,cargo.FRAME_HEIGHT,s.OPENING_WIDTH,s.OPENING_HEIGHT,FAST_RATE)
        floats(*[cfg.length(i) for i in range(1,TOTAL+1)])
        string(cfg.NAME)
        floats(INNER,plant.WIDTH,plant.HEIGHT,plant.LENGTH,plant.STACK_X,SHAFT,plant.power_base(CROWN,0),plant.power_base(CROWN,1),
               s.WALL_HEIGHT+plant.VENT_RISE,plant.LID_Z,services.PORT_Z,plant.POWER_YAW,s.ENTRY);ints(sum(crew.SIZES))
        ints(*crew.LEVELS)
        ints(clock.CAGE_END,*clock.STORE_FILL,yard.INSERT_AT,frames.START,frames.FIRST,frames.END,frames.N,frames.ROWS,frames.FANS)
        floats(frames.WIDTH,frames.HEIGHT,frames.DEPTH,frames.COOL_L,frames.PUMP_L,frames.BACK,frames.D["cooler_capacity_mw"])
        for i in range(frames.N):
            ints(frames.ORDER[i],*frames.times(i))
            floats(frames.base(frames.ORDER[i]),frames.BEARINGS[frames.ORDER[i]])
        # Cooler service, in frames after the pod exchange starts.
        ints(service.K,service.ROW,service.ARRIVE,service.RIG[1],service.DOWN[1],service.DROP,service.INSERT[1],service.RELEASE,service.DONE)
        # Closing scenes, in frames after the store is full.
        ints(closing.FUEL,closing.TANKS,closing.TANK_STEP,*closing.HEADER,*closing.RUN,*closing.RISER,*closing.ROOF,*closing.DROP,
             closing.FUEL_END,closing.PLAN,closing.PLAN_FRAMES,closing.SECTION,closing.SECTION_FRAMES,closing.FADE,fuel.COUNT)
        floats(fuel.BEARING,fuel.FARM_R,fuel.LENGTH,fuel.DIA,fuel.PITCH,fuel.RISER_R,fuel.TOP,fuel.DROP_R,fuel.drop_end(CROWN))
        # Turbine enclosure, the last cutaway and the two power levels.
        ints(*clock.ENCLOSURE_OPEN,*clock.ENCLOSURE_CLOSE,*closing.FINAL,len(plant.GEN_AT))
        floats(cfg.POWER["module_output_mw"],plant.SET_Y,plant.GEN_L,plant.GEN_H,plant.LEVEL[0],plant.EXHAUST_R,plant.INLET_HOUSE[0],
               plant.INLET_HOUSE[2],plant.INLET_AT[0][0],plant.DIESEL_STACK_H,fuel.diesel_end(CROWN),fuel.DROP_R,cfg.STORE["shaft_radius_m"])
        string(cfg.TITLE)
        panels=calcs.panel()
        for rows in (calcs.strip(),calcs.summary(),panels["store"],panels["frames"],panels["fuel"],panels["plan"],panels["section"],
                     panels["turbine"],panels["backup"]):
            ints(len(rows))
            for left,right in rows:string(left);string(right)
        lines=closing.captions()
        ints(len(lines))
        for first,last,text in lines:ints(FILLED+first,FILLED+last);string(text)
        # Truck counts, the lift crew and the 28-day programme.
        for rows in (panels["crew"],panels["dock"]):
            ints(len(rows))
            for left,right in rows:string(left);string(right)
        ints(logistics.DAYS,logistics.C["crew"],len(yard.LOAD_OFFSETS),logistics.C["pods_per_truck"])
        chart=logistics.gantt()
        ints(len(chart))
        for name,first,last in chart:string(name);ints(first,last)
        marks=programme.tags(sys.modules[__name__])
        ints(len(marks))
        for first,last,day,title,note,which in marks:
            ints(first,last);string(day);string(title);string(note);ints(len(which),*which)
        for m in scene.meshes:
            ints(len(m.tris),int(m.terrain),getattr(m,"material",0))
            for a,b,c,col in m.tris:
                floats(*a,*b,*c);file.write(bytes(col))
        for node in scene.nodes:
            typ=1 if "concrete wall" in node['group'] else 2 if node['group']=="Pods" else 0
            if node['name'].endswith("retractable service plug"):typ=3
            if node['group']=="Dry coolers":typ=4
            if node['group'] in s.FRAME_EQUIPMENT:typ=5
            if node['group']=="Crew decks":typ=6
            if node['group']=="Replacement pod":typ=7
            if node['group']=="Silo lid":typ=16
            if node['group']=="Crew poses":typ=9
            if node['group']=="Structure":typ=13
            if node['group']=="Hoist":typ=10+int(node['name']=="Twin self-releasing pickup heads")
            if node['group']=="Replacement services" and node['name'].endswith("retractable service plug"):typ=12
            tracks=node['tracks']
            ints(node['mesh'],node.get('parent',-1),typ)
            floats(*node['translation'],1,1,1,node['angle'])
            for prop in ["translation","scale","yaw"]:
                keys=tracks.get(prop,[])
                if any(isinstance(f,float) and not f.is_integer() for f,_ in keys):
                    keys=flat_keys([s.at(keys,f) for f in range(FRAMES)])
                ints(len(keys))
                for fr,v in keys: ints(int(fr));floats(*v)
        fixings=sorted(n['tracks']['translation'][-1][0] for n in scene.nodes if n['group'] in ("Cooler embeds","Cooler conduits"))
        for frame,(cam,st) in enumerate(zip(scene.camera,scene.states)):
            inf=s.display_info(min(frame,C-1))
            floats(*cam['eye'],*cam['target'],cam['fov'],inf['height'],inf['plan'])
            ints(inf['lift'],int(inf['finish']))
            string(inf['phase'])
            ints(st['i'],st['level'],st['count'] if frame>=FIRST_POD else 0)
            floats(st['u'],st['theta'],st['bunch'],st['pod_z'],st['feed'],st['hook_z'],rack_pose(frame)[2])
            string(st['phase'])
            floats(scene.liquid[frame],st['dock'])
            installed=sum(BAYS for l in range(1,LEVELS+1) if frame>=services.sleeve_frames(l)[1])
            connected=sum(dock_extension(frame,st,j)>.995 for j in range(TOTAL))
            if frame>=FILLED+care.REPAIR:
                w=frame-FILLED-care.REPAIR
                connected=sum(care.extent(w,j)>.995 for j in range(TOTAL))+int(care.extent(w,care.BAD,True)>.995)
            ints(installed,connected)
            ints(bisect.bisect_right(fixings,frame))
            ints(*[scene.counts[name][frame] for name in programme.COUNTERS])


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--glb",type=Path,required=True)
    ap.add_argument("--render-data",type=Path)
    a=ap.parse_args()
    scene=build()
    s.glb_file(scene,a.glb)
    if a.render_data: render_data(scene,a.render_data)
    print(f"{FRAMES} frames, {FRAMES/FPS:.2f} s. {len(scene.nodes)} objects, {len(scene.meshes)} mesh assets.")
