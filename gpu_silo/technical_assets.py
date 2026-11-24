"""Fabricated surface detail for the technical film. Dimensions in local metres."""
import math
import numpy as np
from . import cooler_frames as cf, plant, services, site, silo_model as s

box = site.closed
steel = "829297"
dark = "29383d"
rubber = "293033"
alloy = "c3c9c2"
amber = "eba84c"
glass = "3d6772"


def pipe(m, a, b, radius, col=steel, n=12):
    services.pipe(m, a, b, radius, col, n=n)


def ring(m, x, y, z, radius, wire, colour, n=32):
    loop = [(x, y+radius*math.cos(i*math.tau/n), z+radius*math.sin(i*math.tau/n)) for i in range(n)]
    for a,b in zip(loop,loop[1:]+loop[:1]):
        pipe(m,a,b,wire,colour,6)


def wheel(m, x, y, r, z=None):
    z = r if z is None else z
    sign = 1 if y>0 else -1
    def tube(ra, offset, depth, col, n):
        a=y+sign*offset
        pipe(m,(x,a,z),(x,a+sign*depth,z),ra,col,n)
    tube(r, -.25,.23,rubber,32)
    tube(r*.63,-.026,.045,"465256",24)
    tube(r*.52,.02,.035,alloy,24)
    tube(r*.24,.052,.028,"728287",18)
    for i in range(8):
        a=i*math.tau/8
        xx,zz=x+.39*r*math.cos(a),z+.39*r*math.sin(a)
        pipe(m,(xx,y+sign*.05,zz),(xx,y+sign*.075,zz),r*.055,dark,6)


def cab(m,mixer):
    front = 6.66 if mixer else 4.76
    wind = 6.215 if mixer else 3.481
    side = 1.222 if mixer else 1.254
    rear = 4.31 if mixer else 1.55
    box(m,front,-.78,front+.042,.78,1.02,1.71,dark)
    for i in range(8):
        z=1.056+i*.084
        box(m,front+.04,-.73,front+.063,.73,z,z+.027,alloy)
    for sign in (-1,1):
        yy=sign*.97
        box(m,front+.015,yy-.15,front+.068,yy+.15,1.24,1.47,"f3e8bf")
        box(m,front+.04,yy-.13,front+.077,yy+.13,1.12,1.18,amber)
        y=sign*(side+.025)
        box(m,rear+.23,y-.012,wind-.15,y+.012,1.98,2.78,glass)
        box(m,rear+.38,y-.023,rear+.41,y+.023,1.98,2.78,alloy)
        box(m,rear+.26,y-.031,rear+.49,y+.031,1.77,1.81,dark)
        for z in (.72,.94,1.15):
            box(m,rear-.14,min(y,y+sign*.14),rear+.58,max(y,y+sign*.14),z,z+.045,"a6ada6")
        arm=(wind-.12,y,2.5)
        mast=(wind+.05,sign*1.50,2.61)
        pipe(m,arm,mast,.033,dark)
        box(m,mast[0]-.10,mast[1]-.052,mast[0]+.10,mast[1]+.052,2.49,2.79,dark)
        box(m,mast[0]-.107,mast[1]-.044,mast[0]-.10,mast[1]+.044,2.51,2.76,"9eafb0")
        pipe(m,(wind,sign*.89,2.04),(wind+.014,sign*.25,2.51),.015,dark,6)
        if not mixer:
            pipe(m,(.78,sign*.88,.72),(1.43,sign*.88,.72),.27,alloy,24)
        for x in ((5.3,.65,-.65) if mixer else (3.4,.65,-.65)):
            wheel(m,x,sign*(1.23 if x>2 else 1.36),.52)
        box(m,-1.31,sign*1.01-.24,-1.25,sign*1.01+.24,.16,.76,rubber)
    for i in range(5):
        y=(i-2)*.42
        box(m,wind-.20,y-.052,wind-.09,y+.052,2.94 if mixer else 3.105,3.00 if mixer else 3.15,amber)
    if mixer:
        # Coloured spiral follows the two tapered drum sections.
        last=None
        for i in range(73):
            u=i/72
            x=-1.49+5.44*u
            cy=2.55+(3.05-2.55)*min(1,max(0,(.9-x)/2.4))-.40*max(0,(x-.9)/3.1)
            radius=(.985 if x<.9 else 1.185)+.018
            a=math.tau*u*2
            at=(x,radius*math.cos(a),cy+radius*math.sin(a))
            if last:pipe(m,last,at,.044,"7d9996",6)
            last=at
        for yy in (-.36,.36):
            pipe(m,(-2.22,yy,1.0),(-2.57,yy,3.45),.035,steel)
        for i in range(8):
            z=1.12+.30*i
            x=-2.22-(z-1)*.143
            pipe(m,(x,-.36,z),(x,.36,z),.03,alloy,8)


