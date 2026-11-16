"""Check crew, storage and cable-crane motions in the exported glTF transforms."""
import math
import re

import numpy as np


def check(p,doc,names,parents,get,points,ids,overlap):
    c,crew=p.care,p.crew
    begin=p.FILLED+c.CREW
    repair=p.FILLED+c.REPAIR
    end=p.FRAMES-repair
    def xyz(i):
        t=get(i,"translation",[0,0,0])
        return np.column_stack((t[:,0],-t[:,2],t[:,1]))
    def yaw(i):return get(i,"rotation",[0])[:,0]
    def scale(i):return get(i,"scale",[1,1,1])[:,0]
    def wrap(a):return (a+math.pi)%(2*math.pi)-math.pi
    def rotate(xy,a):
        co,si=np.cos(a),np.sin(a)
        return np.stack((co*xy[...,0]-si*xy[...,1],si*xy[...,0]+co*xy[...,1]),axis=-1)
    rack=names["Preassembled steel store"]
    poses=[(n,i) for n,i in names.items() if re.fullmatch(r"Wedge \d\d \| technician \d",n)]
    assert len(poses)==sum(crew.SIZES) and len(crew.LEVELS)==p.BAYS
    # Cast vertical rays below a boarding deck in all eight wedges. The
    # terrain, pad and concrete must leave room for the underside and shoes.
    tris=np.concatenate([points(names[n]) for n in ("Concrete starter slab","Compacted work pad",
                                                     "Agricultural fields and access track")]).reshape(-1,3,3)
    planar=tris[np.ptp(tris[:,:,2],axis=1)<.00001]
    edges=np.roll(planar[:,:,:2],-1,axis=1)-planar[:,:,:2]
    areas=abs(edges[:,0,0]*edges[:,1,1]-edges[:,0,1]*edges[:,1,0])
    for b,size in enumerate(crew.SIZES):
        prefix=f"Wedge {b+1:02} | "
        deck=names[prefix+"solid lift platform"];root=parents[deck]
        assert parents[root]==rack and abs(wrap(yaw(root)[begin]-p.ENTRY-b*p.UNIFORM))<.00002
        sample=rotate(np.array([3.98,.13]),p.ENTRY+b*p.UNIFORM)
        delta=sample-planar[:,:,:2]
        signs=edges[:,:,0]*delta[:,:,1]-edges[:,:,1]*delta[:,:,0]
        covered=((signs.min(axis=1)>-.0001)|(signs.max(axis=1)<.0001))&(areas>.00001)
        assert np.isclose(planar[covered,:,2].max(),crew.WELL_FLOOR,atol=.00004)
        z=xyz(deck)[:,2]
        assert np.isclose(z[begin],crew.STOW) and np.isclose(z[begin+300],crew.target(b))
        turbine=crew.LEVELS[b]==0;tw=[v-p.clock.CREW for v in p.clock.TURBINE_WORK]
        hold=slice(begin+300,begin+tw[3]) if turbine else slice(begin+247,begin+549)
        assert np.ptp(z[hold])<.00003 and np.max(abs(z[begin+(700 if turbine else 695):begin+786]-crew.STOW))<.00003
        ascent=np.where(np.diff(z[begin:begin+310])>.0001)[0][0]
        assert 105<ascent<139
        pts=points(deck)
        assert np.ptp(pts[:,0])>3.2 and pts[:,2].min()<-.12
        distance=pts[:,0]*math.sin(crew.HALF)-abs(pts[:,1])*math.cos(crew.HALF)
        assert distance.min()>p.cargo.FRAME_WIDTH/2,"deck intersects a stored pod"
        guides=points(names[prefix+"twin guide rails"])
        assert np.hypot(guides[:,0],guides[:,1]).min()>math.hypot(max(p.cfg.length(i) for i in range(1,p.TOTAL+2))+p.INNER,p.cargo.FRAME_WIDTH/2)
        gate=get(names[prefix+"boarding gate"],"scale",[1,1,1])[:,1]
        assert gate[begin+85]<.0001 and gate[begin+107]>.999 and gate[begin+700]<.0001
        assert sum(n.startswith(prefix) for n,i in poses)==size
        for who in range(size):
            n=prefix+f"technician {who+1}";actor=names[n];t=xyz(actor)
            assert parents[actor]==deck and scale(actor)[begin+200]>.999
            assert scale(actor)[begin+780]<.001 and scale(actor)[repair]<.001
            assert t[begin+18,0]<crew.PLATE_IN and t[begin+105,0]>crew.PLATE_IN
            assert np.linalg.norm(t[begin+305,:2]-crew.workpoint(b,who))<.00002
            still=[(105,tw[0]),(tw[1]+8,tw[2]-8),(tw[3]+8,695)] if turbine else [(105,695)]
            for a0,a1 in still:assert np.max(abs(np.diff(t[begin+a0:begin+a1],axis=0)))<.00003
            assert np.allclose(t[begin+775],t[begin+18],atol=.00002)
            moving=z[begin:begin+780]>crew.STOW+.003
            # While the deck travels, everyone is on it. The turbine crew step off it only at the top.
            if turbine:moving&=np.abs(np.gradient(z[begin:begin+780]))>1e-6
            foot=t[begin:begin+780][moving]
            assert np.min(np.hypot(foot[:,0],foot[:,1]))>crew.PLATE_IN
            assert np.max(np.hypot(foot[:,0],foot[:,1]))<crew.PLATE_OUT
            assert np.min(foot[:,0]*math.sin(crew.HALF)-abs(foot[:,1])*math.cos(crew.HALF))>.74
            pose_ids=[i for i,pa in parents.items() if pa==actor]
            assert np.allclose(np.sum([scale(i)[begin+8:begin+777] for i in pose_ids],axis=0),1,atol=.0002)
            active=[i for label,i in names.items() if label.startswith(n+" | inspect ")]
            work=slice(begin+tw[1]+8,begin+tw[2]-8) if turbine else slice(begin+300,begin+400)
            assert len(active)==6 and all(scale(i)[work].max()>.999 for i in active)
            if turbine:
                # At the turbine they stand on the folded side of the module, under the upper module, with the side fully down.
                a=p.plant;at=begin+(tw[1]+tw[2])//2
                assert p.FILLED+p.clock.ENCLOSURE_OPEN[1]<begin+tw[0] and begin+tw[3]<p.FILLED+p.clock.ENCLOSURE_CLOSE[0]
                place=rotate(t[at,:2],yaw(root)[at]-a.POWER_YAW)
                assert abs(place[0])<a.LENGTH/2-.3 and a.WIDTH/2+.2<abs(place[1])<a.WIDTH/2+a.PANEL_HEIGHT-.2
                assert abs(z[at]+t[at,2]-crew.POWER_FLOOR)<.02
                for i in active:
                    assert z[at]+t[at,2]+points(i)[:,2].max()<a.power_base(p.CROWN,1)-.3
                # Before and after, they wait on the deck clear of the swinging side.
                for f in (begin+tw[0]-1,begin+tw[3]+12):
                    wait=rotate(t[f,:2],yaw(root)[f]-a.POWER_YAW)
                    assert abs(wait[1])>a.WIDTH/2+a.PANEL_HEIGHT+.2
    # The camera-facing equipment has a faint real material in the GLB.
    cooler_names=[n for n in names if re.fullmatch(r"Cooler frame \d\d \| cooler \d",n)]
    ghost_ids=[names[n+" | inspection finish"] for n in cooler_names]
    assert len(ghost_ids)==p.cfg.COOLERS and p.cfg.COOLERS//4<=sum(scale(i)[begin+330]>.99 for i in ghost_ids)<=p.cfg.COOLERS*7//8
    orbit=slice(p.FILLED+c.ORBIT,p.FILLED+c.ORBIT_DONE+1)
    assert all(scale(i)[orbit].max()<.001 for i in ghost_ids)
    crown=names["Steel module | shaft, bearings, rim girders and braced columns | inspection finish"]
    assert scale(crown)[begin+480]>.99 and scale(crown)[begin+300]<.001 and scale(crown)[orbit].max()<.001

    fresh=names[f"Replacement {p.TOTAL+1:03} | L{c.LEVEL:02} B{c.BAY:02}"];old=ids[c.BAD]
    skins=[names["Swap | amber fault case"],names[f"Original pod {c.BAD+1:03} | bronze before fault"]]
    assert all(parents[i]==old for i in skins)
    for i in (fresh,skins[0],skins[1]):
        assert np.allclose(np.ptp(points(i),axis=0),[p.cfg.length(p.TOTAL+1 if i==fresh else c.BAD+1),p.cargo.FRAME_WIDTH,p.cargo.FRAME_HEIGHT],atol=.000002)
    assert np.allclose(scale(skins[0])+scale(skins[1]),1,atol=.0002)
    assert scale(skins[0])[repair+35]>.999 and scale(fresh)[repair+299]<.001 and scale(fresh)[repair+301]>.999
    assert doc["extras"]["defectivePod"]==c.BAD+1 and doc["extras"]["neighboursAbove"]==p.LEVELS-c.LEVEL and doc["extras"]["neighboursBelow"]==c.LEVEL-1
    allcases=ids+[fresh];N=len(allcases)
    xy=np.empty((end,N,2));a=np.empty((end,N));z=np.empty((end,N));on=np.empty((end,N),bool)
    ext=np.empty((end,N))
    for j,i in enumerate(allcases):
        slot=parents[i];level=parents[slot]
        assert parents[level]==rack
        carrier=(yaw(slot)+yaw(level))[repair:]
        t=xyz(i)[repair:]
        xy[:,j]=rotate(t[:,:2],carrier)
        a[:,j]=carrier+yaw(i)[repair:]
        z[:,j]=t[:,2];on[:,j]=scale(i)[repair:]>.999
        prefix=f"Pod {j+1:03}" if j<p.TOTAL else f"Replacement {p.TOTAL+1:03}"
        ext[:,j]=scale(names[prefix+" | retractable service plug"])[repair:]
        fixed=ext[:,j]>.002
        bay=j%p.BAYS if j<p.TOTAL else c.BAY-1
        lev=p.LEVELS-j//p.BAYS if j<p.TOTAL else c.LEVEL
        assert np.max(np.abs(wrap(a[fixed,j]-p.services.PORT_ANGLES[bay])))<.00015
        assert np.max(np.abs(xy[fixed,j]))<.00006 and np.max(np.abs(z[fixed,j]-p.level_z(lev)))<.00006
        if j>=p.TOTAL:continue
        if lev!=c.LEVEL and bay==c.BAY-1:
            assert ext[106:1152,j].max()<.005
            assert abs(abs(wrap(a[152,j]-c.PORT))-p.PACKED)<.00003
            assert abs(abs(wrap(a[305,j]-p.ENTRY))-p.PACKED)<.00003
            assert abs(wrap(a[1147,j]-c.PORT))<.00003
        if lev!=c.LEVEL:
            assert abs(z[:,j]-p.level_z(lev)).max()<.00003
    assert np.allclose(ext[109:1151],0,atol=.0001)
    assert (ext[0]>.999).sum()==(ext[-1]>.999).sum()==p.TOTAL and ext[-1,c.BAD]<.00001 and ext[-1,-1]>.999
    for lev in range(p.LEVELS):
        local_angles=a[152,lev*p.BAYS:(lev+1)*p.BAYS]%(2*math.pi)
        normalized=np.sort((local_angles-c.PORT)%(2*math.pi))
        gaps=np.sort(np.diff(np.r_[normalized,normalized[0]+2*math.pi]))*180/math.pi
        if p.LEVELS-lev!=c.LEVEL:assert np.allclose(gaps,[math.degrees(p.PACKED)]*(p.BAYS-1)+[360-math.degrees(p.PACKED)*(p.BAYS-1)],atol=.003)
    expected=rotate(np.array([14.5,4.5]),p.ENTRY)
    assert np.max(np.abs(xy[644:,c.BAD]-expected))<.0001
    assert np.max(abs(wrap(a[644:,c.BAD]-p.ENTRY)))<.00003 and abs(z[504:,c.BAD]).max()<.00003
    staged=rotate(np.array([14.5,-4.5]),p.ENTRY)
    assert np.allclose(xy[301:648,-1],staged,atol=.0001) and np.allclose(z[301:803,-1],0,atol=.00003)
    assert np.allclose(xy[792:,-1],0,atol=.00004) and np.allclose(z[965:,-1],p.level_z(c.LEVEL),atol=.00004)
    assert abs(wrap(a[-1,-1]-c.PORT))<.00002

    # Build actual horizontal footprints at every video frame, including the
    # quarantined case while the occupied rack rotates back to its own ports.
    rect=np.array([p.cargo.footprint(i) for i in range(1,N+1)])
    corners=xy[:,:,None,:]+rotate(rect,a[:,:,None])
    cluster=p.PACKED
    mingap=min(2*(r*math.sin(cluster/2)-w*math.cos(cluster/2)) for r,w in p.cargo.PROFILE)
    for lev in range(p.LEVELS):
        slots=[j for j in range(lev*p.BAYS,(lev+1)*p.BAYS) if j!=c.BAD]
        fixed=np.sort(np.mod(a[:,slots],2*math.pi),axis=1)
        sep=np.diff(np.column_stack((fixed,fixed[:,0]+2*math.pi)),axis=1)
        assert np.min(sep)>=cluster-.0001
    gate=xyz(names["Portal rail insert"])[repair:,2]
    ground_passes=[0,0]
    for pick,j in enumerate((c.BAD,p.TOTAL)):
        for w in np.flatnonzero(on[:,j]):
            along=rotate(corners[w,j],-p.ENTRY)
            # Open portal check applies only to the horizontal transfer on rails.
            if z[w,j]<.001 and np.linalg.norm(xy[w,j])>.01 and along[:,0].max()>p.s.RI and along[:,0].min()<p.s.RO:
                assert np.abs(along[:,1]).max()<p.s.OPENING_WIDTH/2 and abs(z[w,j])<.00002 and gate[w]<-.23
                ground_passes[pick]+=1
            diff=np.abs(z[w]-z[w,j])
            neighbours=np.flatnonzero(on[w]&(diff<p.cargo.FRAME_HEIGHT-.0002))
            for k in neighbours:
                if k!=j:assert not overlap(corners[w,j],corners[w,k]),("pod collision",w,j,k)
    assert min(ground_passes)>10 and min(z[433:503,c.BAD])<.0001 and max(z[433:503,c.BAD])>p.level_z(c.LEVEL)+.07
    heads=names["Twin self-releasing pickup heads"]
    head=xyz(heads)[repair:,2];bearing=yaw(parents[heads])[repair:]
    line=names["Twin suspension ropes"]
    length=get(line,"scale",[1,1,1])[repair:,1]
    assert np.allclose(head+length,p.HEAD,atol=.00005)
    for j,start,stop in ((c.BAD,434,503),(p.TOTAL,805,964)):
        assert abs(head[start:stop]-z[start:stop,j]-p.cargo.FRAME_HEIGHT).max()<.00006
        assert abs(wrap(bearing[start:stop]-a[start:stop,j])).max()<.00004
        assert abs(xy[start:stop,j]).max()<.00002
    shoes=scale(names[f"L{c.LEVEL:02}B{c.BAY:02} shaft root lock"])[repair:]
    assert shoes[463:929].max()<.001 and shoes[946]>.999
    # Test hook and cable on both pick radii against every parked casing they
    # pass by in elevation. A hook touching the top of its own load is allowed.
    for r in p.PICKUPS:
        hook_xy=r*np.stack((np.cos(bearing),np.sin(bearing)),axis=1)
        local=rotate(hook_xy[:,None,:]-xy,-a)
        dx=np.maximum.reduce((p.INNER-local[:,:,0],local[:,:,0]-p.INNER-np.array([p.cfg.length(i) for i in range(1,N+1)]),np.zeros((end,N))))
        dy=np.maximum(abs(local[:,:,1])-p.cargo.FRAME_WIDTH/2,0)
        exposed=on&(head[:,None]<z+p.cargo.FRAME_HEIGHT-.00015)
        assert np.min(np.hypot(dx,dy)[exposed])>.118,"hook envelope touches a parked pod"
    print(f"{p.BAYS} decks and {sum(crew.SIZES)} technicians checked from boarding to disembarkation.")
    print(f"Exchange at level {c.LEVEL}, bay {c.BAY}. All {p.LEVELS-1} direct neighbours clear the lane.")
    print(f"Both crane lines and both cases clear parked units. The exchange ends with {p.TOTAL} live positions.")
