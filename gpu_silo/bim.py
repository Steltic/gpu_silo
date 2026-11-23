"""Export the installed facility in IFC4. Geometry and placements use metres and Z up."""
import math
import re
import uuid
from collections import defaultdict
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import numpy as np

from . import cargo, completion, components, cooler_frames, crew, design as cfg
from . import foundation, layering, plant, pod_scene, reinforcement, services, silo_model as s, site, structure

IDENTITY=np.eye(4)
NAMESPACE=uuid.UUID("be30e495-3f66-400c-8922-03b88fa6ed80")
COLOURS={"Structural steel":(.32,.45,.46), "Concrete":(.66,.67,.62), "Reinforced concrete":(.60,.63,.60),
         "Equipment":(.54,.64,.62), "Rack":(.62,.48,.29),"Process pipe":(.25,.53,.58),
         "Reinforcement":(.44,.29,.22),"Liner":(.32,.56,.55),"Insulated copper":(.85,.57,.21)}


def gid(key):
    return ifcopenshell.guid.compress(uuid.uuid5(NAMESPACE,key).hex)


def pose(pos=(0,0,0),angle=0,scale=(1,1,1)):
    c,q=math.cos(angle),math.sin(angle)
    m=np.eye(4)
    m[:3,:3]=np.array(((c,-q,0),(q,c,0),(0,0,1))) @ np.diag(scale)
    m[:3,3]=pos
    return m


