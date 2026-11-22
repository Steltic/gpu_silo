"""Fuel beside the silo: propane for the turbines and bulk diesel for the backup sets.

The propane tanks stand side by side with their long axes pointing at the silo. One propane line
runs along the ground, up the outside wall behind a cooler frame, over the lid and down to the
turbine level. A small diesel line follows it and carries on down to the day tanks.
"""
import math

from . import closing
from . import cooler_frames as fr
from . import design as cfg
from . import plant
from . import services
from . import silo_model as s
from . import site as roads
from . import traffic
from . import logistics

F=cfg.PROJECT["fuel"]
COUNT=F["tanks"]
DIA,LENGTH,PITCH=F["tank_diameter_m"],F["tank_length_m"],F["tank_spacing_m"]
BEARING=fr.BEARINGS[F["riser_behind_frame"]-1]+math.asin(F["riser_offset_m"]/s.RO)
FARM_R=F["distance_m"]
HEADER_R=FARM_R-LENGTH/2-1.4
RISER_R=s.RO+.22
PIPE=F["line_diameter_m"]/2
D=cfg.PROJECT["diesel"]
DIESEL_PIPE=.04
DIESEL="b5553c"
BULK_D,BULK_L=D["bulk_tank_diameter_m"],D["bulk_tank_length_m"]
SIDE=.34
LOW=.45
BURIED=-cfg.PROJECT["coordination"]["services"]["crossing_centre_depth_m"]
TOP=plant.LID_Z+.80
BULK_Y=-(COUNT-1)*PITCH/2-DIA/2-BULK_D/2-cfg.PROJECT["coordination"]["services"]["bulk_diesel_offset_m"]
# The drops come down beside the turbine sets, clear of the roof equipment.
DROP_R=4.6
GAS="d9b13c"
SHELL="e9e7dc"
OFF,ON=(0,0,0),(1,1,1)


def drop_end(crown):
    return plant.power_base(crown,1)+1.2


def diesel_end(crown):
    return plant.power_base(crown,0)+1.6


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


def unit_pipe(name,axis,gas=True,diesel=True):
    """A one-metre length of line from the origin. Scaling the node along the axis lays the pipe.

    The diesel line runs beside the gas line, offset along local Y.
    """
    m=plant.mesh(name)
    if gas:services.pipe(m,(0,0,0),axis,PIPE,GAS,n=10)
    if diesel:services.pipe(m,(0,SIDE,0),(axis[0],SIDE+axis[1],axis[2]),DIESEL_PIPE,DIESEL,n=8)
    return m


def bulk_tank_mesh():
    m=plant.mesh(f"Diesel bulk tank | {BULK_L:g} m horizontal tank on two saddles")
    r=BULK_D/2;body=BULK_L/2-.3;z=r+.55
    services.pipe(m,(-body,0,z),(body,0,z),r,DIESEL,n=18)
    for sign in (-1,1):
        services.pipe(m,(sign*body,0,z),(sign*BULK_L/2,0,z),r*.8,"9c4a36",n=18)
        plant.closed(m,sign*BULK_L*.3-.4,-r*.82,sign*BULK_L*.3+.4,r*.82,0,z-r*.55,"a9aea4")
    services.pipe(m,(0,0,z+r-.05),(0,0,z+r+.4),.22,"8f9892",n=10)
    return m


BAY_FRONTS=(math.degrees(BEARING)-3.,math.degrees(BEARING)+31.)
BAY_LENGTH=math.degrees((roads.STEER+roads.TANKER_AXLE+2.6)/roads.LAYBY_R)
BAY_RISERS=tuple(front-BAY_LENGTH*.55 for front in BAY_FRONTS)
TRANSPORT_DWELL,TRANSPORT_HEADWAY,TRANSPORTS=70,38,5


def layby_route(front):
    """A lap that pulls out to the lay-by beside the tank header. `front` is the bearing at which the front axle stops."""
    first,last=roads.JOIN[roads.R_RUN],roads.LEAVE[roads.R_RUN]
    rear=front-BAY_LENGTH
    def radius(b):
        out=s.step(max(first+roads.TURN,rear-16),max(first+roads.TURN+8,rear-4),b)-s.step(front+2,front+13,b)
        return roads.R_RUN+(roads.LAYBY_R-roads.R_RUN)*out
    count=math.ceil((last-first-2*roads.TURN)/3)
    marks=[first+roads.TURN+(last-first-2*roads.TURN)*k/count for k in range(count+1)]
    path=roads.Path(roads.arrive()+[s.polar(radius(b),math.radians(b),0)[:2] for b in marks]+roads.depart())
    return path,path.nearest(s.polar(roads.LAYBY_R,math.radians(front),0)[:2])


