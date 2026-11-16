"""Wall-mounted dry cooler frames, their mesh screens, cast-in anchors and conduits,
the travelling crawler pick and the boom-lift crew that connects each frame.

Frame coordinates are metres. Local X points away from the silo from the back
plane of the frame, local Y follows the wall and Z is up from the frame base.
"""
import math

from . import clock
from . import design as cfg
from . import crew
from . import services
from . import silo_model as s

D=cfg.COOL
SITE=cfg.SITE
N=cfg.FRAMES
ROWS=D["coolers_per_frame"]
WIDTH,HEIGHT,DEPTH=D["frame_width_m"],D["frame_height_m"],D["frame_depth_m"]
ROW=HEIGHT/ROWS
COOL_L,PUMP_L=D["cooler_length_m"],D["pump_unit_length_m"]
COOL_H=ROW-.30
COOL_X0,COOL_X1=.25,DEPTH-.15
FANS=max(1,round(COOL_L/2.25))
BACK=s.RO+D["wall_standoff_m"]
TIERS=tuple(D["tier_base_m"])
BEARINGS=[s.ENTRY+s.TAU/N*(k+.5) for k in range(N)]
COLUMNS=tuple(D["anchor_columns_m"])
PUMP_Y=WIDTH/2-PUMP_L/2
COOL_Y=-WIDTH/2+COOL_L/2
CONDUIT_Y=(-PUMP_Y,PUMP_Y)
CONDUIT_R=.15
LAY_R=SITE["laydown_radius_m"]
TRACK_R=SITE["crane_track_radius_m"]
LIFT_R=SITE["boom_lift_track_radius_m"]
LIFT_SIDE=WIDTH/2+7.5
LIFT_ANGLE=math.asin(LIFT_SIDE/LIFT_R)
LIFT_PARK=math.radians(50)
LIFT_AWAY=72.
BASKET_REST=3.1
GROUND=.25
SLING=3.4
OVER=.60
BOOM_LENGTH=62.
SCREEN="c6c8c3"
# The frames stand in laydown from the pod delivery and are hung while the pods are loaded.
START=clock.DELIVERY_AT
FIRST=clock.FRAMES_FIRST
DIR=1 if SITE["direction"]=="anticlockwise" else -1
# The boom lift works at the end of each frame that faces the frames already hung.
SIDE=-DIR
ORDER=[(SITE["first_frame"]+DIR*i)%N for i in range(N)]
THETA=[BEARINGS[SITE["first_frame"]]+DIR*i*s.TAU/N for i in range(N)]
LAY_SHIFT={int(k)-1:math.radians(v) for k,v in SITE["laydown_offset_degrees_by_frame"].items()}
ends=[FIRST]
for i in range(N):
    ends.append(ends[-1]+(SITE["first_cycle_frames"] if i==0 else SITE["repeat_cycle_frames"]))
STARTS=ends[:-1]
END=ends[-1]
LIFT_GONE=END+70
OFF,ON=(0,0,0),(1,1,1)
STRUCT,SILVER,COIL,FIN,DARK,AMBER="4c6266","c4c9be","416c73","93a9a0","32484e","db9955"
BRACE="678078"
LIFT_ORANGE,LIFT_DARK="d98a3d","3f4a4c"


def tier(k):
    return k%len(TIERS)


def base(k):
    """Elevation of the underside of frame k. Neighbouring frames alternate between the tiers."""
    return TIERS[tier(k)]


def times(i):
    """Key frames of installation cycle i: start, rigged, hoisted, at the wall, seated, released, connected, end."""
    a=STARTS[i];d=ends[i+1]-a
    cuts=(0,.10,.36,.54,.62,.76,.90,1) if i==0 else (0,.20,.44,.62,.70,.79,.88,1)
    return [a+round(q*d) for q in cuts]


def lay_bearing(i):
    """Bearing at which frame i of the installation order stands before it is picked."""
    return THETA[i]+LAY_SHIFT.get(ORDER[i],0)