class Model:
    def __init__(self):
        self.file=ifcopenshell.file(schema="IFC4")
        self.e=self.file.create_entity
        self.reps={}
        self.styles={}
        self.items=defaultdict(list)
        self.children=defaultdict(list)
        self.materials=defaultdict(list)
        self.systems=defaultdict(list)
        self.storeys={}
        self.keys=set()
        self.z=self.direction((0,0,1))
        self.x=self.direction((1,0,0))
        self.origin=self.axis((0,0,0))
        self.profile_origin=self.e("IfcAxis2Placement2D",Location=self.point((0,0)),RefDirection=self.direction((1,0)))
        units=[self.e("IfcSIUnit",UnitType=t,Name=n) for t,n in
               (("LENGTHUNIT","METRE"),("AREAUNIT","SQUARE_METRE"),("VOLUMEUNIT","CUBIC_METRE"),("PLANEANGLEUNIT","RADIAN"))]
        context=self.e("IfcGeometricRepresentationContext",ContextType="Model",CoordinateSpaceDimension=3,
                       Precision=1e-6,WorldCoordinateSystem=self.origin)
        self.body=self.e("IfcGeometricRepresentationSubContext",ContextIdentifier="Body",ContextType="Model",
                         ParentContext=context,TargetView="MODEL_VIEW")
        revision=cfg.PROJECT["design_checks"]["revision"]
        proj=self.e("IfcProject",GlobalId=gid("project"),Name="GPU Silo",Phase=f"Revision {revision} | design review",
                    RepresentationContexts=[context],UnitsInContext=self.e("IfcUnitAssignment",Units=units))
        self.site=self.spatial("IfcSite","Site",None)
        self.building=self.spatial("IfcBuilding","GPU Silo",self.site)
        self.children[proj].append(self.site)
        self.children[self.site].append(self.building)
        self.storeys["Site"]=(self.site,0.)
        for key,z in [("Base",-foundation.C["drawn"]),("Store",0.),("Coolers",cfg.COOL["tier_base_m"][0])]+[
                (f"Pod {i:02}",pod_scene.level_z(i)) for i in range(1,cfg.LEVELS+1)]+[
                ("Diesel",cfg.CROWN),("Turbines",cfg.CROWN+plant.LEVEL[0]),("Roof",cfg.SILO["height_m"])]:
            b=self.spatial("IfcBuildingStorey",key,self.building,z)
            self.children[self.building].append(b)
            self.storeys[key]=(b,z)
        self.props(proj,"Basis",{"Revision":revision,"Issue":"Preliminary design for coordination and review",
                   "Coordinates":"Local metres, shaft centre (0,0), raft top Z=0; site unsurveyed",
                   "Register":"design/report.md#2-register-of-design-checks","Racks":cfg.RACKS,"Pods":cfg.TOTAL,
                   "NormalITLimitMW":cfg.CLUSTER["normal_it_limit_mw"],"RackAssignment":"Operator selected"})

    def point(self,p):
        return self.e("IfcCartesianPoint",Coordinates=tuple(float(x) for x in p))

    def direction(self,p):
        return self.e("IfcDirection",DirectionRatios=tuple(float(x) for x in p))

    def axis(self,p,z=None,x=None):
        return self.e("IfcAxis2Placement3D",Location=self.point(p),Axis=z or self.z,RefDirection=x or self.x)

    def spatial(self,kind,name,parent,z=0.):
        place=self.e("IfcLocalPlacement",PlacementRelTo=parent.ObjectPlacement if parent else None,RelativePlacement=self.axis((0,0,z)))
        item=self.e(kind,GlobalId=gid(kind+name),Name=name,ObjectPlacement=place,CompositionType="ELEMENT")
        if kind=="IfcBuildingStorey":item.Elevation=z
        return item

    def props(self,item,label,values):
        props=[]
        for k,v in values.items():
            kind="IfcBoolean" if isinstance(v,bool) else "IfcInteger" if isinstance(v,int) else "IfcReal" if isinstance(v,(float,np.floating)) else "IfcLabel"
            props.append(self.e("IfcPropertySingleValue",Name=k,NominalValue=self.e(kind,v)))
        ps=self.e("IfcPropertySet",GlobalId=gid(item.GlobalId+label),Name="GPU Silo "+label,HasProperties=props)
        self.e("IfcRelDefinesByProperties",GlobalId=gid(ps.GlobalId+"rel"),RelatedObjects=[item],RelatingPropertyDefinition=ps)

    def style(self,material):
        if material not in self.styles:
            rgb=COLOURS.get(material,COLOURS["Equipment"])
            colour=self.e("IfcColourRgb",Red=rgb[0],Green=rgb[1],Blue=rgb[2])
            shade=self.e("IfcSurfaceStyleRendering",SurfaceColour=colour,Transparency=.70 if material=="Liner" else 0.,
                         ReflectanceMethod="NOTDEFINED")
            self.styles[material]=self.e("IfcSurfaceStyle",Name=material,Side="BOTH",Styles=[shade])
        return self.styles[material]

    def shape(self,type_,pieces,material):
        for item in pieces:
            self.e("IfcStyledItem",Item=item,Styles=[self.style(material)])
        rep=self.e("IfcShapeRepresentation",ContextOfItems=self.body,RepresentationIdentifier="Body",RepresentationType=type_,Items=pieces)
        return self.e("IfcProductDefinitionShape",Representations=[rep])

    def mesh(self,key,m,scale,material):
        ix=(key,tuple(np.round(scale,7)),material)
        if ix in self.reps:return self.reps[ix]
        points,lookup,faces=[],{},[]
        for a,b,c,_ in m.tris:
            ids=[]
            for v in (a,b,c):
                pt=tuple(round(float(t)*float(f),6) for t,f in zip(v,scale))
                if pt not in lookup:
                    points.append(pt)
                    lookup[pt]=len(points)
                ids.append(lookup[pt])
            if len(set(ids))==3:
                faces.append(tuple(ids))
        if not faces:raise ValueError(f"No triangles for {key}")
        vertices=self.e("IfcCartesianPointList3D",CoordList=points)
        shell=self.e("IfcTriangulatedFaceSet",Coordinates=vertices,CoordIndex=faces)
        self.reps[ix]=self.shape("Tessellation",[shell],material)
        return self.reps[ix]

    def solid(self,kind,dimensions,length,material):
        key=(kind,*dimensions,length,material)
        if key not in self.reps:
            if kind=="rect":
                profile=self.e("IfcRectangleProfileDef",ProfileType="AREA",Position=self.profile_origin,XDim=dimensions[0],YDim=dimensions[1])
            elif kind=="ring":
                profile=self.e("IfcCircleHollowProfileDef",ProfileType="AREA",Position=self.profile_origin,Radius=dimensions[1],WallThickness=dimensions[1]-dimensions[0])
            else:
                profile=self.e("IfcCircleProfileDef",ProfileType="AREA",Position=self.profile_origin,Radius=dimensions[0])
            item=self.e("IfcExtrudedAreaSolid",SweptArea=profile,Position=self.origin,ExtrudedDirection=self.z,Depth=length)
            self.reps[key]=self.shape("SweptSolid",[item],material)
        return self.reps[key]

    def product(self,key,kind,name,zone,material,rep=None,matrix=IDENTITY,props=None,parent=None,system=None):
        if key in self.keys:raise ValueError("Duplicate asset tag "+key)
        self.keys.add(key)
        storey,z=self.storeys[zone]
        p=matrix[:3,3]-[0,0,z]
        ux=matrix[:3,0]/np.linalg.norm(matrix[:3,0])
        uz=matrix[:3,2]/np.linalg.norm(matrix[:3,2])
        placement=self.e("IfcLocalPlacement",PlacementRelTo=storey.ObjectPlacement,RelativePlacement=self.axis(p,self.direction(uz),self.direction(ux)))
        obj=self.e(kind,GlobalId=gid(key),Name=name,ObjectType=name,Tag=key,ObjectPlacement=placement,Representation=rep)
        if parent is None:self.items[storey].append(obj)
        else:self.children[parent].append(obj)
        if material:self.materials[material].append(obj)
        if system:self.systems[system].append(obj)
        if props:self.props(obj,"Design",props)
        return obj

    def finish(self,path):
        for parent,children in self.children.items():
            self.e("IfcRelAggregates",GlobalId=gid(parent.GlobalId+"parts"),RelatingObject=parent,RelatedObjects=children)
        for spatial,items in self.items.items():
            self.e("IfcRelContainedInSpatialStructure",GlobalId=gid(spatial.GlobalId+"contains"),RelatedElements=items,RelatingStructure=spatial)
        for name,items in self.materials.items():
            self.e("IfcRelAssociatesMaterial",GlobalId=gid("material"+name),RelatedObjects=items,RelatingMaterial=self.e("IfcMaterial",Name=name))
        for name,items in self.systems.items():
            sys=self.e("IfcSystem",GlobalId=gid("system"+name),Name=name)
            self.e("IfcRelAssignsToGroup",GlobalId=gid("members"+name),RelatedObjects=items,RelatingGroup=sys)
        h=self.file.header
        h.file_description.description=("GPU Silo multidisciplinary coordination model",)
        h.file_name.name=path.name
        h.file_name.author=("Steltic GPU Silo project",)
        h.file_name.originating_system=f"GPU Silo revision {cfg.PROJECT['design_checks']['revision']} / IfcOpenShell"
        path.parent.mkdir(parents=True,exist_ok=True)
        self.file.write(str(path))


