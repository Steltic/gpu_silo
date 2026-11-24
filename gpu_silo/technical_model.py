"""Export the baked 2× short, including the moving IFC carrier, for a glTF viewer."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from . import silo_model as s


class BakedMesh:
    def __init__(self,bake,meta):
        self.path=bake/f"mesh_{meta['id']}.npz"
        self.name=meta["name"]
        self.material=meta["mat"]

    @property
    def tris(self):
        with np.load(self.path) as data:
            vertices=data["v"].tolist()
            for (a,b,c),col in zip(data["f"],data["c"].tolist()):
                yield vertices[a],vertices[b],vertices[c],col


def tracks(values):
    if len(values)<2 or np.all(values==values[0]):return [(0,values[0].tolist())]
    changes=np.any(np.abs(np.diff(values.astype(np.float64),n=2,axis=0))>1.e-6,axis=1)
    ids=np.r_[0,np.where(changes)[0]+1,len(values)-1]
    return [(int(i),values[i].tolist()) for i in ids]


def export(bake,path):
    m=json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    pose=np.load(bake/"poses.npy",mmap_mode="r")
    remap={x["id"]:i for i,x in enumerate(m["meshes"])}
    scene=SimpleNamespace(nodes=[],meshes=[BakedMesh(bake,x) for x in m["meshes"]],short_presentation=True,
                          animation_title="Technical short | construction, four IFC studies and exterior orbit")
    scene.project_info={"film":"Technical short","constructionFullWalls_s":5.,"sourceFrameStep":2,
                        "deliveryFrames":m["frames"],"shortFilmIfcSourceSHA256":m["ifcSHA256"],
                        "note":"Every second 24 fps source frame. The plan and section are film-composite graphics."}
    for i,n in enumerate(m["nodes"]):
        if n["mesh"]<0:continue
        q=pose[i]
        if not np.any(np.all(np.abs(q[:,3:6])>1.e-6,axis=1)):continue
        row=dict(name=n["name"],mesh=remap[n["mesh"]],group=n["group"],angle=float(q[0,6]),translation=q[0,:3].tolist(),
                 tracks={"translation":tracks(q[:,:3]),"scale":tracks(q[:,3:6]),"yaw":tracks(q[:,6:7])})
        if "extras" in n:row["extras"]=n["extras"]
        scene.nodes.append(row)
    with np.load(bake/"camera.npz") as camera:
        eye,target=camera["eye"],camera["target"]
        for f in range(m["studio"]+432,m["roof"]):
            u=(f-m["studio"]-432)/144
            k=min(1.,max(0.,(u-.08)/.44));k=k*k*(3-2*k)
            offset=eye[f]-target[f];target[f]+=np.array((-1.,-1.2,1.8))*k
            eye[f]=target[f]+offset*(1-.4*k)
        scene.camera=[dict(eye=e.tolist(),target=t.tolist(),fov=float(f)) for e,t,f in zip(eye,target,camera["fov"])]
    s.glb_file(scene,path,aspect_ratio=16/9)
    print(path,flush=True)


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("bake",type=Path);cli.add_argument("output",type=Path)
    args=cli.parse_args();export(args.bake,args.output)