def trailer(m):
    bounds=np.asarray([t[:3] for t in m.tris]).reshape(-1,3)
    rear=float(bounds[:,0].min())
    width=1.28
    is_tanker=m.name.startswith(("Water tanker","Propane transport"))
    heavy="Heavy-haul" in m.name
    axles=(-20.35,-19,-17.65) if heavy else ((-10.25,-8.95) if is_tanker else (-site.FLAT_AXLE-.65,-site.FLAT_AXLE+.65))
    for sign in (-1,1):
        for x in axles:
            wheel(m,x,sign*(1.43 if heavy else 1.32),.50 if heavy else .52)
        y=sign*width
        for x in np.arange(rear+.42,.66,.76):
            box(m,x,y-.022,x+.30,y+.022,1.10,1.16,"d6e1d6" if int((x-rear)*1.32)%2==0 else "bb5d4d")
        if not heavy:
            for z in (.52,.73):
                box(m,rear+4,y-.034,-2.45,y+.034,z,z+.068,steel)
        for xx in (rear+.32,rear+.64):
            box(m,xx-.05,sign*.94-.1,xx+.05,sign*.94+.1,.81,.93,"ce4f40")
    if is_tanker:
        top=float(bounds[:,2].max())
        for x in (rear+3.6,rear+6.4):
            pipe(m,(x,0,top-.05),(x,0,top+.12),.28,alloy,24)
        for y in (-.28,.28):
            pipe(m,(rear-.075,y,1.12),(rear-.075,y,top+.17),.032,alloy)
        for z in np.arange(1.25,top+.14,.29):
            pipe(m,(rear-.075,-.28,z),(rear-.075,.28,z),.025,alloy,8)
    else:
        for x in np.arange(rear+.6,.7,1.15):
            for y in (-1.24,1.24):
                pipe(m,(x,y,1.24),(x+.13,y,1.24),.034,dark,8)


def tracks(m,half,offset,width,r):
    for sign in (-1,1):
        y=offset*sign
        box(m,-half,y-width/2,half,y+width/2,.055,2*r-.05,rubber)
        # Straight runs and rounded nose/tail form a continuous shoe chain.
        pts=[(-half+2*half*i/24,2*r) for i in range(24)]
        pts += [(half+r*math.sin(i*math.pi/10),r+r*math.cos(i*math.pi/10)) for i in range(10)]
        pts += [(half-2*half*i/24,.034) for i in range(24)]
        pts += [(-half-r*math.sin(i*math.pi/10),r-r*math.cos(i*math.pi/10)) for i in range(10)]
        for i,((x,z),(xx,zz)) in enumerate(zip(pts,pts[1:]+pts[:1])):
            a=(x,y-width*.52,z);b=(xx,y-width*.52,zz)
            c=(xx,y+width*.52,zz);d=(x,y+width*.52,z)
            m.face((a,b,c,d),"435056" if i%2 else "566065")
            s.bar(m,(x,y-width*.52,z),(x,y+width*.52,z),.033,"737c79",.047)
        for x in np.linspace(-half,half,9):
            radius=r*.91 if abs(x)>half-.01 else r*.65
            wheel(m,x,y+sign*width*.50,radius,r)


