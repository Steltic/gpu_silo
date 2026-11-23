"""Fixed coordination components common to the two films and the operating-state IFC."""
from dataclasses import dataclass
import math

from . import completion as calc, crown_detail, design as cfg, foundation, plant, services, silo_model as s

STEEL, ELECTRIC, COOL, FUEL = "668283", "d69c48", "60999a", "ceae63"


@dataclass
class Part:
    tag: str
    kind: str
    name: str
    material: str
    stage: str
    level: str
    mesh: object
    data: dict


def block(tag, kind, name, material, stage, level, pos, size, colour, **data):
    x,y,z = pos
    dx,dy,dz = size
    m = plant.mesh(name)
    plant.closed(m,x-dx/2,y-dy/2,x+dx/2,y+dy/2,z,z+dz,colour)
    return Part(tag,kind,name,material,stage,level,m,data)


def pipe(tag, kind, name, material, stage, level, points, radius, colour, **data):
    m = plant.mesh(name)
    for a,b in zip(points,points[1:]):
        services.pipe(m,a,b,radius,colour,n=12)
    return Part(tag,kind,name,material,stage,level,m,data)


def ring(tag,kind,name,material,stage,level,inner,outer,lo,hi,colour,**data):
    m = plant.mesh(name)
    s.sector(m,inner,outer,lo,hi,0,s.TAU,48,[colour]*4,caps=False)
    return Part(tag,kind,name,material,stage,level,m,data)