def frame_bearing(i,f):
    """A frame stood clear of the terminal is carried round to its own bearing as it moves in."""
    c,d=times(i)[2:4];lay=lay_bearing(i)
    return lay+(THETA[i]-lay)*s.step(c,d,f)


def pose(i,f):
    """Polar radius of the frame's back plane and the elevation of its base."""
    a,b,c,d,e,r,g,end=times(i)
    seat=base(ORDER[i])
    radius=LAY_R+(BACK-LAY_R)*s.step(c,d,f)
    z=GROUND+(seat+OVER-GROUND)*s.step(b,c,f)-OVER*s.step(d,e,f)
    return radius,z


def cycle(f):
    return max(0,min(N-1,sum(1 for a in STARTS if f>=a)-1))


def crane_bearing(f):
    """The crawler tracks round the silo between picks and carries each frame on its own radial line."""
    if f<=STARTS[0]:return lay_bearing(0)
    i=cycle(f);a,b,c,d,e,r,g,end=times(i)
    if f<b:
        if i==0:return lay_bearing(0)
        return THETA[i-1]+(lay_bearing(i)-THETA[i-1])*s.step(times(i-1)[5],b,f)
    if f<=r:return frame_bearing(i,f)
    if i==N-1:return THETA[i]
    return THETA[i]+(lay_bearing(i+1)-THETA[i])*s.step(r,times(i+1)[1],f)


def hook(f):
    """Hook in polar form on the crane's own radial line: radius, bearing and elevation."""
    lug=GROUND+HEIGHT+SLING
    i=cycle(f);a,b,c,d,e,r,g,end=times(i)
    bearing=crane_bearing(f)
    if f<b:
        if i==0:return LAY_R+DEPTH/2,bearing,lug+6*(1-s.step(STARTS[0],b-4,f))
        prev=times(i-1);seat=base(ORDER[i-1])+HEIGHT+SLING
        out=s.step(prev[5],prev[6],f)
        radius=BACK+DEPTH/2+(LAY_R-BACK)*out
        z=seat+2.5*s.step(prev[5],prev[5]+6,f)
        z+=(lug-seat-2.5)*s.step(prev[6]-4,b-3,f)
        return radius,bearing,z
    if f<=r:
        radius,z=pose(i,f)
        return radius+DEPTH/2,bearing,z+HEIGHT+SLING
    seat=base(ORDER[i])+HEIGHT+SLING
    out=s.step(r,g,f)
    z=seat+2.5*s.step(r,r+6,f)
    if i==N-1:z+=6*s.step(g,end,f)
    else:z+=(lug-seat-2.5)*s.step(g-4,times(i+1)[1]-3,f)
    return BACK+DEPTH/2+(LAY_R-BACK)*out,bearing,z


def crane(f):
    """World position of the crawler, hook and boom tip, and the crawler heading."""
    radius,bearing,z=hook(f)
    foot=s.polar(TRACK_R,bearing,0)
    reach=TRACK_R-radius
    tip=2.45+math.sqrt(BOOM_LENGTH**2-reach**2)
    return foot,s.polar(radius,bearing,z),tip,bearing+math.pi/2


def lift_bearing(f):
    """Bearing of the boom lift. It drives to the next frame while the crane hoists."""
    i=cycle(f)
    here=THETA[i]+SIDE*LIFT_ANGLE
    before=THETA[i-1]+SIDE*LIFT_ANGLE if i else here+SIDE*LIFT_PARK
    begin=times(i)[0];ready=times(i)[3]-2
    return before+(here-before)*s.step(begin,ready,f)


def lift_radius(f):
    """The boom lift leaves the silo once the last frame is connected."""
    return LIFT_R+(LIFT_AWAY-LIFT_R)*s.step(stow_end(N-1)+4,LIFT_GONE,f)


def drive(f):
    return s.polar(lift_radius(f),lift_bearing(f),0)


def stow_end(i):
    g,end=times(i)[6:]
    return g+round(.7*(end-g))


