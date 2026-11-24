"""Parametric, metre-based low-poly double-wall silo and jumpform sequence, with a glTF 2.0 exporter."""
from . import design as cfg
from . import film


import argparse
import bisect
import json
import math
import random
import struct
from array import array
from pathlib import Path


OUTSIDE_DIAMETER = cfg.SILO["outside_diameter_m"]
WALL_HEIGHT = cfg.SILO["height_m"]
CLEAR_GAP = cfg.WALL_GAP
OUTER_THICKNESS = cfg.SILO["outer_wall_m"]
INNER_THICKNESS = cfg.SILO["inner_wall_m"]
LIFT = cfg.SILO["concrete_lift_m"]
FPS = 24
SECTORS = 24
INTRO = 36
SLOW_CYCLE = 108
# The short film gives each day of the jumpform long enough to watch the pod cage go up beside it.
FAST_CYCLE = 84 if film.SHORT else 39
REVEAL = 19
HOLD = 85
TAU = 2 * math.pi
ENTRY = math.radians(-37)
FRAME_EQUIPMENT = ("Cooler frames","Cooler screens","Pump units","Frame anchors","Frame pipework")
SITE_CLEARING = 60.
OPENING_WIDTH = cfg.DOOR_WIDTH
OPENING_HEIGHT = cfg.DOOR_HEIGHT

RO = OUTSIDE_DIAMETER / 2
RI_OUTER = RO - OUTER_THICKNESS
RO_INNER = RI_OUTER - CLEAR_GAP
RI = RO_INNER - INNER_THICKNESS
COUNT = round(WALL_HEIGHT / LIFT)
assert math.isclose(COUNT * LIFT, WALL_HEIGHT) and RI > 0
LAST_POUR = INTRO + SLOW_CYCLE + (COUNT - 1) * FAST_CYCLE
FORMS_OFF = LAST_POUR + REVEAL // 2
SHORT_WALL_CLOSE = 10 * FPS
FRAMES = LAST_POUR + REVEAL + HOLD


def clamp(x, low=0.0, high=1.0):
    return max(low, min(high, x))


