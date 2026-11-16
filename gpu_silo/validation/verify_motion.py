"""Check the encoded glTF transforms, portal, lift lanes, service couplings, liquid level and power modules."""
import json
import math
import re
import struct
import sys
from pathlib import Path

import numpy as np
from .. import pod_scene as p


def open_glb(path):
    raw=Path(path).read_bytes()
    assert struct.unpack_from("<4sII",raw)==(b"glTF",2,len(raw))
    n,tag=struct.unpack_from("<I4s",raw,12);assert tag==b"JSON"
    doc=json.loads(raw[20:20+n])
    ns,tag=struct.unpack_from("<I4s",raw,20+n)
    body=memoryview(raw)[28+n:]
    assert tag==b"BIN\0" and ns==len(body)==doc["buffers"][0]["byteLength"]
    acc=[]
    for a in doc["accessors"]:
        view=doc["bufferViews"][a["bufferView"]]
        off,length=view.get("byteOffset",0),view["byteLength"]
        assert off%4==0 and off+length<=ns
        values=np.frombuffer(body[off:off+length],dtype={5126:"<f4",5121:"u1"}[a["componentType"]])
        values=values.reshape(a["count"],{"SCALAR":1,"VEC3":3,"VEC4":4}[a["type"]])
        assert np.isfinite(values).all()
        acc.append(values)
    # Compare stable mesh keys while independently checking the exported viewer labels.
    for group in ("nodes","meshes"):
        for item in doc[group]:
            key=item.get("extras",{}).get("designKey")
            if key:
                assert item["name"]==p.cfg.display(key)
                item["name"]=key
    return doc,acc


def planar_overlap(a,b):
    for polygon in (a,b):
        for dx,dy in np.roll(polygon,-1,axis=0)-polygon:
            d=np.array([-dy,dx]);aa,bb=a@d,b@d
            if aa.max()<=bb.min()+1e-8 or bb.max()<=aa.min()+1e-8:return False
    return True