def products():
    from . import fuel, site, cooler_frames as frames
    from . import layering
    d, u = calc.D, calc.MECH
    yield ring("F-BOSS","IfcFooting","Local raft thickening below shaft","Reinforced concrete","base","Base",0,
               calc.SITE["slab_boss_radius_m"],-foundation.C["drawn"]-calc.SITE["slab_boss_extra_m"],-foundation.C["drawn"],"89928c")
    for i in range(foundation.BASE["bolts"]):
        x,y,_ = s.polar(foundation.BASE["bolt_circle_m"]/2,s.TAU*i/foundation.BASE["bolts"],0)
        yield pipe(f"F-AN-{i+1:02}","IfcMechanicalFastener","M56 headed shaft anchor","Grade 105 steel","base","Base",
                   [(x,y,-2.15),(x,y,.095)],.028,STEEL,EmbedmentM=2.15)
    yield ring("ROOF-CURB","IfcWall","Ventilated roof curb and removable lid seat","Structural steel","roof","Roof",
               cfg.OUTSIDE_R-.15,cfg.OUTSIDE_R,cfg.SILO["height_m"],plant.LID_Z,"91a29d")
    for i,(x,y) in enumerate(plant.EXHAUST_AT):
        a=plant.turned(x,y)
        yield pipe(f"EX-{i+1}","IfcDuctSegment","Insulated turbine exhaust transition","Stainless steel and mineral insulation","roof","Roof",
                   [(a[0],a[1],plant.power_base(cfg.CROWN,1)+plant.SET_H),(a[0],a[1],plant.LID_Z+.01)],
                   plant.EXHAUST_R,"a3b1af",InsulationMm=150,InletTemperatureC=566)
    for i,y in enumerate((-.22,.22)):
        yield pipe(f"MV-{i+1}","IfcCableCarrierSegment","13.8 kV main bus in fixed shaft","Insulated copper","cage","Base",
                   [(0,y,plant.power_base(cfg.CROWN,1)),(0,y,-.75),(0,32+i,-.75),(-51,53+i,-.75)],
                   .13,ELECTRIC,RatedA=u["bus_amps"],VoltageKV=u["bus_kv"])
    yield block("GRID","IfcSwitchingDevice","Utility intertie and protection, 6 MW","Electrical equipment","services","Site",
                (-52,50,0),(5,2.2,2.8),ELECTRIC,CapacityMW=u["grid_import_mw"])
    yield block("UPS","IfcElectricFlowStorageDevice","10 MW essential UPS and battery enclosure","Battery equipment","services","Site",
                (-58,50,0),(10,3.2,3.0),"9bada0",UsableFraction=.8,StoredMWh=u["ups_mwh"],PowerMW=u["ups_mw"])
    for bay,a in enumerate(services.PORT_ANGLES,1):
        # Foundation-supported conversion plant keeps transformer weight off the moving pods.
        tx,ty=-63+4*(bay-1),59.
        yield block(f"TX-{bay:02}","IfcTransformer","Bay transformer 13.8 / 1.0 kV","Dry-type transformer","services","Site",
                    (tx,ty,0),(3.2,4.4,3.4),ELECTRIC,RatedMVA=7.5,Bay=bay)
        yield block(f"SW-{bay:02}","IfcElectricDistributionBoard","Eight-way protected bay switchboard","Electrical equipment","services","Site",
                    (tx,ty+3.1,0),(2.8,1.2,2.2),STEEL,OutgoingCircuits=8,BreakerA=630)
        yield block(f"PAD-{bay:02}","IfcFooting","Transformer and switchboard plinth","Reinforced concrete","base","Site",
                    (tx,ty+.75,-.35),(3.65,6.4,.35),"a1a39a")
        yield pipe(f"MV-F-{bay:02}","IfcCableCarrierSegment","Bay primary feeder","Insulated copper","services","Site",
                   [(-51,53,-.75),(tx,ty,-.75),(tx,ty,0)],.08,ELECTRIC,RatedA=u["level_amps"])
        ra=cfg.OUTSIDE_R+.07
        outside=s.polar(ra,a,-1.0)
        yield pipe(f"LV-Y-{bay:02}","IfcCableCarrierSegment","Eight protected low-voltage circuits to bay","Insulated copper","services","Site",
                   [(tx,ty,0),(tx,ty,-1),outside],.19,ELECTRIC,Circuits=cfg.LEVELS)
        yield pipe(f"LV-R-{bay:02}","IfcCableCarrierSegment","Exterior bay bus riser","Insulated copper","services","Base",
                   [outside,s.polar(ra,a,services.port_height(cfg.LEVELS)-.42)],.14,ELECTRIC,Circuits=cfg.LEVELS)
        for lev in range(1,cfg.LEVELS+1):
            z=services.port_height(lev)-.42
            label=f"Pod {lev:02}"
            yield pipe(f"LV-D-{lev:02}-{bay:02}","IfcCableCarrierSegment","Dry sleeved power tap with movement joint","Insulated copper","services",label,
                       [s.polar(ra,a,z),s.polar(cfg.BORE_R-.005,a,z)],.085,ELECTRIC,RatedA=630,VoltageKV=1)
            yield pipe(f"PLUG-{lev:02}-{bay:02}","IfcOutlet","De-energised docking contact and earth pilot","Electrical equipment","services",label,
                       [s.polar(cfg.BORE_R-.005,a,z),s.polar(cfg.BORE_R-cfg.POD["tip_clearance_m"],a,z)],.075,ELECTRIC,
                       Interlock="Open breaker, prove dead, retract before rotation")
        yield pipe(f"FO-{bay:02}","IfcCableSegment","Dual fibre to stationary docking controls","Optical fibre","cage","Base",
                   [s.polar(.38,a,0),s.polar(.38,a,plant.CURB+cfg.CROWN)],.012,"658a90")
    for lev in range(1,cfg.LEVELS+1):
        z=cfg.STORE["lowest_berth_m"]+(lev-1)*cfg.STORE["pitch_m"]
        for bay,a in enumerate(services.PORT_ANGLES,1):
            for sign in (-1,1):
                lo=services.port_height(lev)+.015
                pts=[services.beside(a,sign*layering.POD_Y,layering.POD_R-off,lo) for off in (.18,.03)]
                yield pipe(f"CV-{lev:02}-{bay:02}-{sign}","IfcValve","Pod branch isolation and balancing valve",
                           "Process pipe","services",f"Pod {lev:02}",pts,.095,COOL,BoreMm=125)
        yield block(f"DR-{lev:02}","IfcElectricMotor","Level indexing drive and brake","Drive equipment","cage",f"Pod {lev:02}",
                    (.86,-.31,z+.15),(.33,.25,.36),STEEL,MotorKW=1.5,LockTorqueKNm=60)
        yield ring(f"OPT-{lev:02}","IfcCommunicationsAppliance","Optical rotary joint and absolute encoder","Control equipment","cage",f"Pod {lev:02}",
                   .59,.64,z+.27,z+.34,"c28b53")
    for i in range(2):
        a=math.radians(118+13*i)
        px,py,_=s.polar(23,a,0)
        yield block(f"AHU-{i+1}","IfcUnitaryEquipment","Bore air handler with independent cooling circuit","HVAC equipment","services","Site",
                    (px,py,.12),(4.8,2.6,2.6),COOL,CoolingKW=u["ahu_kw"],AirM3s=u["ahu_flow_m3s"],Duty="one duty, one standby")
        # Supply and return use the two dry ducts through the raised curb above the tank.
        dx,dy,_=s.polar(19,a,0)
        m=plant.mesh("Bore air supply" if not i else "Bore air return")
        pts=[(px,py,1.3),(dx,dy,1.3),(dx,dy,32.38),s.polar(cfg.BORE_R-.2,a,32.38)]
        for start,end in zip(pts,pts[1:]):
            s.bar(m,start,end,2.5,COOL,.60)
        yield Part(f"AH-D-{i+1}","IfcDuctSegment",m.name,"Galvanised steel","roof","Roof",m,{"AirM3s":u["ahu_flow_m3s"]})
    for r,name in ((23.8,"Supply"),(22.2,"Return")):
        pts=[s.polar(r,math.radians(deg),1.1) for deg in (118,124.5,131)]
        yield pipe("AH-H-"+name,"IfcDuctSegment","Common "+name.lower()+" header and changeover dampers",
                   "Galvanised steel","services","Site",pts,.65,COOL)
    for index in range(2):
        y=(-1,1)[index]*.22
        top=plant.power_base(cfg.CROWN,1)
        pt=plant.turned(plant.SET_L*.32,(-1,1)[index]*plant.SET_Y,top+.42)
        yield pipe(f"MV-G-{index+1}","IfcCableCarrierSegment","Generator lead to shaft bus","Insulated copper","services","Turbines",
                   [pt,(0,y,top+.42),(0,y,top)],.13,ELECTRIC)
    for i,a in enumerate((site.WATER_BEARING+.35,site.WATER_BEARING-.35)):
        if i:
            lo=layering.COVER_Z[0]-.08
            yield pipe("STORE-VENT-2","IfcPipeSegment","Second screened atmospheric breather","Process pipe","roof","Store",
                       [s.polar(s.RI_OUTER-.1,a,lo),s.polar(s.RO+.25,a,lo),s.polar(s.RO+.25,a,lo-.30)],.05,COOL)
        x,y,_=s.polar(s.RI_OUTER-.38,a,0)
        yield pipe(f"TT-{i+1}","IfcSensor","Store temperature string and level transmitter","Control equipment","services","Store",
                   [(x,y,.50),(x,y,layering.COVER_Z[0])],.018,STEEL)
    for i in range(2):
        # The trains share an outdoor discharge manifold at the tank header.
        x,y,_=services.beside(fuel.BEARING,5+6*i,fuel.HEADER_R-7,0)
        yield block(f"VP-{i+1}","IfcHeatExchanger","Indirect hot-water propane vaporiser train","Pressure equipment","fuel","Site",
                    (x,y,.15),(3.6,2.1,2.2),FUEL,DutyMW=u["vapour_train_mw"],OutletBar=30,HeatingWaterC=u["vaporiser_water_c"])
        px,py,_=services.beside(fuel.BEARING,5+6*i,fuel.HEADER_R-4,0)
        yield block(f"FP-{i+1}","IfcPump","LPG liquid booster pump and emergency isolation","Process equipment","fuel","Site",
                    (px,py,.10),(1.5,1,.90),STEEL,NettedDutyKgS=3.1)
        yield pipe(f"VP-L-{i+1}","IfcPipeSegment","Isolatable vaporiser branch","Process steel","fuel","Site",
                   [services.beside(fuel.BEARING,5+6*i,fuel.HEADER_R,.45),(x,y,.45),(x,y,1.2),
                    services.beside(fuel.BEARING,0,fuel.HEADER_R-7,1.2),s.polar(fuel.HEADER_R,fuel.BEARING,fuel.BURIED)],.06,FUEL)
    hx,hy,_=services.beside(fuel.BEARING,10,fuel.HEADER_R-16,0)
    yield block("VP-HEAT","IfcBoiler","Indirect vaporiser startup boiler and circulation skid","Pressure equipment","fuel","Site",
                (hx,hy,0),(4.0,2.4,2.5),STEEL,OutputMW=1.75,WaterC=u["vaporiser_water_c"])
    for sign in (-1,1):
        pts=[(hx,hy+sign*.22,.7),services.beside(fuel.BEARING,5,fuel.HEADER_R-7+sign*.22,.7),
             services.beside(fuel.BEARING,11,fuel.HEADER_R-7+sign*.22,.7)]
        yield pipe("VP-HW-"+str(sign),"IfcPipeSegment","Vaporiser hot-water header","Process steel","fuel","Site",pts,.08,STEEL)
    for i,(x,y,_) in enumerate(plant.GEN_AT):
        z=plant.power_base(cfg.CROWN,0)+.40
        xyz=plant.turned(x,y,z)
        feed=services.beside(fuel.BEARING,-fuel.SIDE,fuel.DROP_R,fuel.diesel_end(cfg.CROWN))
        yield pipe(f"OIL-G-{i+1}","IfcPipeSegment","Isolated diesel branch at generator","Process steel","fuel","Diesel",
                   [feed,(feed[0],feed[1],z),xyz],.025,"aa6150")
    for i,side in enumerate((-1,1)):
        gas=s.polar(fuel.DROP_R,fuel.BEARING,fuel.drop_end(cfg.CROWN))
        pt=plant.turned(0,side*plant.SET_Y,gas[2])
        yield pipe(f"GAS-G-{i+1}","IfcPipeSegment","Regulated fuel branch at turbine","Process steel","fuel","Turbines",
                   [gas,pt],.075,FUEL,DeliveryBar=30)
    bx,by=fuel.FARM_R-fuel.LENGTH/2+fuel.BULK_L/2,fuel.BULK_Y
    local=lambda x,y,z: services.beside(fuel.BEARING,y,x,z)
    bund=plant.mesh("Bulk diesel containment")
    for y in (by-4,by+4):
        s.bar(bund,local(bx-7,y,.60),local(bx+7,y,.60),.20,"9b9c89",1.20)
    for x in (bx-7,bx+7):
        s.bar(bund,local(x,by-4,.60),local(x,by+4,.60),.20,"9b9c89",1.20)
    yield Part("OIL-BUND","IfcWall","Bulk diesel containment with isolated sump","Reinforced concrete","fuel","Site",bund,{"NetRetentionM3":83.0})
    yield pipe("OIL-TRANSFER","IfcPipeSegment","Double-contained diesel transfer to buried header","Process steel","fuel","Site",
               [local(bx,by,.45),local(bx,by,-1.4),local(fuel.HEADER_R,-fuel.SIDE,-1.4)],.042,"ab624a")
    for k,a in enumerate(frames.BEARINGS,1):
        z=frames.base(k-1)
        m=plant.mesh("Discharge separator and frost drain")
        for row in range(frames.ROWS):
            elev=z+(row+1)*frames.ROW-.1
            pts=[services.beside(a,y,r,elev) for r,y in ((frames.BACK+frames.DEPTH,-6),(frames.BACK+frames.DEPTH+1.0,-6),
                                                          (frames.BACK+frames.DEPTH+1.0,6),(frames.BACK+frames.DEPTH,6))]
            m.face(pts,"8ea6a2")
        yield Part(f"CF-D-{k:02}","IfcShadingDevice","Cooler row discharge separators","Coated steel","services","Coolers",m,{"ProjectionM":1.0})
        for j in range(frames.ROWS):
            z0=z+j*frames.ROW+.30
            yield pipe(f"DRN-{k:02}-{j+1}","IfcValve","Automatic frost drain and vacuum relief","Process pipe","services","Coolers",
                       [services.beside(a,frames.PUMP_Y,frames.BACK+.26,z0),services.beside(a,frames.PUMP_Y,frames.BACK+.26,z0-.20)],.065,COOL)
    for level in (0,1):
        lo=plant.power_base(cfg.CROWN,level)+plant.SEAT_Z
        count = plant.TURBINE_MOUNTS if level else plant.RIG["wall_mounts"]
        for j,a in enumerate(plant.mount_angles(count)):
            a+=plant.POWER_YAW
            closure=plant.mesh("Field-fit bearing and weld closure")
            s.sector(closure,cfg.BORE_R-.076,cfg.BORE_R,lo-.14,lo+.44,a-.028,a+.028,4,[STEEL]*4)
            yield Part(f"CLOSURE-{level+1}-{j+1:02}","IfcDiscreteAccessory",closure.name,"Structural steel",
                       "turbine seats" if level else "rig seats","Turbines" if level else "Diesel",closure,{"Fit":"Install after landing"})
            m=plant.mesh("Four bent crown anchor hairpins")
            diameter=calc.D["anchor_rebar_mm"]
            offsets=calc.D["hairpin_near_leg_offsets_m"]
            for y in offsets:
                pts=[services.beside(a,side,cfg.BORE_R+radial,lo+h)
                     for radial,side,h in crown_detail.hairpin_path(y)]
                for pa,pb in zip(pts,pts[1:]):services.pipe(m,pa,pb,diameter/2000,"8e7769",n=6)
            yield Part(f"SEAT-BAR-{level+1}-{j+1:02}","IfcElementAssembly",m.name,"Reinforcement","cage",
                       "Turbines" if level else "Diesel",m,{"NominalDiameterMm":diameter,"Legs":2*len(offsets),
                       "DesignCheck":10 if level else 9,"TailBelowSeatM":calc.D["hairpin_tail_below_seat_m"]})
    for upper in (False,True):
        m=plant.mesh("Portal hoop bypass")
        for row in range(6):
            for col in range(4):
                r=cfg.OUTSIDE_R-.075-col*.075
                elev=cfg.DOOR_HEIGHT+.10+row*.13 if upper else -.20-row*.13
                phi=(2.4+cfg.DOOR_WIDTH/2)/r
                s.sector(m,r-.0179,r+.0179,elev-.0179,elev+.0179,s.ENTRY-phi,s.ENTRY+phi,10,["8e7769"]*4)
        yield Part("PORTAL-"+("HEAD" if upper else "TIE"),"IfcElementAssembly",m.name,"Duplex stainless reinforcement",
                   "base","Store",m,{"BarCount":24,"BarSize":"#11"})
    o=cfg.PROJECT["thermal"]["overflow"]
    for label,offset in (("Fill",0),("Overflow",o["offset_from_fill_line_m"])):
        at=lambda r,z: services.beside(site.WATER_BEARING,offset,r,z)
        yield pipe("W-"+label.upper(),"IfcPipeSegment",label+" line below the ring road","Process pipe","base","Site",
                   [at(cfg.OUTSIDE_R+1.3,.45),at(cfg.OUTSIDE_R+1.3,-1.25),at(site.R_RUN+site.HALF+1.2,-1.25),at(site.R_RUN+site.HALF+1.2,.45)],
                   .10 if offset else .16,COOL)