def step(a, b, x):
    t = clamp((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def sequence(frame):
    if frame < INTRO:
        return 0, 0.0, 0.0, 0.0, "Forms in position"
    if frame >= LAST_POUR:
        return COUNT - 1, 1.0, 1.0, 0.0, "Walls complete"
    time = frame - INTRO
    if time < SLOW_CYCLE:
        k, u = 0, time / SLOW_CYCLE
    else:
        time -= SLOW_CYCLE
        k, u = 1 + int(time // FAST_CYCLE), time % FAST_CYCLE / FAST_CYCLE
    fill = step(.01, .42, u)
    opening = step(.55, .65, u) * (1 - step(.90, .985, u))
    jump = step(.68, .89, u) if k < COUNT - 1 else 0.0
    if k == COUNT - 1:
        opening = step(.55, .70, u)
    if u < .42:
        label = "Pour both walls"
    elif u < .55:
        label = "Concrete sets"
    elif k == COUNT - 1 or u < .68:
        label = "Strip the forms"
    elif u < .89:
        label = "Jump the forms"
    else:
        label = "Reset for next pour"
    return k, fill, opening, jump, label


def display_info(frame):
    k, fill, _, _, label = sequence(frame)
    finished = frame >= LAST_POUR
    return {
        "frame": frame, "phase": label, "lift": k + 1,
        "height": min(WALL_HEIGHT, (k + fill) * LIFT),
        "finish": finished, "plan": step(LAST_POUR + 8, LAST_POUR + 65, frame),
    }


def camera_at(frame):
    k, fill, _, jump, _ = sequence(frame)
    travel = step(INTRO + 18, LAST_POUR - 29, frame)
    height_fraction = clamp((k + .65 * fill + .35 * jump) / COUNT)
    end_view = step(LAST_POUR + 4, LAST_POUR + 73, frame)
    az = math.radians(-64 + 16 * travel + 12 * end_view)
    el = math.radians(12.4 - 1.8 * travel + 31 * end_view)
    target_z = .565*LIFT + .437*WALL_HEIGHT*height_fraction + .06*WALL_HEIGHT*end_view
    # Start close enough to read the crew, then draw back as the forms climb.
    d = (2.67*OUTSIDE_DIAMETER + 1.335*WALL_HEIGHT*height_fraction)*(.80+.20*step(INTRO+SLOW_CYCLE*.7,INTRO+SLOW_CYCLE+3*FAST_CYCLE,frame)) - .53*OUTSIDE_DIAMETER*end_view
    target = (0, 0, target_z)
    eye = (math.cos(az) * math.cos(el) * d, math.sin(az) * math.cos(el) * d,
           target_z + math.sin(el) * d)
    return {"eye": eye, "target": target, "fov": 33.0}


def plus(a, b):
    return tuple(x + y for x, y in zip(a, b))


def minus(a, b):
    return tuple(x - y for x, y in zip(a, b))


def times(a, s):
    return tuple(x * s for x in a)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v)


def polar(radius, angle, z):
    return (radius * math.cos(angle), radius * math.sin(angle), z)


def rgb(code):
    return tuple(int(code[i:i + 2], 16) for i in (0, 2, 4))


def tint(color, scale):
    return tuple(round(clamp(c * scale, 0, 255)) for c in color)


class Mesh:
    def __init__(self, name, terrain=False):
        self.name = name
        self.terrain = terrain
        self.tris = []

    def face(self, pts, color):
        color = rgb(color) if isinstance(color, str) else color
        for i in range(1, len(pts) - 1):
            self.tris.append((pts[0], pts[i], pts[i + 1], color))


def sector(mesh, inside, outside, z0, z1, a0, a1, n, colors, caps=True, shade=0):
    outside_c, inside_c, top_c, tip_c = [rgb(c) if isinstance(c, str) else c for c in colors]
    # Mid-segment vertices keep the wall and formwork facets aligned.
    n *= 2
    for i in range(n):
        a = a0 + (a1 - a0) * i / n
        b = a0 + (a1 - a0) * (i + 1) / n
        o0, o1 = polar(outside, a, z0), polar(outside, b, z0)
        o2, o3 = polar(outside, b, z1), polar(outside, a, z1)
        i0, i1 = polar(inside, a, z0), polar(inside, b, z0)
        i2, i3 = polar(inside, b, z1), polar(inside, a, z1)
        value = 1 + shade * (math.sin(i * 19.7 + .4) + .3 * math.sin(i * 4.8))
        mesh.face([o0, o1, o2, o3], tint(outside_c, value))
        if inside > 0:
            mesh.face([i1, i0, i3, i2], tint(inside_c, value))
        if inside > 0:
            mesh.face([o3, o2, i2, i3], top_c)
            mesh.face([i0, i1, o1, o0], inside_c)
        else:
            mesh.face([o3, o2, i2], top_c)
        if caps and i == 0:
            mesh.face([i0, o0, o3, i3], tip_c)
        if caps and i == n - 1:
            mesh.face([o1, i1, i2, o2], tip_c)


def bar(mesh, a, b, width, color, depth=None):
    w = norm(minus(b, a))
    side = norm(cross(w, (0, 0, 1) if abs(w[2]) < .94 else (0, 1, 0)))
    other = norm(cross(w, side))
    s, t = times(side, width / 2), times(other, (depth or width) / 2)
    offsets = [plus(s, t), plus(times(s, -1), t), times(plus(s, t), -1), minus(s, t)]
    bottom, top = [[plus(p, offset) for offset in offsets] for p in (a, b)]
    mesh.face(top, color)
    mesh.face(bottom[::-1], color)
    for i in range(4):
        j = (i + 1) % 4
        mesh.face([bottom[i], bottom[j], top[j], top[i]], color)


def box(mesh, x0, y0, x1, y1, z0, z1, c):
    mesh.face([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)], c)
    mesh.face([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)], c)
    mesh.face([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)], c)
    mesh.face([(x1,y1,z0),(x0,y1,z0),(x0,y1,z1),(x1,y1,z1)], c)
    mesh.face([(x0,y1,z0),(x0,y0,z0),(x0,y0,z1),(x0,y1,z1)], c)


def quad_xy(mesh, x0, y0, x1, y1, z, c):
    mesh.face([(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)], c)


def tree(mesh, x, y, h, seed):
    rng = random.Random(seed)
    bar(mesh, (x,y,.05), (x,y,h*.5), h*.072, "756b51")
    tiers = []
    lopsided = [(rng.uniform(.86,1.12), rng.uniform(-.06,.06)) for _ in range(7)]
    for r, z in [(.18,.29),(.34,.43),(.31,.68),(.19,.86),(.031,1)]:
        tier = []
        for j, (rad, dz) in enumerate(lopsided):
            a = j*TAU/7 + seed*.16
            tier.append((x+h*r*rad*math.cos(a), y+h*r*rad*math.sin(a),
                         h*(z+dz*.6)))
        tiers.append(tier)
    base = rgb(rng.choice(["6f7852","838958","717e52","85895b","73835e"]))
    for lower, upper in zip(tiers, tiers[1:]):
        for j in range(7):
            k = (j+1) % 7
            mesh.face([lower[j],lower[k],upper[k],upper[j]], tint(base,rng.uniform(.94,1.06)))
    mesh.face(tiers[-1], base)