def penetration(m,wall,key,centre,theta,radius,length):
    # Opening extrusion runs radially outward from the wall's dry face or inside surface.
    radial=(math.cos(theta),math.sin(theta),0)
    origin=m.axis(centre,m.direction(radial),m.z)
    op=m.e("IfcOpeningElement",GlobalId=gid(key),Name=key,ObjectPlacement=m.e("IfcLocalPlacement",
           PlacementRelTo=m.building.ObjectPlacement,RelativePlacement=origin),
           Representation=m.solid("disc",(radius,),length,"Concrete"),PredefinedType="OPENING")
    m.e("IfcRelVoidsElement",GlobalId=gid(key+"void"),RelatingBuildingElement=wall,RelatedOpeningElement=op)


def civil(m):
    R=foundation.RADIUS
    m.product("RAFT","IfcSlab","Circular reinforced foundation raft","Base","Reinforced concrete",
              m.solid("disc",(R,),foundation.C["drawn"],"Reinforced concrete"),pose((0,0,-foundation.C["drawn"])),
              {"ThicknessM":foundation.C["drawn"],"TopDatumM":0.})
    for inner in (True,False):
        ri=cfg.BORE_R if inner else cfg.OUTSIDE_R-cfg.SILO["outer_wall_m"]
        thick=cfg.SILO["inner_wall_m" if inner else "outer_wall_m"]
        for lift in range(s.COUNT):
            low=lift*s.LIFT
            k=("IW" if inner else "OW")+f"-{lift+1:02}"
            wall=m.product(k,"IfcWall",("Inner" if inner else "Outer")+f" wall lift {lift+1:02}","Store","Concrete",
                           m.solid("ring",(ri,ri+thick),s.LIFT,"Concrete"),pose((0,0,low)),{"ThicknessM":thick,"ConcreteMPa":50})
            if lift==0:
                # Rectangular entry tunnel through each leaf, with its own jambs and lintel.
                theta=s.ENTRY
                centre=s.polar(ri+thick/2,theta,0)
                rep=m.solid("rect",(thick+.12,cfg.DOOR_WIDTH),cfg.DOOR_HEIGHT,"Concrete")
                x=m.direction((math.cos(theta),math.sin(theta),0))
                opening=m.e("IfcOpeningElement",GlobalId=gid(k+"entry"),Name="Pod entry portal",
                            ObjectPlacement=m.e("IfcLocalPlacement",RelativePlacement=m.axis(centre,m.z,x)),Representation=rep,PredefinedType="OPENING")
                m.e("IfcRelVoidsElement",GlobalId=gid(k+"doorvoid"),RelatingBuildingElement=wall,RelatedOpeningElement=opening)
            bores=[]
            for a in services.PORT_ANGLES:
                for lev in range(1,cfg.LEVELS+1):
                    z=services.port_height(lev)
                    if inner:bores.append((a,z,services.PORT_RADIUS+.006))
                    bores.append((a,z-.42,.095))
            if not inner:
                for n,a in enumerate(cooler_frames.BEARINGS):
                    for offset,z in cooler_frames.conduit_points(n):bores.append((a+offset,z,cooler_frames.CONDUIT_R+.01))
            for j,(a,z,r) in enumerate(bores):
                if low-r < z < low+s.LIFT+r:
                    penetration(m,wall,f"{k}-sleeve-{j}",s.polar(ri-.02,a,z),a,r,thick+.04)
    steel=structure.C["shaft"]["chosen"]["section"]
    m.product("SHAFT","IfcColumn","Fixed hollow central shaft","Base","Structural steel",
              m.solid("ring",(cfg.STORE["shaft_radius_m"]-steel["wall"],cfg.STORE["shaft_radius_m"]),structure.SHAFT_TOP+.15,"Structural steel"),
              props={"WallMm":1000*steel["wall"],"Steel":"ASTM A572 Grade 50"})
    for i,part in enumerate(pod_scene.cage_parts(include_shaft=False)):
        zone=f"Pod {i+1:02}" if i<cfg.LEVELS else "Diesel"
        m.product(f"CAGE-{i+1:02}","IfcElementAssembly",part.name,zone,"Structural steel",m.mesh(("cage",i),part,(1,1,1),"Structural steel"))

    for i,row in enumerate(reinforcement.C["proposed"]["lifts"]):
        bars=row["bars"]
        for wall,r,bar,spacing,material in (("OW",cfg.OUTSIDE_R-cfg.SILO["outer_wall_m"]/2,bars["bar"]["d"],bars["spacing"],"Duplex stainless reinforcement"),
                                             ("IW",cfg.BORE_R+cfg.SILO["inner_wall_m"]/2,.020,.2,"Reinforcement")):
            thickness=cfg.SILO["outer_wall_m" if wall=="OW" else "inner_wall_m"]
            mesh=plant.mesh("Wall reinforcement")
            for face in (-1,1):
                rr=r+face*(thickness/2-.05-bar/2)
                count=math.ceil(s.LIFT/spacing)
                for j in range(count):
                    z=row["z0"]+(j+.5)*s.LIFT/count
                    gap=math.asin((cfg.DOOR_WIDTH/2+.07)/rr) if z<cfg.DOOR_HEIGHT else 0
                    s.sector(mesh,rr-bar/2,rr+bar/2,z-bar/2,z+bar/2,s.ENTRY+gap,s.ENTRY+s.TAU-gap,32,["938272"]*4,caps=bool(gap))
                vertical=.020 if wall=="IW" else cfg.PROJECT["structure"]["walls"]["vertical_bar_mm"]/1000
                vs=.2 if wall=="IW" else .30
                if wall=="OW" and i==0 and face<0:
                    foot=reinforcement.C["proposed"]["foot"]["bars"]
                    vertical,vs=foot["bar"]["d"],foot["spacing"]
                n=math.ceil(2*math.pi*rr/vs)
                for j in range(n):
                    a=s.ENTRY+s.TAU*j/n
                    z0=cfg.DOOR_HEIGHT if i==0 and math.cos(a-s.ENTRY)>0 and abs(rr*math.sin(a-s.ENTRY))<cfg.DOOR_WIDTH/2+.06 else row["z0"]
                    rb=rr-face*(bar+vertical)/2
                    services.pipe(mesh,s.polar(rb,a,z0),s.polar(rb,a,row["z1"]),vertical/2,"938272",n=4)
            if wall=="OW" and i==0:
                # D16 at a 200 mm square grid supplies 5,027 mm2/m2 above the 4,072 needed.
                for z in np.arange(.1,reinforcement.C["proposed"]["foot"]["reach"]+.1,.2):
                    count=math.ceil(s.TAU*r/.20)
                    for j in range(count):
                        a=s.ENTRY+s.TAU*j/count
                        if math.cos(a-s.ENTRY)>0 and abs(r*math.sin(a-s.ENTRY))<services.JAMB:continue
                        services.pipe(mesh,s.polar(r-thickness/2+.05,a,z),s.polar(r+thickness/2-.05,a,z),.008,"938272",n=4)
            m.product(f"BAR-{wall}-{i+1:02}","IfcElementAssembly",wall+f" reinforcement cage, lift {i+1:02}","Store",material,
                      m.mesh((wall,i),mesh,(1,1,1),material),props={"HoopDiameterMm":round(1000*bar,1),"MaxHoopSpacingMm":1000*spacing,
                      "VerticalSchedule":"20 at 200 both faces" if wall=="IW" else "#8 at 300; #9 at 150 at wetted foot",
                      "Detail":"Coordination cage. Local laps, opening trims and shop bends require detailing."})


