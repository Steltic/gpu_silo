"""Bronze four-rack housing, the grey CDU and pump section, and the two welded side trusses that carry them.

The trusses are drawn from the design in structure.py: the same panel points, chords and web members.
"""
from . import design as cfg

import math
from . import silo_model as s

INNER=cfg.STORE["root_radius_m"]
LENGTH,BODY_WIDTH,BODY_HEIGHT=cfg.BODY_LENGTH,cfg.BODY_WIDTH,cfg.BODY_HEIGHT
OUTER=INNER+LENGTH
FRAME_WIDTH,FRAME_HEIGHT=cfg.FRAME_WIDTH,cfg.FRAME_HEIGHT
# The racks are square-ended, so the frame keeps its full width to the root.
NOSE_HALF=FRAME_WIDTH/2
TAPER=.84*LENGTH/5.
PROFILE=[(INNER,NOSE_HALF),(INNER+TAPER,FRAME_WIDTH/2),(OUTER,FRAME_WIDTH/2)]
BODY_MESH=cfg.NAME+" pod | bronze rack housing and twin cantilever trusses"
FAULT_MESH=cfg.NAME+" pod | amber isolation tabs and graphite trusses"
SPARE_MESH=cfg.NAME+" pod | teal replacement tabs and graphite trusses"
FRAME="414a51"
EDGE="667078"


def half_width(x):
    u=min(1.,max(0.,(x-INNER)/TAPER))
    return NOSE_HALF+u*(FRAME_WIDTH/2-NOSE_HALF)


def footprint(unit=None):
    profile=PROFILE[:-1]+[(OUTER+cfg.extension(unit),FRAME_WIDTH/2)]
    return [(x,-w) for x,w in profile]+[(x,w) for x,w in reversed(profile)]


def prism(m,outline,z0,z1,col):
    bottom=[(x,y,z0) for x,y in outline];top=[(x,y,z1) for x,y in outline]
    m.face(top,col);m.face(bottom[::-1],col)
    for k in range(len(outline)):
        j=(k+1)%len(outline);m.face([bottom[k],bottom[j],top[j],top[k]],col)


def nominal_half_width(x):
    return .38


def longitudinal(m,x0,x1,side,z0,z1,thick,col):
    a=nominal_half_width(x0);b=nominal_half_width(x1)
    xy=[(x0,side*(a-thick)),(x1,side*(b-thick)),(x1,side*b),(x0,side*a)]
    prism(m,xy if side==1 else xy[::-1],z0,z1,col)


def brace(m,x0,z0,x1,z1,side,col):
    # Each web has a rectangular cross section. The inner panel tapers in
    # plan to clear its neighbour when the angular carriages move to 40 deg.
    dx=x1-x0;dz=z1-z0;ll=math.hypot(dx,dz)
    ex=-dz/ll*.035;ez=dx/ll*.035
    ends=[]
    for x,z in ((x0,z0),(x1,z1)):
        ring=[]
        for k,h in ((-1,0),(1,0),(1,1),(-1,1)):
            u=x+k*ex
            ring.append((u,side*(nominal_half_width(u)-.006-.042*h),z+k*ez))
        ends.append(ring)
    lo,hi=ends
    for k in range(4):
        j=(k+1)%4;face=[lo[k],lo[j],hi[j],hi[k]]
        m.face(face if side<0 else face[::-1],col)
    m.face(lo,col);m.face(hi[::-1],col)


