"""Checks that apply only to the short film: the build, with no service or commissioning scenes."""
import re

import numpy as np


def check(p,doc,names,parents,get,points):
    from .. import cagebuild,coating,film,logistics,shortfilm
    a=p.plant;clock=p.clock;closing=p.closing
    assert film.SHORT and doc["extras"].get("film")=="short"
    # Nothing from the service scenes is in this film.
    for name in names:
        assert not re.search(r"Replacement pod|bronze before fault|Service crew|hinged side|Access platform",name),name
    # The cage: one module for each day of the jumpform, built on the pad, lifted onto the stack and replaced by the finished cage.
    top=p.CAGE_TOP;cuts=p.cage_bounds();swap=cagebuild.swap()
    assert top==p.LEVELS+1 and top==logistics.C["cage_modules"] and len(cuts)==top+1
    assert cagebuild.day(top-1)+cagebuild.WELD_ON[1]<=swap<=p.C
    whole=points(names["Steel module | shaft, bearings, rim girders and braced columns"])
    assert get(names["Preassembled steel store"],"scale",[1,1,1])[swap-1,0]<.001 and get(names["Preassembled steel store"],"scale",[1,1,1])[swap,0]>.999
    stacked=[]
    for m in range(top):
        label=f"Cage level {m+1:02}" if m<top-1 else "Cage crown"
        body=names[label+" | module"];size=get(body,"scale",[1,1,1]);where=get(body,"translation",[0,0,0])
        day=cagebuild.day(m);seated=day+cagebuild.LOWER[1]
        assert size[day,0]<.001 and size[seated,0]>.999 and size[swap,0]<.001,label
        pts=points(body)+[where[seated,0],-where[seated,2],where[seated,1]]      # node translations are y-up; the mesh is z-up
        assert abs(pts[:,2].min()-cuts[m])<.35 and pts[:,2].max()<=cuts[m+1]+.35,(label,pts[:,2].min(),pts[:,2].max(),cuts[m],cuts[m+1])
        assert np.allclose(where[seated:swap],where[seated],atol=.0001)
        # On the pad it stands clear of the outer wall and inside the haul ring.
        pad=where[day+cagebuild.HOOK_ON-2];r=np.hypot(pad[0],pad[2])
        assert r-9.>p.s.RO+2 and r+9.<p.site.R_STOP-p.site.LANE/2+.5,(label,r)
        for i in range(cagebuild.TRUCKS):assert f"{label} | steel on truck {i+1}" in names
        stacked.append(pts)
    stack=np.vstack(stacked)
    centre=stack[:,:2].mean(axis=0)
    assert np.allclose(np.ptp(stack,axis=0),np.ptp(whole,axis=0),atol=.05),"the stacked modules must be the cage that is lifted"
    assert abs(centre[0]-p.PICK_X)<.3 and abs(centre[1])<.3
    counts=doc["extras"]["countersAtEnd"]
    assert counts["cage"]==top
    # The liner: sprayed after the concrete has cured for the product's minimum and before any water is in the store.
    liner=names["Store liner"];size=get(liner,"scale",[1,1,1]);base=p.FILLED
    assert size[base+coating.SPAN[0]-6,0]<.001 and size[base+coating.CLEAR,0]<.001
    assert abs(size[base+coating.RISE[1],1]-p.s.WALL_HEIGHT)<.01 and np.diff(size[base+coating.SPAN[0]:base+coating.RISE[1],1]).min()>=-1e-6
    skin=points(liner);radii=np.hypot(skin[:,0],skin[:,1])
    assert radii.min()>p.s.RO_INNER and radii.max()<p.s.RI_OUTER,"the liner is on the two faces of the gap"
    assert sum(1 for name in names if re.match(r"^Spray stage \d+$",name))==coating.STAGES==p.cfg.PROJECT["coating"]["stages"]
    assert logistics.span("coating")[1]<logistics.span("water")[0],"the store is coated before it is filled"
    assert max(p.liquid_level(f) for f in range(base+coating.CLEAR+1))<1e-6,"no water before the liner is finished"
    # Water arrives over the last two weeks and the store is full at the end.
    first,last,_=logistics.span("water")
    assert last==logistics.DAYS and last-first+1>=14 and abs(p.liquid_level(p.FRAMES-1)-p.cfg.LIQUID_TOP)<.01
    assert counts["water"]==logistics.C["water_loads"]
    # Power levels: deck steel and sets are fabricated on the ground before the picks, with no enclosure.
    for j in (0,1):
        holder=names[f"Power level {j+1:02} | being fabricated"];shown=get(holder,"scale",[1,1,1])[:,0]
        assert shown[base+a.FAB[0]]>.999 and shown[base+a.PICK_STARTS[j]]<.001 and a.FAB_DONE<=a.PICK_STARTS[j]
        strips=[i for name,i in names.items() if name.startswith(f"Power level {j+1} | deck steel, strip")]
        assert len(strips)>=4 and all(get(i,"scale",[1,1,1])[base+a.FAB_DONE-1,0]>.999 for i in strips)
        assert sum(1 for name in names if re.match(rf"^Power level {j+1:02} \| welder \d+$",name))==p.cfg.PROJECT["logistics"]["power_fabrication"]["welders"]
    assert sum(1 for name in names if re.match(r"^Diesel set \d+ \| delivery",name))>=p.cfg.PROJECT["diesel"]["sets"]
    # The dock becomes the control office after the last pod has gone in.
    walls=names["Control office | walls"];begin=base+clock.OFFICE[0]
    assert get(walls,"scale",[1,1,1])[begin-1,0]<.001 and np.allclose(get(walls,"scale",[1,1,1])[base+clock.OFFICE[1]:],1,atol=.0001)
    roof=[i for name,i in names.items() if name.startswith("Control office | roof panel")]
    assert len(roof)==p.yard.ROOF_PANELS and all(np.allclose(get(i,"scale",[1,1,1])[base+clock.OFFICE[1]:],1,atol=.0001) for i in roof)
    assert begin>p.FILLED,"the dock is enclosed after the last pod has gone in"
    box=points(walls)
    assert box[:,2].max()>=p.yard.OFFICE_H-.01 and np.ptp(box[:,1])>2*p.yard.SPAN
    # The three cuts away from pod loading are inside it, in order, and every scene carries a day tag.
    spans=shortfilm.cuts(p)
    assert p.FIRST_POD<spans[0][0] and spans[-1][1]<p.FILLED and all(a[1]<b[0] for a,b in zip(spans,spans[1:]))
    tags=shortfilm.tags(p)
    assert tags[0][0]==0 and all(any(a<=f<b for a,b,*_ in tags) for f in range(0,p.FILLED+closing.PLAN,24))
    assert p.FRAMES==p.FILLED+closing.PLAN+closing.PLAN_FRAMES,"the film ends on the plan and section"
    print(f"Short film: {top} cage modules built beside the walls, {coating.STAGES} spray stages, open power levels and a control office. {p.FRAMES/p.FPS:.0f} s.")
