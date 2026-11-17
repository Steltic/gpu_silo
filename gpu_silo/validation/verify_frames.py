"""Check the dry cooler frames, their screens and cast-in fixings, the crawler picks, the boom lift
and the cooler exchange in the GLB."""
import math
import re
import sys

import numpy as np

from .. import calcs
from .. import cooler_frames as fr
from .. import pod_scene as p
from .. import service
from .verify_motion import open_glb


def exchange(p,ids,parents,at,zup,points,car,hook):
    # Cooler exchange: the frame comes down outside the wall, one cooler is changed, and the frame goes back to its seat.
    k=service.K;label=f"Cooler frame {k+1:02}";begin=p.FILLED+p.care.REPAIR
    root=ids[label+f" | {fr.ROWS} dry coolers, {fr.ROWS} pumps and steel"]
    seat=zup(at(root,"translation",begin+service.LIFT[0]-1))
    down=zup(at(root,"translation",begin+service.DOWN[1]))
    assert abs(math.hypot(down[0],down[1])-service.LAND_R)<.01 and abs(down[2]-fr.GROUND)<.01
    for f in range(begin+service.LIFT[0],begin+service.SEAT[1]+1):
        pos=zup(at(root,"translation",f));radius=math.hypot(pos[0],pos[1])
        assert radius>=fr.BACK-1e-4 and pos[2]>=fr.GROUND-1e-4
        if radius<fr.BACK+fr.OVER-.01:assert pos[2]>=fr.base(k)-1e-4
    assert np.allclose(zup(at(root,"translation",begin+service.SEAT[1])),seat,atol=.0003)
    old=ids[label+f" | cooler {service.ROW+1}"];new=ids[label+f" | cooler {service.ROW+1} | replacement in its bay"]
    assert parents[new]==root and np.allclose(points(new),points(old))
    assert at(old,"scale",begin+service.SLIDE[0])[0]>.999 and at(old,"scale",p.FRAMES-1)[0]<.001
    assert at(new,"scale",begin+service.INSERT[1]-1)[0]<.001 and at(new,"scale",p.FRAMES-1)[0]>.999
    assert np.allclose(at(new,"translation",p.FRAMES-1),at(old,"translation",0),atol=.0003)
    assert at(ids[label+" | pipe spools"],"scale",begin+service.DOWN[0])[0]<.01 and at(ids[label+" | pipe spools"],"scale",p.FRAMES-1)[0]>1
    for f in range(begin+service.OUT[0],begin+service.IN[1]+1,4):
        foot=zup(at(car,"translation",f));block=zup(at(hook,"translation",f));reach=np.linalg.norm(block[:2]-foot[:2])
        assert 10<reach<fr.BOOM_LENGTH*.6 and block[2]<2.45+math.sqrt(fr.BOOM_LENGTH**2-reach**2)-2,(f,reach)
    print(f"Frame {k+1:02} comes down for a cooler change during the pod exchange and returns to its seat.")


