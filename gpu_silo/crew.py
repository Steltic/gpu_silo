"""Low-poly maintenance crews, recessed wedge decks and rack-and-pinion guides."""
from . import design as cfg
from . import clock

import math

from . import silo_model as s


LEVELS=tuple(cfg.SERVICE["wedge_destinations"])  # 0 is the underside of the lower power unit.
SIZES=tuple(cfg.SERVICE["crew_by_wedge"])
DISPATCH=(2,11,23,4,18,12,8,20)
# The side of the lower power module folds down to floor level beside this wedge.
# The deck stops just under it and the crew step across onto the folded side.
POWER_FLOOR=cfg.CROWN+.27+.15
POWER_DECK=POWER_FLOOR-.086
PANEL_STEP=.080
POWER_BAY=LEVELS.index(0) if 0 in LEVELS else -1
TURBINE_POINTS=((2.05,1.55),(2.05,-1.45),(2.05,.05))
STOW=-.004
WELL_RADIUS=s.RI-.06
WELL_FLOOR=-.42
PLATE_IN,PLATE_OUT=2.44,s.RI-.40
HALF=math.pi/cfg.BAYS
EDGE=cfg.FRAME_WIDTH/2+.06
ON,OFF=(1.,1.,1.),(0.,0.,0.)
DECK,FRAME,RAIL="c39c5b","566a69","e3b269"


def target(bay):
    return POWER_DECK if LEVELS[bay]==0 else cfg.STORE["lowest_berth_m"]+(LEVELS[bay]-1)*cfg.STORE["pitch_m"]-.025


def travel(w,bay):
    start=108+DISPATCH[bay%len(DISPATCH)]
    stop=start+60+2.95*target(bay)
    rise=s.step(start,stop,w)
    descend=s.step(572+DISPATCH[bay%len(DISPATCH)],670+DISPATCH[bay%len(DISPATCH)],w)
    if LEVELS[bay]==0:descend=s.step(clock.TURBINE_WORK[3]-clock.CREW+2,698,w)
    return rise*(1-descend)


def elevation(w,bay):
    return STOW+(target(bay)-STOW)*travel(w,bay)


def half_angle(r,edge=EDGE):
    return HALF-math.asin(edge/r)


def arc_point(r,side,z):
    return s.polar(r,side*half_angle(r),z)


def recess_floor(scene):
    """A shallow common well lets the parked platforms sit flush with grade."""
    for item in scene.nodes[:4]:
        mesh=scene.meshes[item["mesh"]]
        if item["name"]=="Agricultural fields and access track":
            # Split the field layers under the entire work pad, kept level outside.
            clear=s.RO+4.30
            tris=[]
            for a,b,c,col in mesh.tris:
                if abs(b[1]-a[1])<1e-8 and abs(c[0]-b[0])<1e-8:
                    if a[0]<-clear and b[0]>clear and a[1]<-clear and c[1]>clear:
                        panel=s.Mesh("Inset beneath work pad")
                        for x0,y0,x1,y1 in [(a[0],a[1],-clear,c[1]),(clear,a[1],b[0],c[1]),
                                            (-clear,a[1],clear,-clear),(-clear,clear,clear,c[1])]:
                            s.quad_xy(panel,x0,y0,x1,y1,a[2],col)
                        s.quad_xy(panel,-clear,-clear,clear,clear,WELL_FLOOR-.065,col)
                        tris.extend(panel.tris);continue
                # The second triangle of either complete centre field quad is
                # replaced by the four bordering strips and depressed centre.
                if abs(c[0]-a[0])<1e-8 and abs(c[1]-b[1])<1e-8 and a[0]<-clear and b[0]>clear and a[1]<-clear and c[1]>clear:
                    continue
                tris.append((a,b,c,col))
            mesh.tris=tris
        elif item["name"] in ("Compacted work pad","Concrete starter slab"):
            mesh.tris=[]
            if item["name"]=="Compacted work pad":
                s.sector(mesh,WELL_RADIUS,s.RO+4.15,-.09,-.01,0,s.TAU,48,["aeaa93","ada589","c6bea5","b8ad94"],caps=False)
            else:
                neutral=["9eaaa0","87958e","caced0","c4c9c0"]
                s.sector(mesh,WELL_RADIUS,s.RO+.64,WELL_FLOOR,0,0,s.TAU,s.SECTORS*2,neutral,caps=False)
                s.sector(mesh,0,WELL_RADIUS,WELL_FLOOR-.12,WELL_FLOOR,0,s.TAU,s.SECTORS*2,neutral,caps=False)
                s.sector(mesh,0,PLATE_IN-.035,WELL_FLOOR,0,0,s.TAU,s.SECTORS*2,neutral,caps=False)
                # A solid straight floor carries each pod through the ring of
                # parked decks. The entry wedge closes its outer section.
                lo,hi=PLATE_OUT+.012,WELL_RADIUS+.04
                a=[(lo,-.66,0),(hi,-.66,0),(hi,.66,0),(lo,.66,0)]
                co,si=math.cos(s.ENTRY),math.sin(s.ENTRY)
                mesh.face([(x*co-y*si,x*si+y*co,z) for x,y,z in a],"a7b1a7")
    scene.project_info.update(platformWellDepth_m=-WELL_FLOOR,restingDeckBelowGrade_m=-STOW)