def machinery(m):
    name=m.name
    if name=="Crawler undercarriage" or name.startswith("Boom lift | four-wheel"):
        picker=name.startswith("Boom")
        if picker:
            m.tris.clear()
            box(m,-2.39,-1.02,2.37,1.02,.64,1.16,"cb833e")
            box(m,-2.13,-.94,-.56,.94,1.16,1.85,dark)
            box(m,-.56,-.95,1.34,.95,1.15,2.05,"c77a36")
            m.name="Boom lift | tracked chassis and hydraulic power pack"
        tracks(m,1.86 if picker else 2.48,1.18 if picker else 1.43,.53 if picker else .74,.42 if picker else .38)
        if picker:
            for j in range(9):
                x=-1.98+j*.15
                box(m,x,-.967,x+.062,-.94,1.30,1.67,steel)
            for y in (-.79,.79):
                pipe(m,(-.45,y,1.68),(.64,y,1.95),.063,dark,12)
    elif name in ("Crawler counterweight and cab","Assist crane | operator cab and counterweight"):
        crawler=name.startswith("Crawler")
        y=-1.56 if crawler else 1.26
        z=1.55 if crawler else 0.
        for i in range(14):
            x=-1.65+i*.094
            box(m,x,-1.154,x+.041,-1.14,z+.22,z+.64,dark)
        for x in (-2.51,-1.75,-1.,-.36):
            pipe(m,(x,1.22,z+.69),(x,1.22,z+1.29),.035,alloy)
        pipe(m,(-2.55,1.22,z+1.29),(-.35,1.22,z+1.29),.035,alloy)
        for j in range(3):
            box(m,.2+j*.38,y-.016,.22+j*.38,y+.016,z+.85,z+1.53,dark)
        for side in (-1,1):
            pipe(m,(-1.50,side*.63,z+.78),(-.82,side*.63,z+1.18),.21,rubber,20)
            for j in range(8):
                x=-1.50+j*.078
                pipe(m,(x,side*.63,z+.79+j*.039),(x+.026,side*.63,z+.81+j*.039),.224,steel,16)
    elif name.startswith("Assist crane | all-terrain"):
        for sign in (-1,1):
            for x in (-3.9,-2.4,1.6,3.2):wheel(m,x,sign*1.36,.62)
            for x in (-4.6,.2):
                pipe(m,(x,sign*3.4,.18),(x,sign*3.4,.8),.15,alloy,16)
                box(m,x-.43,sign*3.4-.43,x+.43,sign*3.4+.43,0,.09,dark)
        for i in range(8):
            x=-3.5+i*.23
            box(m,x,-1.32,x+.10,-1.30,1.07,1.38,dark)
    elif name in ("Assist crane | telescopic boom","Boom lift | telescopic boom"):
        dx,dz=(6,14) if name.startswith("Boom lift") else (10,14)
        for yy in (-.32,.32):
            pipe(m,(.16,yy,.22),(dx*.27,yy,dz*.41),.093,amber)
            pipe(m,(dx*.27,yy,dz*.41),(dx*.51,yy,dz*.58),.052,alloy)
            for q in (.49,.73,.91):
                pipe(m,(dx*q,-.28,dz*q),(dx*q,.28,dz*q),.085,dark)
    elif "work basket and guard" in name:
        box(m,.26,-.82,.51,-.16,.76,.94,dark)
        for i in range(3):pipe(m,(.38,-.72+.19*i,.95),(.40,-.72+.19*i,1.07),.034,amber)
    elif name=="Tapered lattice crane boom":
        for sign in (-1,1):
            pipe(m,(-.9,sign*.72,.72),(16.98,sign*.42,59.52),.034,dark,8)
            pipe(m,(17,sign*.19,59.48),(17,sign*.46,59.48),.31,alloy,20)
            pipe(m,(1.2,sign*.85,4.59),(2.42,sign*.85,8.10),.11,amber)
        for j in range(19):
            u=(j+.5)/19
            s.bar(m,(17*u-.30,-.09,59.62*u),(17*u+.30,-.09,59.62*u),.037,alloy)


