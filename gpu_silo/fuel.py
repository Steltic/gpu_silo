"""Propane storage beside the silo and the gas line to the power modules.

The tanks stand side by side with their long axes pointing at the silo. One line
runs along the ground, up the outside wall behind a cooler frame, over the lid
and down to the two power modules.
"""
import math

from . import closing
from . import cooler_frames as fr
from . import design as cfg
from . import plant
from . import services
from . import silo_model as s

F=cfg.PROJECT["fuel"]
COUNT=F["tanks"]
DIA,LENGTH,PITCH=F["tank_diameter_m"],F["tank_length_m"],F["tank_spacing_m"]
BEARING=fr.BEARINGS[F["riser_behind_frame"]-1]+math.asin(F["riser_offset_m"]/s.RO)
FARM_R=F["distance_m"]
HEADER_R=FARM_R-LENGTH/2-1.4
RISER_R=s.RO+.22
PIPE=.14
LOW=.45
TOP=s.WALL_HEIGHT+.80
DROP_R=2.6
GAS="d9b13c"
SHELL="e9e7dc"
OFF,ON=(0,0,0),(1,1,1)


def drop_end(crown):
    return plant.power_base(crown,0)+plant.HEIGHT/2


def offsets():
    return [(j-(COUNT-1)/2)*PITCH for j in range(COUNT)]


def tank_mesh():
    m=plant.mesh(f"{F['gas']} tank | {LENGTH:g} m bullet on two saddles")
    r=DIA/2;body=LENGTH/2-r*.6;z=r+.55
    services.pipe(m,(-body,0,z),(body,0,z),r,SHELL,n=18)
    for sign in (-1,1):
        services.pipe(m,(sign*body,0,z),(sign*(body+r*.34),0,z),r*.88,"dedccf",n=18)
        services.pipe(m,(sign*(body+r*.34),0,z),(sign*LENGTH/2,0,z),r*.58,"d3d1c4",n=18)
        plant.closed(m,sign*LENGTH*.3-.45,-r*.82,sign*LENGTH*.3+.45,r*.82,0,z-r*.55,"a9aea4")
    services.pipe(m,(-.6,0,z),(.6,0,z),r+.02,"c8563c",n=18)
    services.pipe(m,(0,0,z+r-.05),(0,0,z+r+.45),.30,"8f9892",n=10)
    services.pipe(m,(-body+.4,0,z-r+.25),(-LENGTH/2-1.4,0,LOW),PIPE*.8,GAS,n=8)
    return m


def unit_pipe(name,axis):
    """A one-metre length of gas line from the origin. Scaling the node along the axis lays the pipe."""
    m=plant.mesh(name)
    services.pipe(m,(0,0,0),axis,PIPE,GAS,n=10)
    return m


def growth(t,span):
    return s.step(span[0],span[1],t)


def camera(t,orbit_end,cam,blend):
    """Leave the closing orbit for the tank farm, follow the line up the wall and finish above the lid."""
    deg=math.degrees(BEARING)
    farm=cam(s.polar(31,BEARING,7),deg+40,19,150)
    wall=cam(s.polar(7,BEARING,19),deg+32,22,96)
    top=cam((0,0,29.5),deg+26,40,64)
    if t<closing.RUN[1]-12:return blend(orbit_end,farm,s.step(closing.FUEL,closing.FUEL+52,t))
    if t<closing.RISER[1]-18:return blend(farm,wall,s.step(closing.RUN[1]-12,closing.RISER[0]+22,t))
    return blend(wall,top,s.step(closing.RISER[1]-18,closing.ROOF[1]+4,t))


def install(scene,node,p):
    base=p.FILLED
    def window(start,end=None):
        keys=[(0,OFF),(base+start-.02,OFF),(base+start,ON)]
        if end is not None:keys.extend([(base+end-.02,ON),(base+end,OFF)])
        return keys
    def curve(span,fn):
        values=[fn(t) for t in range(span[0],span[1]+1)]
        return [(0,values[0])]+[(base+span[0]+k,v) for k,v in p.flat_keys(values)]
    co,si=math.cos(BEARING),math.sin(BEARING)
    def site(x,y,z=0):
        return (x*co-y*si,x*si+y*co,z)
    pad=plant.mesh("Propane storage | gravel pad and bund kerb")
    half=COUNT*PITCH/2+1.5
    pts=[site(FARM_R+dx,dy,.012) for dx,dy in ((-LENGTH/2-3,-half),(LENGTH/2+2,-half),(LENGTH/2+2,half),(-LENGTH/2-3,half))]
    pad.face(pts,"c2b99f")
    node(pad.name,scene.mesh(pad),"Fuel storage",tracks={"scale":window(closing.FUEL)})
    tank=scene.mesh(tank_mesh())
    for j,y in enumerate(offsets()):
        land=closing.TANKS+j*closing.TANK_STEP
        def lower(t,y=y,land=land):
            return site(FARM_R,y,6.5*(1-s.step(land,land+closing.TANK_STEP-2,t)))
        node(f"Propane tank {j+1:02}",tank,"Fuel storage",ang=BEARING,
             tracks={"translation":curve((land,land+closing.TANK_STEP),lower),"scale":window(land)})
    line=scene.mesh(unit_pipe("Gas line | one metre of pipe along local X",(1,0,0)))
    rise=scene.mesh(unit_pipe("Gas line | one metre of riser",(0,0,1)))
    fall=scene.mesh(unit_pipe("Gas line | one metre of drop",(0,0,-1)))
    width=(COUNT-1)*PITCH
    header=plant.mesh("Gas line | tank header")
    services.pipe(header,(0,-.5,0),(0,.5,0),PIPE,GAS,n=10)
    node("Gas line | header across the tank ends",scene.mesh(header),"Gas line",ang=BEARING,t=site(HEADER_R,0,LOW),
         tracks={"scale":[(0,OFF),(base+closing.HEADER[0]-.02,OFF)]+[(base+t,(1,max(.001,width*growth(t,closing.HEADER)),1))
                           for t in range(closing.HEADER[0],closing.HEADER[1]+1)]})
    def lay(name,mesh_id,origin,angle,span,length,axis):
        def size(t):
            g=max(.001,length*growth(t,span))
            return (g,1,1) if axis=="x" else (1,1,g)
        node(name,mesh_id,"Gas line",ang=angle,t=origin,
             tracks={"scale":[(0,OFF),(base+span[0]-.02,OFF)]+[(base+t,size(t)) for t in range(span[0],span[1]+1)]})
    lay("Gas line | ground run to the silo",line,site(HEADER_R,0,LOW),BEARING+math.pi,closing.RUN,HEADER_R-RISER_R,"x")
    lay("Gas line | riser on the outside wall",rise,site(RISER_R,0,LOW),0,closing.RISER,TOP-LOW,"z")
    lay("Gas line | run across the lid",line,site(RISER_R,0,TOP),BEARING+math.pi,closing.ROOF,RISER_R-DROP_R,"x")
    lay("Gas line | drop to the power modules",fall,site(DROP_R,0,TOP),0,closing.DROP,TOP-drop_end(p.CROWN),"z")
    scene.project_info.update(propaneTanks=COUNT,propaneTank_m=[LENGTH,DIA],propaneStorageDistance_m=FARM_R,
        gasRiserBearing_deg=math.degrees(BEARING),gasLineTop_m=TOP,fuelSceneStart_s=(base+closing.FUEL)/p.FPS)
