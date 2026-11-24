"""Shaped day cabs, mixer bodies and slewing machinery for the close construction shots."""
import math
from collections import Counter
from . import services, site, silo_model as s

DARK="293940"
METAL="a5b0b0"
GASKET="263638"
GLASS="315a6a"
BOX=site.closed


def tube(m,a,b,r,c=METAL,n=12):
    services.pipe(m,a,b,r,c,n=n)


def hull(m,levels,colour):
    """Join chamfered horizontal sections. Each has z, rear, front, left, right and corner inset."""
    loops=[]
    for z,x0,x1,y0,y1,r in levels:
        r=min(r,(x1-x0)*.45,(y1-y0)*.45)
        loops.append([(x0+r,y0,z),(x1-r,y0,z),(x1,y0+r,z),(x1,y1-r,z),
                      (x1-r,y1,z),(x0+r,y1,z),(x0,y1-r,z),(x0,y0+r,z)])
    m.face(loops[0][::-1],colour)
    for lower,upper in zip(loops,loops[1:]):
        for i in range(8):
            j=(i+1)%8
            m.face((lower[i],lower[j],upper[j],upper[i]),colour)
    m.face(loops[-1],colour)


def window(m,points,tint=GLASS):
    m.face(points,GASKET)
    centre=[sum(p[k] for p in points)/len(points) for k in range(3)]
    a,b,c=points[:3]
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    length=math.sqrt(sum(x*x for x in normal))
    offset=[.006*x/max(1.e-9,length) for x in normal]
    inside=[tuple(centre[i]+.93*(p[i]-centre[i])+offset[i] for i in range(3)) for p in points]
    m.face(inside,tint)
    top=[tuple(.17*inside[i][k]+.83*inside[3-i][k]+offset[k] for k in range(3)) for i in (0,1)]
    m.face((top[0],top[1],inside[2],inside[3]),"627e86")


def arch(m,x,y,width,r,colour,zc=.52):
    sign=1 if y>0 else -1
    outer=y+sign*width*.5;inner=y-sign*width*.5
    for j in range(24):
        a=math.radians(4+172*j/24);b=math.radians(4+172*(j+1)/24)
        def point(yy,rr,t):return (x+rr*math.cos(t),yy,zc+rr*math.sin(t))
        m.face((point(outer,r,a),point(outer,r,b),point(inner,r,b),point(inner,r,a)),colour)
        m.face((point(outer,r-.075,a),point(outer,r-.075,b),point(outer,r,b),point(outer,r,a)),colour)


def tank(m,a,b,y,z,r):
    tube(m,(a,y,z),(b,y,z),r,"a9ada7",32)
    for j in (.17,.80):
        xx=a+(b-a)*j
        tube(m,(xx,y,z),(xx+.055,y,z),r+.012,"57656b",32)


