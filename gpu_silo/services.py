"""Geometry and animation for the water-glycol store between the walls and the pod service stations."""
from . import design as cfg

import math

from . import silo_model as s


TAU=s.TAU
BAYS=cfg.BAYS
PITCH=cfg.STORE["pitch_m"]
LEVELS=cfg.LEVELS
PORT_Z=round(cfg.STORE["lowest_berth_m"]+cfg.BODY_HEIGHT/2,8)
PORT_RADIUS=.106
PORT_ANGLES=[s.ENTRY+TAU/BAYS*(i+.5) for i in range(BAYS)]
POD_FACE=cfg.STORE["root_radius_m"]+cfg.BODY_LENGTH
WALL_FACE=s.RI+.009
EXT_END=s.RO+.38
JAMB=cfg.DOOR_WIDTH/2+.20
LINTEL=cfg.DOOR_HEIGHT+.22
ON=(1.,1.,1.)
OFF=(0.,0.,0.)
WATER="388c9e"
SURFACE="67c8c4"
INLET="59bba9"
RETURN="538ba5"
POWER="e6ac61"
BRONZE="c7986b"
METAL="839599"
SEAL="354b50"


def port_height(level):
    return PORT_Z+(level-1)*PITCH


def lift_start(index):
    return s.INTRO if index==0 else s.INTRO+s.SLOW_CYCLE+(index-1)*s.FAST_CYCLE