def check(path):
    doc,access=open_glb(path);nodes=doc["nodes"];ids={}
    for i,node in enumerate(nodes):ids.setdefault(node["name"],i)
    parents={j:i for i,n in enumerate(nodes) for j in n.get("children",[])}
    anim=doc["animations"][0]
    curves={(ch["target"]["node"],ch["target"]["path"]):anim["samplers"][ch["sampler"]] for ch in anim["channels"]}
    def at(i,key,frame):
        default={"rotation":[0,0,0,1],"scale":[1,1,1],"translation":[0,0,0]}
        if (i,key) not in curves:return np.array(nodes[i].get(key,default[key]),dtype=float)
        sm=curves[i,key];times=access[sm["input"]][:,0];vals=access[sm["output"]]
        return np.array([np.interp(np.float32(frame/p.FPS),times,col) for col in vals.T])
    def zup(v):return np.array([v[0],-v[2],v[1]])
    def yaw(i,frame):
        q=at(i,"rotation",frame);return 2*math.atan2(q[1],q[3])
    def points(i):
        if "mesh" not in nodes[i]:i=ids[nodes[i]["name"]+" | full finish"]
        prim=doc["meshes"][nodes[i]["mesh"]]["primitives"][0]
        vs=access[prim["attributes"]["POSITION"]].astype(float)
        return np.stack([vs[:,0],-vs[:,2],vs[:,1]],axis=-1)
    extras=doc["extras"];d=fr.D
    assert extras["coolerFrames"]==fr.N and extras["dryCoolers"]==fr.N*fr.ROWS==p.cfg.COOLERS
    assert abs(extras["heatRejection_MW"]-p.cfg.COOLERS*d["cooler_capacity_mw"])<1e-9
    assert abs(extras["liquidHeatLoad_MW"]-calcs.C["heat_mw"])<1e-9 and extras["gpuRacks"]==p.cfg.RACKS
    # Geometry of one frame and its equipment.
    steel=points(ids["Cooler frame 01 | steel frame"])
    assert np.allclose(steel.min(axis=0),[0,-fr.WIDTH/2,0],atol=.0002)
    assert np.allclose(steel[:,:2].max(axis=0),[fr.DEPTH,fr.WIDTH/2],atol=.0002) and fr.HEIGHT<=steel[:,2].max()<fr.HEIGHT+.3
    cooler=points(ids["Cooler frame 01 | cooler 1"]);pump=points(ids["Cooler frame 01 | pump unit 1"])
    assert np.isclose(np.ptp(cooler[:,1]),fr.COOL_L,atol=.25) and cooler[:,2].max()<=fr.ROW-.15 and cooler[:,2].min()>=0
    assert np.ptp(pump[:,1])<=fr.PUMP_L and cooler[:,0].min()>0 and cooler[:,0].max()<fr.DEPTH+.2
    # Every frame ends flat against its bearing at its tier, clear of the door, the rim and its neighbours.
    seats=[]
    for k in range(fr.N):
        label=f"Cooler frame {k+1:02}"
        root=ids[label+f" | {fr.ROWS} dry coolers, {fr.ROWS} pumps and steel"]
        i=fr.ORDER.index(k);a,b,c,dd,e,r,g,end=fr.times(i)
        bearing=yaw(root,p.FRAMES-1)
        assert abs(math.sin(bearing-fr.BEARINGS[k]))<1e-5 and abs(math.sin(yaw(root,e)-fr.BEARINGS[k]))<1e-5
        # Frames are hung while the pods are being loaded, anticlockwise from the first frame.
        assert p.FIRST_POD<a and end<=p.FILLED and fr.THETA[i]>=fr.THETA[0]
        screen=points(ids[label+" | mesh screen"])
        assert parents[ids[label+" | mesh screen"]]==root and screen[:,0].max()>=fr.DEPTH and np.ptp(screen[:,1])>=fr.WIDTH-.2
        assert screen[:,2].min()<.3 and screen[:,2].max()>fr.HEIGHT-.3
        final=zup(at(root,"translation",p.FRAMES-1))
        assert np.allclose(final,[fr.BACK*math.cos(fr.BEARINGS[k]),fr.BACK*math.sin(fr.BEARINGS[k]),fr.base(k)],atol=.0003)
        assert fr.base(k)>p.s.OPENING_HEIGHT+2 and fr.base(k)+fr.HEIGHT<=p.s.WALL_HEIGHT+1e-6
        # A frame stands in laydown from the day its steel arrives. That is after the walls and before its pick.
        assert at(root,"scale",p.C).max()<.001 and at(root,"scale",a-1).min()>.999
        for part in range(1,fr.ROWS+1):
            assert parents[ids[label+f" | cooler {part}"]]==root and parents[ids[label+f" | pump unit {part}"]]==root
        # The frame never passes through concrete: its back plane stays outside the wall whenever it is off its seat.
        for f in range(a,e+1):
            pos=zup(at(root,"translation",f));radius=math.hypot(pos[0],pos[1])
            assert radius>=fr.BACK-1e-4
            if radius<fr.LAY_R-.01:assert pos[2]>=fr.base(k)-1e-4
        assert np.allclose(zup(at(root,"translation",e)),final,atol=.0003)
        slings=ids[label+" | lifting slings"]
        assert at(slings,"scale",c)[0]>.999 and at(slings,"scale",r+1)[0]<.001 and at(slings,"scale",a-8)[0]<.001
        spool=ids[label+" | pipe spools"]
        assert at(spool,"scale",e)[0]<.01 and at(spool,"scale",g)[0]>1
        seats.append((fr.BEARINGS[k],fr.base(k)))
        # Cast-in anchors and conduits are in the forms before their concrete is poured.
        station=ids[label+" | fixed wall station"]
        fixings=[j for j,pa in parents.items() if pa==station and "cast-in" in nodes[j]["name"]]
        anchors=[j for j in fixings if "anchor" in nodes[j]["name"]];conduits=[j for j in fixings if "conduit" in nodes[j]["name"]]
        assert len(anchors)==len(fr.COLUMNS)*(fr.ROWS+1) and len(conduits)==fr.ROWS*d["conduits_per_cooler"]
        for j in fixings:
            sm=curves[j,"translation"];last=float(access[sm["input"]][-1,0])*p.FPS
            cast=round(last);z=zup(at(j,"translation",cast))[2]
            assert at(j,"scale",cast)[0]>.999 and cast<p.C
            low=z-(.26 if j in anchors else fr.CONDUIT_R)
            assert p.s.display_info(cast)["height"]<=low+1e-4,(nodes[j]["name"],cast,low)
            assert fr.base(k)<z<fr.base(k)+fr.HEIGHT
        for j in anchors:
            pos=zup(at(j,"translation",p.FRAMES-1));turn=yaw(j,0)
            world=np.array([pos[0]*math.cos(bearing)-pos[1]*math.sin(bearing),pos[0]*math.sin(bearing)+pos[1]*math.cos(bearing)])
            assert abs(np.linalg.norm(world)-p.s.RO)<.0005 and abs(math.sin(turn-math.atan2(pos[1],pos[0])))<1e-4
    # Frames that share a tier keep clear of one another round the wall.
    half=math.asin(fr.WIDTH/2/fr.BACK)
    for i,(a0,z0) in enumerate(seats):
        for a1,z1 in seats[i+1:]:
            if abs(z0-z1)<fr.HEIGHT:
                gap=abs((a0-a1+math.pi)%(2*math.pi)-math.pi)
                assert gap>2*half+.01,("frames overlap on one tier",math.degrees(gap))
    # The crawler stays on its track, within the boom's reach, with the hook plumb over the lugs while it carries a frame.
    car=ids["South crawler"];hook=ids["South crawler | retained hook block"]
    for i,k in enumerate(fr.ORDER):
        root=ids[f"Cooler frame {k+1:02} | {fr.ROWS} dry coolers, {fr.ROWS} pumps and steel"]
        a,b,c,dd,e,r,g,end=fr.times(i)
        for f in range(b,r+1):
            foot=zup(at(car,"translation",f));load=zup(at(root,"translation",f));block=zup(at(hook,"translation",f))
            assert abs(math.hypot(foot[0],foot[1])-fr.TRACK_R)<.001
            facing=yaw(root,f)
            centre=load[:2]+fr.DEPTH/2*np.array([math.cos(facing),math.sin(facing)])
            assert np.linalg.norm(block[:2]-centre)<.002 and abs(block[2]-load[2]-fr.HEIGHT-fr.SLING)<.002,(k,f,block,centre,load)
            reach=np.linalg.norm(block[:2]-foot[:2])
            assert 8<reach<fr.BOOM_LENGTH*.6 and block[2]<2.45+math.sqrt(fr.BOOM_LENGTH**2-reach**2)-2
    # One crawler stays from the steel cage until the lid is on. It is away for the closing scenes and returns for the cooler exchange.
    assert at(car,"scale",fr.START)[0]>.999 and at(car,"scale",p.FILLED+p.plant.LID[1])[0]>.999
    assert at(car,"scale",p.FILLED+p.care.ORBIT)[0]<.001 and at(car,"scale",p.FILLED+p.closing.FUEL_END)[0]<.001
    assert at(car,"scale",p.FRAMES-1)[0]<.001
    if not p.film.SHORT:
        assert at(car,"scale",p.FILLED+p.care.REPAIR+service.ARRIVE)[0]>.999 and at(car,"scale",p.FILLED+p.care.REPAIR+service.DONE)[0]>.999
        # The crawler's working position for the exchange is clear of the propane tanks and the gas line.
        spot=zup(at(car,"translation",p.FILLED+p.care.REPAIR+service.DOWN[1]))
        apart=abs((math.atan2(spot[1],spot[0])-p.fuel.BEARING+math.pi)%(2*math.pi)-math.pi)
        assert apart*fr.TRACK_R>p.fuel.COUNT*p.fuel.PITCH/2+fr.WIDTH,"the cooler service is too close to the tank farm"
    # The boom lift is beside each frame end, with its crew at the working rows while the spools are made up.
    basket=ids["Boom lift | work basket"];chassis=ids["Boom lift | chassis"]
    assert sum(1 for n in ids if re.fullmatch(r"Boom lift \| fitter \d",n))==p.cfg.SITE["workers_per_basket"]
    for i,k in enumerate(fr.ORDER):
        a,b,c,dd,e,r,g,end=fr.times(i)
        for f in (e+3,(e+g)//2,g-2):
            pos=zup(at(basket,"translation",f));theta=fr.BEARINGS[k]
            local=np.array([pos[0]*math.cos(theta)+pos[1]*math.sin(theta),-pos[0]*math.sin(theta)+pos[1]*math.cos(theta)])
            assert fr.BACK<local[0]<fr.BACK+fr.DEPTH and fr.WIDTH/2+.3<fr.side(i)*local[1]<fr.WIDTH/2+2
            assert fr.base(k)<pos[2]<fr.base(k)+fr.HEIGHT
        ground=zup(at(chassis,"translation",(e+g)//2))
        assert abs(math.hypot(ground[0],ground[1])-fr.LIFT_R)<.001 and abs(ground[2])<1e-6
    if not p.film.SHORT:exchange(p,ids,parents,at,zup,points,car,hook)
    print(f"{fr.N} cooler frames carry {p.cfg.COOLERS} dry coolers and pumps on {len(fr.TIERS)} tiers, to RL {max(fr.TIERS)+fr.HEIGHT:g} m.")
    print(f"{extras['castInFrameAnchors']} anchors and {extras['castInCoolerConduits']} conduits are cast before their pours. "
          "The crawler and boom lift reach every frame.")


if __name__=="__main__":check(sys.argv[1])