def box(m,x0,y0,x1,y1,z0,z1,col):
    s.box(m,x0,y0,x1,y1,z0,z1,col)
    m.face([(x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0)],col)


def wedge(m,ri,ro,z0,z1,color):
    n=14
    def row(r,u,z):return s.polar(r,(2*u-1)*half_angle(r),z)
    for k in range(n):
        u,v=k/n,(k+1)/n
        a,b,c,d=row(ri,u,z1),row(ro,u,z1),row(ro,v,z1),row(ri,v,z1)
        m.face([a,b,c,d],color)
        for r,col in ((ri,FRAME),(ro,FRAME)):
            face=[row(r,u,z0),row(r,v,z0),row(r,v,z1),row(r,u,z1)]
            m.face(face if r==ro else face[::-1],col)
        m.face([row(ri,v,z0),row(ro,v,z0),row(ro,u,z0),row(ri,u,z0)],FRAME)
    for side in (-1,1):
        ends=[arc_point(ri,side,z0),arc_point(ro,side,z0),arc_point(ro,side,z1),arc_point(ri,side,z1)]
        m.face(ends if side<0 else ends[::-1],FRAME)


def floor_plate(landing=False):
    m=s.Mesh("Ground crew landing" if landing else "Solid wedge personnel deck and climbing shoes")
    m.material=3
    if landing:
        wedge(m,1.05,PLATE_IN-.035,-.10,0,"9ba79a")
        return m
    wedge(m,PLATE_IN,PLATE_OUT,-.155,0,DECK)
    for side in (-1,1):
        a=math.radians(10)*side
        s.bar(m,s.polar(PLATE_OUT-.16,a,-.083),s.polar(s.RI-.126,a,-.083),.18,FRAME,.125)
        s.bar(m,s.polar(s.RI-.132,a,-.37),s.polar(s.RI-.132,a,-.01),.075,FRAME,.036)
        s.bar(m,arc_point(PLATE_IN+.03,side,-.04),arc_point(PLATE_OUT-.04,side,-.04),.055,"ddb477",.06)
    for x in (2.82,3.65,4.48,5.20):
        width=(x*math.sin(HALF)-EDGE)/math.cos(HALF)-.12
        box(m,x-.014,-width,x+.014,width,0,.003,"8e805f")
    return m


def guide(bay):
    m=s.Mesh("Twin perimeter guide rails")
    m.material=3
    for sign in (-1,1):
        a=math.radians(10)*sign
        s.bar(m,s.polar(s.RI-.103,a,-.23),s.polar(s.RI-.103,a,target(bay)+.38),.030,"75847e",.022)
    return m


