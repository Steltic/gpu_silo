"""Path-trace the IFC half-section, circuit studies and liquid transition plates."""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

parser=argparse.ArgumentParser()
parser.add_argument("source",type=Path);parser.add_argument("out",type=Path)
parser.add_argument("--percent",type=int,default=100);parser.add_argument("--samples",type=int,default=96)
parser.add_argument("--shots",nargs="+",default=["store","store_inset","pods","coolers","risers","diffuser","reserve_cold","reserve_warm","reserve_z"])
parser.add_argument("--cpu",action="store_true")
args=parser.parse_args(sys.argv[sys.argv.index("--")+1:])
args.out.mkdir(exist_ok=True,parents=True)
data=json.loads((args.source/"geometry.json").read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine="CYCLES"
sc.render.resolution_x=3840;sc.render.resolution_y=2160;sc.render.resolution_percentage=args.percent
sc.render.image_settings.file_format="PNG";sc.render.image_settings.color_mode="RGB";sc.render.image_settings.color_depth="8";sc.render.image_settings.compression=12
sc.render.use_persistent_data=True;sc.render.threads_mode="FIXED";sc.render.threads=8
sc.cycles.samples=args.samples;sc.cycles.use_adaptive_sampling=True;sc.cycles.adaptive_min_samples=min(5,args.samples)
sc.cycles.adaptive_threshold=.035;sc.cycles.use_denoising=True;sc.cycles.denoising_quality="HIGH";sc.cycles.denoising_prefilter="ACCURATE"
sc.cycles.use_auto_tile=False
sc.cycles.max_bounces=6;sc.cycles.transparent_max_bounces=8;sc.cycles.transmission_bounces=4;sc.cycles.diffuse_bounces=2;sc.cycles.glossy_bounces=3
sc.view_settings.view_transform="AgX";sc.view_settings.look="AgX - Medium High Contrast"
if not args.cpu:
    pref=bpy.context.preferences.addons["cycles"].preferences
    for backend in ("ONEAPI","OPTIX","HIP","METAL","CUDA"):
        try:pref.compute_device_type=backend;pref.refresh_devices()
        except (TypeError,RuntimeError):continue
        if any(d.type==backend for d in pref.devices):
            for d in pref.devices:d.use=d.type==backend
            sc.cycles.device="GPU";sc.cycles.denoising_use_gpu=False;break
print("Thermal Cycles",sc.cycles.device,flush=True)
def object_(name,mesh):
    o=bpy.data.objects.new(name,mesh);sc.collection.objects.link(o);return o
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
def mat(name,color,rough=.6,metal=0,grain=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;bs=nt.nodes.get("Principled BSDF");bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough;bs.inputs["Metallic"].default_value=metal
    if grain:
        tex=nt.nodes.new("ShaderNodeNewGeometry");noise=nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=grain;noise.inputs["Detail"].default_value=3
        nt.links.new(tex.outputs["Position"],noise.inputs["Vector"])
        ramp=nt.nodes.new("ShaderNodeValToRGB")
        for el,u in zip(ramp.color_ramp.elements,(.67,1.19)):el.color=(*(min(.99,v*u) for v in color),1)
        nt.links.new(noise.outputs["Fac"],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs["Base Color"])
        bump=nt.nodes.new("ShaderNodeBump");bump.inputs["Distance"].default_value=.009;bump.inputs["Strength"].default_value=.19
        nt.links.new(noise.outputs["Fac"],bump.inputs["Height"]);nt.links.new(bump.outputs[0],bs.inputs["Normal"])
    return m
def meshobj(name,verts,faces,mats,indices=None):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    for m in mats:mesh.materials.append(m)
    if indices is not None:mesh.polygons.foreach_set("material_index",np.asarray(indices,dtype=np.int32))
    return object_(name,mesh)
palette={
 "wall":mat("Fair-faced cast concrete",(.42,.43,.39),.76,0,8),
 "raft":mat("Cut foundation",(.32,.34,.33),.83,0,10),
 "section":mat("Exposed concrete aggregate",(.56,.51,.39),.84,0,30),
 "steel":mat("Galvanised frame",(.27,.34,.35),.34,.65),
 "rack":mat("Rack cabinet",(.073,.11,.13),.43,.47),
 "cooler":mat("Air cooler housing",(.38,.45,.44),.37,.58),
 "cdu":mat("CDU enclosure",(.21,.36,.36),.32,.52),
 "plant":mat("Power deck",(.23,.27,.28),.45,.51),
 "pump":mat("Pump housing",(.21,.27,.31),.36,.68),
 "pipe":mat("Process pipe",(.31,.39,.39),.31,.67),
 "risers":mat("Other fixed headers",(.26,.35,.34),.31,.66),
 "cover":mat("Annular cover",(.32,.37,.35),.36,.61),
 "Cold":mat("Cool header finish",(.061,.38,.44),.26,.63),
 "Warm":mat("Warm header finish",(.58,.24,.082),.28,.63),
 "plate":mat("Diffuser plate and legs",(.63,.66,.59),.25,.74),
}
axes={k:np.array(v) for k,v in data["axes"].items()}
rows=[];special={}
for row in data["products"]:
    src=np.load(args.source/f"e{row['i']:04}.npz"); v=src["v"]; f=src["f"];side=src["side"]
    for key in (("Cold","Warm") if row["special"] else ("",)):
        if key:
            choose=side==(key=="Warm"); ff=f[choose];axis=axes[row["special"]+key]
            if not len(ff):continue
            centres=v[ff].mean(axis=1);radius=np.linalg.norm(centres[:,:2]-axis[:2],axis=1)
            zplate=data["high"]+data["gap"] if key=="Warm" else data["low"]-data["gap"]
            idx=((radius>.25)&(np.abs(centres[:,2]-zplate)<.44)).astype(np.int32)
            idx[np.abs(centres[:,2]-zplate)<.035]=1
            o=meshobj(row["tag"]+" / "+key,v,ff,[palette[key],palette["plate"]],idx)
            special[row["special"]+key]=o
        else:
            indices=np.zeros(len(f),np.int32);indices[row["cap"]:]=1
            o=meshobj(row["tag"],v,f,[palette[row["kind"]],palette["section"]],indices)
        if row["kind"] not in ("raft","wall"):
            o.data.set_sharp_from_angle(angle=math.radians(32))
        o["IfcGlobalId"]=row["guid"];o["IfcTag"]=row["tag"];rows.append((o,row,key))

def add_box(name,centre,dimensions,material):
    bpy.ops.mesh.primitive_cube_add(size=1,location=centre)
    o=bpy.context.object;o.name=name;o.dimensions=dimensions;o.data.materials.append(material);return o

# Dark studio cove and large reflected sources model the edge of the cut and the fluid meniscus.
stage=mat("Slate stage",(.045,.067,.075),.57,.15,1.1)
floor=add_box("Shadow stage",(0,0,-2.88),(2800,2800,.14),stage)
sc.world=bpy.data.worlds.new("Soft studio environment");sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get("Background");bg.inputs[0].default_value=(.27,.36,.41,1);bg.inputs[1].default_value=.46
def area(name,pos,target,colour,power,size):
    lamp=bpy.data.lights.new(name,"AREA");lamp.color=colour;lamp.energy=power;lamp.shape="DISK";lamp.size=size
    o=object_(name,lamp);o.location=pos;aim(o,target);return o
area("Large left softbox",(-18,-27,41),(0,2,15),(1,.86,.68),33500,24)
area("Cool right edge",(24,8,32),(5,4,15),(.44,.76,1),31500,20)
area("Front return",(4,-24,14),(4,5,13),(.70,.85,.97),12500,14)
area("Warm overhead",(-3,12,45),(3,5,18),(1,.73,.47),24000,14)
area("Top diffuser gleam",(8,4,34),(7,7,30.8),(.80,.91,1),290,2.1)
camdata=bpy.data.cameras.new("Section lens");camdata.type="ORTHO";camdata.sensor_fit="HORIZONTAL";camdata.clip_end=450
cam=object_("Thermal camera",camdata);sc.camera=cam

fluid=mat("Cut thermal fluid",(0,.3,.4),.14)
nt=fluid.node_tree;bs=nt.nodes.get("Principled BSDF")
bs.inputs["IOR"].default_value=1.36;bs.inputs["Transmission Weight"].default_value=.28
bs.inputs["Coat Weight"].default_value=.37;bs.inputs["Coat Roughness"].default_value=.12;bs.inputs["Emission Strength"].default_value=.18
pnode=nt.nodes.new("ShaderNodeNewGeometry");xyz=nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(pnode.outputs["Position"],xyz.inputs[0])
mapz=nt.nodes.new("ShaderNodeMapRange");mapz.inputs["From Min"].default_value=14.5;mapz.inputs["From Max"].default_value=17.4
nt.links.new(xyz.outputs["Z"],mapz.inputs["Value"])
ramp=nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color=(.018,.42,.54,1);ramp.color_ramp.elements[1].color=(.86,.26,.056,1)
nt.links.new(mapz.outputs[0],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs["Base Color"]);nt.links.new(ramp.outputs[0],bs.inputs["Emission Color"])
glass=nt.nodes.new("ShaderNodeBsdfTransparent");mix=nt.nodes.new("ShaderNodeMixShader");mix.inputs[0].default_value=.70
nt.links.new(glass.outputs[0],mix.inputs[1]);nt.links.new(bs.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes.get("Material Output").inputs[0])

def water_mesh():
    v=[];f=[];n=144
    for i in range(n+1):
        a=math.pi*i/n
        for rad,z in ((data["inner"]+.012,.025),(data["outer"]-.012,.025),(data["outer"]-.012,data["liquidTop"]),(data["inner"]+.012,data["liquidTop"])):
            v.append((rad*math.cos(a),rad*math.sin(a),z))
    for i in range(n):
        for j in range(4):f.append((i*4+j,(i+1)*4+j,(i+1)*4+(j+1)%4,i*4+(j+1)%4))
    f.extend(((0,1,2,3),(n*4+3,n*4+2,n*4+1,n*4)))
    return meshobj("Water / 25 percent propylene glycol • cut volume",v,f,[fluid])
water=water_mesh()
cz=data["connections"];eq=data["equipment"]
low,high=data["low"],data["high"]
def pt(axis,z):return [*axes[axis][:2],z]
def offset(p,x=0,y=0,z=0):return [p[0]+x,p[1]+y,p[2]+z]
pod=eq["POD-04-01-CDU"];rack=eq["POD-04-01-R4"];dry=eq["Dry coolers/Cooler frame 01 | cooler 2"];pump=eq["Pump units/Cooler frame 01 | pump unit 2"]
routes={
 "podCold":[offset(pt("podCold",low-.16),1.02,-.2),pt("podCold",low-.12),pt("podCold",cz["rackZ"]),cz["podCold"],offset(pod,0,0,-.38)],
 "podWarm":[offset(pod,0,0,.38),offset(cz["podWarm"],z=.20),pt("podWarm",cz["rackZ"]+.20),pt("podWarm",high+.17),offset(pt("podWarm",high+.17),.93,-.22)],
 "coolerWarm":[offset(pt("coolerWarm",high+.15),-.94,.2),pt("coolerWarm",high+.12),pt("coolerWarm",cz["coolerWarmZ"]),cz["coolerWarm"],pump,offset(dry,0,0,.36)],
 "coolerCold":[offset(dry,0,0,-.38),cz["coolerCold"],pt("coolerCold",cz["coolerColdZ"]),pt("coolerCold",low-.17),offset(pt("coolerCold",low-.17),1.02,-.12)],
 "secondary":[offset(rack,-1.65,-.29,.38),offset(rack,.1,-.29,.38),offset(pod,0,-.35,.38),offset(pod,0,-.35,-.38),offset(rack,-1.65,-.29,-.38)]}
# The film follows these centres and ports from the IFC. Strokes are presentation graphics.
positions={"podCold":-6.7,"podWarm":-3.4,"coolerCold":3.2,"coolerWarm":6.6}
for key in positions:
    hot=key.endswith("Warm")
    lower=low if not hot else (cz["rackZ"] if key.startswith("pod") else cz["coolerWarmZ"])
    upper=high if hot else (cz["rackZ"] if key.startswith("pod") else cz["coolerColdZ"])
    rising=(key in ("podCold","podWarm"))
    pair=[[positions[key],0,lower],[positions[key],0,upper]]
    routes["riser"+key]=pair if rising else pair[::-1]
a0=pt("podWarm",high)
for j,(x,y) in enumerate(((1,0),(-1,0),(0,1),(0,-1))):
    routes["fan"+str(j)]=[offset(a0,z=-.70),a0,offset(a0,x*.12,y*.12,.18),offset(a0,x*.40,y*.40,.22),offset(a0,x*.97,y*.97,.17)]
anchor={**{k:pt(k,high if k.endswith("Warm") else low) for k in axes},"rack":rack,"cdu":pod,"cooler":dry,
        "topPlate":offset(a0,z=data["gap"]+.025),"mouth":a0,
        "upperLayer":[11,0,25.8],"lowerLayer":[11,0,6.2],"topLevel":[10.4,0,data["liquidTop"]]}
for k,x in positions.items():anchor["study"+k]=[x,0,high if k.endswith("Warm") else low]
for side,sign in (("Left",-1),("Right",1)):
    for edge,rad in (("Inner",data["inner"]),("Outer",data["outer"])):
        for level,z in (("Bottom",0),("Top",data["liquidTop"])):
            anchor["section"+side+edge+level]=[sign*rad,0,z]

def cameras(shot):
    if shot=="store":return (-8,3,15),(1,-79,37),76
    if shot=="pods":return (3,4,14),(-7,-72,33),66
    if shot=="coolers":return (5.4,6,15),(21,-76,39),66
    if shot=="risers":return (-6.0,0,15.5),(-7,-68,34),68
    if shot=="diffuser":return (a0[0]-.43,a0[1],a0[2]+.0),(a0[0]+1.25,a0[1]-4.1,a0[2]+1.05),3.36
    return (-7,3,15),(4,-78,34),74

def show(shot,row,key):
    tag=row["tag"];role=row["kind"]
    if shot in ("store","reserve"):return True
    if shot=="risers":return bool(key)
    if shot=="diffuser":return row["special"]=="pod" and key=="Warm"
    if shot=="pods":
        return row["special"]=="pod" or tag.startswith("POD-04-01-")
    return row["special"]=="cooler" or (("frame 01" in tag.lower()) and role in ("pipe","pump","cooler","steel"))
def projection(point):
    uv=world_to_camera_view(sc,cam,Vector(point));return [float(uv.x),float(1-uv.y)]
def set_scene(shot):
    water.hide_render=shot not in ("store","reserve")
    floor.hide_render=False
    for o,row,key in rows:
        o.hide_render=not show(shot,row,key);o.location=(0,0,0)
        if key and shot=="risers":
            ident=row["special"]+key;o.location=(positions[ident]-axes[ident][0],-axes[ident][1],0)
    target,pos,width=cameras(shot);cam.location=pos;aim(cam,target);camdata.ortho_scale=width
    bpy.context.view_layer.update()
    return {"anchors":{k:projection(p) for k,p in anchor.items()},"routes":{k:[projection(p) for p in line] for k,line in routes.items()}}
all_projections={}
for shot in ("store","pods","coolers","risers","diffuser","reserve"):
    all_projections[shot]=set_scene(shot)
(args.out/"projection.json").write_text(json.dumps(all_projections),encoding="utf-8")
ghost_nodes=[]
for name,opacity in (("wall",.13),("cover",.15),("section",.18),("steel",.34),("rack",.37),("plant",.24),("risers",.47)):
    tree=palette[name].node_tree
    surface=tree.nodes.get("Material Output").inputs["Surface"]
    lit=surface.links[0].from_socket
    thin=tree.nodes.new("ShaderNodeBsdfTransparent")
    bind=tree.nodes.new("ShaderNodeMixShader")
    tree.links.new(thin.outputs[0],bind.inputs[1]);tree.links.new(lit,bind.inputs[2]);tree.links.new(bind.outputs[0],surface)
    ghost_nodes.append((bind,opacity))
for key in args.shots:
    file=args.out/(key+".png")
    if file.exists():continue
    shot=key.split("_")[0];set_scene(shot)
    for bind,opacity in ghost_nodes:bind.inputs[0].default_value=opacity if key=="store_inset" else 1
    mix.inputs[0].default_value=.29 if key=="store_inset" else .70
    if shot=="reserve":
        threshold=90 if key.endswith("cold") else -10
        mapz.inputs["From Min"].default_value=threshold;mapz.inputs["From Max"].default_value=threshold+2
    if key=="reserve_z":
        black=bpy.data.materials.new("Object occlusion holdout");black.use_nodes=True;nd=black.node_tree
        dark=nd.nodes.new("ShaderNodeEmission");dark.inputs[0].default_value=(0,0,0,1);nd.links.new(dark.outputs[0],nd.nodes.get("Material Output").inputs[0])
        zm=bpy.data.materials.new("Unlit world height in liquid");zm.use_nodes=True;nd=zm.node_tree
        n=nd.nodes;ln=nd.links;co=n.new("ShaderNodeNewGeometry");se=n.new("ShaderNodeSeparateXYZ");ln.new(co.outputs["Position"],se.inputs[0])
        cv=n.new("ShaderNodeMath");cv.operation="MULTIPLY_ADD";cv.inputs[1].default_value=.9/32;cv.inputs[2].default_value=.05;ln.new(se.outputs["Z"],cv.inputs[0])
        em=n.new("ShaderNodeEmission");ln.new(cv.outputs[0],em.inputs[0]);ln.new(em.outputs[0],n.get("Material Output").inputs[0])
        for o in [v[0] for v in rows]+[floor,water]:
            for slot in o.material_slots:
                slot.material=zm if o==water else black
        bg.inputs[1].default_value=0;sc.view_settings.view_transform="Raw";sc.view_settings.look="None"
        sc.cycles.samples=3;sc.cycles.adaptive_min_samples=1;sc.cycles.use_denoising=False
    sc.render.filepath=str(file.resolve());print("PLATE",key,flush=True)
    bpy.ops.render.render(write_still=True)
