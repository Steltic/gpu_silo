"""Reserve swept cab, load and trailer footprints before keeping a complete filmed trip."""
import math
from collections import Counter
import numpy as np
from . import site


def sample(node, prop, frames):
    default={"yaw":(node["angle"],),"translation":node["translation"],"scale":(1.,1.,1.)}[prop]
    keys=node["tracks"].get(prop)
    if not keys:return np.broadcast_to(default,(len(frames),len(default)))
    times,v=zip(*keys)
    return np.stack([np.interp(frames,times,col) for col in zip(*v)],axis=-1)


def local_bounds(mesh):
    v=np.asarray([t[:3] for t in mesh.tris]).reshape(-1,3)
    return v[:,:2].min(axis=0),v[:,:2].max(axis=0)


def footprints(n,bounds,f):
    pos=sample(n,"translation",f)[:,:2]
    a=sample(n,"yaw",f)[:,0]
    u=np.stack((np.cos(a),np.sin(a)),axis=1)
    v=np.stack((-u[:,1],u[:,0]),axis=1)
    lo,hi=bounds
    centre=(lo+hi)*.5
    mid=pos+u*centre[0]+v*centre[1]
    # Bound every point's travel between samples, including the rotation of long rear overhangs.
    lengths=(hi-lo)*.5
    radius=np.linalg.norm(np.maximum(abs(lo),abs(hi)))
    motion=np.linalg.norm(np.diff(pos,axis=0),axis=1)+np.abs(np.diff(a))*radius
    pad=.08+np.maximum(np.r_[0.,motion],np.r_[motion,0.])
    return np.column_stack((mid,u,v,lengths[0]+pad,lengths[1]+pad))


def collides(a,b):
    delta=b[:,:2]-a[:,:2]
    close=np.all(abs(delta)<(np.linalg.norm(a[:,6:],axis=1)+np.linalg.norm(b[:,6:],axis=1))[:,None],axis=1)
    if not np.any(close):return False
    a,b,d=a[close],b[close],delta[close]
    ok=np.ones(len(a),dtype=bool)
    for axis in (a[:,2:4],a[:,4:6],b[:,2:4],b[:,4:6]):
        radius=lambda q: q[:,6]*abs((axis*q[:,2:4]).sum(axis=1))+q[:,7]*abs((axis*q[:,4:6]).sum(axis=1))
        ok &= abs((d*axis).sum(axis=1))<=radius(a)+radius(b)
        if not ok.any():return False
    return True