def reach(f):
    """0 with the basket stowed on the chassis, 1 at the frame."""
    i=cycle(f);a,b,c,d,e,r,g,end=times(i)
    return s.step(d,e,f)*(1-s.step(g,stow_end(i),f))


def basket(f):
    """World position of the basket floor and the bearing its crew faces."""
    i=cycle(f);a,b,c,d,e,r,g,end=times(i)
    lifted=reach(f)
    k=ORDER[i];bearing=lift_bearing(f)
    cx,cy,_=drive(f)
    heading=bearing+math.pi/2
    rest=(cx+3.6*math.cos(heading),cy+3.6*math.sin(heading),BASKET_REST)
    theta=THETA[i]
    low,high=base(k)+1.15,base(k)+HEIGHT-1.35
    work_z=low+(high-low)*s.step(e+2,g-2,f)
    x,y=BACK+DEPTH/2,SIDE*(WIDTH/2+.95)
    work=(x*math.cos(theta)-y*math.sin(theta),x*math.sin(theta)+y*math.cos(theta),work_z)
    u=lifted
    return tuple(p+(q-p)*u for p,q in zip(rest,work)),heading+(theta-SIDE*math.pi/2-heading)*u


def connected(i,f):
    """Fraction of the pipe spools made up on frame i."""
    a,b,c,d,e,r,g,end=times(i)
    return s.step(e+3,g-1,f)


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


def cooler_mesh():
    """One dry cooler. Air enters the finned coil at the back and leaves through the outward fans."""
    m=mesh(f"Dry cooler | {D['cooler_capacity_mw']:g} MW, finned coil and {FANS} outward axial fans")
    half=COOL_L/2;h=COOL_H
    plenum=COOL_X0+.34
    closed(m,plenum,-half+.06,COOL_X1-.07,half-.06,.10,h-.06,"b3beb9")
    closed(m,COOL_X0,-half+.10,plenum,half-.10,.16,h-.12,COIL)
    fins=max(8,round(COOL_L/.34))
    for j in range(1,fins):
        y=-half+.10+(COOL_L-.20)*j/fins
        both(m,[(COOL_X0-.006,y-.018,.18),(COOL_X0-.006,y+.018,.18),(COOL_X0-.006,y+.018,h-.14),(COOL_X0-.006,y-.018,h-.14)],FIN)
    closed(m,COOL_X0-.03,-half,COOL_X1,half,0,.11,STRUCT)
    closed(m,COOL_X0-.03,-half,COOL_X1,half,h-.07,h,SILVER)
    for y in (-half,half-.12):
        closed(m,COOL_X0-.03,y,COOL_X1,y+.12,.11,h-.07,STRUCT)
    face=COOL_X1-.07
    closed(m,face,-half+.02,face+.07,half-.02,.06,h-.03,"aab6b1")
    radius=min(h/2-.20,COOL_L/FANS/2-.15)
    axis=h/2+.01
    for j in range(FANS):
        y=(j-(FANS-1)/2)*COOL_L/FANS
        services.pipe(m,(face+.07,y,axis),(face+.085,y,axis),radius-.03,DARK,n=18)
        services.pipe(m,(face+.075,y,axis),(face+.24,y,axis),radius+.035,SILVER,radius-.03,n=20)
        services.pipe(m,(face+.085,y,axis),(face+.22,y,axis),radius*.20,"c1b7a1",n=10)
        for k in range(5):
            ang=k*s.TAU/5+.21+j*.4
            def fan(r,a):
                return (face+.17,y+r*math.cos(ang+a),axis+r*math.sin(ang+a))
            m.face([fan(radius*.16,0),fan(radius*.80,-.27),fan(radius*.90,.06),fan(radius*.41,.37),fan(radius*.18,.29)],"99aaa3")
    # Supply and return headers at the pump end.
    for z,col in ((h*.33,services.RETURN),(h*.67,services.INLET)):
        services.pipe(m,(COOL_X0+.16,half-.07,z),(COOL_X0+.16,half+.10,z),.11,col,n=10)
    return m