def scene_transform(n,transforms):
    tr=n["tracks"]
    def last(key,fallback):
        return tr[key][-1][1] if key in tr else fallback
    angle=last("yaw",(n["angle"],))[0]
    local=pose(last("translation",n["translation"]),angle,last("scale",(1,1,1)))
    parent=n.get("parent",-1)
    return transforms[parent] @ local if parent>=0 else local


GROUPS={
    "Cast-in conduits":("IfcPipeFitting","Process pipe","Store","Pod cooling"),
    "Store pipes":("IfcPipeSegment","Process pipe","Store","Thermal store"),
    "Store cover":("IfcCovering","Structural steel","Store","Thermal store"),
    "Store overflow":("IfcPipeSegment","Process pipe","Store","Thermal store"),
    "Door blockout":("IfcElementAssembly","Reinforced concrete","Base",None),
    "Intake":("IfcTransportElement","Structural steel","Base","Pod handling"),
    "Hoist":("IfcTransportElement","Structural steel","Diesel","Pod handling"),
    "Cooler frames":("IfcElementAssembly","Structural steel","Coolers","Heat rejection"),
    "Cooler screens":("IfcCovering","Structural steel","Coolers","Heat rejection"),
    "Dry coolers":("IfcHeatExchanger","Equipment","Coolers","Heat rejection"),
    "Pump units":("IfcPump","Equipment","Coolers","Heat rejection"),
    "Cooler embeds":("IfcDiscreteAccessory","Structural steel","Coolers","Heat rejection"),
    "Frame anchors":("IfcElementAssembly","Structural steel","Coolers","Heat rejection"),
    "Cooler conduits":("IfcPipeSegment","Process pipe","Coolers","Heat rejection"),
    "Frame pipework":("IfcPipeSegment","Process pipe","Coolers","Heat rejection"),
    "Rig mounts":("IfcDiscreteAccessory","Structural steel","Diesel","Power generation"),
    "Gas line":("IfcPipeSegment","Process pipe","Site","Fuel"),
    "Terminal infrastructure":("IfcTransportElement","Structural steel","Site","Pod handling"),
    "Control office":("IfcWall","Equipment","Site",None),
}


