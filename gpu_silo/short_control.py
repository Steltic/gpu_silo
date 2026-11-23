"""Single-lane operations room. Local dock X runs along the rail and the glazed frontage faces -Y."""
import math
from . import silo_model as s, short_art as art, services


def meshes(extent,y,lanes,h,box):
    m=art.material("Control office | cast panels, entrance canopy and mullions")
    glass=art.material("Control room | low-iron glazing",art.GLASS)
    furniture=art.material("Control room | consoles, keyboards, task chairs and server cabinets")
    screens=art.material("Control room | displays and task lighting",art.DISPLAY)
    x0,x1=extent
    lane=lanes[1]
    partition=lane+3.45
    cement,edge,metal="b7b8a8","8c9994","374e55"
    # Long glazing of the operator lane; a concrete work bay survives on the other side of the rail.
    box(m,x0,-y,x1,-y+.30,-.06,.50,cement)
    box(m,x0,-y,x1,-y+.42,4.28,h,cement)
    box(m,x0-.24,-y-1.0,x1+.3,-y+.2,4.18,4.35,edge)
    box(m,x0,-y,x0+.22,y,4.60,h,cement)
    box(m,x0,y-.25,x1,y,0,h,cement)
    box(m,x1-.25,-y,x1,partition,.0,.5,cement)
    box(m,x1-.28,-y,x1,partition+.2,4.28,h,cement)
    # A personnel entrance on the operations side, a single full-height portal on the service side.
    other=lanes[0]
    for ya,yb in ((partition,other-2.45),(other+2.45,y)):
        box(m,x1-.25,ya,x1,yb,0,h,cement)
    box(m,x1-.35,other-2.45,x1+.05,other+2.45,4.72,h,cement)
    for ya,yb in ((-y,-1.05),(1.05,y)):
        box(m,x0,ya,x0+.20,yb,0,4.62,cement)
    for k in range(8):
        x=x0+.12+(x1-x0-.24)*k/7
        box(m,x-.063,-y-.05,x+.063,-y+.29,.49,4.28,metal)
        if k in (0,3,7):box(m,x-.13,-y-.22,x+.13,-y+.42,0,h,edge)
    for z in (.55,3.63,4.19):
        box(m,x0,-y-.04,x1,-y+.04,z,z+.065,metal)
    for yy in (-y+.1,lane-.7,lane+.7,partition):
        box(m,x1-.045,yy-.055,x1+.05,yy+.055,.5,4.28,metal)
    art.quad(glass,[(x0,-y+.10,.55),(x1,-y+.10,.55),(x1,-y+.10,4.2),(x0,-y+.10,4.2)],"badfdd")
    art.quad(glass,[(x1-.095,-y,.55),(x1-.095,partition,.55),(x1-.095,partition,4.22),(x1-.095,-y,4.22)],"badfdd")
    box(m,x0+.2,partition-.11,x1-.2,partition+.11,0,4.22,"344b52")
    box(m,x0+.2,-y+.16,x1-.2,partition,0,.12,"667b79")
    # The rear video wall shows a silo section, load meters and the temperature trend.
    def panel(cx,cy,cz,w,ht,mode):
        box(furniture,cx-w/2-.045,cy-.055,cx+w/2+.045,cy+.065,cz-ht/2-.045,cz+ht/2+.045,"172e36")
        def field(x,z,ww,hh,c):
            box(screens,cx-w/2+x*w,cy-.065, cx-w/2+(x+ww)*w,cy-.061,cz-ht/2+z*ht,cz-ht/2+(z+hh)*ht,c)
        field(.0,.0,1,1,"25494e");field(.045,.84,.48,.045,"8ee0d2")
        if mode==0:
            for i in range(8):
                field(.16,.15+.078*i,.39,.028,"64b7b1")
            for x in (.14,.345,.55):field(x,.13,.025,.66,"abd1bf")
            for i in range(4):field(.68,.17+.13*i,.13+.03*i,.038,"ddb678")
        elif mode==1:
            for i in range(9):
                ht0=.17+.40*(.5+.5*math.sin(i*.9+.6))
                field(.08+.096*i,.13,.055,ht0,"60bfae" if i<7 else "e2b47a")
        else:
            for i in range(12):
                field(.07+i*.070,.40+.17*math.sin(i*.71),.07,.033,"83cebd")
    for k in range(3):
        panel(x0+5.6+k*3.25,partition-.18,2.55,3.02,1.65,k)
    for i in range(3):
        x=x0+4.4+4.15*i
        box(furniture,x-1.43,lane+.10,x+1.43,lane+1.06,.86,.96,"c4c8b8")
        for xx in (x-1.19,x+1.19):box(furniture,xx-.07,lane+.26,xx+.07,lane+.90,.12,.86,metal)
        for j in (-1,1):
            cx=x+j*.62
            box(furniture,cx-.06,lane+.74,cx+.06,lane+.83,.96,1.19,metal)
            panel(cx,lane+.75,1.45,1.1,.58,(i+j)%3)
        box(furniture,x-.43,lane+.22,x+.43,lane+.49,.965,.995,"344750")
        for row in range(3):
            for k in range(9):
                box(furniture,x-.36+k*.082,lane+.25+row*.075,x-.30+k*.082,lane+.29+row*.075,.996,1.007,"8e9d97")
        for dx in (-.32,.32):
            s.bar(furniture,(x,lane-.72,.19),(x+dx,lane-1.02,.15),.07,metal)
        services.pipe(furniture,(x,lane-.72,.16),(x,lane-.72,.53),.06,metal)
        box(furniture,x-.32,lane-1.05,x+.32,lane-.40,.51,.60,"b47e51")
        box(furniture,x-.31,lane-1.08,x+.31,lane-.98,.60,1.16,"5c7475")
    for i in range(2):
        x=x0+.73+i*.72
        box(furniture,x-.32,lane+.87,x+.32,lane+1.69,.12,2.13,metal)
        for j in range(9):
            box(furniture,x-.25,lane+.86,x+.25,lane+.88,.36+.16*j,.42+.16*j,"667c7a")
            box(screens,x+.14,lane+.84,x+.20,lane+.86,.37+.16*j,.40+.16*j,"85c7af")
    # Signage is physical lettering on the concrete lintel.
    mid=(x0+x1)/2
    box(m,mid-3.54,-y-.26,mid+3.54,-y-.21,4.62,5.69,metal)
    art.label(screens,"CONTROL ROOM",lambda x,z:(mid+x,-y-.275,4.79+z),6.3,"d9e8dd")
    for ya in (-y+.6,partition-.48):
        box(screens,x0+.5,ya,x1-.5,ya+.065,3.86,3.93,"e3dcb9")
    for k in range(6):
        x=x0+1.1+k*(x1-x0-2.2)/5
        box(m,x-.20,-y-.64,x+.20,-y-.41,4.10,4.18,metal)
        box(screens,x-.15,-y-.64,x+.15,-y-.60,4.095,4.15,"f0c787")
    return m,glass,furniture,screens