def cab_shell(m,mixer,paint):
    rear,wind,nose=(3.92,5.69,6.66) if mixer else (1.34,3.38,4.78)
    top=wind-.33
    hull(m,[(.96,rear+.12,wind-.02,-1.10,1.10,.19),(1.15,rear,wind+.05,-1.22,1.22,.17),
            (1.95,rear-.015,wind+.06,-1.20,1.20,.13),(2.91,rear+.10,top,-1.075,1.075,.14),
            (3.03,rear+.20,top-.02,-1.04,1.04,.16)],paint)
    hull(m,[(3.015,rear+.03,top+.035,-1.14,1.14,.17),(3.12,rear+.11,top+.025,-1.12,1.12,.15),
            (3.20,rear+.23,top-.14,-1.,1.,.18)],paint)
    hull(m,[(.99,wind-.20,nose-.06,-.89,.89,.15),(1.40,wind-.18,nose+.01,-1.03,1.03,.17),
            (1.72,wind-.17,nose,-.97,.97,.13),(1.94,wind-.14,wind+.20,-.89,.89,.10)],paint)
    for sign in (-1,1):
        lo=(wind+.069,sign*1.025,2.02);hi=(top+.032,sign*.93,2.86)
        inner=(wind+.069,sign*.037,2.02);upper=(top+.032,sign*.032,2.86)
        pts=[inner,lo,hi,upper] if sign>0 else [lo,inner,upper,hi]
        window(m,pts,"3f6878")
        tube(m,(wind+.075,sign*.84,2.05),(wind-.05,sign*.27,2.39),.018,DARK,8)
        side=[(rear+.16,sign*1.207,2.03),(wind-.10,sign*1.207,2.03),
              (top-.11,sign*1.095,2.85),(rear+.23,sign*1.095,2.85)]
        window(m,side if sign<0 else [side[1],side[0],side[3],side[2]])
        tube(m,(rear+.45,sign*1.205,2.04),(rear+.45,sign*1.10,2.84),.019,DARK,8)
        tube(m,(rear+.18,sign*1.228,1.18),(rear+.12,sign*1.218,1.92),.013,"4c6468",6)
        tube(m,(rear+.16,sign*1.236,1.80),(rear+.42,sign*1.237,1.80),.035,DARK,8)
        for level in range(2):
            z=.78+level*.20
            hull(m,[(z,rear-.08,rear+.80,sign*1.07-.16,sign*1.07+.16,.06),
                    (z+.065,rear-.08,rear+.80,sign*1.07-.16,sign*1.07+.16,.06)],"a3afaf")
            for j in range(7):
                xx=rear+.03+j*.098
                BOX(m,xx,sign*1.13-.10,xx+.022,sign*1.13+.10,z+.065,z+.073,DARK)
        arm=(wind-.18,sign*1.18,2.28);mirror=(wind+.025,sign*1.488,2.56)
        tube(m,arm,mirror,.034,DARK);tube(m,(wind-.17,sign*1.12,2.65),mirror,.025,DARK)
        hull(m,[(2.41,wind-.067,wind+.115,sign*1.488-.055,sign*1.488+.055,.035),
                (2.72,wind-.05,wind+.098,sign*1.488-.053,sign*1.488+.053,.032)],DARK)
        BOX(m,wind-.073,sign*1.488-.043,wind-.065,sign*1.488+.043,2.44,2.68,"93adb4")
        xx=nose-.15;yy=sign*.92
        hull(m,[(1.06,xx-.39,nose+.024,yy-.22,yy+.22,.10),(1.38,xx-.3,nose+.04,yy-.20,yy+.20,.07)],paint)
        BOX(m,nose+.038,yy-.16,nose+.065,yy+.16,1.15,1.31,"e8e6d4")
        BOX(m,nose+.053,yy-.14,nose+.069,yy+.14,1.09,1.13,"e9a951")
        for j in range(5):
            xx=wind+.13+j*.095
            BOX(m,xx,sign*.988-.016,xx+.040,sign*.988+.016,1.43,1.64,DARK)
        for xx in (rear+.15,top-.06):
            tube(m,(xx,sign*.82,3.12),(xx,sign*.82,3.19),.047,"d9a34e",10)
    # Rear window and sun visor remain visible when a vehicle exits towards the camera.
    window(m,[(rear-.011,-.73,2.08),(rear-.011,.73,2.08),(rear+.084,.69,2.79),(rear+.084,-.69,2.79)][::-1])
    hull(m,[(2.87,top-.10,top+.16,-1.08,1.08,.055),(2.94,top-.10,top+.19,-1.09,1.09,.065)],"8b9998")
    for j in range(5):
        yy=(j-2)*.38
        BOX(m,top-.17,yy-.045,top-.04,yy+.045,3.11,3.165,"e9aa48")
    hull(m,[(.56,nose-.2,nose+.145,-1.18,1.18,.13),(.82,nose-.21,nose+.16,-1.20,1.20,.13)],"b7bcb6")
    BOX(m,nose-.003,-.66,nose+.036,.66,.90,1.69,DARK)
    for j in range(11):
        z=.938+j*.069
        BOX(m,nose+.035,-.62,nose+.054,.62,z,z+.020,"b4c0bb")
    for y in (-.66,0.,.66):BOX(m,nose+.035,y-.025,nose+.055,y+.025,.9,1.7,"9ba9a8")


