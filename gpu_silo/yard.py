"""Rail terminal and the three-pod flatbed delivery."""
from . import design as cfg

import math

from . import cargo
from . import clock
from . import services
from . import silo_model as s

INSERT_AT=clock.DELIVERY_AT
DELIVERY_FRAMES=clock.DELIVERY_FRAMES
RAIL_OFFSET=22.
LOAD_OFFSETS=tuple(RAIL_OFFSET+sum(cfg.length(i)+.85 for i in range(1,j+1)) for j in range(3))
TRUCK_Y=6.1
DECK=1.33
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


def terminal():
    m=steel("Pod terminal | three receiving cradles and travelling gantry rails")
    box(m,14.62,-.82,42.1,9.25,-.16,-.055,"acae96")
    s.quad_xy(m,18.4,TRUCK_Y-2.22,94.,TRUCK_Y+2.22,-.010,"b8b49d")
    for y in (-.27,.27):
        box(m,15.32,y-.039,40.7,y+.039,-.064,-.008,EDGE)
    for x in range(15,41):
        box(m,x,-.38,x+.055,.38,-.049,-.014,"747e76")
    for i,offset in enumerate(LOAD_OFFSETS):
        for xx in (offset+1.47,offset+5.27):
            box(m,xx-.16,-.46,xx+.16,.46,-.055,-.002,"839390")
            for y in (-1,1):box(m,xx-.15,y*.51-.046,xx+.15,y*.51+.046,0,.13,"bd9255")
    for y in (-1.7,8.82):
        for x in (21.85,30.76,40.):
            box(m,x-.105,y-.105,x+.105,y+.105,0,4.94,IRON)
            box(m,x-.24,y-.24,x+.24,y+.24,0,.12,EDGE)
        box(m,21.4,y-.11,40.46,y+.11,4.83,5.10,EDGE)
    # Partial canopy at the far end leaves all three hoisted pods visible.
    for x in (36.9,40.0):
        box(m,x-.09,-1.7,x+.09,8.82,5.37,5.48,IRON)
    for k in range(12):
        box(m,36.82+k*.29,-1.86,37.09+k*.29,8.98,5.46,5.53,"aeb8af" if k%2 else "a1afa8")
    # Terminal office stays clear of the track and both transfer sidings.
    box(m,21.0,-5.1,26.8,-2.4,0,2.48,"768b84")
    box(m,20.83,-5.25,26.97,-2.24,2.47,2.63,"b4bbae")
    for x in (21.45,22.9,24.35):
        box(m,x,-5.125,x+1.12,-5.10,.91,1.89,"456a72")
    box(m,25.95,-5.13,26.6,-5.10,.05,1.99,"5f6e67")
    return m


def wheel(m,x,y,sign):
    services.pipe(m,(x,y-sign*.125,.49),(x,y+sign*.125,.49),.47,"293238",n=12)
    services.pipe(m,(x,y+sign*.126,.49),(x,y+sign*.158,.49),.245,"88928d",n=10)
    services.pipe(m,(x,y+sign*.159,.49),(x,y+sign*.178,.49),.10,IRON,n=8)


def truck():
    m=steel("Pod flatbed | tractor and extended cargo deck")
    length=LOAD_OFFSETS[-1]-LOAD_OFFSETS[0]+cfg.length(3)+.02
    box(m,-3.03,-.46,length,.46,.58,.85,"414b4c")
    box(m,-3.43,-1.10,-.57,1.10,.73,1.58,"6c938f")
    box(m,-3.07,-1.075,-.64,1.075,1.40,2.68,"7c9d93")
    box(m,-2.99,-1.08,-.72,1.08,2.62,2.79,"c9c7ae")
    box(m,-3.095,-.92,-3.07,.92,1.86,2.51,"5a7880")
    for sign in (-1,1):
        a=sign*1.084
        box(m,-2.9,min(a,a+sign*.017),-1.20,max(a,a+sign*.017),1.89,2.49,"4b6971")
        box(m,-3.455,sign*.70-.17,-3.427,sign*.70+.17,1.10,1.25,"e2c68b")
    box(m,-3.54,-1.13,-3.39,1.13,.66,.86,"a7b0a6")
    box(m,-3.453,-.50,-3.428,.50,.94,1.29,IRON)
    for x in (-2.48,-.02,1.04,length-2.26,length-1.13):
        for sign in (-1,1):wheel(m,x,sign*1.0,sign)
    box(m,-.08,-1.19,length,1.19,.89,1.16,"536667")
    box(m,-.09,-1.19,length,1.19,1.16,DECK,"a2997b")
    for j,offset in enumerate(LOAD_OFFSETS):
        start=offset-LOAD_OFFSETS[0]
        for x in (start+.17,start+cfg.length(j+1)-.17):
            for y in (-1.2,1.2):box(m,x-.065,y-.025,x+.065,y+.025,1.06,1.33,"d4af6b")
    return m


def bridge_mesh():
    m=steel("Terminal bridge | cross girder and twin end trucks")
    for x in (-.37,.37):box(m,x-.063,-1.78,x+.063,8.89,5.02,5.26,"b18c56")
    for y in (-1.70,8.82):box(m,-.52,y-.15,.52,y+.15,4.98,5.21,IRON)
    return m


