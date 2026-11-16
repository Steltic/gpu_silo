"""Check the actual delivery, lifting and rail handoffs in the GLB."""
import math
import sys

import numpy as np
from .. import cargo
from .. import pod_scene as p
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
    start=yard.INSERT_AT
    truck=ids["Terminal | initial three-pod delivery truck"];lift=ids["Terminal | lifting spreader"]
    handoff=[]
    for i,offset in enumerate(yard.LOAD_OFFSETS):
        j=ids[f"Terminal | pod {i+1:03} on truck, crane and rail"]
        store=ids[f"Pod {i+1:03} | L{p.LEVELS:02} B{i+1:02}"]
        assert nodes[j]["mesh"]==nodes[store]["mesh"]
        for t in (0,12,23,47,54):
            deck=zup(at(truck,"translation",start+t));pod=zup(at(j,"translation",start+t))
            np.testing.assert_allclose(pod-deck,[offset-yard.LOAD_OFFSETS[0]-p.INNER,0,yard.DECK],atol=.0001)
        for t in range(63+i*75,107+i*75):
            pod=zup(at(j,"translation",start+t));rig=zup(at(lift,"translation",start+t))
            np.testing.assert_allclose(rig-pod,[p.INNER+p.cfg.length(i+1)/2,0,cargo.FRAME_HEIGHT],atol=.0002)
        np.testing.assert_allclose(zup(at(j,"translation",start+107+i*75)),[offset,0,0],atol=.0001)
        entry=p.STARTS[i]
        assert at(j,"scale",entry-1).min()>.99 and at(j,"scale",entry).max()<.002
        assert at(store,"scale",entry-1).max()<.001 and at(store,"scale",entry).min()>.999
        pos,a=world(j,entry-1);actual,b=world(store,entry)
        np.testing.assert_allclose(actual,pos,atol=.0001)
        assert abs(math.sin(a-b))<.0001
        handoff.append(entry)
    assert len({nodes[ids[f"L{level:02}B{bay:02} shaft root lock"]]["mesh"] for level in range(1,p.LEVELS+1) for bay in range(1,p.BAYS+1)})==1
    print("Three actual pods share the flatbed, stay on the spreader between its two pickups and hand off to the intake at frames",handoff)
    print("Every berth has a shaft root lock.")


if __name__=="__main__":check(sys.argv[1])