def frame(m,mixer,wheel):
    front=6.5 if mixer else 4.56;back=-2.24 if mixer else -1.48
    for y in (-.44,.44):
        BOX(m,back,y-.105,front,y+.105,.53,.83,DARK)
        for x in (-.67,.65):
            tube(m,(x-.46,y,.52),(x+.46,y,.52),.082,"657176",8)
    for x in (back+.19,.15,front-1.85,front-.21):BOX(m,x-.08,-.49,x+.08,.49,.58,.75,"4a565b")
    for x in ((5.30,.65,-.65) if mixer else (3.4,.65,-.65)):
        tube(m,(x,-1,.52),(x,1,.52),.105,DARK)
        tube(m,(x,-.30,.50),(x,.30,.50),.22,"4e5859",16)
        for sign in (-1,1):
            y=sign*(1.23 if x>2 else 1.36)
            wheel(m,x,y,.52)
            arch(m,x,sign*1.03,.52,.648,"526067" if x<2 else "647780")
    tube(m,(-.75,0,.53),(front-1.52,0,.73),.10,"575e5c")
    for sign in (-1,1):
        y=sign*1.02
        BOX(m,-1.30,y-.27,-1.24,y+.27,.15,.85,"323a3b")
        if mixer:
            tank(m,1.32,3.64,sign*.88,1.02,.27)
        else:
            tank(m,.83,1.63,sign*.83,.83,.285)
            tube(m,(1.16,sign*.99,1.10),(1.16,sign*.99,3.47),.075,"889695",20)
            tube(m,(1.16,sign*.99,1.34),(1.16,sign*.99,2.55),.11,"acb3ad",24)
            for j in range(5):
                zz=1.52+j*.19
                tube(m,(1.16,sign*.99,zz),(1.16,sign*.99,zz+.026),.114,"566368",16)
    if not mixer:
        tube(m,(0,0,.85),(0,0,1.10),.55,DARK,28)
        for j in range(3):
            y=-.28+j*.16
            tube(m,(1.36,y,1.48),(.62,y+.08,1.07),.033,"bc9c60" if j==1 else DARK,8)


def mixer_body(m,paint):
    profile=[(-2.00,3.09,.43),(-1.71,3.02,.64),(-.70,2.84,1.06),(.22,2.66,1.20),
             (1.53,2.42,1.18),(2.65,2.21,.95),(3.49,2.07,.63),(3.83,2.02,.37)]
    def section(x):
        for (a,za,ra),(b,zb,rb) in zip(profile,profile[1:]):
            if x<=b+1.e-6:
                t=(x-a)/(b-a);return za+(zb-za)*t,ra+(rb-ra)*t
        return profile[-1][1:]
    def at(x,ang,extra=0.):
        z,r=section(x);return (x,(r+extra)*math.cos(ang),z+(r+extra)*math.sin(ang))
    for (x,_,_),(xx,_,_) in zip(profile,profile[1:]):
        for k in range(48):
            a=k*math.tau/48;b=(k+1)*math.tau/48
            m.face((at(x,a),at(x,b),at(xx,b),at(xx,a)),"c9cdc4")
    m.face([at(-2,k*math.tau/48) for k in reversed(range(48))],DARK)
    for offset,width,col in ((.0,.25,paint),(.34,.085,"687f81"),(math.pi,.21,paint)):
        last=None
        for j in range(97):
            t=j/96;x=-1.8+5.40*t;ang=offset+math.tau*1.14*t
            current=(at(x,ang,.009),at(x,ang+width,.009))
            if last:m.face((last[0],last[1],current[1],current[0]),col)
            last=current
    for x in (-.88,2.84):
        z,r=section(x)
        tube(m,(x,0,z),(x+.066,0,z-.015),r+.035,"879196",48)
        for sign in (-1,1):
            s.bar(m,(x,sign*.54,.83),(x,sign*.81,z-r*.65),.145,"59696b",.18)
            tube(m,(x-.18,sign*.76,z-r*.63),(x+.18,sign*.76,z-r*.63),.165,DARK,20)
    # Loading hopper and open U-section discharge chute.
    hull(m,[(2.85,-2.36,-1.87,-.28,.28,.04),(3.48,-2.53,-1.70,-.69,.69,.08),
            (3.59,-2.57,-1.68,-.73,.73,.09)],"828e8c")
    BOX(m,-2.49,-.52,-2.34,.52,.87,2.65,"536269")
    for sign in (-1,1):
        tube(m,(-2.1,sign*.80,1.50),(-2.47,sign*.80,3.77),.034,METAL)
        tube(m,(-2.47,sign*.80,3.77),(-1.97,sign*.80,3.77),.034,METAL)
        tube(m,(-2.00,sign*.52,2.59),(-2.31,sign*.60,3.38),.078,DARK)
    for j in range(8):
        z=1.53+.26*j;x=-2.08-(z-1.5)*.16
        tube(m,(x,-.80,z),(x,-.24,z),.032,METAL,8)
    for side in (-1,1):
        m.face([(-2.26,side*.26,2.67),(-3.31,side*.22,1.48),(-3.31,side*.19,1.30),(-2.26,side*.20,2.44)],"839292")
    m.face([(-2.26,-.20,2.44),(-3.31,-.19,1.30),(-3.31,.19,1.30),(-2.26,.20,2.44)],"4b595f")
    tube(m,(-2.15,0,1.02),(-2.87,0,1.86),.075,"b59d6c",12)