def transport_visits():
    """(bay, connected from, connected until) in frames after the store is full. The downstream bay fills first."""
    start=closing.LINE-12
    return [(1-n%2,start+n*TRANSPORT_HEADWAY,start+n*TRANSPORT_HEADWAY+TRANSPORT_DWELL) for n in range(TRANSPORTS)]


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
    pad=plant.mesh("Propane storage | gravel pad, jacking portals and unloading risers")
    half=COUNT*PITCH/2+1.5
    north=BULK_Y
    pts=[site(FARM_R+dx,dy,.012) for dx,dy in ((-LENGTH/2-3,north-BULK_D/2-1.5),(roads.BACK_ROAD-FARM_R-2.5,north-BULK_D/2-1.5),
                                                (roads.BACK_ROAD-FARM_R-2.5,half),(-LENGTH/2-3,half))]
    pad.face(pts,"c2b99f")
    node(pad.name,scene.mesh(pad),"Fuel storage",tracks={"scale":window(closing.FUEL-150)})
    # Unloading risers beside the ring lay-by, one for each transport bay.
    posts=plant.mesh("Propane unloading | two risers at the lay-by")
    for bearing in BAY_RISERS:
        x,y,_=s.polar(roads.LAYBY_R+2.6,math.radians(bearing),0)
        plant.closed(posts,x-.25,y-.25,x+.25,y+.25,0,1.5,"8f9892")
        services.pipe(posts,(x,y,1.3),(x+.9*math.cos(math.radians(bearing)+2.4),y+.9*math.sin(math.radians(bearing)+2.4),1.0),.07,"30383a",n=6)
        services.pipe(posts,(x,y,.4),s.polar(HEADER_R,BEARING+math.asin(s.clamp(math.sin(math.radians(bearing)-BEARING)*roads.LAYBY_R/HEADER_R,-.99,.99)),LOW),PIPE*.5,GAS,n=6)
    node(posts.name,scene.mesh(posts),"Fuel storage",tracks={"scale":window(closing.LINE-30)})
    tank=scene.mesh(tank_mesh())
    fleet=scene.fleet
    hauler=fleet.mesh("haul trailer",roads.haul_trailer)
    flat=fleet.mesh("flatbed",roads.flatbed)
    portal=plant.mesh("Tank jacking portals | lift each tank off its trailer and lower it to the pad")
    def slot_route(y,short=False):
        """Ring to a tank slot, out through the back of the farm and north to the public road."""
        reach=math.sqrt(roads.R_RUN**2-y*y)
        bearing=math.degrees(BEARING+math.asin(y/roads.R_RUN))
        points=roads.arrive()+roads.lap(roads.JOIN[roads.R_RUN],bearing)
        points+=[site(reach,y)[:2],site(roads.BACK_ROAD,y)[:2]]+roads.back_road()[1:]
        return roads.Path(points,8.)
    step=closing.TANK_STEP;settle=closing.TANK_SETTLE
    deliveries=[(f"Propane tank {j+1:02}",tank,y,FARM_R,hauler,roads.HAUL_AXLE,-11.6,.98,closing.TANKS+j*step) for j,y in enumerate(offsets())]
    last=closing.TANKS+(COUNT-1)*step
    deliveries.append(("Diesel bulk tank",scene.mesh(bulk_tank_mesh()),north,FARM_R-LENGTH/2+BULK_L/2,flat,roads.FLAT_AXLE,traffic.DECK_MID,roads.DECK,last))
    for name,mesh_id,y,x,trailer,axle,seat,deck,stops in deliveries:
        route=slot_route(y)
        stop=route.nearest(site(x,y)[:2])+roads.STEER-seat
        trip=roads.Trip()
        traffic.come(trip,route,stop,base+stops+2)
        traffic.go(trip,route,stop,base+stops+9,gate=roads.back_road()[1])
        towed,_,_=fleet.rig(name+" | delivery",trip,trailer,axle,group="Fuel delivery")
        lifted=base+stops+4
        node(name+" | on its trailer",mesh_id,"Fuel delivery",towed,t=(seat,0,deck),tracks={"scale":roads.window(0,lifted)})
        def height(t,deck=deck,stops=stops):
            return deck+.3*s.step(stops+4,stops+8,t)-(deck+.3)*s.step(stops+settle-10,stops+settle,t)
        node(name,mesh_id,"Fuel storage",ang=BEARING,
             tracks={"translation":curve((stops+4,stops+settle),lambda t,x=x,y=y,height=height:site(x,y,height(t))),
                     "scale":[(0,OFF),(lifted-.02,OFF),(lifted,ON)]})
        if trailer==hauler:
            for dx in (-LENGTH*.3,LENGTH*.3):
                for sign in (-1,1):
                    px,py,_=site(x+dx,y+sign*1.95)
                    plant.closed(portal,px-.22,py-.22,px+.22,py+.22,0,4.7,"d7a84c")
                a,b=site(x+dx,y-1.95,4.6),site(x+dx,y+1.95,4.6)
                s.bar(portal,a,b,.36,"d7a84c",.4)
    node(portal.name,scene.mesh(portal),"Fuel delivery",tracks={"scale":window(closing.FUEL-150,last+settle+8)})
    landed=sorted(base+stops+settle for *_,stops in deliveries)
    scene.counts["tanks"]=[sum(1 for at in landed if f>=at) for f in range(p.FRAMES)]
    # Propane transports unload at the ring lay-by once the tanks are set.
    transport=fleet.mesh("propane transport",lambda:roads.tanker("Propane transport semi-trailer","e9e7dc",12.6,2.2,"c8563c"))
    routes=[layby_route(front) for front in BAY_FRONTS]
    visits=transport_visits()
    for n,(bay,a,b) in enumerate(visits):
        route,stop=routes[bay]
        trip=roads.Trip()
        traffic.come(trip,route,stop,base+a);traffic.go(trip,route,stop,base+b)
        fleet.rig(f"Propane transport {n+1:02}",trip,transport,roads.TANKER_AXLE,group="Fuel delivery")
    loads=logistics.C["propane_loads"]
    ends=[base+b for _,_,b in visits]
    scene.counts["propane"]=[min(loads,math.ceil(loads*sum(1 for e in ends if f>=e)/len(ends))) for f in range(p.FRAMES)]
    line=scene.mesh(unit_pipe("Fuel lines | one metre of gas and diesel pipe along local X",(1,0,0)))
    rise=scene.mesh(unit_pipe("Fuel lines | one metre of gas and diesel riser",(0,0,1)))
    fall=scene.mesh(unit_pipe("Gas line | one metre of drop",(0,0,-1),diesel=False))
    oil=scene.mesh(unit_pipe("Diesel line | one metre of drop",(0,0,-1),gas=False))
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
    diesel_transition=scene.mesh(unit_pipe("Diesel header transition",(0,0,1),gas=False))
    lay("Diesel header | transition to buried crossing",diesel_transition,site(HEADER_R,0,BURIED),BEARING+math.pi,closing.RUN,LOW-BURIED,"z")
    lay("Gas line | buried road crossing",line,site(HEADER_R,0,BURIED),BEARING+math.pi,closing.RUN,HEADER_R-RISER_R,"x")
    lay("Gas line | riser on the outside wall",rise,site(RISER_R,0,BURIED),BEARING+math.pi,closing.RISER,TOP-BURIED,"z")
    lay("Gas line | run across the lid",line,site(RISER_R,0,TOP),BEARING+math.pi,closing.ROOF,RISER_R-DROP_R,"x")
    lay("Gas line | drop to the power modules",fall,site(DROP_R,0,TOP),BEARING+math.pi,closing.DROP,TOP-drop_end(p.CROWN),"z")
    lay("Diesel line | drop to the day tanks",oil,site(DROP_R,0,TOP),BEARING+math.pi,closing.DROP,TOP-diesel_end(p.CROWN),"z")
    scene.project_info.update(dieselBulkTank_m=[BULK_L,BULK_D],propaneTanks=COUNT,propaneTank_m=[LENGTH,DIA],propaneStorageDistance_m=FARM_R,
        gasRiserBearing_deg=math.degrees(BEARING),gasLineTop_m=TOP,fuelSceneStart_s=(base+closing.FUEL)/p.FPS)