def pump_mesh():
    m=mesh("Cooler pump unit | solid grey housing")
    color=D["pump_colour"].lstrip("#")
    half=PUMP_L/2-.08
    closed(m,COOL_X0+.25,-half,COOL_X1-.35,half,.16,COOL_H-.34,color)
    closed(m,COOL_X0+.12,-half-.03,COOL_X1-.22,half+.03,.02,.16,STRUCT)
    services.pipe(m,(COOL_X0+.02,0,COOL_H*.67),(COOL_X0+.26,0,COOL_H*.67),.13,"8f9796",n=10)
    return m


def frame_mesh():
    m=mesh(f"Dry cooler frame | {WIDTH:g} m × {HEIGHT:g} m steel, {ROWS} cooler bays and lifting lugs")
    xs=(.10,DEPTH-.10)
    ys=(-WIDTH/2+.10,WIDTH/2-PUMP_L,WIDTH/2-.10)
    for x in xs:
        for y in ys:
            closed(m,x-.10,y-.10,x+.10,y+.10,0,HEIGHT,STRUCT)
    for j in range(ROWS+1):
        z=min(HEIGHT-.16,j*ROW)
        for x in xs:
            closed(m,x-.09,-WIDTH/2,x+.09,WIDTH/2,z,z+.16,"839594" if j==ROWS else "54696b")
        for y in ys:
            closed(m,xs[0],y-.07,xs[1],y+.07,z+.01,z+.15,"54696b")
    for j in range(ROWS):
        z0,z1=j*ROW+.16,(j+1)*ROW
        a,b=(ys[0],ys[1]) if j%2==0 else (ys[1],ys[0])
        s.bar(m,(.10,a,z0),(.10,b,z1),.09,BRACE)
        for y in ys[::2]:
            s.bar(m,(xs[0],y,z0),(xs[1],y,z1),.08,BRACE)
    for y in LUGS:
        closed(m,DEPTH/2-.13,y-.09,DEPTH/2+.13,y+.09,HEIGHT,HEIGHT+.24,AMBER)
        closed(m,xs[0],y-.08,xs[1],y+.08,HEIGHT-.16,HEIGHT,"839594")
    return m


LUGS=(-WIDTH*.30,WIDTH*.30)


def sling_mesh():
    m=mesh("Cooler frame pick | spreader beam and two vertical slings")
    top=HEIGHT+SLING
    closed(m,DEPTH/2-.14,LUGS[0]-.25,DEPTH/2+.14,LUGS[1]+.25,top-1.55,top-1.25,"bc9356")
    for y in LUGS:
        s.bar(m,(DEPTH/2,y,HEIGHT+.20),(DEPTH/2,y,top-1.50),.06,"80765c")
        s.bar(m,(DEPTH/2,y,top-1.27),(DEPTH/2,0,top),.06,"80765c")
    return m


def screen_mesh():
    """Concrete-grey steel mesh over the face, both ends and the top of one cooler frame."""
    m=mesh("Dry cooler screen | concrete-grey steel mesh on the face, ends and top")
    pitch,bar=.50,.12
    face=DEPTH+.07;ends=WIDTH/2+.07;side="b6bab4"
    def strips(count,make,colour):
        for j in range(count+1):
            wide=bar*1.8 if j in (0,count) else bar
            both(m,make(j*pitch,wide/2),colour)
    across,up,deep=round(WIDTH/pitch),round(HEIGHT/pitch),round((DEPTH-.3)/pitch)
    strips(across,lambda y,w:[(face,y-WIDTH/2-w,0),(face,y-WIDTH/2+w,0),(face,y-WIDTH/2+w,HEIGHT),(face,y-WIDTH/2-w,HEIGHT)],SCREEN)
    strips(up,lambda z,w:[(face,-WIDTH/2,z-w),(face,WIDTH/2,z-w),(face,WIDTH/2,z+w),(face,-WIDTH/2,z+w)],SCREEN)
    for y in (-ends,ends):
        strips(deep,lambda x,w:[(.3+x-w,y,0),(.3+x+w,y,0),(.3+x+w,y,HEIGHT),(.3+x-w,y,HEIGHT)],side)
        strips(up,lambda z,w:[(.3,y,z-w),(face,y,z-w),(face,y,z+w),(.3,y,z+w)],side)
    top=HEIGHT+.26
    strips(across,lambda y,w:[(.3,y-WIDTH/2-w,top),(face,y-WIDTH/2-w,top),(face,y-WIDTH/2+w,top),(.3,y-WIDTH/2+w,top)],"d0d2cc")
    strips(deep,lambda x,w:[(.3+x-w,-WIDTH/2,top),(.3+x+w,-WIDTH/2,top),(.3+x+w,WIDTH/2,top),(.3+x-w,WIDTH/2,top)],"d0d2cc")
    return m