def truck(m,mixer,wheel):
    colours={tuple(s.rgb(c)):c for c in site.CABS}
    palette=Counter(tuple(face[3]) for face in m.tris if tuple(face[3]) in colours)
    paint=colours[palette.most_common(1)[0][0]] if palette else "77918d"
    m.tris.clear()
    frame(m,mixer,wheel);cab_shell(m,mixer,paint)
    if mixer:mixer_body(m,paint)


def tanker_shell(m):
    propane=m.name.startswith("Propane")
    length,radius,body,band=(12.6,1.1,"e9e7dc","c8563c") if propane else (11.2,1.0,"b9c4c2","5f8f9a")
    old={tuple(s.rgb(c)) for c in (body,band)}
    m.tris=[t for t in m.tris if tuple(t[3]) not in old]
    front=site.DECK_FRONT;rear=front-length
    centre=1.25+radius;depth=.65*radius
    def loop(x,r):
        return [(x,r*math.cos(i*math.tau/48),centre+r*math.sin(i*math.tau/48)) for i in range(48)]
    def join(a,b,colour):
        for i in range(48):
            j=(i+1)%48
            m.face((a[i],a[j],b[j],b[i]),colour)
    left=loop(rear+depth,radius);right=loop(front-depth,radius)
    join(left,right,body)
    for direction,x in ((-1,rear+depth),(1,front-depth)):
        last=loop(x,radius)
        for j in range(1,9):
            angle=j*math.pi/16
            cur=loop(x+direction*depth*math.sin(angle),max(.003,radius*math.cos(angle)))
            join(last,cur,body);last=cur
    mid=(front+rear)/2
    join(loop(mid-.46,radius+.012),loop(mid+.46,radius+.012),band)
    for x in (rear+depth,rear+2.57,mid,front-2.43,front-depth):
        join(loop(x-.016,radius+.021),loop(x+.016,radius+.021),"9daaa7")
    for y in (-.26,.26):
        tube(m,(rear+.72,y,centre+radius+.045),(front-1.03,y,centre+radius+.045),.032,METAL)
        for j in range(5):
            x=rear+1.05+j*(length-2.4)/4
            tube(m,(x,y,centre+radius-.04),(x,y,centre+radius+.048),.027,DARK)
    for j in range(35):
        x=rear+.75+j*(length-1.84)/34
        BOX(m,x,-.25,x+.074,.25,centre+radius+.015,centre+radius+.045,"8c9998")
    BOX(m,mid-1.95,-1.04,mid-.98,-.68,.57,1.12,"66777b")
    BOX(m,mid-1.86,-1.054,mid-1.06,-1.039,.64,1.05,"9baba9")
    tube(m,(mid-1.72,-1.068,.83),(mid-1.42,-1.068,.83),.025,DARK)
    for yy in (.77,.92):
        tube(m,(rear+.45,yy,.84),(front-1.45,yy,.84),.060,"81918f",16)
        for x in (mid-1.44,mid+1.32):
            tube(m,(x,yy,.84),(x,yy,1.17),.056,"887b60",12)
            tube(m,(x,yy,1.15),(x,yy,1.20),.115,band,16)


def carrier_cab(m):
    # Keep the existing chassis, suspension and deployed outrigger assemblies.
    old_glass=tuple(s.rgb("4b6971"));old_paint=tuple(s.rgb("d7a84c"))
    m.tris=[t for t in m.tris if not (tuple(t[3])==old_glass or
            (tuple(t[3])==old_paint and min(p[2] for p in t[:3])>=1.55 and min(p[0] for p in t[:3])>=3.6))]
    hull(m,[(1.55,3.48,5.04,-1.30,.02,.14),(1.88,3.50,5.08,-1.32,.02,.12),
            (2.70,3.66,4.89,-1.24,-.03,.11),(2.78,3.71,4.85,-1.21,-.06,.12)],"d7a84c")
    window(m,[(5.065,-1.19,1.94),(5.065,-.12,1.94),(4.91,-.16,2.59),(4.91,-1.14,2.59)])
    window(m,[(3.70,-1.327,1.94),(4.91,-1.327,1.94),(4.75,-1.264,2.58),(3.80,-1.264,2.58)])
    for sign in (-1,1):
        for x in (-4.77,-4.40,4.52,4.86):
            y=sign*1.309
            m.face(((x,y,1.02),(x+.12,y,1.02),(x+.34,y,1.41),(x+.22,y,1.41)),"584f3f")
        BOX(m,5.005,sign*1.06-.14,5.034,sign*1.06+.14,.86,1.02,"e7e3cd")
    for y in (-1.17,-.18):
        tube(m,(4.52,y,2.73),(4.52,y,2.85),.064,"e7aa46")


