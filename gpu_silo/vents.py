"""Ventilation of the bore: a fan plug in the ground door and air vents in the lid.

Air enters through the door plug at the bottom, rises past the pods as they warm it,
and leaves through the roof vents. The plug comes out for a pod exchange and goes back in.
"""
import math

from . import clock
from . import design as cfg
from . import maintenance as care
from . import plant
from . import services
from . import silo_model as s

V=cfg.PROJECT["ventilation"]
FANS=V["door_fans"]
FAN_R=V["door_fan_diameter_m"]/2
ROOF=V["roof_air_vents"]
ROOF_R=V["roof_air_vent_diameter_m"]/2
ROOF_RADIUS=4.35
ROOF_HEIGHT=.62
PLUG_FACE=s.RO+.10
# Frames after the start of the pod exchange: the plug comes out, then goes back.
PLUG_OUT=(332,376)
PLUG_IN=(812,858)
SET_ASIDE=(1.1,2.35)
OFF,ON=(0,0,0),(1,1,1)


def fan(m,centre,axis,radius,blades=5):
    """A dark throat, a ring, a hub and flat blades facing along axis (a unit vector)."""
    u=s.norm(s.cross((0,0,1) if abs(axis[2])<.9 else (1,0,0),axis));w=s.cross(axis,u)
    def at(r,a,lift=0.):
        return s.plus(centre,s.plus(s.plus(s.times(u,r*math.cos(a)),s.times(w,r*math.sin(a))),s.times(axis,lift)))
    n=20
    disc=[at(radius,j*s.TAU/n,.004) for j in range(n)]
    m.face(disc,"2f3d42");m.face(disc[::-1],"2f3d42")
    for j in range(n):
        a,b=j*s.TAU/n,(j+1)*s.TAU/n
        m.face([at(radius,a,.004),at(radius,b,.004),at(radius+.045,b,.05),at(radius+.045,a,.05)],"e4e6e0")
        m.face([at(radius+.045,a,.05),at(radius+.045,b,.05),at(radius+.045,b,0),at(radius+.045,a,0)],"c2c6c0")
    for k in range(blades):
        a=k*s.TAU/blades
        blade=[at(radius*.16,a-.30,.03),at(radius*.90,a-.05,.03),at(radius*.90,a+.42,.03),at(radius*.16,a+.30,.03)]
        m.face(blade,"dfe2dc");m.face(blade[::-1],"dfe2dc")
    hub=[at(radius*.20,j*s.TAU/10,.045) for j in range(10)]
    m.face(hub,"f0f1ec");m.face(hub[::-1],"f0f1ec")
    for a in (0,math.pi/2):
        s.bar(m,at(radius,a,.055),at(radius,a+math.pi,.055),.02,"c2c6c0")


def plug_mesh():
    """A panel that fills the ground door, with stacked fans. Local X points out of the silo."""
    m=plant.mesh(f"Door plug | ventilation panel with {FANS} fans")
    w,h=s.OPENING_WIDTH/2-.02,s.OPENING_HEIGHT-.03
    plant.closed(m,PLUG_FACE-.16,-w,PLUG_FACE,w,.02,h,"cdd0c9")
    for y in (-w-.04,w-.02):
        plant.closed(m,PLUG_FACE-.02,y,PLUG_FACE+.03,y+.06,.0,h+.03,"8e9690")
    plant.closed(m,PLUG_FACE-.02,-w-.04,PLUG_FACE+.03,w+.04,h-.03,h+.03,"8e9690")
    pitch=h/FANS
    for k in range(FANS):
        fan(m,(PLUG_FACE,0,pitch*(k+.5)),(1,0,0),min(FAN_R,w-.05))
    return m


def roof_vent_mesh():
    m=plant.mesh("Roof air vent | curb, fan and guard")
    services.pipe(m,(0,0,0),(0,0,ROOF_HEIGHT),ROOF_R,"c9cdc6",ROOF_R-.06,n=20)
    services.pipe(m,(0,0,0),(0,0,.10),ROOF_R+.12,"8e9690",ROOF_R-.06,n=20)
    fan(m,(0,0,ROOF_HEIGHT-.06),(0,0,1),ROOF_R-.08,6)
    return m


def roof_positions():
    return [s.polar(ROOF_RADIUS,plant.POWER_YAW+math.pi/4+k*s.TAU/ROOF,plant.LID_Z+plant.LID_THICK) for k in range(ROOF)]


def plug_offset(t):
    """Local offset of the plug (out, along the wall) at frames after the store is full."""
    arrive=3.2*(1-s.step(*clock.DOOR,t))
    w=t-care.REPAIR
    away=s.step(PLUG_OUT[0],PLUG_OUT[0]+18,w)-s.step(PLUG_IN[1]-18,PLUG_IN[1],w)
    aside=s.step(PLUG_OUT[0]+16,PLUG_OUT[1],w)-s.step(PLUG_IN[0],PLUG_IN[1]-16,w)
    return arrive+SET_ASIDE[0]*away,SET_ASIDE[1]*aside


def install(scene,node,p):
    co,si=math.cos(s.ENTRY),math.sin(s.ENTRY)
    def place(t):
        out,along=plug_offset(t)
        return (out*co-along*si,out*si+along*co,0)
    values=[place(t) for t in range(care.END)]
    node("Door plug | ventilation panel in the ground door",scene.mesh(plug_mesh()),"Door plug",ang=s.ENTRY,
         tracks={"translation":[(0,values[0])]+[(p.FILLED+f,v) for f,v in p.flat_keys(values)],
                 "scale":[(0,OFF),(p.FILLED+clock.DOOR[0]-.02,OFF),(p.FILLED+clock.DOOR[0],ON)]})
    vent=scene.mesh(roof_vent_mesh())
    step=(clock.ROOF[1]-clock.ROOF[0]-16)/max(1,ROOF-1)
    for k,(x,y,z) in enumerate(roof_positions()):
        start=clock.ROOF[0]+round(k*step)
        drop=[(x,y,z+2.4*(1-s.step(start,start+16,t))) for t in range(start,start+17)]
        node(f"Roof air vent {k+1:02}",vent,"Roof vents",
             tracks={"translation":[(0,drop[0])]+[(p.FILLED+start+f,v) for f,v in p.flat_keys(drop)],
                     "scale":[(0,OFF),(p.FILLED+start-.02,OFF),(p.FILLED+start,ON),
                              (p.REGHOST-.02,ON),(p.REGHOST,OFF),(p.RESTORE2-.02,OFF),(p.RESTORE2,ON)]})
    scene.project_info.update(doorPlugFans=FANS,roofAirVents=ROOF,doorPlugInstalled_s=(p.FILLED+clock.DOOR[1])/p.FPS,
        boreVentilation="Air enters through the fan plug in the ground door, rises past the pods and leaves through the roof vents.")