def dunnage_mesh():
    m=mesh("Cooler frame laydown | timber dunnage and raking props")
    for y in (-WIDTH/2+.6,0,WIDTH/2-.6):
        closed(m,-.5,y-.20,DEPTH+.5,y+.20,0,GROUND,"8f8064")
    for y in (-WIDTH/2+.3,WIDTH/2-.3):
        for sign in (-1,1):
            # Short feet on the silo side leave the boom lift a clear lane.
            x=DEPTH/2+sign*(DEPTH/2-.1);run=3.1 if sign>0 else 1.0
            s.bar(m,(x,y,GROUND+4.2 if sign>0 else GROUND+1.6),(x+sign*run,y,.10),.12,"9a8a66")
            closed(m,x+sign*run-.3,y-.3,x+sign*run+.3,y+.3,0,.10,"8f8064")
    return m


def anchor_z(k,j):
    """Elevation of anchor row j on frame k. The end rows sit just inside the frame."""
    return base(k)+min(max(j*ROW,.30),HEIGHT-.30)


def wall_x(y):
    return math.sqrt(s.RO**2-y*y)


def embed_plate():
    m=mesh("Cast-in frame anchor | steel faceplate, four headed studs and threaded bushes")
    lo,hi=-.26,.26
    closed(m,-.019,-.235,.003,.235,lo,hi,"ae8d67")
    for yy in (-.147,.147):
        for z in (lo+.079,hi-.079):
            services.pipe(m,(-.195,yy,z),(-.018,yy,z),.024,"b5c4bb",n=8)
            services.pipe(m,(-.209,yy,z),(-.189,yy,z),.048,"879993",n=8)
            services.pipe(m,(-.003,yy,z),(.008,yy,z),.034,"5f6c63",.017,n=8)
    return m


def strut_mesh():
    """Bolted brackets between the curved wall and the flat back of one frame, in station coordinates."""
    m=mesh("Cooler frame seats | bolted bearing plates and wall struts")
    for y in COLUMNS:
        x=wall_x(y)
        for j in range(ROWS+1):
            z=min(max(j*ROW,.30),HEIGHT-.30)
            turn=math.asin(y/s.RO);cs,sn=math.cos(turn),math.sin(turn)
            plate=[(.004,-.20),(.05,-.20),(.05,.20),(.004,.20)]
            ring=[(x+u*cs-v*sn,y+u*sn+v*cs) for u,v in plate]
            bottom=[(px,py,z-.22) for px,py in ring];top=[(px,py,z+.22) for px,py in ring]
            m.face(top,STRUCT);m.face(bottom[::-1],STRUCT)
            for a in range(4):
                b=(a+1)%4;m.face([bottom[a],bottom[b],top[b],top[a]],STRUCT)
            s.bar(m,(x+.04,y,z),(BACK+.02,y,z),.16,SILVER,.18)
            if BACK-x>.5:s.bar(m,(x+.05,y,z-.20),(BACK,y,z-.02),.09,STRUCT)
    return m