def turbine_detail(side):
    m=site.steel("Package detail | turbine flanges, instrumentation and ventilation")
    y=side*(plant.SET_Y-.08)
    z=.14+1.07*1.22
    for x,r in [(-5.16,1.13),(-4.71,.83),(-4.06,.83),(-3.40,.83),(-2.72,.83),(-1.78,.89),(-.80,1.07)]:
        for j in range(16):
            a=j*math.tau/16
            yy,zz=y+(r-.039)*math.cos(a),z+(r-.039)*math.sin(a)
            pipe(m,(x-.032,yy,zz),(x+.05,yy,zz),.047,alloy,6)
    for j in range(12):
        a=j*math.tau/12
        cy,sz=math.cos(a),math.sin(a)
        pipe(m,(-2.55,y+cy*.98,z+sz*.98),(-2.57,y+cy*1.08,z+sz*1.08),.065,steel,8)
        pipe(m,(-2.57,y+cy*1.08,z+sz*1.08),(-2.20,y+cy*1.105,z+sz*1.105),.035,"b88953",8)
    for sign in (-1,1):
        yy=y+sign*1.115
        for j in range(3):
            x=2.03+j*1.44
            box(m,x,yy-.028,x+1.26,yy+.028,.61,1.98,"344c5b")
            for k in range(12):
                zz=.67+k*.106
                box(m,x+.061,yy-.052,x+1.20,yy+.052,zz,zz+.029,"869ca1")
        for x in (-4.5,-3.76,-2.95):
            pipe(m,(x,yy,.55),(x,yy,1.24),.027,alloy,8)
            pipe(m,(x,yy,1.24),(x+.17,yy*.85+y*.15,1.50),.027,alloy,8)
        for j in range(4):
            xx=1.29+j*.144
            ring(m,xx,y,z,.373,.026,amber,20)
        for x in (-6.21,-4.05,-1.83,2.20,5.80):
            for dy in (-.09,.09):
                pipe(m,(x+dy,yy,.30),(x+dy,yy,.368),.057,alloy,6)
    for j in range(5):
        for k in range(9):
            xx=-6.50+j*.20
            zz=.60+k*.212
            box(m,xx,y-1.137,xx+.112,y-1.124,zz,zz+.122,"667d83")
    for xx in (.22,.48,.74,1.):
        box(m,xx,y-.99,xx+.036,y+.93,3.67,3.705,alloy)
    return m


def extents(m):
    v=np.asarray([t[:3] for t in m.tris]).reshape(-1,3)
    return v.min(axis=0),v.max(axis=0)


def overlay(target, addition, shift=(0.,0.,0.)):
    for a,b,c,col in addition.tris:
        points=[tuple(value+offset for value,offset in zip(point,shift)) for point in (a,b,c)]
        target.tris.append((*points,col))


def cooler_guard(m):
    lo,hi=extents(m)
    x=hi[0]+.017
    z=lo[2]+cf.COOL_H*.5+.01
    rad=min(cf.COOL_H/2-.20,cf.COOL_L/cf.FANS/2-.15)
    for j in range(cf.FANS):
        y=lo[1]+(j+.5)*cf.COOL_L/cf.FANS
        for frac in (.30,.49,.68,.86,1.):
            ring(m,x+.045*(1-frac),y,z,rad*frac,.011 if frac<1 else .017,alloy,36)
        for i in range(8):
            a=i*math.tau/8
            cy,sz=math.cos(a)*rad,math.sin(a)*rad
            pipe(m,(x+.035,y+cy*.22,z+sz*.22),(x,y+cy,z+sz),.014,steel,6)


def pump_cabinet(m):
    lo,hi=extents(m)
    x=hi[0]+.016;y=(lo[1]+hi[1])*.5;z=(lo[2]+hi[2])*.5
    height=min(1.72,hi[2]-lo[2]-.09);width=min(.74,hi[1]-lo[1]-.10)
    box(m,x-.018,y-width/2,x+.022,y+width/2,z-height/2,z+height/2,"738688")
    for j in range(10):
        h=z+.07+j*.055
        box(m,x+.023,y-width*.38,x+.052,y+width*.38,h,h+.025,"3a4e54")
    pipe(m,(x+.07,y+width*.33,z-.48),(x+.07,y+width*.33,z-.22),.025,alloy)
    box(m,x+.024,y-width*.36,x+.034,y-width*.02,z-.40,z-.27,alloy)


def enhance(scene):
    for m in scene.meshes:
        n=m.name
        if n.startswith("Road tractor") or n.startswith("Truck mixer"):
            cab(m,n.startswith("Truck mixer"))
        elif n.startswith(("Flatbed semi","Heavy-haul","Water tanker","Propane transport")):
            trailer(m)
        elif "aeroderivative gas turbine" in n or n.startswith("Power modules/Turbine set"):
            if n.startswith("Power modules/"):
                # The IFC exporter seats the drawings across the centreline.
                side=-1 if "set A" in n else 1
                shift=extents(m)[0]-extents(plant.turbine_mesh(side))[0]
            else:
                side=1 if "set A" in n else -1
                shift=(0.,0.,0.)
            overlay(m,turbine_detail(side),shift)
        elif n.startswith(("Dry coolers/Cooler frame","Dry cooler | ")):
            cooler_guard(m)
        elif n.startswith("Pump units/Cooler frame"):
            pump_cabinet(m)
        else:
            machinery(m)