def install(scene,node,p):
    from . import closing
    from . import maintenance as care
    stages={"base":1,"cage":p.clock.CAGE_END,"services":p.FILLED+plant.DIESEL_SEATED,
            "roof":p.FILLED+care.LID[1],"fuel":p.FILLED+closing.LINE,"rig seats":p.clock.RIG_END,
            "turbine seats":p.FILLED+plant.PICK_STARTS[1]+plant.PICK_LENGTH}
    groups={}
    for part in products():
        if scene.short_presentation and (part.tag=="PORTAL-HEAD" or part.tag.startswith("CF-D-")):
            continue
        group=groups.setdefault(part.stage,plant.mesh("Revision J | "+part.stage+" components"))
        group.tris.extend(part.mesh.tris)
        if scene.short_presentation and part.tag in ("AHU-1","AHU-2"):
            from . import short_art
            positions=[v for tri in part.mesh.tris for v in tri[:3]]
            low=[min(v[i] for v in positions) for i in range(3)]
            high=[max(v[i] for v in positions) for i in range(3)]
            short_art.air_handler(group,((low[0]+high[0])/2,(low[1]+high[1])/2,low[2]))
    for stage,m in groups.items():
        f=stages[stage]
        node(m.name,scene.mesh(m),"Permanent services",tracks={"scale":[(0,(0,0,0)),(f-.02,(0,0,0)),(f,(1,1,1))]})