def railing(gate=False):
    m=s.Mesh("Telescopic boarding gate" if gate else "Recessing wedge guards")
    m.material=3
    if gate:
        r=PLATE_IN+.045
        for z in (.48,.94):s.bar(m,arc_point(r,-1,z),arc_point(r,1,z),.032,RAIL)
        return m
    for sign in (-1,1):
        for r in (PLATE_IN+.045,PLATE_OUT-.065):
            p=arc_point(r,sign,0);s.bar(m,p,(p[0],p[1],.94),.045,FRAME)
        # Low work-side returns leave the access face clear for an inspector's tools.
        for ri,ro in ((PLATE_IN+.045,PLATE_IN+.53),(PLATE_OUT-.43,PLATE_OUT-.065)):
            s.bar(m,arc_point(ri,sign,.94),arc_point(ro,sign,.94),.041,RAIL)
            p=arc_point(ro if ri<3 else ri,sign,0)
            s.bar(m,p,(p[0],p[1],.94),.035,FRAME)
    r=PLATE_OUT-.065
    for z in (.48,.94):
        for j in range(7):
            a=(j/7*2-1)*half_angle(r);b=((j+1)/7*2-1)*half_angle(r)
            s.bar(m,s.polar(r,a,z),s.polar(r,b,z),.040,RAIL)
    return m


def ellipse(m,c,rx,ry,rz,col,n=8):
    x,y,z=c
    rings=[]
    for t in (-1.32,-.65,.18,.91,1.43):
        rings.append([(x+rx*math.cos(t)*math.cos(j*s.TAU/n),y+ry*math.cos(t)*math.sin(j*s.TAU/n),
                       z+rz*math.sin(t)) for j in range(n)])
    for lower,upper in zip(rings,rings[1:]):
        for j in range(n):
            k=(j+1)%n;m.face([lower[j],lower[k],upper[k],upper[j]],col)
    m.face(rings[0][::-1],col);m.face(rings[-1],col)


def trunk(m,rows,n=8):
    prev=None
    for x,z,rx,ry,col in rows:
        pts=[(x+rx*math.cos((j+.5)*s.TAU/n),ry*math.sin((j+.5)*s.TAU/n),z) for j in range(n)]
        if prev is None:m.face(pts[::-1],col)
        else:
            for j in range(n):
                k=(j+1)%n;m.face([prev[j],prev[k],pts[k],pts[j]],col)
        prev=pts
    m.face(prev,col)


def limb(m,a,b,r0,r1,col):
    w=s.norm(s.minus(b,a));side=s.norm(s.cross((0,1,0),w));v=s.cross(w,side)
    rings=[]
    for pt,r in ((a,r0),(b,r1)):
        rings.append([s.plus(pt,s.plus(s.times(side,r*math.cos(i*s.TAU/6)),s.times(v,r*math.sin(i*s.TAU/6)))) for i in range(6)])
    lo,hi=rings
    for i in range(6):
        j=(i+1)%6;m.face([lo[i],lo[j],hi[j],hi[i]],col)
    m.face(lo[::-1],col);m.face(hi,col)


MODES={"stand":1,"walk":8,"inspect":6,"underside":6}


