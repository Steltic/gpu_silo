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
    short=p.film.SHORT
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
        mesh_id=names.get(f"Original pod {unit:03} | bronze before fault",idx) if unit==p.care.BAD+1 else idx
        cube=points(mesh_id)
        assert np.allclose(np.ptp(cube,axis=0),[p.cfg.length(unit),p.cargo.FRAME_WIDTH,p.cargo.FRAME_HEIGHT],atol=.000002)
        tip=cube[:,0]>p.OUTER+.00001
        assert bool(tip.any())==bool(p.cfg.extension(unit))
        if tip.any():
            prim=doc["meshes"][nodes[mesh_id]["mesh"]]["primitives"][0]
            colour=acc[prim["attributes"]["COLOR_0"]][:,:3]
            # The grey CDU and pump section fills the pod from the rack housing to the wall end, inside the two trusses.
            grey=np.all(colour==np.rint(np.array(p.cfg.linear_rgb(p.cfg.POD["cdu_pump_section_colour"]))*255),axis=1)
            box=cube[grey];steel=cube[tip&~grey]
            assert np.isclose(box[:,0].min(),p.OUTER) and np.isclose(box[:,0].max(),p.OUTER+p.cfg.extension(unit))
            assert np.isclose(np.abs(box[:,1]).max(),p.cfg.BODY_WIDTH/2) and np.isclose(np.ptp(box[:,2]),p.cfg.BODY_HEIGHT)
            chord=p.structure.C["design"]["chord"]["h"]
            beside=np.abs(steel[:,1])>p.cfg.BODY_WIDTH/2-1e-6
            across=(steel[:,2]<chord+1e-6)|(steel[:,2]>p.cargo.FRAME_HEIGHT-chord-1e-6)
            assert len(steel) and np.all(beside|across),"truss steel must pass beside, above or below the CDU and pump section"
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
    assert outer_r<p.s.RI and p.structure.SHAFT_TOP<=steel[:,2].max()<p.CROWN+p.cfg.POWER['floor_structure_m']      # the shaft runs up into the collar of the rig
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
    if short:
        # The store stays dry until the last pod is in, then fills to the end of the build.
        assert np.max(np.abs(heights[:p.FILLED+1]))<.00001 and heights[p.FILLED+24]>0 and heights[p.FILLED+p.clock.WATER[1]-1]<top
    else:
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
        final_link=0 if j==p.care.BAD and not short else 1
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
    assert len([n for n in names if n.endswith(" | fluid and power online")])==p.TOTAL+(0 if short else 1)
    a=p.plant
    def cleared(pts,x0,y0,x1,y1,gap):
        """True when no point of a level-coordinate box comes within gap of the access wedge."""
        for x in np.linspace(x0,x1,9):
            for y in np.linspace(y0,y1,9):
                r=math.hypot(x,y)
                if r>p.crew.PLATE_IN-gap and abs(math.atan2(x,y))<p.crew.HALF+gap/max(r,1):return False
        return True
    for j,label in enumerate(("Power level 01 | diesel deck assembly","Power level 02 | turbine deck assembly")):
        body=names[label]
        xyz=get(body,"translation",[0,0,0])
        pts=points(body)
        # Every level fits in the bore, sits on its floor structure and stays under the lid.
        assert np.linalg.norm(pts[:,:2],axis=1).max()<p.s.RI-.05
        # Each level has shoes below its ring beam. Those of the support rig still clear the crown of the cage.
        assert np.isclose(np.min(pts[:,2]),a.SEAT_Z-.14,atol=.02)
        assert a.power_base(p.CROWN,0)+a.SEAT_Z-.14>p.CROWN-.10
        first=p.clock.RIG_PICK if j==0 else p.FILLED+a.PICK_STARTS[j]
        landing=first+a.PICK_LENGTH
        ground=a.DECK+.25 if j==0 else a.GROUND
        assert np.allclose(xyz[first],[a.PICK_SITES[j][0],ground,-a.PICK_SITES[j][1]],atol=.00003)
        assert np.allclose(xyz[landing:],[0,a.power_base(p.CROWN,j),0],atol=.00003)
        assert abs(get(body,"rotation",[0])[-1,0]-a.POWER_YAW)<.00002
        while_crossing=(np.linalg.norm(xyz[:,[0,2]],axis=1)>1.e-4)&(np.linalg.norm(xyz[:,[0,2]],axis=1)<15.)
        assert np.min(xyz[while_crossing,1]+pts[:,2].min())>p.s.WALL_HEIGHT+2
        assert xyz[-1,1]+pts[:,2].min()>=p.CROWN-.10 and xyz[-1,1]+pts[:,2].max()<a.LID_Z
        seen=get(body,"scale",[1,1,1])[:,0]
        if j==0:
            assert p.C+298 < first < landing < p.FIRST_POD and seen[first:].min()>.999
            assert pts[:,2].max()<.1,"the early lift must contain only the support steel"
        else:
            assert seen[p.FILLED+(a.FAB_DONE-1 if short else 0)]<.001
    hook=get(names["South crawler | retained hook block"],"translation",[0,0,0])
    deck=get(names["Power level 01 | diesel deck assembly"],"translation",[0,0,0])
    flight=slice(p.clock.RIG_PICK,p.clock.RIG_PICK+a.PICK_LENGTH+1)
    assert np.allclose(hook[flight]-deck[flight],[0,a.APEX,0],atol=.001)
    for i,(x,y,angle) in enumerate(a.DIESEL_LOADS):
        name=f"Diesel set {i+1} | skid" if i<len(a.GEN_AT) else f"Diesel day tank {i-len(a.GEN_AT)+1} | tank and saddles"
        body=names[name];xyz=get(body,"translation",[0,0,0])
        first=p.FILLED+a.PICK_STARTS[0]+i*a.DIESEL_CYCLE;end=first+a.DIESEL_FLIGHT
        cx,cy,_=a.turned(x,y)
        assert np.allclose(xyz[first],[a.PICK_SITES[0][0]+cx,a.GROUND,-a.PICK_SITES[0][1]-cy],atol=.001)
        assert np.allclose(xyz[end:],[cx,a.power_base(p.CROWN,0),-cy],atol=.001)
        assert np.allclose(hook[first:end+1]-xyz[first:end+1],[0,a.diesel_apex(i),0],atol=.001)
        assert get(body,"scale",[1,1,1])[p.FIRST_POD,0]<.001 and get(body,"scale",[1,1,1])[first:,0].min()>.999
    assert a.power_base(p.CROWN,1)-a.power_base(p.CROWN,0)>=a.GEN_H+a.DECK-1e-9
    assert a.power_base(p.CROWN,1)+a.SET_H<=a.LID_Z
    # Two turbine sets side by side clear the wall. The diesel sets clear each other, the wall and the crew's access wedge.
    assert math.hypot(a.SET_L/2,a.SET_Y+a.SET_W/2)<p.s.RI-.25 and a.SET_Y-a.SET_W/2>=.5
    boxes=[]
    for cx,cy,deg in a.GEN_AT:
        long,wide=(a.GEN_L,a.GEN_W) if not deg else (a.GEN_W,a.GEN_L)
        box=(cx-long/2,cy-wide/2,cx+long/2,cy+wide/2)
        assert max(math.hypot(x,y) for x in box[::2] for y in box[1::2])<p.s.RI-.3
        assert cleared(None,*box,.2),"a diesel set blocks the access wedge"
        for other in boxes:
            assert box[0]>other[2]+.6 or other[0]>box[2]+.6 or box[1]>other[3]+.6 or other[1]>box[3]+.6
        boxes.append(box)
    assert len(boxes)==p.cfg.PROJECT["diesel"]["sets"] and abs(p.crew.PLATE_IN-(a.SET_Y+a.SET_W/2))>=.1
    assert doc["extras"]["dryCoolers"]==p.cfg.COOLERS and doc["extras"]["exhaustStacks"]==p.cfg.POWER["modules"]
    # Roof equipment: each stack and inlet house stands over its turbine set, and nothing on the roof overlaps.
    for (ex,ey),(ix,iy) in zip(a.EXHAUST_AT,a.INLET_AT):
        assert abs(abs(ey)-a.SET_Y)<1e-9 and abs(ex)<a.SET_L/2 and abs(iy)==abs(ey) and ex-ix>a.EXHAUST_R+a.INLET_HOUSE[0]/2+1.5
    assert a.EXHAUST_H>a.INLET_HOUSE[2]+1.5,"exhaust must discharge above the air inlets"
    roof=[(x,y,a.EXHAUST_R,a.EXHAUST_R) for x,y in a.EXHAUST_AT]+[(x,y,a.DIESEL_STACK_R,a.DIESEL_STACK_R) for x,y in a.DIESEL_STACKS]
    roof+=[(x,y,a.INLET_HOUSE[0]/2,a.INLET_HOUSE[1]/2) for x,y in a.INLET_AT]+[(x,y,a.ROOM_VENT[0]/2,a.ROOM_VENT[1]/2) for x,y in a.ROOM_VENTS]
    for i,(x,y,hx,hy) in enumerate(roof):
        assert math.hypot(abs(x)+hx,abs(y)+hy)<a.LID_R
        for u,v,qx,qy in roof[:i]:
            assert abs(x-u)>hx+qx+.3 or abs(y-v)>hy+qy+.3,("roof equipment overlaps",(x,y),(u,v))
    # Diesel exhausts rise through the turbine level beside the sets or in the aisle.
    for x,y in a.DIESEL_STACKS:
        assert abs(y)<a.AISLE/2-a.DIESEL_STACK_R or abs(y)>a.SET_Y+a.SET_W/2+a.DIESEL_STACK_R
    view0,view1=p.FILLED+p.care.ORBIT,p.FILLED+p.care.ORBIT_DONE
    camera=get(names["Construction camera"],"translation",[0,0,0])[view0:view1+1]
    angles=np.unwrap(np.arctan2(-camera[:,2],camera[:,0]))
    assert abs(angles[-1]-angles[0]-2*math.pi)<.00003 and np.diff(angles).min()>0
    assert np.allclose(camera[0],camera[-1],atol=.0001)
    for name,i in names.items():
        if short:
            # The short film has one cutaway. The concrete is solid again from the orbit to the end.
            if re.match(r"^(Inner|Outer) wall \| lift",name):
                assert np.allclose(get(i,"scale",[1,1,1])[view0:],1,atol=.00002) and np.allclose(get(i,"scale",[1,1,1])[p.PORTAL_VIEW+17:p.RESTORE],0,atol=.00002)
            if name.startswith("Ghosted concrete |"):
                assert np.allclose(get(i,"scale",[1,1,1])[view0:],0,atol=.00002) and np.allclose(get(i,"scale",[1,1,1])[p.PORTAL_VIEW+17:p.RESTORE],1,atol=.00002)
            continue
        if re.match(r"^(Inner|Outer) wall \| lift",name):
            # Solid for the orbit and the last shot, removed for the two cutaways.
            assert np.allclose(get(i,"scale",[1,1,1])[view0:p.REGHOST],1,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.RESTORE2:],1,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.PORTAL_VIEW+17:p.RESTORE],0,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.REGHOST:p.RESTORE2],0,atol=.00002)
        if name.startswith("Ghosted concrete |"):
            assert np.allclose(get(i,"scale",[1,1,1])[view0:p.REGHOST],0,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.PORTAL_VIEW+17:p.RESTORE],1,atol=.00002)
            assert np.allclose(get(i,"scale",[1,1,1])[p.REGHOST:p.RESTORE2],1,atol=.00002)
    # The lid closes the bore and the store after the vents are up, with the vents standing through it.
    lid=names["Silo lid | crane placement"];deck=points(lid);seat=get(lid,"translation",[0,0,0])
    assert np.allclose(seat[p.FILLED+a.LID[1]:],[0,a.LID_Z,0],atol=.0001)
    assert np.linalg.norm(deck[:,:2],axis=1).max()>=p.s.RO and p.s.WALL_HEIGHT<=a.LID_Z+deck[:,2].min()
    assert abs(a.LID_Z+deck[:,2].max()-p.s.WALL_HEIGHT-a.VENT_RISE)<.01 and a.LID[0]>a.VENT_END
    assert get(lid,"scale",[1,1,1])[p.FILLED+a.LID[0],0]>.999 and get(lid,"scale",[1,1,1])[-1,0]>.999
    floor=a.power_base(p.CROWN,1)+a.HINGE_Z
    if short:
        # Both turbine sets stand open on their deck, with no enclosure and no hinged side.
        assert not any("hinged side" in name for name in names)
        for side,label in ((1,"A"),(-1,"B")):
            machine=points(names[f"Turbine set {label} | gas turbine and generator"])
            assert np.abs(machine[:,0]).max()<a.SET_L/2-.1 and (side*machine[:,1]).min()>a.SET_Y-a.SET_W/2+.05 and (side*machine[:,1]).max()<a.SET_Y+a.SET_W/2-.05
        deck=points(names["Power level 02 | turbine deck assembly"])
        assert deck[:,2].max()<=.001,"the turbine deck carries no enclosure in the short film"
    else:
        hinged(p,a,names,get,points,floor)
    assert abs(p.crew.POWER_FLOOR-floor)<1e-9 and p.cfg.POWER["modules"]*p.cfg.POWER["module_output_mw"]>=p.calcs.C["heat_mw"]-1e-9
    walkways_and_fuel(p,a,doc,names,parents,get,points,ids,planar_overlap,roof,floor,short)
    # The support rig holds the top of the shaft. Its plates are cast into the wall before their pour, the shaft runs up
    # into the collar, and the deck girders stop clear of the shaft.
    rig=p.structure.RIG
    for level,label,count in ((0,"Top rig mount",rig["wall_mounts"]),(1,"Turbine level mount",a.TURBINE_MOUNTS)):
        seat=a.power_base(p.CROWN,level)+a.SEAT_Z
        mounts=[i for name,i in names.items() if name.startswith(label)]
        assert len(mounts)==count>=8
        pour=p.services.lift_start(int((seat-.45)//p.s.LIFT))
        for i in mounts:
            where=get(i,"translation",[0,0,0]);final=where[-1]
            assert abs(np.hypot(final[0],final[2])-p.s.RI)<1e-5 and abs(final[1]-seat)<1e-5,"a wall plate is not on the bore face at the seat level"
            assert get(i,"scale",[1,1,1])[pour-1,0]>.999 and np.allclose(where[pour-1:],final,atol=1e-5),"a wall plate is not in the forms before its pour"
            bearing=(math.atan2(-final[2],final[0])-a.POWER_YAW-math.pi/2+math.pi)%(2*math.pi)-math.pi
            assert abs(bearing)>a.ACCESS_HALF,"a wall plate is in the access wedge"
        assert seat-.45>p.CROWN-1 and seat-.45+a.PLATE_H<p.s.WALL_HEIGHT
    crown=points(names["Steel module | crown and hoist beams"]) if "Steel module | crown and hoist beams" in names else points(names["Steel module | shaft, bearings, rim girders and braced columns"])
    assert crown[:,2].max()>=p.structure.SHAFT_TOP,"the shaft does not reach the connector"
    deck=points(names["Power level 01 | diesel deck assembly"])
    inside=deck[(np.hypot(deck[:,0],deck[:,1])<p.SHAFT+1e-5)&(deck[:,2]<-.01)]
    assert len(inside)==0 and a.COLLAR>p.SHAFT+.05,"the rig steel must stop at the collar round the shaft"
    assert p.structure.SHAFT_TOP<a.power_base(p.CROWN,0) and p.structure.C["shaft"]["chosen"]["passes"]
    fuel=p.fuel
    if short:
        from .verify_short import check
        check(p,doc,names,parents,get,points)
    else:
        from .verify_service import check
        check(p,doc,names,parents,get,points,ids,planar_overlap)
    print(f"{p.TOTAL} ground-fed {p.cfg.NAME} pods on {p.LEVELS} levels. All framed dimensions, CDU section colours and dock strokes passed.")
    print(f"Clear bore {2*p.s.RI:.2f} m. Steel cage radius {outer_r:.3f} m. Bunched inner-corner clearance {bunched_gap*1000:.1f} mm.")
    print(f"The bare rig seats before the first pod. The crawler lands {len(a.GEN_AT)} diesel sets and {len(a.DAY_TANKS)} day tanks on it after loading.")
    print((f"Both turbine sets stand open on their deck at {floor:.2f} m. " if short else f"Turbine set A's side folds to a work floor at {floor:.2f} m. ")+f"{len(a.GEN_AT)} diesel sets leave the access wedge clear. "
          f"The lid carries {len(a.EXHAUST_AT)} exhaust stacks to {p.s.WALL_HEIGHT+a.VENT_RISE:.1f} m.")
    print(f"Pod sleeves end in the store at radius {l.TANK_END:.2f} m. {fuel.COUNT} propane tanks at {fuel.FARM_R:g} m feed one gas line.")
    print(f"Water-glycol reaches {top:.2f} m between the walls. Lower storage tiers run at {p.FAST_RATE:g}x.")


if __name__=="__main__": main(sys.argv[1])


def hinged(p,a,names,get,points,floor):
    lid=names["Silo lid | crane placement"]
    assert np.allclose(get(lid,"scale",[1,1,1])[p.FILLED+p.care.CREW+16:p.RESTORE-1],0,atol=.00002)
    assert np.allclose(get(lid,"scale",[1,1,1])[p.REGHOST:p.RESTORE2-1],0,atol=.00002)
    # The lower power module holds a gas turbine. Its near side folds down to the crew's floor level and closes again.
    clock=p.clock
    poses=[names[f"Turbine set A | hinged side, pose {k+1:02}"] for k in range(a.PANEL_POSES)]
    shown=np.array([get(i,"scale",[1,1,1])[:,0]>.5 for i in poses])
    assert (shown.sum(axis=0)==1).all(), "exactly one pose of the hinged side is shown at a time"
    opened=p.FILLED+clock.ENCLOSURE_OPEN[1];closed=p.FILLED+clock.ENCLOSURE_CLOSE[1]
    assert shown[0,:p.FILLED+clock.ENCLOSURE_OPEN[0]].all() and shown[0,closed+1:].all()
    assert shown[-1,opened+1:p.FILLED+clock.ENCLOSURE_CLOSE[0]].all()
    flat=points(poses[-1]);wall=points(poses[0])
    assert np.ptp(flat[:,1])>a.PANEL_HEIGHT-.01 and abs(flat[flat[:,1]>a.HINGE_Y+.3][:,2].max()-a.HINGE_Z)<.03
    assert np.linalg.norm(flat[:,:2],axis=1).max()<p.s.RI-.2,"the folded side must stay inside the bore"
    assert wall[:,1].max()<a.SET_Y+a.SET_W/2+.02 and np.ptp(wall[:,2])>a.PANEL_HEIGHT-.01
    turbine=names["Turbine set A | gas turbine and generator"];machine=points(turbine)
    assert np.abs(machine[:,0]).max()<a.SET_L/2-.1 and machine[:,1].min()>a.SET_Y-a.SET_W/2+.05 and machine[:,1].max()<a.SET_Y+a.SET_W/2-.05
    assert machine[:,2].min()>.1 and machine[:,2].max()<a.SET_H-.1


def walkways_and_fuel(p,a,doc,names,parents,get,points,ids,planar_overlap,roof,floor,short):
    # A walkway ring at every level joins the sectors, between the shaft and the pod roots.
    cage=points(names["Steel module | shaft, bearings, rim girders and braced columns"])
    for level in range(1,p.LEVELS+1):
        z=p.level_z(level);ring=cage[(np.abs(cage[:,2]-(z-.09))<.002)]
        radii=np.linalg.norm(ring[:,:2],axis=1)
        if short:
            assert not np.any((radii>p.SHAFT+.21)&(radii<p.INNER)), "shaft walkway visible in build cut"
        else:
            assert radii.min()<p.SHAFT+.25 and p.INNER-.2<radii[radii<p.INNER].max()<p.INNER, "walkway ring missing"
    # The access round the shaft is the width given in the design file, and the pod roots still clear each other when bunched.
    assert abs(p.INNER-p.SHAFT-p.cfg.STORE["shaft_access_m"])<1e-9 and p.crew.PLATE_IN>p.INNER
    assert p.calcs.C["root_gap_packed"]>0 and p.calcs.C["root_gap_lane"]>0,"the pod roots touch: widen the access round the shaft"
    # Fuel: every tank lands on the pad and each leg of the gas line is at full length at the end.
    fuel,closing=p.fuel,p.closing
    tanks=[names[f"Propane tank {j+1:02}"] for j in range(fuel.COUNT)]
    shell=points(tanks[0])
    assert np.isclose(shell[:,0].max(),fuel.LENGTH/2,atol=.01) and np.isclose(np.ptp(shell[:,1]),fuel.DIA,atol=.1)
    spots=[]
    for j,i in enumerate(tanks):
        t=get(i,"translation",[0,0,0]);landed=p.FILLED+closing.TANKS+j*closing.TANK_STEP+closing.TANK_SETTLE+1
        assert get(i,"scale",[1,1,1])[p.FILLED+closing.FUEL,0]<.001 and get(i,"scale",[1,1,1])[landed,0]>.999
        assert np.allclose(t[landed:],t[-1],atol=.0001) and abs(t[-1,1])<.0001
        spots.append(t[-1,[0,2]])
    spots=np.array(spots);centre=spots.mean(axis=0)
    assert abs(np.linalg.norm(centre)-fuel.FARM_R)<.01 and fuel.FARM_R-fuel.LENGTH/2>p.s.RO+25
    assert np.allclose(np.linalg.norm(np.diff(spots,axis=0),axis=1),fuel.PITCH,atol=.001) and fuel.PITCH>fuel.DIA+.5
    bulk=names["Diesel bulk tank"];where=get(bulk,"translation",[0,0,0])[-1]
    assert abs(where[1])<.0001 and get(bulk,"scale",[1,1,1])[-1,0]>.999 and np.linalg.norm(where[[0,2]]-centre)>fuel.COUNT*fuel.PITCH/2
    assert fuel.PIPE*2>=.1,"the propane line is drawn at its design bore"
    assert fuel.BURIED + fuel.PIPE <= -1.2
    legs={"Gas line | buried road crossing":(0,fuel.HEADER_R-fuel.RISER_R),"Gas line | riser on the outside wall":(2,fuel.TOP-fuel.BURIED),
          "Gas line | run across the lid":(0,fuel.RISER_R-fuel.DROP_R),"Gas line | drop to the power modules":(2,fuel.TOP-fuel.drop_end(p.CROWN)),
          "Diesel line | drop to the day tanks":(2,fuel.TOP-fuel.diesel_end(p.CROWN))}
    for name,(axis,length) in legs.items():
        size=get(names[name],"scale",[1,1,1])
        assert size[p.FILLED+closing.FUEL,0]<.001 and abs(size[-1,{0:0,2:1}[axis]]-length)<.001,name
    assert fuel.TOP>a.LID_Z+.3 and fuel.RISER_R>p.s.RO and fuel.diesel_end(p.CROWN)<fuel.drop_end(p.CROWN)<fuel.TOP
    # The drops come down beside the turbine sets and clear of the roof equipment.
    turn=fuel.BEARING-a.POWER_YAW;drop=(fuel.DROP_R*math.cos(turn),fuel.DROP_R*math.sin(turn))
    assert abs(drop[1])>a.SET_Y+a.SET_W/2+.3 and math.hypot(*drop)<p.s.RI-.5
    for x,y,hx,hy in roof:
        assert abs(drop[0]-x)>hx+.4 or abs(drop[1]-y)>hy+.4