def racks(m,assembly,pod,n,world,zone):
    extra=cfg.extension(n)
    fr=plant.mesh("Pod side trusses and plan bracing")
    cargo.trusses(fr,extra)
    mid=(1,1,1)
    m.product(pod+"-FRAME","IfcElementAssembly","Two side trusses and plan bracing",zone,"Structural steel",
              m.mesh(("truss",extra),fr,mid,"Structural steel"),world,parent=assembly)
    bottom=(cfg.FRAME_HEIGHT-cfg.BODY_HEIGHT)/2
    pitch=cfg.BODY_LENGTH/cfg.CLUSTER["racks_per_pod"]
    for i in range(cfg.CLUSTER["racks_per_pod"]):
        pos=world @ pose((cargo.INNER+(i+.5)*pitch,0,bottom))
        m.product(pod+f"-R{i+1}","IfcCommunicationsAppliance",f"{cfg.CLUSTER['rack_model']} rack {i+1}",zone,"Rack",
                  m.solid("rect",(pitch-.025,cfg.BODY_WIDTH),cfg.BODY_HEIGHT,"Rack"),pos,
                  {"DesignKW":cfg.CLUSTER["liquid_heat_per_rack_kw"],"OperatingMassT":cfg.POD["rack_mass_t"]},assembly,"IT")
    x=cargo.OUTER
    for code,kind,desc,start,l in (("CDU","IfcHeatExchanger","Coolant distribution unit",x,extra*.63),
                                     ("P","IfcPump","Pod circulation pump",x+extra*.63,extra*.37)):
        m.product(pod+"-"+code,kind,desc,zone,"Equipment",m.solid("rect",(l-.012,cfg.BODY_WIDTH),cfg.BODY_HEIGHT,"Equipment"),
                  world @ pose((start+l/2,0,bottom)),parent=assembly,system="Pod cooling")