def install_terminal(scene,node,p):
    start=INSERT_AT
    def show(t0,t1=None):
        k=[(0,OFF),(t0-.02,OFF),(t0,ON)]
        if t1 is not None:k.extend([(t1-.02,ON),(t1,OFF)])
        return k
    def relative(keys):return [(start+t,v) for t,v in keys]
    def absolute(keys):return [(0,keys[0][1])]+relative(keys)
    def compact(fn):
        vals=[fn(i) for i in range(DELIVERY_FRAMES+1)]
        return absolute(p.flat_keys(vals))
    yard=node("Rail terminal and manoeuvring apron",scene.mesh(terminal()),"Terminal infrastructure",ang=p.ENTRY,
              tracks={"scale":show(start)})
    primary=LOAD_OFFSETS[0]+cargo.INNER
    def truck_offset(f):
        elapsed=f-start
        return 45*(1-s.step(0,49,elapsed))+46*s.step(285,329,elapsed)
    flat=node("Terminal | initial three-pod delivery truck",scene.mesh(truck()),"Road delivery",yard,
        tracks={"translation":compact(lambda i:(primary+truck_offset(start+i),TRUCK_Y,0)),"scale":show(start,start+331)})
    bridge=scene.mesh(bridge_mesh())
    trolley=steel("Terminal trolley | powered hoist drums")
    box(trolley,-.61,-.34,.61,.34,4.94,5.34,"8c998a")
    carrier=steel("Terminal lifting spreader | two pickup points")
    box(carrier,-1.83,-.12,1.83,.12,0,.092,"c59d63")
    rope=steel("Terminal hoist | two falls")
    for r in (-1.65,1.65):box(rope,r-.018,-.02,r+.018,.02,0,1,"56534b")
    centres=[offset+cargo.INNER+cfg.length(i+1)/2 for i,offset in enumerate(LOAD_OFFSETS)]
    def axis(t):
        if t<55:return (centres[0],TRUCK_Y,4.62)
        idx=min(2,int((t-55)//75));u=(t-55)-idx*75
        x=centres[idx]
        if u>=61 and idx<2:x+=(centres[idx+1]-centres[idx])*s.step(61,75,u)
        y=TRUCK_Y*(1-s.step(20,39,u))+TRUCK_Y*s.step(62,74,u)*int(idx<2)
        z=4.62+(DECK+cargo.FRAME_HEIGHT-4.62)*s.step(0,8,u)+(4.18-DECK-cargo.FRAME_HEIGHT)*s.step(10,17,u)
        z+=(cargo.FRAME_HEIGHT-4.18)*s.step(40,51,u)+(4.62-cargo.FRAME_HEIGHT)*s.step(52,62,u)
        return x,y,z
    node("Terminal | powered bridge",bridge,"Terminal infrastructure",yard,
         tracks={"translation":compact(lambda t:(axis(t)[0],0,0))})
    node("Terminal | traversing trolley",scene.mesh(trolley),"Terminal infrastructure",yard,
         tracks={"translation":compact(lambda t:(axis(t)[0],axis(t)[1],0))})
    node("Terminal | twin lift cables",scene.mesh(rope),"Terminal infrastructure",yard,
         tracks={"translation":compact(axis),"scale":compact(lambda t:(1.,1.,4.96-axis(t)[2]))})
    node("Terminal | lifting spreader",scene.mesh(carrier),"Terminal infrastructure",yard,tracks={"translation":compact(axis)})
    for j in range(3):
        label=f"Pod {j+1:03} | L{p.LEVELS:02} B{j+1:02}"
        body=next(n for n in scene.nodes if n["name"]==label)
        loadmesh=body["mesh"] if body["mesh"]>=0 else next(n["mesh"] for n in scene.nodes if n["name"]==f"Original pod {j+1:03} | bronze before fault")
        f0=55+j*75
        def pose(t):
            if t<f0:return (LOAD_OFFSETS[j]+truck_offset(start+t),TRUCK_Y,DECK)
            u=t-f0;x=LOAD_OFFSETS[j]
            y=TRUCK_Y*(1-s.step(20,39,u))
            z=DECK+(1.78-DECK)*s.step(10,17,u)-1.78*s.step(40,51,u)
            return x,y,z
        pickup=p.STARTS[j]
        tracks=compact(pose)
        # The rack assumes ownership of the same visible assembly as its
        # leading end enters the silo. Queued pods advance along a straight rail.
        if j:
            advance=p.STARTS[j-1]+(35 if j==1 else 12)
            tracks.extend([(advance,(LOAD_OFFSETS[j],0,0)),(pickup-1,(RAIL_OFFSET,0,0))])
        node(f"Terminal | pod {j+1:03} on truck, crane and rail",loadmesh,"Terminal cargo",yard,
             tracks={"translation":tracks,"scale":show(start,pickup)})
    scene.project_info.update(terminalTruckLoad=3,terminalToIntake_m=22.)


def delivery_camera(frame,p):
    t=frame-INSERT_AT
    wide=camera(coords(p.ENTRY,(30.0,3.2,2.0)),-91,22,36.)
    close=camera(coords(p.ENTRY,(26.1,4.0,2.45)),-111,12,15.5)
    rail=camera(coords(p.ENTRY,(27.0,1.25,1.8)),-96,29,30.)
    if t<62:return wide
    if t<141:return blend(wide,close,s.step(62,90,t))
    if t<278:return blend(close,rail,s.step(141,180,t))
    return blend(rail,camera(coords(p.ENTRY,(19.0,.5,1.65)),-98,17,30.),s.step(278,335,t))