def technician(style,mode,index):
    m=s.Mesh(f"Technician {style+1} | {mode} pose {index+1}")
    phase=s.TAU*index/MODES[mode]
    walk=mode=="walk";work=mode in ("inspect","underside");high=mode=="underside"
    wave=math.sin(phase);bob=.021*abs(math.sin(phase)) if walk else .010*(1+wave) if work else 0
    lean=.037 if work else .006
    skin=("b27954","d3a07a","805845")[style]
    vest=("e08b40","e4ba5d","80b9ae")[style]
    hat=("edc56a","f2e8cd","e29554")[style]
    pants="354953";sleeve="526870";glove="d9c29b";stripe="e7e2c6"
    for sign in (-1,1):
        drift=sign*.19*wave if walk else .044*sign
        lift=.09*max(0,math.cos(phase)*sign) if walk else 0
        y=.105*sign
        hip=(0,y,.83+bob);knee=(drift*.48+.037+lift*.58,y,.47+bob+lift*.35);ankle=(drift,y,.12+lift)
        limb(m,hip,knee,.098,.084,pants);limb(m,knee,ankle,.085,.063,"435863")
        box(m,drift-.079,y-.066,drift+.143,y+.066,.012+lift,.117+lift,"393e3a")
    trunk(m,[(0,.75+bob,.127,.199,pants),(0,.91+bob,.146,.208,pants),
             (lean,.955+bob,.153,.201,vest),(lean,1.01+bob,.154,.206,stripe),
             (lean,1.20+bob,.161,.238,vest),(lean,1.25+bob,.157,.242,stripe),
             (lean,1.37+bob,.137,.232,vest),(lean,1.42+bob,.089,.134,sleeve)])
    neck=(lean+.012,0,1.443+bob)
    ellipse(m,neck,.069,.067,.088,skin)
    head=(lean+.021,0,1.535+bob)
    ellipse(m,head,.104,.100,.135,skin,9)
    box(m,head[0]+.066,-.091,head[0]+.106,.091,1.533+bob,1.572+bob,"455758")
    ellipse(m,(lean+.018,0,1.620+bob),.137,.123,.024,hat,10)
    ellipse(m,(lean+.010,0,1.653+bob),.117,.108,.082,hat,10)
    for sign in (-1,1):
        shoulder=(lean,sign*.204,1.326+bob)
        if high:
            elbow=(.145,sign*.243,1.49+bob)
            hand=(.22+.028*wave,sign*(.14+.025*wave),1.635+.025*wave+bob)
        elif work:
            elbow=(.18+.025*wave,sign*.234,1.10+.035*wave+bob)
            hand=(.328+.045*wave,sign*(.14+.035*wave),1.20+sign*.115+.03*wave+bob)
        else:
            swing=-sign*.17*wave if walk else .027
            elbow=(swing*.53-.012,sign*.249,1.074+bob)
            hand=(swing+.057,sign*.232,.884+bob)
        limb(m,shoulder,elbow,.073,.056,sleeve);limb(m,elbow,hand,.059,.043,"677e80")
        ellipse(m,hand,.047,.047,.055,glove,6)
        if work and sign==1:
            if high:
                tip=(hand[0]+.018,hand[1],1.781+.003*(1+wave))
                limb(m,hand,tip,.034,.014,"9a983f")
            else:
                limb(m,hand,(hand[0]+.075,hand[1],hand[2]+.015),.044,.018,"ab9e55")
    return m


def workpoint(bay,worker):
    if LEVELS[bay]==0:
        # Clear of the folding side until it is down.
        return ((5.30,.55),(4.75,-.50),(4.20,.15))[worker]
    x=(4.58,3.85,3.06)[worker]
    sign=(1,-1,1)[worker]
    y=sign*(x*math.sin(HALF)-(cfg.FRAME_WIDTH/2+.415))/math.cos(HALF)
    return x,y


def progress(w,bay,worker):
    start=21+worker*9+DISPATCH[bay%len(DISPATCH)]*.32
    end=75+worker*9+DISPATCH[bay%len(DISPATCH)]*.32
    enter=s.step(start,end,w)
    leave=s.step(701+worker*6,748+worker*6,w)
    return enter*(1-leave)


def at_turbine(w,worker):
    """0 on the deck, 1 on the folded side of the power module."""
    a,b,c,d=(v-clock.CREW for v in clock.TURBINE_WORK)
    return s.step(a+worker*2,b+worker*2,w)*(1-s.step(c-worker*2,d-worker*2,w))


def worker_pose(w,bay,worker):
    fraction=progress(w,bay,worker)
    if LEVELS[bay]==0 and at_turbine(w,worker)>0:
        g=at_turbine(w,worker)
        x0,y0=workpoint(bay,worker);x1,y1=TURBINE_POINTS[worker]
        walking=math.atan2(y1-y0,x1-x0)+(math.pi if w>clock.TURBINE_WORK[2]-clock.CREW-worker*2 else 0)
        yaw=math.pi if g>.997 else walking
        return (x0+(x1-x0)*g,y0+(y1-y0)*g,.006+PANEL_STEP*s.step(.15,.45,g)),yaw
    x0,y0=((2.24,.23),(1.89,-.19),(1.39,.005))[worker]
    x1,y1=workpoint(bay,worker)
    yaw=(math.atan2(y1-y0,x1-x0))*(1-s.step(.80,1.,fraction))
    facing=(math.radians(106 if worker!=1 else -106) if LEVELS[bay] else math.pi)
    yaw+=facing*s.step(.80,1.,fraction)
    if w>695:yaw+=math.pi*(1-s.step(749,775,w))*s.step(695,702,w)
    return (x0+(x1-x0)*fraction,y0+(y1-y0)*fraction,.006),yaw


