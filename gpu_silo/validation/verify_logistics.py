"""Check the trucks, the receiving dock, the cooler deliveries, the tankers and the jumpform crew in the GLB."""
import math
import sys

import numpy as np
from .. import cargo
from .. import clock
from .. import cooler_frames as fr
from .. import fuel
from .. import jumpform
from .. import layering
from .. import logistics
from .. import pod_scene as p
from .. import silo_model as s
from .. import site
from .. import traffic
from .. import yard
from .verify_motion import open_glb


def check(path):
    doc,access=open_glb(path);nodes=doc["nodes"];ids={}
    for i,node in enumerate(nodes):ids.setdefault(node["name"],i)
    parents={j:i for i,n in enumerate(nodes) for j in n.get("children",[])}
    anim=doc["animations"][0]
    curves={(ch["target"]["node"],ch["target"]["path"]):anim["samplers"][ch["sampler"]] for ch in anim["channels"]}
    def at(i,key,frame):
        default={"rotation":[0,0,0,1],"scale":[1,1,1],"translation":[0,0,0]}
        if (i,key) not in curves:return np.array(nodes[i].get(key,default[key]))
        sm=curves[i,key];times=access[sm["input"]][:,0];vals=access[sm["output"]]
        return np.array([np.interp(np.float32(frame/p.FPS),times,col) for col in vals.T])
    def zup(tr):return np.array([tr[0],-tr[2],tr[1]])
    def world(i,f):
        local=zup(at(i,"translation",f));q=at(i,"rotation",f);angle=2*math.atan2(q[1],q[3])
        if i not in parents:return local,angle
        pos,yaw=world(parents[i],f)
        return pos+yard.coords(yaw,local),yaw+angle
    def shown(i,f):
        return at(i,"scale",f).min()>.5 and (i not in parents or shown(parents[i],f))
    def dock(point):
        c,d=math.cos(p.ENTRY),math.sin(p.ENTRY)
        return np.array([point[0]*c+point[1]*d,-point[0]*d+point[1]*c,point[2]])
    lg=logistics.C;per=lg["pods_per_truck"]
    table=yard.plan(p)
    visits=table["visits"]
    assert len(visits)==lg["pod_trucks"]==math.ceil(p.TOTAL/per)
    assert lg["pod_load_t"]<=p.cfg.PROJECT["logistics"]["flatbed"]["payload_t"] and (per+1)*lg["pod_t"]>p.cfg.PROJECT["logistics"]["flatbed"]["payload_t"] or per==lg["pods_by_space"]
    lift=ids["Dock | lifting spreader"]
    centre=cargo.INNER+p.cfg.length(1)/2
    handoff=[]
    for k,visit in enumerate(visits):
        trailer=ids[f"Pod truck {k+1:02} | trailer"]
        assert len(visit["pods"])<=per
        for index in visit["pods"]:
            level,bay=p.LEVELS-index//p.BAYS,index%p.BAYS+1
            store=ids[f"Pod {index+1:03} | L{level:02} B{bay:02}"]
            riding=ids[f"Pod {index+1:03} | on its truck"];carried=ids[f"Pod {index+1:03} | on the gantry and rail"]
            assert parents[riding]==trailer
            mesh=nodes[store].get("mesh",nodes[riding]["mesh"])
            assert nodes[riding]["mesh"]==nodes[carried]["mesh"]==mesh
            # The pod leaves the truck where the gantry picks it up, with the truck square in its lane.
            lifted=next(f for f in range(yard.INSERT_AT,p.FRAMES) if at(riding,"scale",f).max()<.5)
            assert shown(carried,lifted) and not shown(carried,lifted-1) and shown(riding,lifted-1)
            on_truck,heading=world(riding,lifted);on_hook,_=world(carried,lifted)
            np.testing.assert_allclose(on_truck[:2],on_hook[:2],atol=.25)
            assert -1e-3<=on_hook[2]-on_truck[2]<=yard.HOVER+1e-3
            spot=dock(on_truck)
            assert abs(spot[1]-yard.LANE_Y[visit["lane"]])<.75 and abs(math.sin(heading-p.ENTRY))<.03 and abs(spot[2]-yard.DECK)<1e-3
            assert yard.RUNWAY[0]<spot[0]+cargo.INNER and spot[0]+cargo.INNER+p.cfg.length(1)<yard.RUNWAY[1]
            # The spreader stays on the pod through the lift, and the pod ends on the rail at the opening.
            landed=next(f for f in range(lifted,p.FRAMES) if at(carried,"translation",f)[1]<1e-4 and abs(zup(at(carried,"translation",f))[1])<1e-3)
            for f in range(lifted+1,landed):
                rig=zup(at(lift,"translation",f));pod=zup(at(carried,"translation",f))
                np.testing.assert_allclose(rig-pod,[centre,0,cargo.FRAME_HEIGHT],atol=.25)
            entry=p.STARTS[index]
            assert landed<=entry-1 and at(carried,"scale",entry-1).min()>.99 and at(carried,"scale",entry).max()<.002
            # In the faster section a pod's start can fall between two film frames.
            assert at(store,"scale",entry-2).max()<.001 and at(store,"scale",entry-1).max()<.999 and at(store,"scale",entry).min()>.999
            np.testing.assert_allclose(zup(at(carried,"translation",entry-1)),[yard.RAIL_OFFSET,0,0],atol=.002)
            begins=p.SOURCE_STARTS[index] if index<2*p.BAYS else p.SPEED_FRAME+(p.SOURCE_STARTS[index]-p.SWITCH_SOURCE)/p.FAST_RATE
            pos,a=world(carried,entry-1);actual,b=world(store,begins)
            np.testing.assert_allclose(actual,pos,atol=.002)
            assert abs(math.sin(a-b))<.0001
            handoff.append(entry)
    # One truck at a time in each dock lane.
    trailers=[ids[f"Pod truck {k+1:02} | trailer"] for k in range(len(visits))]
    for f in range(yard.INSERT_AT,p.FILLED+40,3):
        busy={}
        for k,i in enumerate(trailers):
            if at(i,"scale",f).min()<.5:continue
            spot=dock(zup(at(i,"translation",f)))
            if 20<spot[0]<site.R_STOP-site.HALF:
                lane=min(range(yard.LANES),key=lambda j:abs(spot[1]-yard.LANE_Y[j]))
                if abs(spot[1]-yard.LANE_Y[lane])<1.5:
                    assert lane not in busy,(f,lane,busy[lane],k)
                    busy[lane]=k
    assert len({nodes[ids[f"L{level:02}B{bay:02} shaft root lock"]]["mesh"] for level in range(1,p.LEVELS+1) for bay in range(1,p.BAYS+1)})==1
    print(f"{len(visits)} trucks bring {p.TOTAL} pods, {per} each. Every pod is carried from its truck to the rail and handed to the hoist; the first at frames",handoff[:3])
    # Coolers: each one travels by truck, is lifted by the assist crane and ends in its own bay before the frame is picked.
    plan=traffic.cooler_times(p)
    for i in range(fr.N):
        k=fr.ORDER[i];label=f"Cooler frame {k+1:02}"
        steel_at,done=plan[i]
        root=ids[label+f" | {fr.ROWS} dry coolers, {fr.ROWS} pumps and steel"]
        assert at(root,"scale",steel_at).max()<.01 and at(root,"scale",steel_at+8+traffic.ERECT).min()>.999
        for row,when in enumerate(done):
            fixed=ids[label+f" | cooler {row+1}"];moving=ids[label+f" | dry cooler {row+1} on the crane"]
            assert when<fr.times(i)[0] and at(fixed,"scale",when-1).max()<.01 and at(fixed,"scale",when).min()>.999
            a,_=world(moving,when-.05);b,_=world(fixed,when)
            np.testing.assert_allclose(a,b,atol=.03)
            riding=ids[label+f" | dry cooler {row+1} on the truck"]
            truck,_=world(parents[riding],when-traffic.LIFT)
            assert abs(math.hypot(truck[0],truck[1])-site.R_STOP)<1.6
    crane=ids["Assist crane | carrier"]
    for f in range(p.C,fr.END,7):
        if at(crane,"scale",f).min()<.5:continue
        spot=zup(at(crane,"translation",f));radius=math.hypot(spot[0],spot[1])
        assert fr.LAY_R-1<radius<site.R_STOP+1.5 or radius>site.R_STOP,(f,radius)
    print(f"{p.cfg.COOLERS} coolers and {fr.N} loads of frame steel arrive by truck, and every cooler is in its frame before the crawler picks it.")
    # Water tankers stop in the bays of their own drive and never use the haul ring.
    tankers=traffic.water_visits(p)
    for n,(bay,a,b) in enumerate(tankers):
        i=ids[f"Water tanker {n+1:02} | trailer"]
        spot=zup(at(i,"translation",(a+b)//2))
        assert abs(spot[1]-site.WATER_Y[bay])<.2 and site.WATER_IN<spot[0]<site.WATER_OUT
        for f in range(max(0,a-200),min(p.FRAMES-1,b+200),9):
            if at(i,"scale",f).min()>.5:
                spot=zup(at(i,"translation",f));assert math.hypot(spot[0],spot[1])>site.R_RUN+site.LANE+12
    assert len(tankers)>=2*site.WATER_BAYS and lg["water_bays_needed"]<=site.WATER_BAYS
    # Truck mixers back up to the pump hopper while a lift is poured.
    for n,(bay,a,b) in enumerate(traffic.mixer_visits()):
        i=ids[f"Truck mixer {n+1:02}"]
        spot=dock(zup(at(i,"translation",(a+b)//2)));heading=2*math.atan2(at(i,"rotation",(a+b)//2)[1],at(i,"rotation",(a+b)//2)[3])
        assert abs(abs(spot[1])-traffic.MIXER_BAY_Y)<.1 and abs(spot[0]-traffic.MIXER_REAR-traffic.HOPPER_X-.3)<.3 and abs(math.sin(heading-p.ENTRY))<.03
    assert lg["lift_trucks"]*s.COUNT==lg["wall_trucks"]
    # The jumpform crew rides the forms and matches the listed crew.
    actors=[i for i,n in enumerate(nodes) if n["name"].startswith("Jumpform crew | ") and n["name"].count("|")==1]
    assert len(actors)==lg["crew"]==sum(count for _,count in p.cfg.PROJECT["jumpform"]["crew"])
    mid=s.INTRO+s.SLOW_CYCLE+4*s.FAST_CYCLE+5
    k=s.sequence(mid)[0]
    riders=[i for i in actors if i in parents and nodes[parents[i]]["name"]=="Jumpform | climbing assembly"]
    assert len(riders)==lg["crew"]-1
    for i in riders:
        height=world(i,mid)[0][2]-k*s.LIFT
        assert min(abs(height-deck) for deck in (jumpform.MAIN,jumpform.POUR))<.01
    # Fuel: every tank comes in on a truck and the transports use the lay-by.
    for j in range(fuel.COUNT):
        assert ids[f"Propane tank {j+1:02} | on its trailer"] and ids[f"Propane tank {j+1:02} | delivery | trailer"]
    for n,(bay,a,b) in enumerate(fuel.transport_visits()):
        i=ids[f"Propane transport {n+1:02} | trailer"]
        spot=zup(at(i,"translation",p.FILLED+(a+b)//2))
        assert abs(math.hypot(spot[0],spot[1])-site.LAYBY_R)<.6
    print(f"{len(tankers)} water tankers, {len(traffic.mixer_visits())} truck mixers, {fuel.COUNT+1} tank deliveries and {fuel.TRANSPORTS} propane transports are shown. The lift crew of {lg['crew']} rides the forms.")
    print("Every berth has a shaft root lock.")
    # Layered store: a pair of pipes for every bay and every cooler frame, a cover and an overflow, all in place when the fill begins.
    layering.check()
    fill=layering.start(p.liquid_level(f) for f in range(p.FRAMES))
    pipes=[i for i,n in enumerate(nodes) if n["name"].endswith("| store pipes")]
    assert len(pipes)==p.BAYS+fr.N
    for i in pipes+[ids["Store cover | sealed deck"],ids["Store overflow | standpipe"]]:
        assert not shown(i,max(0,fill-2)) and shown(i,fill) and shown(i,p.FRAMES-1), nodes[i]["name"]
    print(f"{len(pipes)} pairs of store pipes, the cover and the overflow are in place when the fill begins. Cold fill to {layering.COLD_FILL:.2f} m, overflow at {layering.OVERFLOW_Z:.2f} m.")


if __name__=="__main__":check(sys.argv[1])
