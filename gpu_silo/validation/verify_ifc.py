"""Reopen the STEP exchange and check schema, spatial structure, equipment and every body."""
from collections import Counter
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.validate
import numpy as np

from .. import completion, crown_detail, design as cfg, plant


def verify(path):
    f=ifcopenshell.open(str(path))
    assert f.schema=="IFC4"
    roots=f.by_type("IfcRoot")
    assert len({o.GlobalId for o in roots})==len(roots)
    log=ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(f,log)
    if log.statements:
        raise ValueError([str(i["message"])[:350] for i in log.statements[:5]])
    project,=f.by_type("IfcProject")
    site,=project.IsDecomposedBy[0].RelatedObjects
    building,=site.IsDecomposedBy[0].RelatedObjects
    assert site.is_a("IfcSite") and building.is_a("IfcBuilding")
    floors=f.by_type("IfcBuildingStorey")
    assert all(o.Decomposes[0].RelatingObject==building for o in floors)
    assert len(floors)==cfg.LEVELS+6
    elements=[o for o in f.by_type("IfcElement") if not o.is_a("IfcFeatureElement")]
    tags={o.Tag:o for o in elements}
    assert len(tags)==len(elements)
    for obj in elements:
        assert len(obj.ContainedInStructure)+len(obj.Decomposes)==1, obj.Name
    racks=f.by_type("IfcCommunicationsAppliance")
    racks=[o for o in racks if o.Tag.startswith("POD-")]
    assert len(racks)==cfg.RACKS
    boxes=[o for o in f.by_type("IfcElementAssembly") if o.Tag.startswith("POD-") and not o.Tag.endswith("-FRAME")]
    assert len(boxes)==cfg.TOTAL
    centres=[]
    for pod in boxes:
        parts=pod.IsDecomposedBy[0].RelatedObjects
        counts=Counter(o.is_a() for o in parts)
        assert counts["IfcCommunicationsAppliance"]==cfg.CLUSTER["racks_per_pod"]
        assert counts["IfcPump"]==counts["IfcHeatExchanger"]==1
        rack=next(o for o in parts if o.Tag.endswith("-R1"))
        pos=ifcopenshell.util.placement.get_local_placement(rack.ObjectPlacement)[:3,3]
        centres.append(tuple(np.round(pos,4)))
        assert abs(np.hypot(*pos[:2])-(cfg.STORE["root_radius_m"]+cfg.BODY_LENGTH/8))<1e-4
    assert len(set(centres))==cfg.TOTAL
    assert len(f.by_type("IfcElectricGenerator"))==cfg.POWER["modules"]+cfg.PROJECT["diesel"]["sets"]
    assert len([k for k in tags if k.startswith("Dry coolers/")])==cfg.COOLERS
    basis=ifcopenshell.util.element.get_psets(project)["GPU Silo Basis"]
    assert basis["Revision"]==cfg.PROJECT["design_checks"]["revision"]
    assert basis["NormalITLimitMW"]==cfg.CLUSTER["normal_it_limit_mw"] and basis["RackAssignment"]=="Operator selected"
    for kind,member in ((7,"Diesel/Open ring beam"),(8,"Diesel/Collar drag arm 01"),(10,"Turbines/Open ring beam")):
        assert ifcopenshell.util.element.get_psets(tags[member])["GPU Silo Design"]["DesignCheck"]==kind
    for level,prefix in enumerate(("Top rig mount","Turbine level mount")):
        deck=completion.floor(level)
        hef=completion.seat(level,deck,completion.lateral())["hef"]
        for j,v in enumerate(deck["all_mounts"],1):
            plate=tags[f"Rig mounts/{prefix} {j:02} | cast-in wall plate"]
            data=ifcopenshell.util.element.get_psets(plate)["GPU Silo Design"]
            assert data["SeatNumber"]==j and data["DesignCheck"]==(10 if level else 9)
            assert np.isclose(data["FactoredVerticalKN"],1.6*v)
            plate_z=ifcopenshell.util.placement.get_local_placement(plate.ObjectPlacement)[2,3]
            assert min(crown_detail.cone_clearances(plate_z,completion.angles(len(deck["all_mounts"])),hef))>0
            bars=tags[f"SEAT-BAR-{level+1}-{j:02}"]
            bar_data=ifcopenshell.util.element.get_psets(bars)["GPU Silo Design"]
            assert bar_data["Legs"]==2*len(completion.D["hairpin_near_leg_offsets_m"])
            assert bar_data["TailBelowSeatM"]==completion.D["hairpin_tail_below_seat_m"]
    assert len([k for k in tags if k.startswith("Cooler embeds/")])==160
    assert len([k for k in tags if k.startswith("Fuel storage/Propane tank")])==cfg.PROJECT["fuel"]["tanks"]
    assert len([k for k in tags if k.startswith("TX-")])==cfg.BAYS
    assert tags["RAFT"].Representation and tags["LID"].Representation and tags["SHAFT"].Representation
    inventory={obj.id():obj for obj in elements if obj.Representation}
    settings=ifcopenshell.geom.settings()
    settings.set("use-world-coords",True)
    it=ifcopenshell.geom.iterator(settings,f,2,include=list(inventory.values()))
    assert it.initialize()
    seen=set()
    while True:
        shape=it.get()
        coords=np.asarray(shape.geometry.verts).reshape(-1,3)
        assert len(coords)>=3 and np.isfinite(coords).all() and len(shape.geometry.faces)>=3
        name=inventory[shape.id].Tag
        if name.startswith("SEAT-BAR-"):
            level=int(name.split("-")[2])-1
            seat_z=plant.power_base(cfg.CROWN,level)+plant.SEAT_Z
            assert np.isclose(coords[:,2].min(),seat_z-completion.D["hairpin_tail_below_seat_m"],atol=.001)
            assert seat_z+completion.D["hairpin_top_m"] <= coords[:,2].max() <= seat_z+completion.D["hairpin_top_m"]+.020
        if name=="RAFT":
            assert np.allclose([coords[:,2].min(),coords[:,2].max()],[-cfg.PROJECT["logistics"]["concrete"]["slab_thickness_m"],0],atol=1e-4)
        if name=="LID":
            assert coords[:,2].min()>cfg.SILO["height_m"]
        seen.add(shape.id)
        if not it.next():break
    missing=set(inventory)-seen
    if missing:raise ValueError("Unreadable IFC bodies: "+", ".join(inventory[i].Name for i in missing))
    print(f"{Path(path).name}: IFC4, {len(elements)} assets, {len(floors)} storeys, {len(seen)} geometric bodies, "
          f"{len(boxes)} pods / {len(racks)} racks; schema and full geometry passed.")