def current_pose(w,bay,worker):
    g=progress(w,bay,worker)
    seed=worker*3+bay*2
    if .003<g<.997:return "walk",(int((w+seed)/2.1)%8)
    if LEVELS[bay]==0:
        t=at_turbine(w,worker)
        if .003<t<.997:return "walk",(int((w+seed)/2.1)%8)
        if t>=.997:return "inspect",int((w+seed*3)/4.2)%6
        return "stand",0
    if travel(w,bay)>.999 and w>185 and w<552:
        return "inspect",int((w+seed*3)/4.2)%6
    return "stand",0


def install(scene,node,p,begin):
    """Add objects attached to the assembled steel cage and independent boarding tracks."""
    def add(m):return scene.mesh(m)
    def show(t0,t1=None):
        v=[(0,OFF),(t0-.025,OFF),(t0,ON)]
        if t1 is not None:v.extend([(t1-.025,ON),(t1,OFF)])
        return v
    def curve(vals):
        return [(0,vals[0])]+[(begin+w,v) for w,v in p.flat_keys(vals)]
    rack=next(i for i,n in enumerate(scene.nodes) if n['name']=="Preassembled steel store")
    deck,landing,rails,gate=map(add,(floor_plate(),floor_plate(True),railing(),railing(True)))
    people={}
    duration=785
    for bay,size in enumerate(SIZES):
        label=f"Wedge {bay+1:02}"
        angle=s.ENTRY+bay*s.TAU/cfg.BAYS
        wedge_node=node(label+" | service equipment",-1,"Crew lifts",rack,ang=angle)
        node(label+" | twin guide rails",add(guide(bay)),"Crew guides",wedge_node)
        node(label+" | ground landing",landing,"Crew access",wedge_node,t=(0,0,STOW))
        elev=[elevation(w,bay) for w in range(duration)]
        deck_node=node(label+" | solid lift platform",deck,"Crew decks",wedge_node,
                       tracks={"translation":curve([(0,0,z) for z in elev])})
        for hardware,m,a,b,c,d in [("perimeter rails",rails,5,27,754,777),("boarding gate",gate,96,106,693,700)]:
            node(label+" | "+hardware,m,"Crew guards",deck_node,tracks={"scale":curve([
                (1,1,s.step(a,b,w)*(1-s.step(c,d,w))) for w in range(duration)])})
        for worker in range(size):
            person=f"{label} | technician {worker+1}"
            poses=[worker_pose(w,bay,worker) for w in range(duration)]
            actor=node(person,-1,"Maintenance crews",deck_node,tracks={
                "translation":curve([pos for pos,_ in poses]),"yaw":curve([(yaw,) for _,yaw in poses]),
                "scale":show(begin+3+worker*2,begin+778)})
            sequence=[current_pose(w,bay,worker) for w in range(duration)]
            style=(bay+worker)%3
            for mode,index in dict.fromkeys(sequence):
                spec=(style,mode,index)
                if spec not in people:people[spec]=add(technician(*spec))
                # Step changes preserve a solid, articulated silhouette between poses.
                initial=ON if sequence[0]==(mode,index) else OFF
                keys=[(0,initial)]
                for w in range(1,duration):
                    was=sequence[w-1]==(mode,index);is_on=sequence[w]==(mode,index)
                    if was!=is_on:keys.extend([(begin+w-.025,ON if was else OFF),(begin+w,ON if is_on else OFF)])
                node(person+f" | {mode} {index+1}",people[spec],"Crew poses",actor,tracks={"scale":keys})
