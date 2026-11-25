"""Extract the full-rate closing camera and the revised physical facade from the short."""
import argparse
import json
import os
from pathlib import Path
os.environ["GPU_SILO_FILM"] = "short"
import numpy as np
from . import pod_scene as p, short_art


def prepare(bake, destination):
    destination.mkdir(parents=True, exist_ok=True)
    meta = json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    scene = p.build()
    start, stop = meta["roof"]*2, meta["drawing"]*2
    path = scene.camera[start:stop]
    np.savez(destination/"orbit-camera.npz", eye=[v["eye"] for v in path],
             target=[v["target"] for v in path], fov=[v["fov"] for v in path], source=np.arange(start,stop))
    assert len(path)==540
    by_name = {n["name"]: n for n in scene.nodes}
    display = scene.meshes[by_name["Control room | displays and task lighting"]["mesh"]]
    facade = scene.meshes[by_name["Control office | walls"]["mesh"]]
    ink = tuple(short_art.s.rgb("d9e8dd"))
    facade.tris.extend(t for t in display.tris if tuple(t[3])==ink)
    from . import silo_model, site
    landscape = scene.meshes[by_name["Field boundaries, farm sheds and trees"]["mesh"]]
    count = len(silo_model.build_land()[1].tris)
    def keep_furniture(tri):
        x,y,_=np.mean(tri[:3],axis=0)
        return not (site.LEG_X-10.1<x<site.LEG_X-5 and site.PUBLIC_Y-14<y<site.PUBLIC_Y-8.3)
    landscape.tris = [t for t in landscape.tris[count:] if keep_furniture(t)]
    for mesh, name in ((facade,"facade"),(landscape,"farm-furniture")):
        vertices = np.array([tri[:3] for tri in mesh.tris], dtype=np.float32)
        colours = np.array([tri[3] for tri in mesh.tris], dtype=np.uint8)
        v, ix = np.unique(np.round(vertices.reshape(-1,3),5),axis=0,return_inverse=True)
        faces = ix.reshape(-1,3)
        keep = np.all(faces!=np.roll(faces,1,axis=1),axis=1)
        np.savez(destination/f"{name}.npz",v=v,f=faces[keep].astype(np.int32),c=colours[keep])
    print(f"Full-rate source frames {start}–{stop-1}, {len(path)/24} s. Physical sign STELTICAI.COM.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bake",type=Path); parser.add_argument("out",type=Path)
    a=parser.parse_args()
    prepare(a.bake,a.out)
