"""Verify the delivered 2× frame clock, carrier poses and vehicle geometry from the baked scene."""
import argparse
import json
import math
import struct
from pathlib import Path
import numpy as np
from .. import technical_traffic as traffic


def check(bake,model=None):
    info=json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    q=np.load(bake/"poses.npy",mmap_mode="r")
    if (info["sourceFrames"],info["sourceStep"],info["fps"],q.shape[1])!=(6289,2,24,3145):
        raise ValueError("The fixed reference cut has changed")
    nodes=info["nodes"];studies=info["studio"]
    def find(name):return next(i for i,n in enumerate(nodes) if n["name"]==name)
    shaft=q[find("IFC detail | SHAFT"),studies:studies+144]
    holder=q[find("IFC carrier | POD-06-01-FRAME"),studies:studies+144]
    if not np.allclose(shaft,shaft[0],atol=1.e-6):raise ValueError("Fixed IFC shaft moves")
    if not np.allclose(holder[:,:3],shaft[:,:3],atol=.001):raise ValueError("Holder rotates about the wrong origin")
    if not np.allclose(holder[[0,87,143],6],[0,math.pi/4,math.pi/2],atol=.0001):
        raise ValueError("Two 45-degree indexes were not completed")
    before=q[:,119,3:6];after=q[:,120,3:6]
    wall=[i for i,n in enumerate(nodes) if n["group"] in ("Outer concrete wall","Inner concrete wall")]
    if not np.any(np.abs(before[wall]-after[wall])>.9):raise ValueError("Missing wall closure at 5 s")
    # This replay reads the final frame bake, separately from the source-path reservation stage.
    bounds={};vehicles=[]
    def bodies(i):
        n=nodes[i]
        if n["mesh"] not in bounds:
            with np.load(bake/f"mesh_{n['mesh']}.npz") as mesh:
                xy=mesh["v"][:,:2];bounds[n["mesh"]]=(xy.min(axis=0),xy.max(axis=0))
        lo,hi=bounds[n["mesh"]];mid=(lo+hi)*.5
        v=q[i];u=np.column_stack((np.cos(v[:,6]),np.sin(v[:,6])));w=np.column_stack((-u[:,1],u[:,0]))
        xy=v[:,:2]+mid[0]*u+mid[1]*w
        data=np.column_stack((xy,u,w,np.broadcast_to((hi-lo)*.5,(len(v),2))))
        return data,np.all(abs(v[:,3:6])>.00001,axis=1)
    for i,n in enumerate(nodes):
        if n["name"].endswith(" | tractor"):
            if not nodes[i+1]["name"].endswith(" | trailer"):raise ValueError(n["name"])
            vehicle=[bodies(i),bodies(i+1)]
        elif n["name"].startswith("Truck mixer "):vehicle=[bodies(i)]
        else:continue
        if vehicle[0][1].any():vehicles.append((n["name"],vehicle))
    for i,(name,left) in enumerate(vehicles):
        for other,right in vehicles[i+1:]:
            for a,on in left:
                for b,there in right:
                    frames=on&there
                    if frames.any() and traffic.collides(a[frames],b[frames]):
                        raise ValueError(f"Delivered truck body collision: {name} / {other}")
    if model:
        with model.open("rb") as f:
            header=f.read(20)
            magic,version,size,n,fmt=struct.unpack("<4sIII4s",header)
            if (magic,version,size,fmt)!=(b"glTF",2,model.stat().st_size,b"JSON"):raise ValueError("Invalid GLB header")
            gl=json.loads(f.read(n))
        camera=gl["cameras"][0]["perspective"]
        if abs(camera["aspectRatio"]-16/9)>1.e-6:raise ValueError("Wrong GLB camera aspect")
        products=[n for n in gl["nodes"] if n["name"].startswith("IFC carrier | ")]
        if len(products)!=2 or any(len(n["extras"]["ifcGlobalId"])!=22 for n in products):raise ValueError("Lost IFC carrier identifiers")
        duration=max(gl["accessors"][s["input"]]["max"][0] for a in gl["animations"] for s in a["samplers"])
        if abs(duration-3144/24)>1.e-4:raise ValueError("GLB timing differs from picture samples")
    print(f"Verified {len(vehicles)} complete journeys across {q.shape[1]} delivered frames, fixed shaft, two indexes and 5 s wall closure.")


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("bake",type=Path)
    cli.add_argument("--model",type=Path)
    a=cli.parse_args();check(a.bake,a.model)