def operation(m):
    scene=pod_scene.build()
    floors=[completion.floor(level) for level in (0,1)]
    transforms=[]
    pod_assemblies={}
    for i,n in enumerate(scene.nodes):
        world=scene_transform(n,transforms)
        transforms.append(world)
        name,group=n["name"],n["group"]
        if n["mesh"]<0:continue
        matrix=world.copy()
        scale=np.linalg.norm(matrix[:3,:3],axis=0)
        if min(scale)<1e-9:continue
        matrix[:3,:3]/=scale
        mesh=scene.meshes[n["mesh"]]
        parent=None
        props={}
        if group=="Pods":
            num,lev,bay=map(int,re.findall(r"\d+",name))
            tag=f"POD-{lev:02}-{bay:02}"
            zone=f"Pod {lev:02}"
            pod=m.product(tag,"IfcElementAssembly",f"4SU pod L{lev:02} B{bay:02}",zone,None,matrix=matrix,
                          props={"OperatingMassT":structure.C["pod_t"],"Level":lev,"Bay":bay},system="IT")
            pod_assemblies[num]=(tag,pod,zone)
            racks(m,pod,tag,num,matrix,zone)
            continue
        if group=="Pod services":
            num=int(re.search(r"\d+",name).group())
            tag,parent,zone=pod_assemblies[num]
            kind,mat,system="IfcPipeFitting","Process pipe","Pod cooling"
        elif group=="Steel shoes":
            lev=int(name[1:3])
            zone=f"Pod {lev:02}"
            kind,mat,system="IfcDiscreteAccessory","Structural steel","Pod handling"
        elif group=="Power modules":
            if "deck assembly" in name:continue
            kind="IfcTank" if "tank" in name else "IfcElectricGenerator"
            zone="Turbines" if "Turbine set" in name else "Diesel"
            mat,system="Equipment","Power generation"
            if kind=="IfcElectricGenerator":
                props["NameplateMW"]=cfg.POWER["module_output_mw"] if zone=="Turbines" else cfg.PROJECT["diesel"]["set_output_mw"]
                props["Duty"]="Normal supply" if zone=="Turbines" else "Emergency only"
        elif group=="Fuel storage":
            kind="IfcTank" if "tank" in name.lower() and "pad" not in name else "IfcDistributionChamberElement" if "unloading" in name and "gravel" not in name else "IfcSlab"
            zone,mat,system="Site","Equipment","Fuel"
        elif group in GROUPS:
            kind,mat,zone,system=GROUPS[group]
            if group=="Rig mounts":
                upper=int(name.startswith("Turbine"))
                zone="Turbines" if upper else "Diesel"
                seat=int(re.search(r"mount (\d+)",name).group(1))
                props.update(DesignCheck=10 if upper else 9,SeatNumber=seat,
                             FactoredVerticalKN=float(1.6*floors[upper]["all_mounts"][seat-1]))
            if group=="Control office" and "roof" in name:kind="IfcRoof"
            if group=="Dry coolers":props["NominalMW"]=cfg.COOL["cooler_capacity_mw"]
        else:continue
        m.product(group+"/"+name,kind,name,zone,mat,m.mesh(n["mesh"],mesh,scale,mat),matrix,props,parent,system)

    for j,zone in enumerate(("Diesel","Turbines")):
        world=pose((0,0,plant.power_base(cfg.CROWN,j)),plant.POWER_YAW)
        for kind,part in plant.deck_components(j):
            guide=part.name.startswith(("Sliding shaft collar","Collar drag arm"))
            m.product(zone+"/"+part.name,kind,zone+" – "+part.name,zone,"Structural steel",
                      m.mesh((zone,part.name),part,(1,1,1),"Structural steel"),world,
                      props={"DesignCheck":10 if j else 8 if guide else 7})
    # The presentation cuts away the turbine enclosures. The BIM has both closed.
    for j,side in enumerate((-1,1)):
        l,w,h=plant.SET_L,plant.SET_W,plant.SET_H
        zone="Turbines"
        mesh=plant.mesh("Demountable acoustic enclosure")
        for y in (-w/2,w/2-.045):
            plant.closed(mesh,-l/2,y,l/2,y+.045,0,h,"9b9c89")
        for x in (-l/2,l/2-.045):
            plant.closed(mesh,x,-w/2,x+.045,w/2,0,h,"9b9c89")
        plant.closed(mesh,-l/2,-w/2,l/2,w/2,h-.045,h,"9b9c89")
        m.product(f"ENC-{j+1}","IfcElementAssembly",f"Turbine acoustic enclosure {j+1}",zone,"Structural steel",
                  m.mesh("enclosure",mesh,(1,1,1),"Structural steel"),pose(plant.turned(0,side*plant.SET_Y,plant.power_base(cfg.CROWN,1)),plant.POWER_YAW))
    for bay in range(cfg.BAYS):
        for tag,kind,mesh in (("PLAT","IfcTransportElement",crew.floor_plate()),("LAND","IfcSlab",crew.floor_plate(True)),("GUIDE","IfcMember",crew.guide(bay)),
                              ("RAIL","IfcRailing",crew.railing()),("GATE","IfcRailing",crew.railing(True))):
            m.product(f"ACCESS-{bay+1}-{tag}",kind,f"Service wedge {bay+1} {tag}","Base","Structural steel",
                      m.mesh(("access",bay,tag),mesh,(1,1,1),"Structural steel"),pose((0,0,0 if tag=="GUIDE" else crew.STOW),s.ENTRY+bay*s.TAU/cfg.BAYS),system="Pod handling")