def barn(mesh, x, y, width, length, h):
    x0,x1,y0,y1 = x-width/2, x+width/2, y-length/2, y+length/2
    box(mesh,x0,y0,x1,y1,.04,h,"b89c77")
    for yy, sign in [(y0,-1),(y1,1)]:
        points = [(x0,yy,h),(x1,yy,h),(x,yy,h+width*.23)]
        mesh.face(points if sign<0 else points[::-1], "d2c2a3")
    for edge in [x0-.35,x1+.35]:
        pts=[(edge,y0-.35,h-.05),(edge,y1+.35,h-.05),
             (x,y1+.35,h+width*.23),(x,y0-.35,h+width*.23)]
        mesh.face(pts[::-1] if edge<x else pts,"7b7b70")
    box(mesh,x0+1,y0-.09,x0+width*.49,y0,h*.02,h*.76,"786d5c")


def build_land():
    fields = Mesh("Agricultural fields and access track", terrain=True)
    details = Mesh("Field boundaries, farm sheds and trees")
    rng = random.Random(9274)
    quad_xy(fields,-890,-890,890,890,-.06,"bbc093")
    xs = [-650,-405,-285,-183,-119,-64,-26,28,71,130,202,292,452,650]
    ys = [-590,-402,-268,-169,-105,-54,-24,26,71,125,206,318,460,630]
    palette = ["b9c090","c9b17b","adba89","b5bf91","d3c38e","b5bf89","c1c593","a9b28a"]
    for ix,(xa,xb) in enumerate(zip(xs,xs[1:])):
        for iy,(ya,yb) in enumerate(zip(ys,ys[1:])):
            if ix==6 and iy==6:
                base = "c0b491"
            else:
                base = rng.choice(palette)
            quad_xy(fields,xa+.5,ya+.6,xb-.5,yb-.6,-.041,base)
            if abs(xa)>290 or abs(ya)>270:
                continue
            if ix==6 and iy==6:
                continue
            along_x = (ix + 2*iy) % 4 != 1
            start, end = (ya,yb) if along_x else (xa,xb)
            g=start+2
            pitch = rng.choice([1.7,2.1,2.5,3.2])
            line_c=tint(rgb(base),rng.choice([.93,.94,.95,1.035]))
            while g<end-1:
                if along_x:
                    quad_xy(fields,xa+1,g,xb-1,g+.32,-.031,line_c)
                else:
                    quad_xy(fields,g,ya+1,g+.32,yb-1,-.031,line_c)
                g+=pitch
    # The farm lane stays level all the way to the horizon. The public road and the site roads are added by site.py.
    quad_xy(fields,-124.5,-525,-121.2,480,.004,"c8c2a5")
    def clear(x,y):
        """Keep trees off the work area, the access road, the holding lanes and the water drive."""
        return math.hypot(x,y)>SITE_CLEARING and not (-112<x<24 and 44<y<126) and not 108<y<124 and not (-112<x<-50 and -40<y<50)
    for i in range(50):
        x = -260+i*10.1+rng.uniform(-2.5,2.5)
        if -31 < x < 50 or rng.random()<.16:
            continue
        y,h=27.5+rng.uniform(-1,2.5),rng.uniform(3.2,6.2)
        if clear(x,y):tree(details,x,y,h,760+i)
    for i in range(48):
        x=-258+i*11.8+rng.uniform(-2,3)
        if rng.random()<.25:
            continue
        y,h=79+rng.uniform(-4,3),rng.uniform(3.6,8.8)
        if clear(x,y):tree(details,x,y,h,220+i)
    for i in range(18):
        tree(details,-127+rng.uniform(-2.2,1.2),-99+i*8,rng.uniform(3.1,6.1),100+i)
    for i in range(70):
        if rng.random()>.15:
            tree(details,-285+i*8.5+rng.uniform(-1,2),164+rng.uniform(-8,8),rng.uniform(3.4,7.5),1300+i)
    barn(details,61,140,8.2,13,3.9)
    barn(details,72,144,6.5,10,3.05)
    for j,(x,y,h) in enumerate([(53,142,6.9),(51,145,6.1),(76,149,6.2),(78,150,4.8)]):
        tree(details,x,y,h,1060+j)
    return fields, details


WIDTH = TAU / SECTORS


def wall_mesh(name, inner_r, outer_r, cut, outer):
    m = Mesh(name)
    lo,hi=(-6,-2) if outer else (-5,-3)
    a0,a1=(lo*WIDTH,hi*WIDTH) if cut else (hi*WIDTH,TAU+lo*WIDTH)
    spans=4*((hi-lo) if cut else (SECTORS-hi+lo))
    c0,c1=("c6c8c3","879690") if outer else ("a7b0a7","a9b3ae")
    profiles=[(0,.013),(.034,0),(LIFT-.028,0),(LIFT,.010)]
    for j in range(spans):
        a=a0+(a1-a0)*j/spans
        b=a0+(a1-a0)*(j+1)/spans
        variation=1+.006*math.sin(j*19.7+.4)
        for seg,((z0,d0),(z1,d1)) in enumerate(zip(profiles,profiles[1:])):
            o0,o1=polar(outer_r-d0,a,z0),polar(outer_r-d0,b,z0)
            o2,o3=polar(outer_r-d1,b,z1),polar(outer_r-d1,a,z1)
            i0,i1=polar(inner_r+d0,a,z0),polar(inner_r+d0,b,z0)
            i2,i3=polar(inner_r+d1,b,z1),polar(inner_r+d1,a,z1)
            m.face([o0,o1,o2,o3],tint(rgb(c0),variation*(.86 if seg==0 else 1)))
            m.face([i1,i0,i3,i2],tint(rgb(c1),variation*(.9 if seg==0 else 1)))
            if j==0: m.face([i0,o0,o3,i3],"e1e2d6")
            if j==spans-1: m.face([o1,i1,i2,o2],"e1e2d6")
            if seg==0: m.face([i0,i1,o1,o0],"959f9a")
            if seg==2: m.face([o3,o2,i2,i3],"e1e4d9")
    return m


