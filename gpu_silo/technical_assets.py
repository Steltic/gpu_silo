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

def trailer(m):
    bounds=np.asarray([t[:3] for t in m.tris]).reshape(-1,3)
    rear=float(bounds[:,0].min())
    width=1.28
    is_tanker=m.name.startswith(("Water tanker","Propane transport"))
    heavy="Heavy-haul" in m.name
    if is_tanker:
        from .technical_vehicles import tanker_shell
        tanker_shell(m)
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
    from .technical_vehicles import carrier_cab, crane_housing, hull
    name=m.name
    if name=="Crawler undercarriage" or name.startswith("Boom lift | four-wheel"):
        picker=name.startswith("Boom")
        if picker:
            m.tris.clear()
            hull(m,[(.63,-2.18,2.22,-.94,.94,.22),(.82,-2.38,2.37,-1.02,1.02,.26),
                    (1.15,-2.27,2.19,-.98,.98,.23)],"b17a47")
            pipe(m,(0,0,1.14),(0,0,1.27),.95,"566567",36)
            hull(m,[(1.25,-1.99,1.49,-.95,.95,.27),(1.61,-2.10,1.4,-.91,.91,.26),
                    (1.97,-1.65,.82,-.77,.77,.18),(2.07,-1.21,.60,-.67,.67,.12)],"cc823e")
            for sign in (-1,1):
                for j in range(10):
                    x=-1.78+j*.105
                    box(m,x,sign*.922-.02,x+.047,sign*.922+.02,1.34,1.60,dark)
                box(m,.05,sign*.90-.012,.59,sign*.90+.012,1.37,1.55,"d6bf87")
                pipe(m,(.82,sign*.42,1.35),(.29,sign*.42,2.13),.12,"7a8480")
                pipe(m,(.26,sign*.52,2.02),(.26,sign*.63,2.02),.12,alloy,16)
            pipe(m,(-1.18,-.22,2.01),(-1.18,-.22,2.13),.125,dark,20)
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
        crane_housing(m,crawler)
    elif name.startswith("Assist crane | all-terrain"):
        carrier_cab(m)
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
    for j in range(4):
        ring(m,1.29+j*.144,y,z,.373,.026,amber,20)
    # Removable duplex oil filters, gauge faces and isolated pipework beside the core.
    yy=y-.86
    box(m,-3.96,yy-.22,-2.74,yy+.22,.31,.49,"526365")
    for x in (-3.67,-3.05):
        pipe(m,(x,yy,.49),(x,yy,1.11),.176,"c6cccc",28)
        pipe(m,(x,yy,1.08),(x,yy,1.18),.206,steel,28)
        pipe(m,(x,yy,1.18),(x,yy,1.31),.11,dark,20)
        pipe(m,(x,yy-.04,1.23),(x,yy-.23,1.23),.076,"c7d0c6",20)
        s.bar(m,(x-.035,yy-.236,1.19),(x+.014,yy-.236,1.26),.015,"37484c")
    pipe(m,(-3.67,yy,1.24),(-3.05,yy,1.24),.046,"af8c57")
    # A ladder-type cable tray follows the generator up to its terminal box.
    for off in (.70,.93):
        box(m,2.18,y+off-.018,6.14,y+off+.018,2.54,2.65,"89999a")
    for j in range(21):
        xx=2.22+j*.189
        box(m,xx,y+.70,xx+.035,y+.93,2.54,2.57,steel)
    box(m,5.56,y-.36,6.38,y+.44,2.45,2.74,"4d6675")
    for yy in (y-.19,y+.055,y+.29):
        pipe(m,(6.31,yy,2.60),(6.50,yy,2.60),.072,alloy,12)
    for radius,dx,col in ((.81,.08,"71868b"),(.61,.15,"939fa0"),(.32,.21,"5a6e75"),(.18,.26,"929c9b")):
        pipe(m,(6.595,y,z),(6.60+dx,y,z),radius,col,32)
    for j in range(16):
        a=j*math.tau/16;yy=y+.728*math.cos(a);zz=z+.728*math.sin(a)
        pipe(m,(6.67,yy,zz),(6.707,yy,zz),.042,alloy,6)
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
    from .technical_vehicles import truck
    by_name={n["name"]:n for n in scene.nodes}
    display=scene.meshes[by_name["Control room | displays and task lighting"]["mesh"]]
    facade=scene.meshes[by_name["Control office | walls"]["mesh"]]
    # The white stencil is painted on a lintel that rises during the enclosure shot.
    # Keep it with that physical surface while the screens switch on independently.
    lettering=s.rgb("d9e8dd")
    facade.tris.extend(t for t in display.tris if tuple(t[3])==tuple(lettering))
    display.tris=[t for t in display.tris if tuple(t[3])!=tuple(lettering)]
    for m in scene.meshes:
        n=m.name
        if n.startswith("Road tractor") or n.startswith("Truck mixer"):
            truck(m,n.startswith("Truck mixer"),wheel)
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
