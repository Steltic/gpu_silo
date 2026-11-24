"""Bake the 24 fps technical short from every second source frame for native Blender rendering."""
import argparse
import json
import os
from pathlib import Path
os.environ["GPU_SILO_FILM"]="short"
import numpy as np
from . import pod_scene as p, short_reels, technical_assets, technical_shaft, technical_traffic


def prepare(out):
    out.mkdir(parents=True,exist_ok=True)
    scene=p.build()
    def node(name,mesh,group,parent=-1,angle=0.,t=(0.,0.,0.),tracks=None):
        scene.node(name,mesh,group,angle,t,tracks)
        scene.nodes[-1]["parent"]=parent
        return len(scene.nodes)-1
    technical_assets.enhance(scene)
    technical_shaft.install(scene,p,node)
    traffic=technical_traffic.schedule(scene,node)
    (out/"traffic.json").write_text(json.dumps(traffic,indent=2),encoding="utf-8")
    print("Complete truck journeys:",sum("omitted" not in r for r in traffic),"/",len(traffic),flush=True)
    frames=np.arange(0,p.FRAMES,2)
    count=len(scene.nodes)
    pose=np.empty((count,len(frames),7),np.float32)
    eye=np.array([scene.camera[f]["eye"] for f in frames])
    target=np.array([scene.camera[f]["target"] for f in frames])
    physical=pose.copy()
    inside=(frames>=p.PORTAL_VIEW+17)&(frames<p.RESTORE)
    wall={"Cast-in conduits","Door blockout","Cooler embeds","Cooler conduits","Frame anchors"}
    installed={"Dry coolers","Cooler frames","Cooler screens","Pump units","Discharge separators","Frame pipework"}
    metas=[]
    for i,n in enumerate(scene.nodes):
        pos=technical_traffic.sample(n,"translation",frames)
        scale=technical_traffic.sample(n,"scale",frames).copy()
        yaw=technical_traffic.sample(n,"yaw",frames)[:,0]
        parent=n.get("parent",-1)
        if parent>=0:
            par=physical[parent]
            local=pos*par[:,3:6]
            cs,ss=np.cos(par[:,6]),np.sin(par[:,6])
            pos=par[:,:3]+np.stack((cs*local[:,0]-ss*local[:,1],ss*local[:,0]+cs*local[:,1],local[:,2]),axis=1)
            scale*=par[:,3:6];yaw=yaw+par[:,6]
        physical[i]=np.column_stack((pos,scale,yaw))
        if n["group"] in wall:scale[inside]=0
        if n["group"] in installed and parent>=0:
            bearing=physical[parent,:,6]
            facing=eye[:,0]*np.cos(bearing)+eye[:,1]*np.sin(bearing)>.15*np.hypot(eye[:,0],eye[:,1])
            seated=np.hypot(physical[parent,:,0],physical[parent,:,1])<p.s.RO+3.4
            scale[inside&facing&seated]=0
        pose[i]=np.column_stack((pos,scale,yaw))
        metas.append({k:n[k] for k in ("name","group","mesh","extras") if k in n})
    del physical
    meshes=[]
    for i,m in enumerate(scene.meshes):
        if not m.tris:continue
        pts=np.array([row[:3] for row in m.tris],dtype=np.float32)
        v,indices=np.unique(np.round(pts.reshape(-1,3),5),axis=0,return_inverse=True)
        faces=indices.reshape(-1,3)
        nonzero=(faces[:,0]!=faces[:,1]) & (faces[:,1]!=faces[:,2]) & (faces[:,0]!=faces[:,2])
        f=faces[nonzero].astype(np.int32)
        colour=np.array([row[3] for row in m.tris],dtype=np.uint8)[nonzero]
        np.savez(out/f"mesh_{i}.npz",v=v,f=f,c=colour)
        meshes.append({"id":i,"name":m.name,"mat":getattr(m,"material",0),"triangles":len(f)})
    np.save(out/"poses.npy",pose)
    np.savez(out/"camera.npz",eye=eye,target=target,fov=[scene.camera[f]["fov"] for f in frames])
    from . import closing,clock
    ceil=lambda v:(v+1)//2
    manifest=dict(sourceFrames=p.FRAMES,frames=len(frames),fps=p.FPS,sourceStep=2,ifcSHA256=short_reels.SOURCE,
                  studio=ceil(p.FILLED+clock.DETAIL_START),roof=ceil(p.FILLED+clock.SOLID_BEGIN),
                  office=ceil(p.FILLED+closing.FUEL_END),drawing=ceil(p.FILLED+closing.PLAN),
                  meshes=meshes,nodes=metas)
    (out/"scene.json").write_text(json.dumps(manifest,ensure_ascii=False),encoding="utf-8")
    print(f"Prepared {len(frames)} frames, {len(meshes)} meshes, {count} timed nodes.",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out",type=Path)
    prepare(parser.parse_args().out)
