"""Register an issued pod frame and lock to the fixed shaft in the film's IFC study."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from . import short_reels as reels, silo_model as s

CACHE = Path(__file__).with_name("technical_holder.json.gz")
TAGS = ("POD-06-01-FRAME", "Steel shoes/L06B01 shaft root lock")


def extract(path):
    import ifcopenshell
    import ifcopenshell.geom as geom
    import ifcopenshell.util.placement as placement
    if hashlib.sha256(path.read_bytes()).hexdigest() != reels.SOURCE:
        raise ValueError("Use the issued revision K IFC")
    model=ifcopenshell.open(str(path))
    elements={e.Tag:e for e in model.by_type("IfcElement") if e.Tag and e.Representation}
    settings=geom.settings()
    settings.set("use-world-coords",True)
    mat=placement.get_local_placement(elements["SHAFT"].ObjectPlacement)
    yaw=math.atan2(mat[1,0],mat[0,0])
    axes=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1]])
    def mesh(tag):
        shape=geom.create_shape(settings,elements[tag])
        return np.array(shape.geometry.verts).reshape(-1,3) @ axes, np.array(shape.geometry.faces).reshape(-1,3)
    # Recover the exact assembly datum from the same shaft vertices in the existing offline excerpt.
    cached=json.loads(gzip.decompress(reels.CACHE.read_bytes()))["groups"][0][0]
    datum=mesh("SHAFT")[0].min(axis=0)-np.array(cached["mm"]).min(axis=0)*.001
    products=[]
    for tag in TAGS:
        v,f=mesh(tag)
        products.append(dict(tag=tag,guid=elements[tag].GlobalId,mm=np.rint((v-datum)*1000).astype(int).tolist(),faces=f.tolist()))
    CACHE.write_bytes(gzip.compress(json.dumps({"sha256":reels.SOURCE,"products":products},separators=(",",":")).encode(),mtime=0))


def install(scene,p,node):
    from . import connection, cargo
    data=json.loads(gzip.decompress(CACHE.read_bytes()))
    if data["sha256"]!=reels.SOURCE:raise ValueError("Incorrect IFC for holder")
    parent=next(i for i,n in enumerate(scene.nodes) if n["name"]=="IFC study | The steel shaft")
    start=p.FILLED+p.clock.DETAIL_START
    stop=start+p.clock.DETAIL_LENGTH
    u=np.linspace(0,1,49)
    # Positive index matches the mechanism's operating sense. Two discrete bay indexes with a dwell.
    angles=[(start+28+3*i,(math.radians(45)*float(t*t*(3-2*t)),)) for i,t in enumerate(u)]
    angles.extend((start+180+1.5*i,(math.radians(45)*(1+float(t*t*(3-2*t))),)) for i,t in enumerate(u))
    rot=node("Driven carrier | two separate 45-degree indexes",-1,"IFC studio",parent,tracks={"yaw":angles})
    for num,product in enumerate(data["products"]):
        mesh=s.Mesh(product["tag"]);mesh.material=3
        v=np.array(product["mm"])*.001
        for a,b,c in product["faces"]:mesh.tris.append((tuple(v[a]),tuple(v[b]),tuple(v[c]),s.rgb("cf8a47" if num==0 else "849e9e")))
        idx=node("IFC carrier | "+product["tag"],scene.mesh(mesh),"IFC studio",rot)
        scene.nodes[idx]["extras"]={"ifcGlobalId":product["guid"],"ifcTag":product["tag"]}
        if num==0:
            bottom=float(v.min(axis=0)[2]);centre_z=float((v.min(axis=0)[2]+v.max(axis=0)[2])*.5)
    drum=connection.HUB["drum_diameter_m"]/2
    mesh=s.Mesh("Driven hub | barrel, flanges and gear ring");mesh.material=3
    top=bottom+cargo.FRAME_HEIGHT-.12
    p.annulus(mesh,drum-connection.HUB["drum_wall_mm"]/1000,drum,bottom,top,"597a7c",n=64)
    for z in (bottom,top-.12):
        p.annulus(mesh,drum-.02,connection.R["hub_ring_radius_m"],z,z+.12,"bf914f",n=64)
    for j in range(64):
        a=j*math.tau/64
        s.bar(mesh,s.polar(.75,a,bottom+.061),s.polar(.82,a,bottom+.061),.035,"d0b179",.09)
    node(mesh.name,scene.mesh(mesh),"IFC studio",rot)
    for f in range(start,stop):
        t=f-start
        z=13.5+(centre_z-13.5)*s.step(12,99,t)
        dist=65.-40.*s.step(10,92,t)+4.*s.step(213,280,t)
        az=-69+16*s.step(0,270,t)
        x=1.4*s.step(10,99,t)
        camera=p.camera((reels.STUDIO[0]+x,reels.STUDIO[1],z),az,17+5*s.step(10,99,t),dist)
        scene.camera[f]=camera


if __name__=="__main__":
    import sys
    extract(Path(sys.argv[1]))
