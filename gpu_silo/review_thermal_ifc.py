"""Cut the issued IFC along a vertical diameter and retain the back half for the thermal film."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import numpy as np
import ifcopenshell
import ifcopenshell.geom as geom
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union, triangulate
from . import short_reels, layering as layer, services, cooler_frames

BEARING = math.radians(-55)
C,S=math.cos(BEARING),math.sin(BEARING)
AXES=np.array(((C,-S,0),(S,C,0),(0,0,1)))
def rotated(p):return (np.array(p) @ AXES).tolist()


def classify(tag):
    if re.fullmatch(r"(?:IW|OW)-\d\d",tag):return "wall"
    if tag=="RAFT":return "raft"
    if tag=="SHAFT" or tag.startswith("CAGE-"):return "steel"
    if re.fullmatch(r"POD-\d\d-\d\d-R[1-4]",tag):return "rack"
    if tag.startswith("POD-") and tag.endswith("-CDU"):return "cdu"
    if tag.startswith("POD-") and tag.endswith("-P"):return "pump"
    if tag.startswith("POD-") and tag.endswith("-FRAME"):return "steel"
    if tag.startswith("Store pipes/"):return "risers"
    if tag.startswith("Dry coolers/"):return "cooler"
    if tag.startswith("Cooler frames/"):return "steel"
    if tag.startswith("Pump units/"):return "pump"
    if tag.startswith(("Cooler conduits/","Frame pipework/","Cast-in conduits/")):return "pipe"
    if tag.startswith("Store cover/"):return "cover"
    if tag=="LID" or tag.startswith(("Turbines/Rail girder","Turbines/Open ring","Power modules/Turbine set")):return "plant"
    return None


def bisect(verts, faces, do_cap):
    tri=verts[faces]
    inside=tri[:,:,1]>=-1.e-7
    blocks=[tri[inside.all(axis=1)]]
    cuts=[]; output=[]
    for points in tri[inside.any(axis=1)&~inside.all(axis=1)]:
        poly=[]; edge=[]
        for a,b in zip(points,np.roll(points,-1,axis=0)):
            ina,inb=a[1]>=-1.e-7,b[1]>=-1.e-7
            if ina:poly.append(a)
            if ina!=inb:
                hit=a+(b-a)*(-a[1]/(b[1]-a[1])); hit[1]=0
                poly.append(hit);edge.append(tuple(np.round(hit[[0,2]],5)))
        for j in range(1,len(poly)-1):output.append((poly[0],poly[j],poly[j+1]))
        if do_cap and len(edge)==2 and edge[0]!=edge[1]:cuts.append(LineString(edge))
    if output:blocks.append(np.array(output))
    faces3=np.concatenate(blocks)
    if not len(faces3):return None
    caps=[]
    if cuts:
        for poly in polygonize(unary_union(cuts)):
            if poly.area<.00005:continue
            for t in triangulate(poly):
                if poly.covers(t.representative_point()):
                    caps.append([(x,0,z) for x,z in list(t.exterior.coords)[:3]])
    cap_offset=len(faces3)
    if caps:faces3=np.concatenate([faces3,np.array(caps)])
    v,inv=np.unique(np.round(faces3.reshape(-1,3),5),axis=0,return_inverse=True)
    f=inv.reshape(-1,3)
    return v.astype("f4"),f.astype("i4"),cap_offset


def export(ifc,out):
    digest=sha256(ifc.read_bytes()).hexdigest()
    if digest!=short_reels.SOURCE:raise ValueError("Use the issued Revision K IFC for this film.")
    out.mkdir(parents=True,exist_ok=True)
    model=ifcopenshell.open(str(ifc));settings=geom.settings();settings.set("use-world-coords",True)
    rows=[]; names={}
    (cr,zr),(ch,zh)=layer.cooler_points(0)
    def polar(r,a,z=0):return np.array([r*math.cos(a),r*math.sin(a),z])
    rot=lambda a: np.array(((math.cos(a),-math.sin(a),0),(math.sin(a),math.cos(a),0),(0,0,1)))
    az=services.PORT_ANGLES[0]
    centres={key:rotated(rot(az) @ np.array((layer.POD_R,side*layer.POD_Y,0)))
             for key,side in (("podCold",-1),("podWarm",1))}
    for key,turn in (("coolerCold",cr),("coolerWarm",ch)):
        centres[key]=rotated(polar(layer.COOLER_R,cooler_frames.THETA[0]+turn))
    rz=services.port_height(4)+.015
    for e in model.by_type("IfcElement"):
        tag=e.Tag or ""; role=classify(tag)
        if not role or not e.Representation:continue
        shape=geom.create_shape(settings,e);v=np.asarray(shape.geometry.verts,dtype=float).reshape(-1,3)@AXES
        f=np.asarray(shape.geometry.faces,dtype=np.int32).reshape(-1,3)
        if not len(v) or np.max(v[:,1])<0:continue
        mesh=bisect(v,f,role in ("wall","raft","cover","plant","steel"))
        if mesh is None:continue
        v,f,cap=mesh; idx=len(rows)
        special=None
        if tag=="Store pipes/Bay 01 | store pipes":special="pod"
        if tag=="Store pipes/Cooler frame 01 | store pipes":special="cooler"
        side=np.zeros(len(f),dtype=np.uint8)
        if special:
            pc=np.array(centres[special+"Cold"])[:2];pw=np.array(centres[special+"Warm"])[:2]
            centres3=v[f].mean(axis=1);xy=centres3[:,:2]
            side=(np.linalg.norm(xy-pw,axis=1)<np.linalg.norm(xy-pc,axis=1)).astype(np.uint8)
            # The two axes are close enough for half of a wide mouth plate to lie
            # nearer the other header. Only one pipe reaches each end elevation.
            side[centres3[:,2]>=layer.TOP_MOUTH-.015]=1
            side[centres3[:,2]<=layer.FLOOR_MOUTH+.015]=0
        np.savez_compressed(out/f"e{idx:04}.npz",v=v,f=f,side=side)
        rows.append(dict(i=idx,tag=tag,guid=e.GlobalId,kind=role,cap=cap,special=special))
        if tag in ("POD-04-01-CDU","POD-04-01-R4","Dry coolers/Cooler frame 01 | cooler 2","Pump units/Cooler frame 01 | pump unit 2"):
            names[tag]=(v.min(0)*.5+v.max(0)*.5).tolist()
    # Points at the wall penetration and physical ports, in the cut coordinate system.
    connections={"rackZ":rz,"coolerColdZ":zr[1],"coolerWarmZ":zh[1]}
    for name,sign in (("podCold",-1),("podWarm",1)):
        connections[name]=rotated(rot(az) @ np.array((services.TANK_END,sign*services.PORT_OFFSET,rz)))
    for name,turn,zz in (("coolerCold",cr,zr[1]),("coolerWarm",ch,zh[1])):
        connections[name]=rotated(polar(layer.s.RI_OUTER,cooler_frames.THETA[0]+turn,zz))
    if not all(p[1]>layer.PLATE for p in centres.values()):raise ValueError("A featured header crosses the selected cut plane")
    data=dict(sha256=digest,cutBearingDeg=math.degrees(BEARING),products=rows,axes=centres,connections=connections,equipment=names,
              low=layer.FLOOR_MOUTH,high=layer.TOP_MOUTH,liquidTop=layer.cfg.LIQUID_TOP,
              inner=layer.s.RO_INNER,outer=layer.s.RI_OUTER,diffuser=layer.PLATE*2,gap=layer.GAP,
              diameter=layer.RADIUS*2,podPairs=layer.cfg.BAYS,coolerPairs=cooler_frames.N)
    (out/"geometry.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    print("Retained",len(rows),"clipped IFC products. Their tags and GUIDs accompany the mesh data.",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("ifc",type=Path);p.add_argument("out",type=Path)
    a=p.parse_args();export(a.ifc,a.out)