def fixed_equipment(m):
    concrete,steel="Reinforced concrete","Structural steel"
    R=foundation.RADIUS-.075
    for face,z,db,step in (("TOP",-.11,.032,.12),("BOTTOM",-foundation.C["drawn"]+.11,.0254,.25)):
        mesh=plant.mesh("Raft "+face+" reinforcement")
        # Divide the disc into bands. Bars that would bunch towards the centre
        # terminate in adjoining bands with mechanical continuity at the split.
        for low,high in ((.40,2.5),(2.5,5.),(5.,8.),(8.,10.5),(10.5,R)):
            n=math.ceil(s.TAU*high/step)
            for j in range(n):
                a=s.TAU*j/n
                services.pipe(mesh,s.polar(low,a,z),s.polar(high,a,z),db/2,"937d70",n=4)
        n=math.ceil((R-.2)/step)
        for j in range(n):
            r=.2+(j+.5)*(R-.2)/n
            s.sector(mesh,r-db/2,r+db/2,z+db/2,z+db*1.5,0,s.TAU,32,["937d70"]*4,caps=False)
        m.product("RAFT-"+face,"IfcElementAssembly","Raft "+face.lower()+" radial and circumferential mat","Base","Reinforcement",
                  m.mesh(("raft",face),mesh,(1,1,1),"Reinforcement"),props={"MaxSpacingMm":step*1000,"BarDiameterMm":db*1000})
    extra=plant.mesh("Radial ties beneath the store")
    count=math.ceil(s.TAU*s.RI_OUTER/.150)
    for j in range(count):
        a=s.TAU*j/count
        services.pipe(extra,s.polar(s.RO_INNER-.75,a,-.22),s.polar(R-.15,a,-.22),.010,"8c7168",n=4)
    m.product("RAFT-STORE-TIE","IfcElementAssembly","Additional 20 mm radial ties across store floor","Base","Reinforcement",
              m.mesh("raft-store-tie",extra,(1,1,1),"Reinforcement"),props={"MaxCircumferentialSpacingMm":150,"BarDiameterMm":20})
    ties=plant.mesh("Shear links within two effective depths of walls")
    for r in np.arange(cfg.BORE_R-3.75,R-.15,.4):
        count=math.ceil(s.TAU*r/.4)
        for j in range(count):
            a=s.TAU*j/count
            for off in (-.075,.075):
                services.pipe(ties,s.polar(r+off,a,-1.88),s.polar(r+off,a,-.12),.008,"8c7168",n=4)
    m.product("RAFT-LINK","IfcElementAssembly","Two-legged 16 mm raft shear ties","Base","Reinforcement",
              m.mesh("ties",ties,(1,1,1),"Reinforcement"),props={"MaxRadialSpacingM":.4,"MaxTangentialSpacingM":.4})
    for j in range(foundation.BASE["bolts"]):
        mesh=plant.mesh("Shaft anchor hairpin")
        a=s.TAU*j/foundation.BASE["bolts"]
        for off in (-.035,.035):
            x,y,_=s.polar(.80+off,a,0)
            services.pipe(mesh,(x,y,-2.54),(x,y,-.14),.016,"8c7168",n=6)
        s.bar(mesh,s.polar(.765,a,-2.54),s.polar(.835,a,-2.54),.032,"8c7168")
        m.product(f"HP-{j+1:02}","IfcReinforcingBar","Shaft anchor two-legged 32 mm hairpin","Base","Reinforcement",
                  m.mesh(("hp",j),mesh,(1,1,1),"Reinforcement"))
    lid=m.product("LID","IfcRoof","Removable structural lid","Roof",steel,m.solid("disc",(plant.LID_R,),plant.LID_THICK,steel),pose((0,0,plant.LID_Z)))
    top=plant.LID_Z+plant.LID_THICK
    for role,pts,r,h in (("Turbine exhaust",plant.EXHAUST_AT,plant.EXHAUST_R,plant.EXHAUST_H),
                         ("Diesel exhaust",plant.DIESEL_STACKS,plant.DIESEL_STACK_R,plant.DIESEL_STACK_H)):
        for i,(x,y) in enumerate(pts):
            p=plant.turned(x,y,plant.LID_Z-.01)
            cut=m.e("IfcOpeningElement",GlobalId=gid(role+str(i)+"cut"),Name=role+" roof penetration",
                    ObjectPlacement=m.e("IfcLocalPlacement",RelativePlacement=m.axis(p)),Representation=m.solid("disc",(r,),plant.LID_THICK+.02,steel),PredefinedType="OPENING")
            m.e("IfcRelVoidsElement",GlobalId=gid(role+str(i)+"void"),RelatingBuildingElement=lid,RelatedOpeningElement=cut)
            m.product(role+str(i),"IfcStackTerminal",f"{role} stack {i+1}","Roof",steel,m.solid("ring",(r-.04,r),h,steel),
                      pose(plant.turned(x,y,top)),system="Exhaust")
    for role,pts,size in (("Turbine inlet",plant.INLET_AT,plant.INLET_HOUSE),("Diesel room vent",plant.ROOM_VENTS,plant.ROOM_VENT)):
        for i,(x,y) in enumerate(pts):
            p=plant.turned(x,y,plant.LID_Z-.01)
            ux=m.direction((math.cos(plant.POWER_YAW),math.sin(plant.POWER_YAW),0))
            cut=m.e("IfcOpeningElement",GlobalId=gid(role+str(i)+"cut"),Name=role+" roof penetration",
                    ObjectPlacement=m.e("IfcLocalPlacement",RelativePlacement=m.axis(p,m.z,ux)),Representation=m.solid("rect",size[:2],plant.LID_THICK+.02,steel),PredefinedType="OPENING")
            m.e("IfcRelVoidsElement",GlobalId=gid(role+str(i)+"void"),RelatingBuildingElement=lid,RelatedOpeningElement=cut)
            m.product(role+str(i),"IfcAirTerminal",f"{role} {i+1}","Roof","Equipment",m.solid("rect",size[:2],size[2],"Equipment"),
                      pose(plant.turned(x,y,top),plant.POWER_YAW),system="Ventilation")
    for side,r in (("Inner",s.RO_INNER),("Outer",s.RI_OUTER)):
        mesh=plant.mesh(side+" wetted liner")
        gap=math.asin(services.JAMB/r)
        for lo,hi,start,end in ((0,services.LINTEL,s.ENTRY+gap,s.ENTRY+s.TAU-gap),
                                (services.LINTEL,cfg.SILO["height_m"],0,s.TAU)):
            t=cfg.PROJECT["coating"]["thickness_mm"]/1000
            rr=r if side=="Inner" else r-t
            s.sector(mesh,rr,rr+t,lo,hi,start,end,64,["5d9693"]*4,caps=False)
        cover=m.product("LINER-"+side,"IfcCovering",side+" wetted liner","Store","Liner",m.mesh(("liner",side),mesh,(1,1,1),"Liner"),
                  props={"ThicknessMm":cfg.PROJECT["coating"]["thickness_mm"],"CrackBridgeAcceptanceMm":1.0})
        # The thin waterproof layer is terminated by a clamping flange at every penetration.
        for i,a in enumerate(services.PORT_ANGLES):
            for lev in range(1,cfg.LEVELS+1):
                h=services.port_height(lev)
                if side=="Inner":
                    penetration(m,cover,f"Liner-{side}-wet-{i}-{lev}",s.polar(r-.025,a,h),a,services.PORT_RADIUS+.006,.05)
                penetration(m,cover,f"Liner-{side}-dry-{i}-{lev}",s.polar(r-.025,a,h-.42),a,.095,.05)
        if side=="Outer":
            for k,a in enumerate(cooler_frames.BEARINGS):
                for j,(angle,z) in enumerate(cooler_frames.conduit_points(k)):
                    penetration(m,cover,f"Liner-{side}-cooler-{k}-{j}",s.polar(r-.025,a+angle,z),a+angle,cooler_frames.CONDUIT_R+.01,.05)
    m.product("LINER-FLOOR","IfcCovering","Annular floor liner","Base","Liner",
              m.solid("ring",(s.RO_INNER,s.RI_OUTER),cfg.PROJECT["coating"]["thickness_mm"]/1000,"Liner"))
    # Liquid is represented as an assigned design volume, so viewers can isolate the tank and its equipment.
    m.product("STORE","IfcTank","Lined annular thermal store","Store",None,props={
        "HotOperatingVolumeM3":structure_volume(),"HotLiquidLevelM":cfg.LIQUID_TOP,"ColdFillLevelM":layering.COLD_FILL,
        "GlycolVolumeFraction":cfg.FLUID["glycol_fraction"]},system="Thermal store")
    m.product("CATCH","IfcTank","Overflow catch tank","Site","Equipment",
              m.solid("disc",(1.25,),20/(math.pi*1.25**2),"Equipment"),
              pose(services.beside(site.WATER_BEARING,cfg.PROJECT["thermal"]["overflow"]["catch_tank_from_pump_skid_m"],71.5,.12)),
              {"CapacityM3":20.},system="Thermal store")
    m.product("FILL-P","IfcPump","Fill and transfer pump skid","Site","Equipment",m.solid("rect",(4.4,2.4),1.7,"Equipment"),
              pose(site.PUMP_SKID),props={"LimitM3h":completion.MECH["catch_inflow_m3h"]},system="Thermal store")
    m.product("RING-ROAD","IfcSlab","Two-lane site ring road","Site","Concrete",
              m.solid("ring",(min(site.R_RUN,site.R_STOP)-site.HALF,max(site.R_RUN,site.R_STOP)+site.HALF),.25,"Concrete"),pose((0,0,-.25)))


def structure_volume():
    from . import calcs
    return calcs.C["tank_m3"]


def write(path):
    m=Model()
    civil(m)
    operation(m)
    for part in components.products():
        system={"fuel":"Fuel","services":"Building services","roof":"Roof plant","cage":"Pod services","base":"Civil works","rig seats":"Power generation","turbine seats":"Power generation"}[part.stage]
        mat=IDENTITY
        if part.tag=="F-BOSS":
            depth=completion.SITE["slab_boss_extra_m"]
            rep=m.solid("disc",(completion.SITE["slab_boss_radius_m"],),depth,part.material)
            mat=pose((0,0,-foundation.C["drawn"]-depth))
        else:
            rep=m.mesh(part.tag,part.mesh,(1,1,1),part.material)
        m.product(part.tag,part.kind,part.name,part.level,part.material,rep,mat,part.data,system=system)
    fixed_equipment(m)
    m.finish(Path(path))
    return len(m.keys)