def sleeve_mesh():
    m=mesh("Cast-in cooler conduit | sleeve through the outer wall with bolted flange")
    services.barrel(m,s.RI_OUTER-.06,s.RO+.14,CONDUIT_R,"aa966f",CONDUIT_R-.03)
    services.barrel(m,s.RO+.10,s.RO+.15,CONDUIT_R+.07,services.BRONZE,CONDUIT_R-.03)
    services.barrel(m,s.RI_OUTER-.07,s.RI_OUTER-.03,CONDUIT_R+.05,"89938c",CONDUIT_R-.03)
    return m


def spool_origin():
    y=CONDUIT_Y[1];turn=math.asin(y/s.RO)
    return (s.RO+.15)*math.cos(turn)


def spool_mesh():
    """Unit-length pipe spools in station coordinates. Scaling X makes every joint up together."""
    m=mesh("Cooler frame pipework | supply and return spools to the wall conduits")
    for side,y in zip((-1,1),CONDUIT_Y):
        turn=math.asin(y/s.RO)
        yy=(s.RO+.15)*math.sin(turn)
        for row in range(ROWS):
            for part,col in ((.33,services.RETURN),(.67,services.INLET)):
                if (part>.5)!=(side>0):continue
                z=row*ROW+.15+COOL_H*part
                services.pipe(m,(0,yy,z),(1,yy,z),.105,col,n=10)
    return m


def conduit_points(k):
    """Angle from the frame bearing and elevation of every cast-in conduit of frame k."""
    points=[]
    for side,y in zip((-1,1),CONDUIT_Y):
        for row in range(ROWS):
            part=.33 if side<0 else .67
            points.append((math.asin(y/s.RO),base(k)+row*ROW+.15+COOL_H*part))
    return points


def pour_frames(z,low):
    """Fixings are set in the forms of the lift that contains their lower edge."""
    pour=max(0,math.floor((z+low)/s.LIFT))
    return (8,33) if pour==0 else (services.lift_start(pour)-9,services.lift_start(pour)-1)


def chassis_mesh():
    m=mesh("Boom lift | four-wheel chassis, turntable and counterweight")
    closed(m,-2.6,-1.15,2.6,1.15,.55,1.15,LIFT_ORANGE)
    closed(m,-1.1,-1.0,1.3,1.0,1.15,2.05,"c77a36")
    closed(m,-2.2,-.95,-1.1,.95,1.15,1.85,LIFT_DARK)
    for x in (-1.9,1.9):
        for sign in (-1,1):
            services.pipe(m,(x,sign*1.05,.55),(x,sign*1.40,.55),.55,"293238",n=12)
            services.pipe(m,(x,sign*1.40,.55),(x,sign*1.43,.55),.26,"88928d",n=10)
    return m


BOOM_NOMINAL=(6.,14.)


def boom_mesh():
    m=mesh("Boom lift | telescopic boom")
    dx,dz=BOOM_NOMINAL
    s.bar(m,(0,0,0),(dx*.55,0,dz*.55),.50,LIFT_ORANGE,.46)
    s.bar(m,(dx*.50,0,dz*.50),(dx,0,dz),.36,"e6ae69",.32)
    return m


def basket_mesh():
    m=mesh("Boom lift | work basket and guard rails")
    closed(m,-.55,-1.2,.55,1.2,-.10,0,LIFT_DARK)
    for x in (-.52,.52):
        for y in (-1.17,0,1.17):
            s.bar(m,(x,y,0),(x,y,1.08),.05,LIFT_ORANGE)
        for z in (.55,1.08):
            s.bar(m,(x,-1.17,z),(x,1.17,z),.045,LIFT_ORANGE)
    for y in (-1.17,1.17):
        for z in (.55,1.08):
            s.bar(m,(-.52,y,z),(.52,y,z),.045,LIFT_ORANGE)
    closed(m,-.20,-.25,.20,.25,-.42,-.10,LIFT_ORANGE)
    return m