def mesh(status="normal",extra=0.):
    m=s.Mesh({"normal":BODY_MESH,"fault":FAULT_MESH,"spare":SPARE_MESH}[status])
    m.material=3
    a,b=.86,5.86
    body_faces=set()
    # The 2.30 m rack housing sits between the top and bottom chords.
    core=[(a,-.286),(a+.84,-.286),(b,-.286),(b,.286),(a+.84,.286),(a,.286)]
    prism(m,core,.05,2.35,"25272e")
    body_faces.update(range(len(m.tris)))
    for side in (-1,1):
        start=len(m.tris)
        for i in range(8):
            x0=a+.13+i*.594;x1=x0+.545
            def skin(x,z,out=0.):
                h=.30
                # Recess the inner panels into the dark body with a shallow crown.
                return (x,side*min(.30,h+.0005+out),z)
            def face(points,c):
                q=[skin(x,z,o) for x,z,o in points]
                m.face(q if side==-1 else q[::-1],c)
            # Separate black vertical reveals and bronze recessed panels.
            bands=8
            for row in range(bands):
                z0=.32+row*.20;z1=z0+.183
                col=("997d4d","a08959","9d8351","ae9563")[(i+row)%4]
                # Project the low-poly panels onto a slight inner recess of the core
                # on both long faces. No marking sits outside the 600 mm housing.
                q=[skin(x0,z0),skin(x1,z0),skin(x1,z1),skin(x0,z1)]
                m.face(q if side==-1 else q[::-1],col)
            face([(x0,2.04,0),(x1,2.04,0),(x1,2.19,0),(x0,2.19,0)],"534a39")
            face([(x0+.07,2.13,0),(x1-.07,2.13,0),(x1-.07,2.17,0),(x0+.07,2.17,0)],"b7a16d")
        body_faces.update(range(start,len(m.tris)))
    # End fascia and status plates. The bronze panels stay recognisable in
    # each state, including the isolated pod and the spare.
    accent={"normal":"a58f66","fault":"e99748","spare":"5eb7a5"}[status]
    for x,side in ((a,-1),(b,1)):
        for z in (.23,1.92):
            rect=[(x,-.183,z),(x,.183,z),(x,.183,z+.15),(x,-.183,z+.15)]
            m.face(rect if side==1 else rect[::-1],accent)
    for sign in (-1,1):
        longitudinal(m,b-.36,b-.15,sign,.11,.30,.061,accent)
    def sized(v,body):
        x,y,z=v
        rx=INNER+(x-.86)*LENGTH/5.
        if body:
            return rx,y*BODY_WIDTH/.60,(FRAME_HEIGHT-BODY_HEIGHT)/2+(z-.05)*BODY_HEIGHT/2.30
        return rx,y*FRAME_WIDTH/.76,z*FRAME_HEIGHT/2.40
    m.tris=[(sized(u,i in body_faces),sized(v,i in body_faces),sized(w,i in body_faces),c)
            for i,(u,v,w,c) in enumerate(m.tris)]
    if extra:
        colour=cfg.POD["cdu_pump_section_colour"].lstrip("#")
        m.name += f" | {extra:.2f} m light-grey CDU and pump section"
        half=BODY_WIDTH/2
        bottom=(FRAME_HEIGHT-BODY_HEIGHT)/2
        prism(m,[(OUTER,-half),(OUTER+extra,-half),(OUTER+extra,half),(OUTER,half)],
              bottom,bottom+BODY_HEIGHT,colour)
    trusses(m,extra)
    return m


def stations(extra):
    """Panel points from the root: one panel to a rack, then the CDU and pump section."""
    from . import structure
    racks=cfg.CLUSTER["racks_per_pod"];panels=structure.T["cdu_panels"] if extra>1e-6 else 0
    return [i*LENGTH/racks for i in range(racks+1)]+[LENGTH+(i+1)*extra/panels for i in range(panels)]


def trusses(m,extra):
    """Two side trusses as designed: HSS chords with the long side vertical, verticals at every panel point and tension diagonals."""
    from . import structure
    design=structure.C["design"]
    chord,web,cross=design["chord"],design["web"],structure.CROSS
    xs=[INNER+x for x in stations(extra)]
    deep,wide,size=chord["h"],chord["b"],web["b"]
    top=FRAME_HEIGHT
    for side in (-1,1):
        y0,y1=sorted((side*(FRAME_WIDTH/2-wide),side*FRAME_WIDTH/2))
        y=(y0+y1)/2
        outline=[(xs[0],y0),(xs[-1],y0),(xs[-1],y1),(xs[0],y1)]
        prism(m,outline,0,deep,FRAME)
        prism(m,outline,top-deep,top,EDGE)
        for i,x in enumerate(xs):
            at=min(max(x,xs[0]+size/2),xs[-1]-size/2)
            s.bar(m,(at,y,deep),(at,y,top-deep),size,FRAME,size)
            if i+1<len(xs):
                s.bar(m,(at+size/2,y,top-deep),(xs[i+1]-size/2,y,deep),size,"667076",size)
    inside=FRAME_WIDTH/2-wide
    for i,x in enumerate(xs):
        at=min(max(x,xs[0]+cross["b"]/2),xs[-1]-cross["b"]/2)
        for z in (deep/2,top-deep/2):
            s.bar(m,(at,-inside,z),(at,inside,z),cross["b"],FRAME,cross["b"])
            if i+1<len(xs):
                # Plan bracing, one diagonal a panel, turns the two trusses into a box.
                side=1 if i%2 else -1
                s.bar(m,(at+cross["b"]/2,side*inside,z),(xs[i+1]-cross["b"]/2,-side*inside,z),cross["b"],FRAME,cross["b"])


def root_dock():
    """The root connection on the hub: the upper clevis takes the pull and the weight, the lower bearing takes the thrust."""
    m=s.Mesh("Cantilever root | upper clevis and lower bearing");m.material=3
    x0=cfg.STORE["shaft_radius_m"]+.045;x1=INNER-.02
    for z in (-.075,FRAME_HEIGHT-.11):
        s.box(m,x0,-.155,x1,.155,z,z+.078,"738184")
        for y in (-.202,.161):
            s.box(m,x0+.065,y,INNER+.03,y+.041,z+.04,z+.115,"647278")
    return m