def door_cut(mesh, inside, outside, jambs):
    """Subtract the exact rectangular passage in doorway coordinates."""
    cs,sn=math.cos(ENTRY),math.sin(ENTRY)
    along=lambda p: p[0]*cs+p[1]*sn
    across=lambda p: -p[0]*sn+p[1]*cs
    planes=[along,lambda p:across(p)+OPENING_WIDTH/2,
            lambda p:OPENING_WIDTH/2-across(p),lambda p:OPENING_HEIGHT-p[2]]
    def split(poly,fn):
        pos,neg=[],[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da,db=fn(a),fn(b)
            (pos if da>=0 else neg).append(a)
            if (da<0<db) or (db<0<da):
                f=da/(da-db)
                cut=tuple(v+(w-v)*f for v,w in zip(a,b))
                pos.append(cut);neg.append(cut)
            elif db==0 and da<0:
                neg.append(b)
            elif da==0 and db<0:
                neg.append(a)
        return pos,neg
    result=Mesh(mesh.name+" | ground portal")
    for a,b,c,color in mesh.tris:
        poly=[a,b,c]
        for fn in planes:
            if not poly: break
            poly,out=split(poly,fn)
            if len(out)>=3: result.face(out,color)
    if jambs:
        def p(r,w,z):
            along_r=math.sqrt(r*r-w*w)
            return (cs*along_r-sn*w,sn*along_r+cs*w,z)
        hw,h=OPENING_WIDTH/2,OPENING_HEIGHT
        for sign in (-1,1):
            w=sign*hw
            pts=[p(inside,w,0),p(outside,w,0),p(outside,w,h),p(inside,w,h)]
            result.face(pts if sign>0 else pts[::-1],"b4beb1")
        result.face([p(inside,hw,h),p(outside,hw,h),p(outside,-hw,h),p(inside,-hw,h)],"adb4aa")
    return result


def form_mesh(name, r, sense, deck):
    m = Mesh(name)
    half = WIDTH/2
    delta = .004
    a0,a1 = -half+delta,half-delta
    skin = .09
    low, high = sorted((r, r+sense*skin))
    c = ["d58b4b","bf7442","efb56d","985a39"] if sense==1 else ["c27a45","d68c50","efb56d","985a39"]
    sector(m,low,high,.055,LIFT+.035,a0,a1,2,c)
    # Two backing walers and three panel stiffeners. All four faces close
    # against their own concrete face, including both sides of the clearance.
    for z in (.57,LIFT-.44):
        r0,r1=sorted((r+sense*(skin+.006),r+sense*(skin+.115)))
        sector(m,r0,r1,z-.045,z+.045,a0,a1,2,["985b37","9b5f3a","c4834d","a0693e"])
    for a in (a0+.003,0,a1-.003):
        z1 = LIFT-.02
        rr=r+sense*(skin+.035)
        bar(m,polar(rr,a,.10),polar(rr,a,z1),.059,"ac683c",.064)
    # Tie plates on the panel face, and push-pull props that plumb the panel from the working platform.
    for a in (a0+WIDTH*.25,a1-WIDTH*.25):
        for z in (.57,LIFT/2,LIFT-.44):
            rr=r+sense*(skin+.125)
            bar(m,polar(rr-sense*.02,a,z),polar(rr+sense*.05,a,z),.11,"d9c28a",.11)
    if deck:
        for a in (a0+WIDTH*.33,a1-WIDTH*.33):
            bar(m,polar(r+sense*.62,a,.30),polar(r+sense*(skin+.13),a,LIFT-.50),.055,"c8563c")
    if deck:
        platform=1.02 if sense>0 else .73
        start,end=sorted((r+sense*.12,r+sense*platform))
        sector(m,start,end,.17,.27,a0-.002,a1+.002,2,
               ["59665f","53645e","a69979","796d57"])
        rr=r+sense*(platform-.065)
        for a in (a0+.005,):
            bar(m,polar(rr,a,.25),polar(rr,a,1.18),.053,"e2bd76")
        for z in (.74,1.15):
            for a,b in ((a0,0),(0,a1)):
                bar(m,polar(rr,a,z),polar(rr,b,z),.045,"e7bd71")
        for a in (a0+.048,):
            bar(m,polar(r+sense*.15,a,.30),polar(r+sense*(platform-.09),a,.30),
                .085,"566b64")
            bar(m,polar(r+sense*(platform-.09),a,.30),polar(r+sense*.16,a,1.07),
                .075,"61736a")
    return m


class Scene:
    def __init__(self):
        self.meshes = []
        self.nodes = []
        self.camera = [camera_at(i) for i in range(FRAMES)]
        self.info = [display_info(i) for i in range(FRAMES)]

    def mesh(self,m):
        self.meshes.append(m)
        return len(self.meshes)-1

    def node(self,name,mesh,group,angle=0,translation=(0,0,0),tracks=None):
        self.nodes.append(dict(name=name,mesh=mesh,group=group,angle=angle,
                               translation=translation,tracks=tracks or {}))


def keys(values):
    # Keep only changes of slope, while retaining the ends of constant spans.
    result=[]
    for i, val in enumerate(values):
        if i==0 or i==len(values)-1 or any(abs((n-c)-(c-p))>1.e-7
                for p,c,n in zip(values[i-1],val,values[i+1])):
            result.append((i,val))
    return result


def build(*, wall_close_frame=FORMS_OFF):
    scene=Scene()
    scene.wall_close_frame=wall_close_frame
    fields,details=build_land()
    scene.node(fields.name,scene.mesh(fields),"Landscape")
    scene.node(details.name,scene.mesh(details),"Landscape")
    footing=Mesh("Concrete starter slab")
    sector(footing,0,RO+.64,-.12,0,0,TAU,SECTORS*2,
           ["9eaaa0","a3aca1","caced0","c4c9c0"],caps=False)
    base=Mesh("Compacted work pad")
    sector(base,0,RO+4.15,-.09,-.01,0,TAU,48,["aeaa93","ada589","c6bea5","b8ad94"],caps=False)
    scene.node(base.name,scene.mesh(base),"Foundation")
    scene.node(footing.name,scene.mesh(footing),"Foundation")
    # World units are metres. The radial void between RI_OUTER and RO_INNER
    # is kept free of concrete for the full height of every lift.
    states=[sequence(i) for i in range(FRAMES)]
    for wall,inside,outside in [("Outer",RI_OUTER,RO),("Inner",RI,RO_INNER)]:
        for piece in (False,True):
            wallpart=wall_mesh(wall+(" inspection sector" if piece else " wall"),
                               inside,outside,piece,wall=="Outer")
            mesh=scene.mesh(wallpart)
            contains_door=piece if wall=="Outer" else not piece
            groundmesh=scene.mesh(door_cut(wallpart,inside,outside,contains_door)) if contains_door else mesh
            for k in range(COUNT):
                scales=[]
                for i,(active,fill,_,__,___) in enumerate(states):
                    h = 1 if active>k else fill if active==k else 0
                    on = 1 if not piece or i>=wall_close_frame else 0
                    scales.append((on,on,on*h))
                name=f"{wall} wall | lift {k+1:02d}"+(" | cutaway insert" if piece else "")
                scene.node(name,groundmesh if k==0 else mesh,f"{wall} concrete wall",translation=(0,0,k*LIFT),
                           tracks={"scale":keys(scales)})
    form_faces=[("Outer wall - exterior",RO,1,True),
                ("Outer wall - gap face",RI_OUTER,-1,False),
                ("Inner wall - gap face",RO_INNER,1,False),
                ("Inner wall - interior",RI,-1,True)]
    for label, r, sense, deck in form_faces:
        mesh=scene.mesh(form_mesh(label+" panels",r,sense,deck))
        for j in range(SECTORS):
            hidden=range(SECTORS-7,SECTORS-1) if label.startswith("Outer") else range(SECTORS-5,SECTORS-2)
            inspection_panel=j in hidden
            if inspection_panel and wall_close_frame>=FORMS_OFF:
                continue
            angle=(j+.5)*WIDTH
            c,s=math.cos(angle),math.sin(angle)
            trans=[]; scales=[]
            for i,(k,_,opening,jump,__) in enumerate(states):
                dist=sense*.145*opening
                trans.append((c*dist,s*dist,LIFT*(k+jump)))
                on=int(i<FORMS_OFF and (not inspection_panel or i>=wall_close_frame))
                scales.append((on,on,on))
            scene.node(f"{label} | gang {j+1:02d}",mesh,label,angle=angle,
                       tracks={"translation":keys(trans),"scale":keys(scales)})
    return scene


def at(keys_list,frame):
    i=bisect.bisect_right(keys_list,(frame,(math.inf,)))-1
    if i<0: return keys_list[0][1]
    if i==len(keys_list)-1: return keys_list[i][1]
    a,x=keys_list[i]; b,y=keys_list[i+1]; t=(frame-a)/(b-a)
    return tuple(p+(q-p)*t for p,q in zip(x,y))


def render_data(scene,path):
    """Compact scratch handoff for the reference renderer."""
    with open(path,'wb') as handle:
        def ints(*args): handle.write(struct.pack('<'+'i'*len(args),*args))
        def floats(*args): handle.write(struct.pack('<'+'f'*len(args),*args))
        handle.write(b'SILO003\0')
        ints(len(scene.meshes),len(scene.nodes),FRAMES,FPS)
        floats(RO,RI_OUTER,RO_INNER,RI,WALL_HEIGHT,LIFT)
        ints(COUNT,LAST_POUR,LAST_POUR+REVEAL//2,LAST_POUR+REVEAL)
        for m in scene.meshes:
            ints(len(m.tris),int(m.terrain))
            for a,b,c,color in m.tris:
                floats(*a,*b,*c)
                handle.write(bytes(color))
        for item in scene.nodes:
            ints(item['mesh'])
            floats(item['angle'])
            for i in range(FRAMES):
                tracks=item['tracks']
                t=at(tracks['translation'],i) if 'translation' in tracks else item['translation']
                s=at(tracks['scale'],i) if 'scale' in tracks else (1,1,1)
                floats(*t,*s)
        for cam,info in zip(scene.camera,scene.info):
            floats(*cam['eye'],*cam['target'],cam['fov'],info['height'],info['plan'])
            ints(info['lift'],int(info['finish']))
            b=info['phase'].encode('utf-8')
            ints(len(b));handle.write(b)


def gl_point(pt):
    x,y,z=pt
    return [x,z,-y]


def gl_scale(pt):
    x,y,z=pt
    return [x,z,y]


def camera_quat(eye,target):
    # Columns are right, up and local +Z (back), all in glTF space.
    back=norm(minus(gl_point(eye),gl_point(target)))
    right=norm(cross((0,1,0),back))
    up=cross(back,right)
    m00,m10,m20=right; m01,m11,m21=up; m02,m12,m22=back
    t=1+m00+m11+m22
    if t>1e-7:
        w=math.sqrt(t)/2
        return norm(((m21-m12)/(4*w),(m02-m20)/(4*w),(m10-m01)/(4*w),w))
    raise ValueError("Camera rotation outside the configured range")


class Glb:
    def __init__(self):
        self.bin=bytearray()
        self.doc={"asset":{"version":"2.0","generator":"GPU Silo parametric model"},
                  "scene":0,"scenes":[{"name":"GPU Silo","nodes":[]}],
                  "nodes":[],"meshes":[],"animations":[],"materials":[],"accessors":[],"bufferViews":[]}
        self.lookup={}

    def add(self,data,kind,typecode,target=None,bounds=False,normalized=False):
        ct={'f':5126,'B':5121}[typecode]
        n={'SCALAR':1,'VEC3':3,'VEC4':4}[kind]
        buf=array(typecode,data).tobytes()
        key=(kind,typecode,target,bounds,normalized,buf)
        if key in self.lookup:
            return self.lookup[key]
        self.bin.extend(bytes((-len(self.bin))%4))
        view={"buffer":0,"byteOffset":len(self.bin),"byteLength":len(buf)}
        if target: view['target']=target
        end=self.doc['bufferViews']; vid=len(end); end.append(view); self.bin.extend(buf)
        ac={"bufferView":vid,"componentType":ct,"count":len(data)//n,"type":kind}
        if normalized: ac["normalized"]=True
        if bounds:
            ac['min']=[min(data[j::n]) for j in range(n)]
            ac['max']=[max(data[j::n]) for j in range(n)]
        idx=len(self.doc['accessors']); self.doc['accessors'].append(ac)
        self.lookup[key]=idx
        return idx

    def node(self,data):
        i=len(self.doc["nodes"]);self.doc["nodes"].append(data);return i

    def save(self,path):
        self.bin.extend(bytes((-len(self.bin))%4))
        self.doc["buffers"]=[{"byteLength":len(self.bin)}]
        text=json.dumps(self.doc,ensure_ascii=False,separators=(',',':')).encode()
        text+=b' '*((-len(text))%4)
        with open(path,'wb') as out:
            out.write(struct.pack('<4sII',b'glTF',2,28+len(text)+len(self.bin)))
            out.write(struct.pack('<I4s',len(text),b'JSON'));out.write(text)
            out.write(struct.pack('<I4s',len(self.bin),b'BIN\0'));out.write(self.bin)


def glb_file(scene,path,*,aspect_ratio=1034/720):
    gl=Glb(); doc=gl.doc; roots=doc['scenes'][0]['nodes']
    doc["extras"]={"outsideDiameter_m":OUTSIDE_DIAMETER,"height_m":WALL_HEIGHT,"clearGap_m":CLEAR_GAP,
                   "outerWall_m":OUTER_THICKNESS,"innerWall_m":INNER_THICKNESS,"lift_m":LIFT,
                   "insideDiameter_m":2*RI,"frameRate":FPS,"note":"Staggered camera-facing viewing sectors during construction. Full rings at completion. Time compressed."}
    doc["extras"].update(getattr(scene,"project_info",{}))
    doc["materials"].append({"name":"Matte site palette","doubleSided":True,
        "pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"metallicFactor":0,"roughnessFactor":.94}})
    # Cutaway views remove the concrete altogether. Only its rim and joint lines remain as a faint guide.
    for name,alpha in [("Concrete shell | cutaway view",0.),("Shell rim and portal edges",.30)]:
        doc["materials"].append({"name":name,"doubleSided":False,"alphaMode":"BLEND",
            "pbrMetallicRoughness":{"baseColorFactor":[.71,.90,.94,alpha],"metallicFactor":0,"roughnessFactor":.9}})
    doc["materials"].append({"name":"Painted structural steel","doubleSided":True,
        "pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"metallicFactor":.28,"roughnessFactor":.56}})
    for name,opacity in [("Water-glycol | body",.16),("Water-glycol | free surface",.62)]:
        doc["materials"].append({"name":name,"alphaMode":"BLEND","doubleSided":False,
            "pbrMetallicRoughness":{"baseColorFactor":[1,1,1,opacity],"metallicFactor":0,"roughnessFactor":.32}})
    doc["materials"].append({"name":"Service coupled | indicator","emissiveFactor":[.08,.36,.19],"doubleSided":True,
        "pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"metallicFactor":0,"roughnessFactor":.5}})
    if getattr(scene,"short_presentation",False):
        for name,opacity,glow in (("Discharge separators",.14,None),("Control room glazing",.14,None),
                                  ("Control room displays",1,[.25,.40,.34]),("Satellite uplink core",1,[1,.025,.035]),
                                  ("Satellite uplink halo",.17,[.75,.012,.024])):
            mat={"name":name,"doubleSided":True,"pbrMetallicRoughness":{"baseColorFactor":[1,1,1,opacity],"metallicFactor":0,"roughnessFactor":.38}}
            if opacity<1:mat["alphaMode"]="BLEND"
            if glow:mat["emissiveFactor"]=glow
            doc["materials"].append(mat)
    lin=[round(255*((i/255/12.92) if i<=10 else ((i/255+.055)/1.055)**2.4)) for i in range(256)]
    for m in scene.meshes:
        pos=[]; normals=[]; colors=[]
        for a,b,c,col in m.tris:
            raw=cross(minus(b,a),minus(c,a))
            if sum(i*i for i in raw)<1e-12: continue
            normal=gl_point(norm(raw))
            for p in (a,b,c):
                pos.extend(gl_point(p)); normals.extend(normal); colors.extend([lin[i] for i in col]+[255])
        attrs={"POSITION":gl.add(pos,"VEC3","f",34962,True),
               "NORMAL":gl.add(normals,"VEC3","f",34962),
               "COLOR_0":gl.add(colors,"VEC4","B",34962,normalized=True)}
        doc["meshes"].append({"name":m.name,"primitives":[{"attributes":attrs,"material":getattr(m,'material',0)}]})
    groups={}
    channels=[];samplers=[]; sam_lookup={}
    def channel(idx,prop,points,fn,kind):
        times0=[i/FPS for i,_ in points]
        vals=[v for _,x in points for v in fn(x)]
        av=gl.add(times0,"SCALAR","f",bounds=True); bv=gl.add(vals,kind,"f")
        key=av,bv
        if key not in sam_lookup:
            sam_lookup[key]=len(samplers)
            samplers.append({"input":av,"output":bv,"interpolation":"LINEAR"})
        channels.append({"sampler":sam_lookup[key],"target":{"node":idx,"path":prop}})
    node_ids=[]
    for item in scene.nodes:
        group=item['group']
        parent=item.get('parent',-1)
        if parent<0 and group not in groups:
            groups[group]=gl.node({"name":group,"children":[]});roots.append(groups[group])
        tracks=item['tracks']
        a=tracks.get('yaw',[(0,(item['angle'],))])[0][1][0]
        t=tracks.get('translation',[(0,item['translation'])])[0][1]
        s=tracks.get('scale',[(0,(1,1,1))])[0][1]
        nd={"name":item['name'],"translation":gl_point(t),"scale":gl_scale(s)}
        if "extras" in item:nd["extras"]=item["extras"]
        if item['mesh']>=0: nd["mesh"]=item['mesh']
        if a: nd['rotation']=[0,math.sin(a/2),0,math.cos(a/2)]
        idx=gl.node(nd);node_ids.append(idx)
        pid=node_ids[parent] if parent>=0 else groups[group]
        doc['nodes'][pid].setdefault('children',[]).append(idx)
        for prop,points in tracks.items():
            if len(points)<2: continue
            if prop=="yaw":
                channel(idx,"rotation",points,lambda x:(0,math.sin(x[0]/2),0,math.cos(x[0]/2)),"VEC4")
            else:
                channel(idx,prop,points,gl_point if prop=="translation" else gl_scale,"VEC3")
    # Retain the complete, selectable equipment. Standard animated mesh children
    # carry the inspection and solid finishes so common glTF players can show
    # the maintenance crews through the same foreground equipment as the film.
    if hasattr(scene,"inspection_windows"):
        ghost_material=len(doc["materials"])
        doc["materials"].append({"name":"Equipment | maintenance inspection finish","alphaMode":"BLEND","doubleSided":False,
            "pbrMetallicRoughness":{"baseColorFactor":[.86,.94,.94,.057],"metallicFactor":.03,"roughnessFactor":.72}})
        ghost_meshes={}; finish_keys={}
        for j,item in enumerate(scene.nodes):
            equipment=item["group"]=="Dry coolers" or item["group"] in FRAME_EQUIPMENT
            frame_part=item["group"]=="Structure"
            if not (equipment or frame_part):continue
            bearing=scene.nodes[item["parent"]]["angle"] if equipment else None
            finish=(bearing,frame_part)
            if finish not in finish_keys:
                switches=[];previous=False
                windows=(scene.power_detail,) if frame_part else scene.inspection_windows
                if equipment:windows=(*windows,scene.storage_inspection)
                for f,view in enumerate(scene.camera):
                    inspect=any(start<=f<end for start,end in windows)
                    if inspect and bearing is not None:
                        x,y,_=view["eye"]
                        inspect=x*math.cos(bearing)+y*math.sin(bearing)>-.12*math.hypot(x,y)
                    if inspect!=previous:
                        switches.extend([(f-.02,int(previous)),(f,int(inspect))])
                        previous=inspect
                finish_keys[finish]=[(0,0)]+switches
            idx=node_ids[j];root=doc["nodes"][idx];mid=root.pop("mesh")
            if mid not in ghost_meshes:
                prim=doc["meshes"][mid]["primitives"][0]
                ghost_meshes[mid]=len(doc["meshes"])
                doc["meshes"].append({"name":doc["meshes"][mid]["name"]+" | inspection finish",
                    "primitives":[{"attributes":prim["attributes"],"material":ghost_material}]})
            for ghost in (False,True):
                initial=0 if ghost else 1
                child=gl.node({"name":item["name"]+(" | inspection finish" if ghost else " | full finish"),
                    "mesh":ghost_meshes[mid] if ghost else mid,"scale":[initial]*3})
                root.setdefault("children",[]).append(child)
                values=[(f,((on if ghost else 1-on),)*3) for f,on in finish_keys[finish]]
                if len(values)>1:channel(child,"scale",values,gl_scale,"VEC3")
    doc["cameras"]=[{"type":"perspective","name":"Construction camera","perspective":{
        "yfov":math.radians(scene.camera[0]['fov']),"aspectRatio":aspect_ratio,"znear":.1,"zfar":1400}}]
    cams=scene.camera; first=cams[0]
    ci=gl.node({"name":"Construction camera","camera":0,"translation":gl_point(first['eye']),
                "rotation":camera_quat(first['eye'],first['target'])});roots.append(ci)
    channel(ci,"translation",keys([c['eye'] for c in cams]),gl_point,"VEC3")
    rotations=[]
    for c in cams:
        quat=camera_quat(c['eye'],c['target'])
        if rotations and sum(a*b for a,b in zip(quat,rotations[-1]))<0:quat=tuple(-v for v in quat)
        rotations.append(quat)
    channel(ci,"rotation",keys(rotations),lambda x:x,"VEC4")
    doc["extensionsUsed"]=["KHR_lights_punctual"]
    doc["extensions"]={"KHR_lights_punctual":{"lights":[
        {"name":"Afternoon sun","type":"directional","intensity":2.7,"color":[1,.98,.93]},
        {"name":"Sky fill","type":"directional","intensity":1.0,"color":[.9,.96,1]}]}}
    for i,(name,direction) in enumerate([("Afternoon sun",(-.52,-.47,.79)),("Sky fill",(.60,-.30,.77))]):
        roots.append(gl.node({"name":name,"rotation":camera_quat(direction,(0,0,0)),
                              "extensions":{"KHR_lights_punctual":{"light":i}}}))
    doc["scenes"][0]["name"]=cfg.display(cfg.TITLE+" | construction, dry cooler frames, pod loading and service")
    doc["animations"].append({"name":getattr(scene,"animation_title",cfg.display("Construction, cooler frames, pod loading, crew access, pod exchange and exterior orbit")),"samplers":samplers,"channels":channels})
    gl.save(path)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--glb',required=True,type=Path)
    parser.add_argument('--render-data',type=Path)
    args=parser.parse_args()
    scene=build()
    glb_file(scene,args.glb)
    if args.render_data: render_data(scene,args.render_data)
    print(f"{FRAMES} frames at {FPS} fps, {len(scene.nodes)} nodes, {len(scene.meshes)} shared meshes")