def track_mesh():
    """Crawler track and laydown apron. Both stop short of the pod terminal."""
    m=mesh("Crawler track and frame laydown apron")
    tone=["b8ad94","b8ad94","c2b89d","b8ad94"]
    s.sector(m,TRACK_R-4.2,TRACK_R+3.4,-.03,.004,s.ENTRY+math.radians(17),s.ENTRY+math.radians(354),90,tone)
    s.sector(m,s.RO+4.1,LAY_R+DEPTH+4.2,-.03,.002,s.ENTRY+math.radians(36),s.ENTRY+math.radians(352),84,
             ["b3ac93","b3ac93","bdb59c","b3ac93"])
    return m


def add(scene,node,p):
    def window(start,end=None):
        keys=[(0,OFF),(start-.02,OFF),(start,ON)]
        if end is not None:keys.extend([(end-.02,ON),(end,OFF)])
        return keys
    def curve(a,b,fn):
        values=[fn(f) for f in range(a,b+1)]
        return [(0,values[0])]+[(a+k,v) for k,v in p.flat_keys(values)]
    apron=track_mesh()
    node(apron.name,scene.mesh(apron),"Site works",tracks={"scale":window(START)})
    steel=scene.mesh(frame_mesh());cooler=scene.mesh(cooler_mesh());pump=scene.mesh(pump_mesh())
    screen=scene.mesh(screen_mesh())
    slings=scene.mesh(sling_mesh());dunnage=scene.mesh(dunnage_mesh())
    plate=scene.mesh(embed_plate());struts=scene.mesh(strut_mesh());sleeve=scene.mesh(sleeve_mesh())
    spool=scene.mesh(spool_mesh());reach_x=BACK+COOL_X0+.16-spool_origin()
    scene.cooler_frames={}
    for i,k in enumerate(ORDER):
        a,b,c,d,e,r,g,end=times(i)
        bearing=BEARINGS[k];label=f"Cooler frame {k+1:02}"
        def place(f,i=i):
            radius,z=pose(i,f)
            return s.polar(radius,frame_bearing(i,f),z)
        tracks={"translation":curve(a,e,place),"scale":window(START)}
        if lay_bearing(i)!=THETA[i]:tracks["yaw"]=curve(a,e,lambda f,i=i:(frame_bearing(i,f),))
        root=node(label+f" | {ROWS} dry coolers, {ROWS} pumps and steel",-1,"Dry cooler frames",ang=bearing,tracks=tracks)
        node(label+" | steel frame",steel,"Cooler frames",root)
        node(label+" | mesh screen",screen,"Cooler screens",root)
        coolers=[]
        for row in range(ROWS):
            z=row*ROW+.15
            coolers.append(node(label+f" | cooler {row+1}",cooler,"Dry coolers",root,t=(0,COOL_Y,z)))
            node(label+f" | pump unit {row+1}",pump,"Pump units",root,t=(0,PUMP_Y,z))
        sling=node(label+" | lifting slings",slings,"Frame rigging",root,tracks={"scale":window(b-5,r)})
        lay=lay_bearing(i)
        node(label+" | laydown dunnage",dunnage,"Frame laydown",ang=lay,t=s.polar(LAY_R,lay,0),
             tracks={"scale":window(START,g)})
        station=node(label+" | fixed wall station",-1,"Cooler frame stations",ang=bearing)
        for y in COLUMNS:
            turn=math.asin(y/s.RO);x,yy,_=s.polar(s.RO,turn,0)
            for j in range(ROWS+1):
                z=anchor_z(k,j);start,cast=pour_frames(z,-.26)
                node(label+f" | cast-in anchor {COLUMNS.index(y)+1}.{j+1}",plate,"Cooler embeds",station,ang=turn,
                     tracks={"scale":window(start),"translation":[(0,(x,yy,z+.46)),(start,(x,yy,z+.46)),(cast,(x,yy,z))]})
        node(label+" | bolted wall seats",struts,"Frame anchors",station,t=(0,0,base(k)),tracks={"scale":window(START)})
        for n,(turn,z) in enumerate(conduit_points(k)):
            start,cast=pour_frames(z,-CONDUIT_R)
            node(label+f" | cast-in conduit {n+1}",sleeve,"Cooler conduits",station,ang=turn,
                 tracks={"scale":window(start),"translation":[(0,(0,0,z+.40)),(start,(0,0,z+.40)),(cast,(0,0,z))]})
        pipes=node(label+" | pipe spools",spool,"Frame pipework",station,t=(spool_origin(),0,base(k)),
             tracks={"scale":[(0,OFF),(e+2,OFF)]+[(f,(max(.001,reach_x*connected(i,f)),1,1)) for f in range(e+3,g+1)]})
        scene.cooler_frames[k]=dict(root=root,coolers=coolers,slings=sling,spools=pipes,station=station,reach=reach_x)
    # One boom lift follows the crane round the silo with a two-person connection crew.
    def heading(f):
        return (lift_bearing(f)+math.pi/2,)
    car=node("Boom lift | chassis",scene.mesh(chassis_mesh()),"Boom lift",
             tracks={"translation":curve(START,LIFT_GONE,drive),"yaw":curve(START,LIFT_GONE,heading),"scale":window(START,LIFT_GONE)})
    def boom(f):
        (bx,by,bz),_=basket(f);cx,cy,_=drive(f)
        dx,dz=math.hypot(bx-cx,by-cy),bz-.35-2.0
        return dx,dz,math.atan2(by-cy,bx-cx)
    node("Boom lift | telescopic boom",scene.mesh(boom_mesh()),"Boom lift",car,t=(0,0,2.0),tracks={
        "yaw":curve(START,LIFT_GONE,lambda f:(boom(f)[2]-heading(f)[0],)),
        "scale":curve(START,LIFT_GONE,lambda f:(boom(f)[0]/BOOM_NOMINAL[0],1,boom(f)[1]/BOOM_NOMINAL[1]))})
    cage=node("Boom lift | work basket",scene.mesh(basket_mesh()),"Boom lift",tracks={
        "translation":curve(START,LIFT_GONE,lambda f:basket(f)[0]),"yaw":curve(START,LIFT_GONE,lambda f:(basket(f)[1],)),
        "scale":window(START,LIFT_GONE)})
    people={}
    for worker in range(SITE["workers_per_basket"]):
        actor=node(f"Boom lift | fitter {worker+1}",-1,"Connection crew",cage,t=(-.12,(-.62,.62,0)[worker%3],0))
        for index in range(crew.MODES["inspect"]):
            spec=(worker%3,"inspect",index)
            if spec not in people:people[spec]=scene.mesh(crew.technician(*spec))
            keys=[(0,ON if index==0 else OFF)]
            for f in range(FIRST,END+1):
                was=((f-1+worker*3)//5)%crew.MODES["inspect"]==index
                now=((f+worker*3)//5)%crew.MODES["inspect"]==index
                if was!=now:keys.extend([(f-.025,ON if was else OFF),(f,ON if now else OFF)])
            node(f"Boom lift | fitter {worker+1} | pose {index+1}",people[spec],"Connection crew poses",actor,tracks={"scale":keys})
    scene.project_info.update(coolerFrames=N,coolersPerFrame=ROWS,dryCoolers=cfg.COOLERS,coolerPumps=cfg.COOLERS*D["pumps_per_cooler"],
        coolerCapacity_MW=D["cooler_capacity_mw"],coolerFrame_m=[WIDTH,HEIGHT,DEPTH],coolerCasing_m=[COOL_L,COOL_X1-COOL_X0,COOL_H],
        coolerFrameBackRadius_m=BACK,coolerFrameBearings_deg=[math.degrees(b) for b in BEARINGS],
        coolerFrameBase_m=[base(k) for k in range(N)],coolerFrameInstallOrder=[k+1 for k in ORDER],
        coolerFrameSeatFrames=[times(i)[4] for i in range(N)],coolerScreen="Concrete-grey steel mesh on every frame",castInFrameAnchors=N*len(COLUMNS)*(ROWS+1),
        castInCoolerConduits=N*ROWS*D["conduits_per_cooler"],craneTrackRadius_m=TRACK_R,boomLiftCrew=SITE["workers_per_basket"])
