"""Short-film dressing for cast concrete, field equipment and the roof terminal."""
import math
from . import silo_model as s, services

SEPARATOR, GLASS, DISPLAY, BEAM, HALO = range(7,12)
DISH=(5.2,-8.0)
FONT={
    "S":["01111","10000","10000","01110","00001","00001","11110"],
    "T":["11111","00100","00100","00100","00100","00100","00100"],
    "A":["01110","10001","10001","11111","10001","10001","10001"],
    "R":["11110","10001","10001","11110","10100","10010","10001"],
    "L":["10000","10000","10000","10000","10000","10000","11111"],
    "I":["11111","00100","00100","00100","00100","00100","11111"],
    "N":["10001","11001","11001","10101","10011","10011","10001"],
    "K":["10001","10010","10100","11000","10100","10010","10001"],
    "O":["01110","10001","10001","10001","10001","10001","01110"],
    "C":["01111","10000","10000","10000","10000","10000","01111"],
    "M":["10001","11011","10101","10101","10001","10001","10001"],
    " ":["00000"]*7,
}


def label(mesh,text,point,width,colour):
    pixel=width/(len(text)*6-1)
    for i,ch in enumerate(text):
        for j,row in enumerate(FONT[ch]):
            for k,lit in enumerate(row):
                if lit=="0":continue
                x=(6*i+k)*pixel-width/2
                y=(6-j)*pixel
                pts=[point(x,y),point(x+pixel,y),point(x+pixel,y+pixel),point(x,y+pixel)]
                mesh.face(pts,colour);mesh.face(pts[::-1],colour)


def material(name,mat=3):
    mesh=s.Mesh(name);mesh.material=mat
    return mesh


def quad(m,points,colour):
    m.face(points,colour);m.face(points[::-1],colour)


def roof(scene,node,cover,p):
    from . import plant, clock
    plate=material("Roof terminal | STARLINK flat array")
    z=plant.LID_THICK+.02
    for y in (-.34,.34):
        s.box(plate,-.54,y-.09,.54,y+.09,z,z+.13,"7f8a8c")
    services.pipe(plate,(0,0,z+.10),(0,0,z+.93),.075,"687e83")
    s.bar(plate,(-.42,-.32,z+.12),(0,0,z+.68),.04,"85979a")
    def face(x,y,offset=0):return (x,y,1.18+.38*y+offset)
    corners=[(-.52,-.34),(.52,-.34),(.58,-.28),(.58,.28),(.52,.34),(-.52,.34),(-.58,.28),(-.58,-.28)]
    lo=[face(x,y,0) for x,y in corners];hi=[face(x,y,.055) for x,y in corners]
    quad(plate,hi,"ecefe9");quad(plate,lo,"32484f")
    for j in range(len(lo)):quad(plate,[lo[j-1],lo[j],hi[j],hi[j-1]],"657a80")
    label(plate,"STARLINK",lambda x,y:face(x,y-.052,.058),.83,"243a40")
    head=node("STARLINK | labelled roof antenna",scene.mesh(plate),"Roof communications",cover,t=(*DISH,0))
    # The red ray is a presentation overlay. Its axis is normal to the array.
    normal=s.norm((0,-.38,1))
    start=(0,0,1.245)
    for role,radius,mat,col in (("halo",.14,HALO,"ff4b52"),("core",.048,BEAM,"ff373c")):
        ray=material("STARLINK | uplink "+role,mat)
        end=s.plus(start,s.times(normal,85))
        services.pipe(ray,start,end,radius,col,n=10)
        a=p.FILLED+clock.ORBIT;b=p.FILLED+clock.ORBIT_DONE
        node(ray.name,scene.mesh(ray),"Signal beam",head,tracks={"scale":[(0,(0,0,0)),(a-.02,(0,0,0)),(a,(1,1,1)),(b-.02,(1,1,1)),(b,(0,0,0))]})