def schedule(scene,node):
    bounds={i:local_bounds(m) for i,m in enumerate(scene.meshes) if m.tris}
    nodes=scene.nodes
    groups=[]
    for i,n in enumerate(nodes):
        if n["name"].endswith(" | tractor"):
            groups.append((n["group"],i,i+1))
            assert nodes[i+1]["name"].endswith(" | trailer")
        elif n["name"].startswith("Truck mixer "):groups.append((n["group"],i,i))
    priority={"Pod delivery":0,"Fuel delivery":1,"Concrete supply":2,"Cooler delivery":3,"Cage build":4,"Water delivery":5}
    seen=Counter()
    def order(item):
        group,i,j=item
        k=seen[group];seen[group]+=1
        # Give the first visit of each class its original slot; reserve hero deliveries early.
        return (0 if k==0 else 1,priority.get(group,6),k)
    groups=sorted(groups,key=order)
    reservations=[]
    schedule=[]
    crib=site.steel("Staging trestles | timber crossheads")
    for x in (-2.7,2.7):
        site.closed(crib,x-.19,-1.12,x+.19,1.12,site.DECK-.18,site.DECK,"987d5e")
        for y in (-.82,.82):
            site.closed(crib,x-.14,y-.13,x+.14,y+.13,.02,site.DECK-.18,"586b6b")
    crib_id=scene.mesh(crib)
    for group,i,j in groups:
        ids=(i,) if i==j else (i,j)
        cab=nodes[i]; tow=nodes[j]
        children=[n for n in nodes if n.get("parent")==j and n["mesh"]>=0]
        stops=[n["tracks"]["scale"][-1][0] for n in children if n["tracks"].get("scale")]
        visible=cab["tracks"]["scale"]
        first=next(t for t,val in visible if val[0]>.99)
        last=visible[-1][0]
        if last<=first:continue
        f=np.arange(math.ceil(first),math.floor(last)+1)
        pose=sample(tow,"translation",f)[:,:2]
        # Centre the drive-time adjustment on the unload, never on a public road hold.
        if stops:
            early,late=min(stops),max(stops)
        else:
            still=np.r_[False,np.linalg.norm(np.diff(pose,axis=0),axis=1)<.015]
            idx=np.where(still)[0]
            anchor=f[idx[np.argmin(np.linalg.norm(pose[idx],axis=1))]] if len(idx) else f[len(f)//2]
            early=late=anchor
        lo,hi=bounds[tow["mesh"]]
        for c in children:
            ca,cb=bounds[c["mesh"]]
            angle=c["angle"];cc,ss=math.cos(angle),math.sin(angle)
            corners=np.array([(x*cc-y*ss,x*ss+y*cc) for x in (ca[0],cb[0]) for y in (ca[1],cb[1])])+c["translation"][:2]
            lo=np.minimum(lo,corners.min(axis=0));hi=np.maximum(hi,corners.max(axis=0))
        shapes=[bounds[cab["mesh"]]] if i==j else [bounds[cab["mesh"]],(lo,hi)]
        def mapped(times,rate,shift,reverse=False):
            early_at=early+(0 if reverse else shift);late_at=late+(0 if reverse else shift)
            if reverse:
                return np.where(times<early_at,early_at+(times-early_at)/rate,np.where(times>late_at,late_at+(times-late_at)/rate,times))+shift
            t=times-shift
            return np.where(times<early_at,early+(t-early)*rate,np.where(times>late_at,late+(t-late)*rate,t))
        def clashes(start,end,poses):
            for a,b,others in reservations:
                l,h=max(a,start),min(b,end)
                if h<=l:continue
                for body in poses:
                    for other in others:
                        if collides(body[l-start:h-start],other[l-a:h-a]):return True
            return False
        # Source cargo transfer frames are fixed. Background tankers have flexible dispatch times.
        shifts=(0,) if stops else (0,-24,24,-60,60,-102,102)
        accepted=False
        for shift in shifts:
            for rate in (1.,1.32,.84,1.85,2.6):
                ab=mapped(np.array([first,last]),rate,shift,True)
                if ab[1]<=0:continue
                a=max(0,math.floor(ab[0]*4));b=min(6289*4,math.ceil(ab[1]*4)+1)
                if b<=a:continue
                times=mapped(np.arange(a,b)*.25,rate,shift)
                poses=[footprints(nodes[idx],shape,times) for idx,shape in zip(ids,shapes)]
                if clashes(a,b,poses):continue
                for idx in ids:
                    for prop,keys in list(nodes[idx]["tracks"].items()):
                        k=mapped(np.array([t for t,v in keys]),rate,shift,True)
                        nodes[idx]["tracks"][prop]=[(float(t),v) for t,(_,v) in zip(k,keys)]
                    nodes[idx]["tracks"]["scale"]=site.window(max(0.,float(ab[0])),float(ab[1]))
                reservations.append((a,b,poses))
                schedule.append(dict(name=cab["name"],group=group,drive_rate=rate,offset=shift))
                accepted=True
                break
            if accepted:break
        if accepted:continue
        for c in children:
            end=c["tracks"]["scale"][-1][0]
            centre=sample(tow,"translation",[end])[0]
            angle=sample(tow,"yaw",[end])[0,0]
            x,y,z=c["translation"]
            cc,ss=math.cos(angle),math.sin(angle)
            place=(centre[0]+cc*x-ss*y,centre[1]+ss*x+cc*y,centre[2]+z)
            c["parent"]=-1;c["angle"]+=angle;c["translation"]=tuple(float(v) for v in place)
            c["name"]=c["name"].split(" | ")[0]+" | pre-staged load"
            c["tracks"]["scale"]=site.window(max(0,end-14),end)
            node("Pre-staged load | trestles",crib_id,"Delivery staging",angle=angle,t=(place[0],place[1],0),tracks={"scale":site.window(max(0,end-14),end)})
        for idx in ids:nodes[idx]["tracks"]["scale"]=[(0,site.OFF)]
        schedule.append(dict(name=cab["name"],group=group,omitted=True,staged=len(children)))
    # Independently replay every reserved pair, including articulating trailers.
    for i,(a,b,bodies) in enumerate(reservations):
        for c,d,others in reservations[i+1:]:
            l,h=max(a,c),min(b,d)
            if h<=l:continue
            if any(collides(x[l-a:h-a],y[l-c:h-c]) for x in bodies for y in others):
                raise ValueError("Truck swept envelopes intersect")
    return schedule