def main(path):
    doc,acc=open_glb(path)
    nodes=doc["nodes"];names={}
    for i,n in enumerate(nodes):names[n["name"]]=i
    props={};curves={};parents={j:i for i,n in enumerate(nodes) for j in n.get("children",[])}
    anim=doc["animations"][0]; keys=(np.arange(p.FRAMES,dtype=float)/p.FPS).astype(np.float32).astype(float)
    for ch in anim["channels"]:
        sample=anim["samplers"][ch["sampler"]]
        ix=ch["target"]["node"];pathkey=ch["target"]["path"]
        tt=acc[sample["input"]][:,0].astype(float);vv=acc[sample["output"]].astype(float)
        assert (np.diff(tt)>0).all() and tt[0]>=0,(nodes[ix]["name"],pathkey)
        if pathkey=="rotation":
            if "camera" in nodes[ix]["name"].lower(): continue
            assert np.allclose(np.linalg.norm(vv,axis=1),1,atol=.00001)
            vv=np.unwrap(2*np.arctan2(vv[:,1],vv[:,3]))[:,None]
        props[ix,pathkey]=np.stack([np.interp(keys,tt,col) for col in vv.T],axis=-1)
        curves[ix,pathkey]=tt,vv
    def get(ix,key,default):
        if (ix,key) in props: return props[ix,key]
        v=np.asarray(nodes[ix].get(key,default),dtype=float)
        if key=="rotation" and len(v)==4: v=np.asarray([2*math.atan2(v[1],v[3])])
        return np.broadcast_to(v,(p.FRAMES,len(v)))
    def points(i):
        if "mesh" not in nodes[i]:
            i=names[nodes[i]["name"]+" | full finish"]
        prim=doc['meshes'][nodes[i]["mesh"]]["primitives"][0]
        vs=acc[prim["attributes"]["POSITION"]].astype(float)
        return np.stack([vs[:,0],-vs[:,2],vs[:,1]],axis=-1)
    def values(i,key,t,default):
        if (i,key) in curves:
            tt,vv=curves[i,key]
            return np.array([np.interp(t,tt,vv[:,j]) for j in range(vv.shape[1])]).T
        return np.broadcast_to(get(i,key,default)[0],(len(t),len(default)))
    ids=[i for text,i in names.items() if re.match(r"^Pod \d{3} \| L\d{2} B\d{2}$",text)]
    assert len(ids)==p.TOTAL
    ids.sort(key=lambda i:nodes[i]["name"])
    for unit,idx in enumerate(ids,1):
        mesh_id=names[f"Original pod {unit:03} | bronze before fault"] if unit==p.care.BAD+1 else idx
        cube=points(mesh_id)
        assert np.allclose(np.ptp(cube,axis=0),[p.cfg.length(unit),p.cargo.FRAME_WIDTH,p.cargo.FRAME_HEIGHT],atol=.000002)
        tip=cube[:,0]>p.OUTER+.00001
        assert bool(tip.any())==bool(p.cfg.extension(unit))
        if tip.any():
            prim=doc["meshes"][nodes[mesh_id]["mesh"]]["primitives"][0]
            colour=acc[prim["attributes"]["COLOR_0"]][tip,:3]
            assert np.all(colour==np.rint(np.array(p.cfg.linear_rgb(p.cfg.POD["cdu_pump_section_colour"]))*255))
            assert np.isclose(cube[:,0].max(),p.OUTER+p.cfg.extension(unit))
    assert np.allclose(cube[:,0].min(),p.INNER)
    wall=points(names[f'Outer wall | lift {p.s.COUNT:02}'])
    assert np.isclose(np.linalg.norm(wall[:,:2],axis=1).max(),p.s.RO)
    wall=points(names[f'Inner wall | lift {p.s.COUNT:02}'])
    assert np.isclose(np.linalg.norm(wall[:,:2],axis=1).min(),p.s.RI,atol=.00001)
    rack=names["Preassembled steel store"]
    xyz=get(rack,"translation",[0,0,0])
    steel=points(names["Steel module | shaft, bearings, rim girders and braced columns"])
    outer_r=np.linalg.norm(steel[:,:2],axis=1).max();floor=steel[:,2].min()
    assert outer_r<p.s.RI and np.isclose(steel[:,2].max(),p.CROWN,atol=.001)
    for x,z,_ in xyz[p.C:p.FIRST_POD]:
        if abs(x)+outer_r>p.s.RI and abs(x)-outer_r<p.s.RO: assert z+floor>p.s.WALL_HEIGHT
    assert np.allclose(xyz[p.FIRST_POD:],0) and np.allclose(xyz[p.C+8],[p.PICK_X,0,0])
    local=[np.array(p.cargo.footprint(i)) for i in range(1,p.TOTAL+1)]
    num=p.FRAMES
    pos=np.zeros((num,p.TOTAL,2));angles=np.zeros((num,p.TOTAL));z0=np.zeros((num,p.TOTAL));show=np.zeros((num,p.TOTAL),bool)
    for j,i in enumerate(ids):
        slot,level=parents[i],parents[parents[i]]
        angles[:,j]=get(level,"rotation",[0])[:,0]+get(slot,"rotation",[0])[:,0]
        dis=get(i,"translation",[0,0,0]);ca,sa=np.cos(angles[:,j]),np.sin(angles[:,j])
        pos[:,j,0]=ca*dis[:,0];pos[:,j,1]=sa*dis[:,0];z0[:,j]=dis[:,1]
        show[:,j]=get(i,"scale",[1,1,1])[:,0]>.999
        first=np.nonzero(show[:,j])[0][0]
        assert first==p.STARTS[j] and abs(z0[first,j])<1e-5 and dis[first,0]+p.INNER>p.s.RO
        initial=slice(first,p.FILLED+1)
        moving=(dis[initial,0]>.001)&show[initial,j]
        assert np.max(np.abs(z0[initial,j][moving]))<.0001
        assert np.max(np.abs(np.sin(angles[initial,j][moving]-p.ENTRY)))<.0002
        assert np.allclose(z0[p.FILLED,j],p.level_z(p.LEVELS-j//p.BAYS),atol=.00002)
    bunched_gap=min(2*(x*math.sin(p.PACKED/2)-w*math.cos(p.PACKED/2)) for x,w in p.cargo.PROFILE)
    assert bunched_gap>0
    for lev in range(p.LEVELS):
        pod_angles=angles[-1,lev*p.BAYS:(lev+1)*p.BAYS]%(2*math.pi)
        differences=np.diff(np.r_[np.sort(pod_angles),np.min(pod_angles)+2*math.pi])
        assert np.allclose(differences,p.UNIFORM,atol=.00002)
    def verts(frame,j):
        a=angles[frame,j]
        co,si=math.cos(a),math.sin(a)
        return pos[frame,j]+local[j]@np.array([[co,si],[-si,co]])
    # Compare the moving pod with all stored ones across every shared Z interval.
    # Independently confirm that suspended ropes at both pick radii clear parked boxes.
    head=names["Twin self-releasing pickup heads"]
    hoist=parents[head];rope_yaw=get(hoist,"rotation",[0])[:,0]
    head_z=get(head,"translation",[0,0,0])[:,1]
    for f in range(p.FIRST_POD,p.FILLED):
        st=p.lift_state(f);j=st["i"]
        aa=verts(f,j)
        if np.linalg.norm(pos[f,j])<.0001:
            assert np.linalg.norm(aa,axis=1).max()<p.s.RI
        along=aa@np.array([math.cos(p.ENTRY),math.sin(p.ENTRY)])
        if st["u"]<.28 and along.min() < p.s.RO and along.max() > p.s.RI:
            right=np.array([-math.sin(p.ENTRY),math.cos(p.ENTRY)])
            assert np.abs(aa@right).max()<p.s.OPENING_WIDTH/2,(f,j,angles[f,j],pos[f,j],np.abs(aa@right).max())
            assert z0[f,j]+p.cargo.FRAME_HEIGHT<p.s.OPENING_HEIGHT
        for k in range(j):
            if min(z0[f,j],z0[f,k])+p.cargo.FRAME_HEIGHT-max(z0[f,j],z0[f,k])>.0005:
                assert not planar_overlap(aa,verts(f,k)),(f,j,k,"pod collision")
        parked=j if st['u']<.811 else j+1
        for k in range(parked):
            if head_z[f]>=z0[f,k]+p.cargo.FRAME_HEIGHT-.0001: continue
            rel=rope_yaw[f]-angles[f,k]
            for r in p.PICKUPS:
                x,y=r*math.cos(rel),r*math.sin(rel)
                dist=math.hypot(max(p.INNER-x,0,x-p.OUTER-p.cfg.extension(k+1)),max(abs(y)-p.cargo.FRAME_WIDTH/2,0))
                assert dist>.081,(f,k,"rope or hook interference",dist)
    assert doc['extras']['groundAperture_m']==[p.s.OPENING_WIDTH,p.s.OPENING_HEIGHT]
    assert doc['extras']['storageLevels']==p.LEVELS and doc['extras']['podsPerLevel']==p.BAYS
    l=p.services
    sleeves=[i for name,i in names.items() if name.endswith(" | cast-in service conduit")]
    assert len(sleeves)==p.TOTAL and len({nodes[i]['mesh'] for i in sleeves})==1
    # Nothing belonging to a pod reaches the outer wall: no flange, cover or sleeve outside the store.
    assert not [n for n in names if "exterior service" in n or "blind cover" in n]
    pipe=points(sleeves[0])
    assert np.isclose(pipe[:,0].min(),l.WALL_FACE,atol=.001)
    assert p.s.RO_INNER<pipe[:,0].max()<=l.TANK_END+.002<p.s.RI_OUTER
    assert l.port_height(p.LEVELS)<p.CROWN, "sleeves are only needed up to the top of the pod store"
    for slot in sleeves:
        level=int(nodes[slot]['name'][1:3]);bearing=int(nodes[slot]['name'][5:7])-1
        t=get(slot,'translation',[0,0,0]);ay=get(slot,'rotation',[0])[-1,0]
        assert abs(math.sin(ay-l.PORT_ANGLES[bearing]))<1e-5
        assert np.allclose(t[-1],[0,l.port_height(level),0],atol=1e-5)
        finish=l.sleeve_frames(level)[1]
        assert get(slot,"scale",[1,1,1])[finish,0]>.999
        assert abs(t[finish,1]-l.port_height(level))<1e-5
        assert p.s.display_info(finish)["height"]<l.port_height(level)
    # Cast a centreline ray through the triangles of the receiving lift: the inner wall
    # is bored at every sleeve and the outer wall is left solid.
    for level in range(1,p.LEVELS+1):
        h=l.port_height(level);lift=math.floor(h/p.s.LIFT)
        for face in ["Inner","Outer"]:
            meshes=[points(names[f'{face} wall | lift {lift+1:02}'+suffix]) for suffix in ('',' | cutaway insert')]
            tris=np.concatenate(meshes).reshape(-1,3,3)
            L=tris[:,1]-tris[:,0];M=tris[:,2]-tris[:,0];q0=np.array([0,0,h-lift*p.s.LIFT])-tris[:,0]
            for a in l.PORT_ANGLES:
                v=np.array([math.cos(a),math.sin(a),0])
                perp=np.cross(v,M);det=(perp*L).sum(axis=1);ok=abs(det)>1.e-9
                det=np.where(ok,det,1)
                u=(q0*perp).sum(axis=1)/det
                cross=np.cross(q0,L);vv=(v*cross).sum(axis=1)/det
                distance=(M*cross).sum(axis=1)/det
                hit=(ok&(u>=-.00001)&(vv>=-.00001)&(u+vv<=1.00001)&(distance>p.s.RI-.2)).any()
                assert hit==(face=="Outer"),(face,level,"sleeve opening")
    liquid=names["Free liquid surface | full ring"]
    heights=get(liquid,"translation",[0,0,0])[:,1]
    top=p.cfg.LIQUID_TOP
    assert np.diff(heights).min()>-.00005 and abs(heights[-1]-top)<1e-5 and top<=p.s.WALL_HEIGHT
    assert np.max(np.abs(heights[:p.C+1]))<.00001 and heights[p.C+10]>0
    assert heights[p.FIRST_POD]>l.port_height(p.LEVELS) and np.isclose(heights[p.clock.STORE_FILL[1]],top)
    for f in range(p.C): assert heights[f]<=p.s.display_info(f)['height']+.0001
    low=points(names["Water-glycol store | sealed doorway band"])
    # No triangle in the lower band crosses the blocked doorway strip.
    radial=np.array([math.cos(p.ENTRY),math.sin(p.ENTRY)])
    lateral=np.array([-radial[1],radial[0]])
    for tri in low.reshape(-1,3,3):
        if np.min(tri[:,:2]@radial)>0:
            y=tri[:,:2]@lateral
            assert np.min(y)>l.JAMB-.00001 or np.max(y)<-l.JAMB+.00001
    assert p.SPEED_FRAME==p.STARTS[2*p.BAYS]
    assert p.source_time(p.SPEED_FRAME+40)-p.source_time(p.SPEED_FRAME)==40*p.FAST_RATE
    for j,idx in enumerate(ids):
        slot,level=parents[idx],parents[parents[idx]]
        plug=names[f'Pod {j+1:03} | retractable service plug']
        tt,extent=curves[plug,"scale"]
        live=tt[extent[:,0]>.999]
        final_link=0 if j==p.care.BAD else 1
        assert len(live)>0 and math.isclose(get(plug,'scale',[1,1,1])[-1,0],final_link,abs_tol=1e-6)
        t0=p.SOURCE_STARTS[j]+.91*p.motion_ticks(j)
        t1=t0+p.dock_frames(j)
        disp=lambda v:v if v<=p.SWITCH_SOURCE else p.SPEED_FRAME+(v-p.SWITCH_SOURCE)/p.FAST_RATE
        assert min(abs(live*p.FPS-disp(t0+(t1-t0)*.55))) < (p.dock_frames(j)/2+1)
        # Test all positive-extension keyframes, including the 3x subframes.
        attached=tt[extent[:,0]>.002]
        yaw=values(slot,'rotation',attached,[0])[:,0]+values(level,"rotation",attached,[0])[:,0]
        displacement=values(idx,"translation",attached,[0,0,0])
        mis=(yaw-p.ENTRY-p.UNIFORM/2+p.UNIFORM/2)%p.UNIFORM-p.UNIFORM/2
        assert np.abs(mis).max()<.00012,(j,"fixed pipe swung with a pod",np.abs(mis).max())
        assert np.abs(displacement[:,0]).max()<.00003
        assert np.abs(displacement[:,1]+p.POD_H/2-l.port_height(p.LEVELS-j//p.BAYS)).max()<.00004
        assert abs(p.OUTER+p.cfg.extension(j+1)+points(plug)[:,0].max()-l.WALL_FACE)<.00001
    assert len([n for n in names if n.endswith(" | fluid and power online")])==p.TOTAL+1
    a=p.plant
    for j in (0,1):
        name=f"Power unit {j+1:02}"
        body=names[name+" | closed container body"]
        xyz=get(body,"translation",[0,0,0])
        pts=points(body)
        assert np.allclose(np.ptp(pts,axis=0)[:2],[a.LENGTH,a.WIDTH])
        assert np.isclose(np.min(pts[:,2]),-a.BASE_STUB)
        assert np.isclose(np.max(pts[:,2]),a.HEIGHT+a.ROOF_STUB)
        rad=np.linalg.norm(pts[:,:2],axis=1).max()
        assert a.RADIAL_CLEARANCE-.00001<=p.s.RI-rad<a.RADIAL_CLEARANCE+.0051
        first=p.FILLED+a.PICK_STARTS[j]
        landing=first+a.PICK_LENGTH
        assert np.allclose(xyz[first],[a.PICK_SITES[j][0],a.GROUND,-a.PICK_SITES[j][1]],atol=.00003)
        assert np.allclose(xyz[landing:],[0,a.power_base(p.CROWN,j),0],atol=.00003)
        yaw=get(body,"rotation",[0])[-1,0]
        assert abs(yaw-a.POWER_YAW-j*math.pi/2)<.00002
        while_crossing=(np.linalg.norm(xyz[:,[0,2]],axis=1)>1.e-4)&(np.linalg.norm(xyz[:,[0,2]],axis=1)<15.)
        assert np.min(xyz[while_crossing,1]+pts[:,2].min())>p.s.WALL_HEIGHT+2
        rest=xyz[-1,1]+np.min(pts[:,2])
        support=p.CROWN if j==0 else a.power_base(p.CROWN,0)+a.HEIGHT+a.ROOF_STUB
        assert np.isclose(rest,support,atol=.00003)
        for sign in ["negative","positive"]:
            stack=names[name+" | "+sign+" end stack 3 lip"]
            assert parents[stack]==body
            offsets=get(stack,"translation",[0,0,0])
            assert abs(abs(offsets[-1,0])-a.STACK_X)<.00005
            assert abs(xyz[-1,1]+offsets[-1,1]+points(stack)[:,2].max()-p.s.WALL_HEIGHT-a.VENT_RISE)<.00005
            assert np.max(np.abs(np.diff(offsets[:p.FILLED+a.VENT_START+1,1])))<.00002
            assert np.isclose(np.linalg.norm(points(stack)[:,:2],axis=1).min(),a.STACK_R-.038*2-.038,atol=.00002)
        assert get(body,"scale",[1,1,1])[p.FILLED,0]<.001
    assert doc["extras"]["dryCoolers"]==p.cfg.COOLERS and doc["extras"]["exhaustStacks"]==4
    view0,view1=p.FILLED+p.care.ORBIT,p.FILLED+p.care.ORBIT_DONE
    camera=get(names["Construction camera"],"translation",[0,0,0])[view0:view1+1]
    angles=np.unwrap(np.arctan2(-camera[:,2],camera[:,0]))
    assert abs(angles[-1]-angles[0]-2*math.pi)<.00003 and np.diff(angles).min()>0
    assert np.allclose(camera[0],camera[-1],atol=.0001)
    for name,i in names.items():
        if re.match(r"^(Inner|Outer) wall \| lift",name):
            assert np.allclose(get(i,"scale",[1,1,1])[view0:],1,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.PORTAL_VIEW+17:p.RESTORE],0,atol=.00002)
        if name.startswith("Ghosted concrete |"):
            assert np.allclose(get(i,"scale",[1,1,1])[view0:],0,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.PORTAL_VIEW+17:p.RESTORE],1,atol=.00002)
    # The lid closes the bore and the store after the vents are up, with the vents standing through it.
    lid=names["Silo lid | crane placement"];deck=points(lid);seat=get(lid,"translation",[0,0,0])
    assert np.allclose(seat[p.FILLED+a.LID[1]:],[0,a.LID_Z,0],atol=.0001)
    assert np.linalg.norm(deck[:,:2],axis=1).max()>=p.s.RO and p.s.WALL_HEIGHT<=a.LID_Z+deck[:,2].min()
    assert a.LID_Z+deck[:,2].max()<p.s.WALL_HEIGHT+a.VENT_RISE-.2 and a.LID[0]>a.VENT_END
    assert get(lid,"scale",[1,1,1])[p.FILLED+a.LID[0],0]>.999 and get(lid,"scale",[1,1,1])[-1,0]>.999
    assert np.allclose(get(lid,"scale",[1,1,1])[p.FILLED+p.care.CREW+16:p.RESTORE-1],0,atol=.00002)
    # Fuel: every tank lands on the pad and each leg of the gas line is at full length at the end.
    fuel,closing=p.fuel,p.closing
    tanks=[names[f"Propane tank {j+1:02}"] for j in range(fuel.COUNT)]
    shell=points(tanks[0])
    assert np.isclose(shell[:,0].max(),fuel.LENGTH/2,atol=.01) and np.isclose(np.ptp(shell[:,1]),fuel.DIA,atol=.1)
    spots=[]
    for j,i in enumerate(tanks):
        t=get(i,"translation",[0,0,0]);landed=p.FILLED+closing.TANKS+(j+1)*closing.TANK_STEP
        assert get(i,"scale",[1,1,1])[p.FILLED+closing.FUEL,0]<.001 and get(i,"scale",[1,1,1])[landed,0]>.999
        assert np.allclose(t[landed:],t[-1],atol=.0001) and abs(t[-1,1])<.0001
        spots.append(t[-1,[0,2]])
    spots=np.array(spots);centre=spots.mean(axis=0)
    assert abs(np.linalg.norm(centre)-fuel.FARM_R)<.01 and fuel.FARM_R-fuel.LENGTH/2>p.s.RO+25
    assert np.allclose(np.linalg.norm(np.diff(spots,axis=0),axis=1),fuel.PITCH,atol=.001) and fuel.PITCH>fuel.DIA+.5
    legs={"Gas line | ground run to the silo":(0,fuel.HEADER_R-fuel.RISER_R),"Gas line | riser on the outside wall":(2,fuel.TOP-fuel.LOW),
          "Gas line | run across the lid":(0,fuel.RISER_R-fuel.DROP_R),"Gas line | drop to the power modules":(2,fuel.TOP-fuel.drop_end(p.CROWN))}
    for name,(axis,length) in legs.items():
        size=get(names[name],"scale",[1,1,1])
        assert size[p.FILLED+closing.FUEL,0]<.001 and abs(size[-1,{0:0,2:1}[axis]]-length)<.001,name
    assert fuel.TOP>a.LID_Z+.3 and fuel.RISER_R>p.s.RO and fuel.drop_end(p.CROWN)<fuel.TOP
    from .verify_service import check
    check(p,doc,names,parents,get,points,ids,planar_overlap)
    print(f"{p.TOTAL} ground-fed {p.cfg.NAME} pods on {p.LEVELS} levels. All framed dimensions, CDU section colours and dock strokes passed.")
    print(f"Clear bore {2*p.s.RI:.2f} m. Steel cage radius {outer_r:.3f} m. Bunched inner-corner clearance {bunched_gap*1000:.1f} mm.")
    print(f"Two {a.LENGTH:.2f} m power units seat at 90 degrees. Four vents stand through the lid to {p.s.WALL_HEIGHT+a.VENT_RISE:.2f} m.")
    print(f"Pod sleeves end in the store at radius {l.TANK_END:.2f} m. {fuel.COUNT} propane tanks at {fuel.FARM_R:g} m feed one gas line.")
    print(f"Water-glycol reaches {top:.2f} m between the walls. Lower storage tiers run at {p.FAST_RATE:g}x.")


if __name__=="__main__": main(sys.argv[1])