def wall_finish(scene,node,p):
    m=material("Architectural concrete | lift joints and form-tie recesses")
    r=s.RO+.012
    for level in range(s.COUNT):
        z=(level+1)*s.LIFT
        for k in range(60):
            a,b=k*s.TAU/60,(k+1)*s.TAU/60
            quad(m,[s.polar(r,a,z-.043),s.polar(r,b,z-.043),s.polar(r,b,z-.018),s.polar(r,a,z-.018)],"707e7d")
        for j in range(36):
            a=(j+.5*(level%2))*s.TAU/36
            for dz in (.64,2.35):
                h=level*s.LIFT+dz
                if h<s.OPENING_HEIGHT and abs(math.sin((a-s.ENTRY)/2))*2*r<s.OPENING_WIDTH/2+.1:continue
                pts=[s.polar(r+.003,a+.044*math.cos(i*s.TAU/6)/r,h+.044*math.sin(i*s.TAU/6)) for i in range(6)]
                quad(m,pts,"768482")
    frame=p.FILLED+p.clock.SOLID_END
    node(m.name,scene.mesh(m),"Architectural finish",tracks={"scale":[(0,(0,0,0)),(frame-.02,(0,0,0)),(frame,(1,1,1))]})


def pump_detail(m,x0,x1,half,h):
    """Visible service face of the pump pack on a cooler frame."""
    face=x1+.012
    for y in (-half*.65,half*.59):
        for j in range(5):
            s.box(m,face,y-.16,face+.018,y+.16,h*.48+j*.080,h*.48+j*.080+.027,"4c6060")
        s.box(m,face+.02,y-.14,face+.05,y+.14,.29,.49,"91a19d")
    for yy in (-half,half):
        s.box(m,x0,yy-.025,x1+.015,yy+.025,.19,h-.04,"909d98")
    services.pipe(m,(face+.03,0,.63),(face+.19,0,.63),.20,"657775",n=14)
    services.pipe(m,(face+.16,0,.63),(face+.21,0,.63),.115,"b8bab0",n=12)


def rack_fascia(tag,lo,hi):
    """Illustrative cabinet fronts fitted to the exact IFC equipment bounds."""
    m=material("Enclosure finish | "+tag)
    x0,y,z0=lo;x1,_,z1=hi
    def face(xa,za,xb,zb,d,col):
        s.box(m,xa,y-d,xb,y-.001,za,zb,col)
    face(x0+.035,z0+.035,x1-.035,z1-.035,.020,"354d55")
    if "-R" in tag:
        for i in range(10):
            z=z0+.18+i*(z1-z0-.35)/10
            face(x0+.10,z,x1-.10,z+.116,.031,"61747b")
            for k in range(7):
                x=x0+.13+k*(x1-x0-.32)/7
                face(x,z+.026,x+.038,z+.086,.036,"243940")
            face(x1-.195,z+.045,x1-.146,z+.077,.039,"96d6b6")
        face(x0+.09,z1-.14,x0+.38,z1-.085,.036,"d4b77f")
    else:
        face(x0+.10,z0+.17,x1-.10,z1-.42,.028,"687e7c")
        for j in range(5):
            z=z0+.30+.13*j
            face(x0+.14,z,x1-.16,z+.046,.036,"3f595b")
        face(x0+.14,z1-.71,x0+.39,z1-.55,.043,"81bbac")
    return m


def air_handler(m,pos):
    """Cladding, louvres, access latches and field services outside the two IFC equipment envelopes."""
    px,py,pz=pos
    def box(x,y,xx,yy,z,zz,c):s.box(m,px+x,py+y,px+xx,py+yy,pz+z,pz+zz,c)
    box(-2.62,-1.49,2.62,1.49,-.12,0,"9da29a")
    box(-2.46,-1.34,2.46,1.34,.02,2.64,"a5b0a8")
    box(-2.50,-1.39,2.50,1.39,2.64,2.74,"c9c9b9")
    for side in (-1,1):
        y=side*1.35
        for k in range(3):
            x=-2.20+1.43*k
            box(x,y-.025,x+1.30,y+.025,.25,2.35,"677b78")
            box(x+.045,y-.04,x+1.26,y+.04,.30,2.30,"99a69f")
            for j in range(9):
                z=1.01+j*.128
                box(x+.16,y-.065,x+1.15,y+.065,z,z+.043,"4d6362")
            box(x+1.07,y-.08,x+1.12,y+.08,.58,.78,"d0cbc0")
    for side in (-1,1):
        x=px+side*2.47
        services.pipe(m,(x,py,pz+1.38),(x+side*.12,py,pz+1.38),.81,"617673",n=20)
        services.pipe(m,(x+side*.12,py,pz+1.38),(x+side*.16,py,pz+1.38),.69,"87968d",.61,n=22)
        for j in range(7):
            z=pz+1.38+(j-3)*.15
            width=math.sqrt(max(0,.58**2-((j-3)*.15)**2))
            s.bar(m,(x+side*.18,py-width,z),(x+side*.18,py+width,z),.028,"415957")