def crane_housing(m,crawler):
    """Slewing house with stepped ballast, glazed control cab, service deck and twin winches."""
    m.tris.clear()
    z=1.44 if crawler else .02
    deck="bb985f" if crawler else "d4aa58"
    rear=-3.18 if crawler else -3.33
    hull(m,[(z,rear+.28,1.42,-1.18,1.18,.23),(z+.22,rear+.12,1.5,-1.27,1.27,.22),
            (z+.33,rear+.30,1.36,-1.23,1.23,.19)],"75817d")
    hull(m,[(z+.30,-1.94,.42,-1.10,1.10,.15),(z+.88,-1.90,.39,-1.07,1.07,.18),
            (z+1.04,-1.70,.26,-.94,.94,.16)],deck)
    for j in range(4):
        h=z+.22+j*.225
        hull(m,[(h,rear+.04,-1.67,-1.20,1.20,.18),(h+.035,rear-.02,-1.68,-1.25,1.25,.16),
                (h+.204,rear+.015,-1.71,-1.23,1.23,.17)],"a09076" if j%2 else "b8a582")
    for side in (-1,1):
        for x in (-1.78,-1.13,-.48):
            y=side*1.106
            BOX(m,x,y-.012,x+.52,y+.012,z+.39,z+.80,"77827b")
            for k in range(7):
                xx=x+.05+k*.061
                BOX(m,xx,y-.023,xx+.023,y+.023,z+.44,z+.73,"384b4c")
        for x in (-2.88,-2.38):
            y=side*.87
            tube(m,(x,y,z+1.10),(x,y,z+1.23),.045,"5e6e70")
            tube(m,(x,y,z+1.23),(x+.18,y,z+1.23),.045,"5e6e70")
            tube(m,(x+.18,y,z+1.23),(x+.18,y,z+1.10),.045,"5e6e70")
    for j in range(7):
        y=-.80+.23*j
        m.face([(rear-.005,y,z+.49),(rear-.005,y+.10,z+.49),(rear-.005,y+.29,z+.78),(rear-.005,y+.19,z+.78)],"454b44")
    # Cab is asymmetric on the revolving deck; all four visible elevations carry glass.
    side=-1 if crawler else 1
    low,high=sorted((side*1.52,side*.51));cabx0,cabx1=-.20,1.47
    cz=z+.31;top=cz+(1.64 if crawler else 1.19)
    hull(m,[(cz,cabx0,cabx1-.08,low+.03,high-.03,.15),(cz+.30,cabx0-.06,cabx1,low,high,.115),
            (top-.13,cabx0+.10,cabx1-.22,low+.075,high-.075,.10),(top,cabx0+.13,cabx1-.23,low+.07,high-.07,.12)],deck)
    zl,zt=cz+.40,top-.19
    for yy,delta in ((low,-1),(high,1)):
        panel=[(cabx0+.10,yy+delta*.009,zl),(cabx1-.12,yy+delta*.009,zl),
               (cabx1-.36,yy-delta*.064,zt),(cabx0+.23,yy-delta*.064,zt)]
        window(m,panel if delta<0 else [panel[1],panel[0],panel[3],panel[2]],"3a626f")
        tube(m,(.3,yy+delta*.017,zl),(.35,yy-delta*.057,zt),.025,DARK)
    for front in (False,True):
        xx=cabx1-.023 if front else cabx0-.058
        xt=cabx1-.21 if front else cabx0+.104
        panel=[(xx,low+.17,zl),(xx,high-.17,zl),(xt,high-.19,zt),(xt,low+.19,zt)]
        window(m,panel if front else panel[::-1],"456971")
    hull(m,[(top-.02,cabx0+.01,cabx1-.12,low-.01,high+.01,.13),(top+.065,cabx0+.09,cabx1-.20,low+.035,high-.035,.12)],"899591")
    by=-side*.70
    for xx in (.03,.72):
        tube(m,(xx,by-.28,z+.68),(xx,by+.28,z+.68),.27,DARK,26)
        for j in range(9):
            y=by-.25+j*.06
            tube(m,(xx,y,z+.68),(xx,y+.02,z+.68),.28,"788388",24)
    for x in (-1.74,-1.06,-.39):
        tube(m,(x,-side*1.20,z+.34),(x,-side*1.20,z+1.15),.034,METAL)
    tube(m,(-1.78,-side*1.20,z+1.15),(-.35,-side*1.20,z+1.15),.038,METAL)
    tube(m,(.67,(low+high)*.5,top+.065),(.67,(low+high)*.5,top+.14),.071,"edaf52",16)