def sleeve_frames(level):
    k=int(port_height(level)//s.LIFT)
    if k==0: return 5,28
    start=lift_start(k)
    return start-8,start


def cap_frames(level):
    k=int(port_height(level)//s.LIFT)
    start=lift_start(k)
    span=s.SLOW_CYCLE if k==0 else s.FAST_CYCLE
    at=math.ceil(start+.93*span)
    return at,at+5


def pipe(m,a,b,r,col,ri=0.,n=12):
    """A capped rod or an open, hollow pipe between two 3-D centres."""
    v=s.norm(s.minus(b,a))
    u=s.norm(s.cross((0,0,1) if abs(v[2])<.9 else (0,1,0),v))
    w=s.cross(v,u)
    def rim(p,radius):
        return [s.plus(p,s.plus(s.times(u,radius*math.cos(j*TAU/n)),
                                s.times(w,radius*math.sin(j*TAU/n)))) for j in range(n)]
    lo,hi=rim(a,r),rim(b,r)
    if ri: li,ui=rim(a,ri),rim(b,ri)
    for j in range(n):
        k=(j+1)%n
        m.face([lo[j],lo[k],hi[k],hi[j]],col)
        if ri:
            m.face([li[k],li[j],ui[j],ui[k]],SEAL)
            m.face([hi[j],hi[k],ui[k],ui[j]],col)
            m.face([lo[k],lo[j],li[j],li[k]],col)
    if not ri: m.face(hi,col);m.face(lo[::-1],col)


def barrel(m,a,b,r,col,ri=0,n=16):
    pipe(m,(a,0,0),(b,0,0),r,col,ri,n)


def station_mesh():
    m=s.Mesh("Cast-in pod service sleeve | supply, return and dry power and data duct")
    m.material=3
    barrel(m,WALL_FACE,s.RO+.015,PORT_RADIUS,BRONZE,.082)
    # Wall flanges and annulus pickup/return branches. The barrel contains a
    # separately insulated dry pin chamber for the electrical circuit.
    for x in (s.RI+.18,s.RI_OUTER+.05):
        barrel(m,x-.022,x+.022,.157,"89938c",.083)
    barrel(m,WALL_FACE,WALL_FACE+.040,.142,"799794",.094)
    barrel(m,WALL_FACE+.005,WALL_FACE+.040,.090,SEAL)
    for lateral,col in [(-.043,INLET),(.043,RETURN)]:
        pipe(m,(WALL_FACE+.001,lateral,.015),(s.RO+.016,lateral,.015),.028,col,ri=.017)
    for x,sign,col in [(s.RO_INNER+.35,1,INLET),(s.RO_INNER+.70,-1,RETURN)]:
        pipe(m,(x,sign*.039,.01),(x,sign*.235,-.055),.044,col,ri=.024)
    pipe(m,(WALL_FACE+.001,0,-.047),(s.RO+.018,0,-.047),.018,POWER)
    return m


def outside_cap():
    m=s.Mesh("Exterior power and data entry | bolted flange")
    m.material=3
    barrel(m,s.RO+.004,EXT_END-.045,.095,"aa966f",.068)
    barrel(m,s.RO+.025,s.RO+.060,.132,"bcb49b",.069)
    barrel(m,EXT_END-.09,EXT_END-.035,.161,BRONZE,.066)
    return m


def blind_cover():
    m=s.Mesh("Removable weather cover, gasket and bolts")
    m.material=3
    barrel(m,EXT_END-.036,EXT_END,.154,"88a9a3")
    barrel(m,EXT_END,EXT_END+.009,.093,"369384")
    for j in range(6):
        a=TAU*j/6
        y,z=.118*math.cos(a),.118*math.sin(a)
        pipe(m,(EXT_END-.01,y,z),(EXT_END+.013,y,z),.014,"d4cab0",n=6)
    return m


def moving_parts(face=POD_FACE):
    socket=s.Mesh("Pod service socket | flush end face")
    barrel(socket,face-.027,face+.0008,.116,"677575")
    barrel(socket,face+.0008,face+.0019,.080,"324e52")
    slide=s.Mesh("Retractable service plug | telescopic stroke")
    barrel(slide,0,WALL_FACE-face,.064,"94bdb8")
    # A visible shoulder identifies the latch even at small screen sizes.
    barrel(slide,.065,.090,.086,"cba46e")
    barrel(slide,.124,WALL_FACE-face,.085,"4d9b8e")
    lamp=s.Mesh("Service connected | status lamp")
    lamp.material=6
    barrel(lamp,face+.002,face+.005,.056,"81e3bc")
    return socket,slide,lamp


def cut_polygon(poly,fn):
    inside,outside=[],[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=fn(a),fn(b)
        (inside if da>=0 else outside).append(a)
        if (da>0>db) or (da<0<db):
            f=da/(da-db);p=tuple(x+(y-x)*f for x,y in zip(a,b))
            inside.append(p);outside.append(p)
        elif db==0 and da<0: outside.append(b)
        elif da==0 and db<0: outside.append(a)
    return inside,outside


def bore_rows(mesh,zbase,world_heights):
    out=s.Mesh(mesh.name+" | bored at service stations");out.material=getattr(mesh,"material",0)
    if not world_heights: out.tris=mesh.tris[:];return out
    radius=PORT_RADIUS+.006
    side_count=12
    normals=[(math.cos((k+.5)*TAU/side_count),math.sin((k+.5)*TAU/side_count)) for k in range(side_count)]
    apothem=radius*math.cos(math.pi/side_count)
    triangles=mesh.tris[:]
    for h in world_heights:
        z=h-zbase
        for a in PORT_ANGLES:
            cs,sn=math.cos(a),math.sin(a)
            selected=[]
            for v0,v1,v2,col in triangles:
                pts=[v0,v1,v2]
                ys=[y*cs-x*sn for x,y,_ in pts]
                if (min(ys)>radius or max(ys)<-radius or min(pt[2] for pt in pts)>z+radius or
                    max(pt[2] for pt in pts)<z-radius or max(x*cs+y*sn for x,y,_ in pts)<=0):
                    selected.append((v0,v1,v2,col));continue
                for nu,nv in normals:
                    pts,other=cut_polygon(pts,lambda q:apothem-nu*(q[1]*cs-q[0]*sn)-nv*(q[2]-z))
                    for k in range(1,len(other)-1):
                        selected.append((other[0],other[k],other[k+1],col))
                    if len(pts)<3: break
            triangles=selected
    out.tris=triangles
    return out


def perforate_concrete(scene):
    cache={}
    for obj in scene.nodes:
        if "concrete wall" not in obj["group"]: continue
        floor=obj['translation'][2]
        heights=tuple(port_height(i) for i in range(1,LEVELS+1) if floor<port_height(i)<floor+s.LIFT)
        if not heights:continue
        key=(obj['mesh'],floor)
        if key not in cache:
            cache[key]=scene.mesh(bore_rows(scene.meshes[obj['mesh']],floor,heights))
        obj['mesh']=cache[key]


def door_barrier():
    m=s.Mesh("Sealed portal | two jambs, lintel and flush sill")
    def piece(y0,y1,z0,z1):
        def pt(r,y,z): return math.sqrt(r*r-y*y),y,z
        pts=[pt(r,y,z) for z in (z0,z1) for r,y in
             [(s.RO_INNER-.035,y0),(s.RI_OUTER+.035,y0),(s.RI_OUTER+.035,y1),(s.RO_INNER-.035,y1)]]
        for face,col in [((3,2,1,0),"718b80"),((4,5,6,7),"b4c6b6"),((0,1,5,4),"79a39a"),
                         ((1,2,6,5),"859d90"),((2,3,7,6),"79a39a"),((3,0,4,7),"91a597")]:
            m.face([pts[i] for i in face],col)
    w=s.OPENING_WIDTH/2
    piece(-JAMB,-w,0,LINTEL);piece(w,JAMB,0,LINTEL)
    piece(-w,w,s.OPENING_HEIGHT,LINTEL);piece(-JAMB,JAMB,-.095,0)
    return m


def liquid_mesh(name,notch,top=False):
    """Side shells for two height bands, or the moving horizontal free surface."""
    m=s.Mesh(name);m.material=5 if top else 4
    ri,ro=s.RO_INNER,s.RI_OUTER
    def point(r,t,z):
        a=math.asin(JAMB/r) if notch else 0
        return s.polar(r,s.ENTRY+a+(TAU-2*a)*t,z)
    count=64
    for j in range(count):
        u,v=j/count,(j+1)/count
        if top:
            m.face([point(ro,u,0),point(ro,v,0),point(ri,v,0),point(ri,u,0)],SURFACE)
        else:
            m.face([point(ro,u,0),point(ro,v,0),point(ro,v,1),point(ro,u,1)],WATER)
            m.face([point(ri,v,0),point(ri,u,0),point(ri,u,1),point(ri,v,1)],WATER)
    if notch and not top:
        for t in (0,1):
            a=[point(ri,t,0),point(ro,t,0),point(ro,t,1),point(ri,t,1)]
            m.face(a if t==0 else a[::-1],WATER)
    return m


def add_fixed(scene,node,flat_keys,levels):
    """Cast-in pod stations, the sealed doorway and the liquid. ``levels`` is the fill elevation at every frame."""
    sleeve=scene.mesh(station_mesh())
    cap=scene.mesh(outside_cap())
    blind=scene.mesh(blind_cover())
    for level in range(1,LEVELS+1):
        z=port_height(level);start,end=sleeve_frames(level);cap0,cap1=cap_frames(level)
        for bay,angle in enumerate(PORT_ANGLES,1):
            name=f"L{level:02} P{bay:02}"
            node(name+" | cast-in service conduit",sleeve,"Cast-in conduits",ang=angle,t=(0,0,z),
                 tracks={"scale":[(0,OFF),(start-1,OFF),(start,ON)],
                         "translation":[(0,(0,0,z+.40)),(start,(0,0,z+.40)),(end,(0,0,z))]})
            dx=.26*math.cos(angle);dy=.26*math.sin(angle)
            for suffix,part in [("exterior service flange",cap),("removable blind cover",blind)]:
                node(name+" | "+suffix,part,"Exterior service flanges",ang=angle,t=(0,0,z),
                     tracks={"scale":[(0,OFF),(cap0-1,OFF),(cap0,ON)],
                             "translation":[(0,(dx,dy,z)),(cap0,(dx,dy,z)),(cap1,(0,0,z))]})
    m=door_barrier()
    node(m.name,scene.mesh(m),"Door blockout",ang=s.ENTRY,tracks={"scale":[(0,OFF),(3,OFF),(4,ON)]})
    h=list(levels)
    for bottom,z0 in [(True,0),(False,LINTEL)]:
        m=liquid_mesh("Water-glycol store | "+("sealed doorway band" if bottom else "annulus to the rim"),bottom)
        node(m.name,scene.mesh(m),"Thermal store",t=(0,0,z0),tracks={"scale":flat_keys([
            (1.,1.,min(z,LINTEL) if bottom else max(0.,z-LINTEL)) for z in h])})
        m=liquid_mesh("Free liquid surface | "+("around portal" if bottom else "full ring"),bottom,True)
        node(m.name,scene.mesh(m),"Thermal store",tracks={
            "translation":flat_keys([(0,0,z) for z in h]),
            "scale":flat_keys([ON if (0<z<LINTEL if bottom else z>=LINTEL) else OFF for z in h])})
    return h
