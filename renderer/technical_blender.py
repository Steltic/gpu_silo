"""Render a range of the baked short using Blender 4.5 LTS. Frame numbers start at zero.

blender -b -P renderer/technical_blender.py -- BAKE OUTPUT FIRST LAST [--percent 100] [--samples N]
"""
import argparse
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector, Euler

args=argparse.ArgumentParser()
args.add_argument("bake",type=Path)
args.add_argument("out",type=Path)
args.add_argument("first",type=int)
args.add_argument("last",type=int)
args.add_argument("--percent",type=int,default=100)
args.add_argument("--samples",type=int,default=0)
args.add_argument("--cpu",action="store_true")
args.add_argument("--threads",type=int,default=10,help="CPU thread limit for scene preparation and rendering")
args.add_argument("--rural-review",type=Path,help="full-rate camera and revised facade for the standalone orbit")
args.add_argument("--facade",type=Path,help="revised physical office facade for a technical review shot")
args.add_argument("--stills",type=int,nargs="+",help="render only these frames for review")
a=args.parse_args(sys.argv[sys.argv.index("--")+1:])
a.out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((a.bake/"scene.json").read_text(encoding="utf-8"))
pose=np.load(a.bake/"poses.npy",mmap_mode="r")
camera=np.load(a.bake/"camera.npz")
office,studio,roof=(manifest[k] for k in ("office","studio","roof"))
def mode(f):
    if f<office:return "day"
    if f<studio:return "office"
    if f<roof:return "studio"
    if f<manifest["drawing"]:return "dusk"
    return "drawing"
review=a.rural_review is not None
kind="dusk" if review else mode(a.first)
if not review and (mode(a.last)!=kind or kind=="drawing"):raise ValueError("Select one photographic lighting setup")
if review:
    native=np.load(a.rural_review/"orbit-camera.npz")
    if not (0<=a.first<=a.last<len(native["eye"])):raise ValueError("Invalid full-rate orbit frame range")
    camera=native
source_first,source_last=(roof,manifest["drawing"]-1) if review else (a.first,a.last)
print("PHOTOGRAPHY",kind,a.first,a.last,flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine="BLENDER_EEVEE_NEXT" if kind=="day" else "CYCLES"
sc.render.resolution_x,sc.render.resolution_y=3840,2160
sc.render.resolution_percentage=a.percent
sc.render.image_settings.file_format="JPEG"
sc.render.image_settings.quality=95
sc.render.image_settings.color_mode="RGB"
sc.render.threads_mode="FIXED";sc.render.threads=a.threads
sc.render.fps=24;sc.render.film_transparent=False
sc.render.use_persistent_data=True
sc.view_settings.view_transform="AgX"
sc.view_settings.look="AgX - Medium High Contrast"
if sc.render.engine=="CYCLES":
    sc.cycles.samples=a.samples or (32 if review else 10)
    if review:
        sc.cycles.use_adaptive_sampling=True
        sc.cycles.adaptive_min_samples=min(5,sc.cycles.samples)
        sc.cycles.adaptive_threshold=.070
    sc.cycles.use_denoising=True
    sc.cycles.use_auto_tile=False
    sc.cycles.denoising_use_gpu=not a.cpu
    sc.cycles.denoising_quality="HIGH" if review else "FAST"
    sc.cycles.denoising_prefilter="ACCURATE" if review else "FAST"
    sc.cycles.max_bounces=4
    sc.cycles.diffuse_bounces=2
    sc.cycles.glossy_bounces=2
    sc.cycles.transparent_max_bounces=4
    if not a.cpu:
        try:
            pref=bpy.context.preferences.addons["cycles"].preferences
            devices=[]
            for backend in ("ONEAPI","OPTIX","METAL","HIP","CUDA"):
                try:
                    pref.compute_device_type=backend
                    pref.refresh_devices()
                except (TypeError,RuntimeError):
                    continue
                devices=[d for d in pref.devices if d.type==backend]
                if devices:
                    for d in pref.devices:d.use=d.type==backend
                    sc.cycles.device="GPU"
                    break
            sc.cycles.denoising_use_gpu=bool(devices)
            print("Cycles compute",sc.cycles.device,[d.name for d in devices],flush=True)
        except (TypeError,RuntimeError) as err:print("Cycles CPU",err,flush=True)
else:
    sc.eevee.taa_render_samples=a.samples or 8
    sc.eevee.use_shadows=True
    sc.eevee.shadow_pool_size="512"
    sc.eevee.use_raytracing=False

def obj(name,data):
    o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);return o

def aim(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()

def light(name,kind,loc,target,color,energy,size=1):
    data=bpy.data.lights.new(name,kind);data.color=color;data.energy=energy
    if kind=="AREA":
        data.shape="DISK";data.size=size
    if kind=="SUN":data.angle=math.radians(size)
    if kind=="POINT":data.shadow_soft_size=size
    o=obj(name,data);o.location=loc;aim(o,target);return o

def flat(name,col,rough=.68,metal=.08):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bs=mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*col,1.)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    return mat

def plane(name,points,material):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(points,[],[list(range(len(points)))]);mesh.update()
    obj(name,mesh);mesh.materials.append(material)

def hub_material(code,mtype):
    key=(code,mtype)
    if key in materials:return materials[key]
    rough,metal={"land":(.94,0),"concrete":(.86,0),"machine":(.38,.46),"studio":(.33,.55),"other":(.65,.18)}[mtype]
    mat=flat(f"{mtype} / {code}",(.3,.35,.36),rough,metal)
    tree=mat.node_tree;bs=tree.nodes.get("Principled BSDF")
    attr=tree.nodes.new("ShaderNodeVertexColor");attr.layer_name="Finish"
    tree.links.new(attr.outputs["Color"],bs.inputs["Base Color"])
    if mtype=="land":
        coord=tree.nodes.new("ShaderNodeTexCoord");noise=tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=.75;noise.inputs["Detail"].default_value=2.
        tree.links.new(coord.outputs["Object"],noise.inputs["Vector"])
        grade=tree.nodes.new("ShaderNodeValToRGB")
        grade.color_ramp.elements[0].color=(.53,.57,.48,1);grade.color_ramp.elements[1].color=(1.,1.,.95,1)
        tree.links.new(noise.outputs["Fac"],grade.inputs[0])
        grain=tree.nodes.new("ShaderNodeMixRGB");grain.blend_type="MULTIPLY";grain.inputs[0].default_value=.49
        tree.links.new(attr.outputs["Color"],grain.inputs[1]);tree.links.new(grade.outputs[0],grain.inputs[2])
        tree.links.new(grain.outputs[0],bs.inputs["Base Color"])
    bs.inputs["Alpha"].default_value={1:0.,2:.12,4:.105,5:.30,6:.86,7:.14,8:.14,11:.13}.get(code,1.)
    if code in (6,9,10,11):
        tree.links.new(attr.outputs["Color"],bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value={6:.7,9:2.2,10:4.,11:1.5}[code]
    if mtype=="concrete" and code==0:
        tex=tree.nodes.new("ShaderNodeTexCoord");noise=tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=25.;noise.inputs["Detail"].default_value=2.
        tree.links.new(tex.outputs["Object"],noise.inputs["Vector"])
        bump=tree.nodes.new("ShaderNodeBump");bump.inputs["Distance"].default_value=.004;bump.inputs["Strength"].default_value=.22
        tree.links.new(noise.outputs["Fac"],bump.inputs["Height"]);tree.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    materials[key]=mat;return mat

materials={}
mesh_meta={m["id"]:m for m in manifest["meshes"]}
meshes={}
def read_mesh(i,mtype):
    if (i,mtype) in meshes:return meshes[i,mtype]
    record=mesh_meta[i]
    name=record["name"]
    path=a.bake/f"mesh_{i}.npz"
    if (review or a.facade) and any(n["mesh"]==i and n["name"]=="Control office | walls" for n in manifest["nodes"]):
        path=a.facade or a.rural_review/"facade.npz"
    elif review and i==1:
        path=a.rural_review/"farm-furniture.npz"
    src=np.load(path)
    v,f,col=(src[k] for k in ("v","f","c"))
    if (review or a.facade) and any(n["mesh"]==i and n["name"]=="Control room | displays and task lighting" for n in manifest["nodes"]):
        # The replacement lettering is part of the lintel. Preserve the screens
        # and task lights in the old bake while removing the former lettering.
        keep=~np.all(col==[217,232,221],axis=1)
        f,col=f[keep],col[keep]
    mesh=bpy.data.meshes.new(record["name"])
    mesh.vertices.add(len(v));mesh.vertices.foreach_set("co",np.ascontiguousarray(v).ravel())
    mesh.loops.add(f.size);mesh.loops.foreach_set("vertex_index",f.ravel())
    mesh.polygons.add(len(f))
    mesh.polygons.foreach_set("loop_start",np.arange(0,f.size,3,dtype=np.int32))
    mesh.update(calc_edges=True)
    if mtype in ("land","concrete") or len(f)<10:
        mesh.shade_flat()
    else:
        mesh.set_sharp_from_angle(angle=math.radians(32))
    attr=mesh.color_attributes.new(name="Finish",type="BYTE_COLOR",domain="CORNER")
    rgba=np.ones((len(col),4),np.float32);rgba[:,:3]=col/255.
    attr.data.foreach_set("color_srgb",np.repeat(rgba,3,axis=0).ravel())
    mesh.materials.append(hub_material(record["mat"],mtype))
    meshes[i,mtype]=mesh
    return mesh

sc.world=bpy.data.worlds.new("Film sky");sc.world.use_nodes=True
nt=sc.world.node_tree;bg=nt.nodes.get("Background")
if kind=="studio":
    bg.inputs["Color"].default_value=(.42,.52,.58,1);bg.inputs["Strength"].default_value=.34
    shift=(600,600)
    def studio_light(name,xy,z,target,energy,size,color):
        light(name,"AREA",(600+xy[0],600+xy[1],z),(600,600,target),color,energy,size)
    studio_light("High softbox",(7,-11),19,7,11600,12,(1.,.90,.76))
    studio_light("Long rim",(-12,8),17,7,14200,11,(.81,.92,1.))
    studio_light("Front bounce",(2,-14),7,6,4500,10,(.79,.91,1.))
    studio_light("Upper shaft strip",(-3,-9),29,23,7600,9,(1.,.90,.74))
    stage_mat=flat("Slate cyclorama",(.055,.084,.094),.69)
    # A circular cove keeps the floor continuous through each lens movement.
    radius=max(55.,float(np.linalg.norm(camera["eye"][studio:roof,:2]-(600,600),axis=1).max())+12)
    profile=[(radius,0.)]+[(radius+13*math.sin(j*math.pi/24),13*(1-math.cos(j*math.pi/24))) for j in range(1,13)]+[(radius+13,95.)]
    v=[(600.,600.,0.)]+[(600+r*math.cos(j*math.tau/96),600+r*math.sin(j*math.tau/96),z) for r,z in profile for j in range(96)]
    ix=lambda ring,j:1+ring*96+j%96
    faces=[(0,ix(0,j),ix(0,j+1)) for j in range(96)]
    faces.extend((ix(k,j),ix(k+1,j),ix(k+1,j+1),ix(k,j+1)) for k in range(len(profile)-1) for j in range(96))
    mesh=bpy.data.meshes.new("Continuous studio cove");mesh.from_pydata(v,[],faces);mesh.update()
    mesh.materials.append(stage_mat);stage=obj(mesh.name,mesh)
    for face in mesh.polygons:face.use_smooth=True
else:
    dusk=kind=="dusk"
    # World-space altitude ramp gives a bright horizon and a cooler zenith beyond the modelled fields.
    tex=nt.nodes.new("ShaderNodeTexCoord");sep=nt.nodes.new("ShaderNodeSeparateXYZ");nt.links.new(tex.outputs["Generated"],sep.inputs[0])
    absolute=nt.nodes.new("ShaderNodeMath");absolute.operation="ABSOLUTE";nt.links.new(sep.outputs["Z"],absolute.inputs[0])
    ramp=nt.nodes.new("ShaderNodeValToRGB")
    stops=[(0.,(.37,.37,.49) if dusk else (.82,.86,.84)),(.22,(.13,.22,.41) if dusk else (.42,.62,.73)),(.78,(.031,.072,.17) if dusk else (.17,.36,.56))]
    for j,(at,col) in enumerate(stops):
        el=ramp.color_ramp.elements[j] if j<2 else ramp.color_ramp.elements.new(at)
        el.position=at;el.color=(*col,1)
    nt.links.new(absolute.outputs[0],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bg.inputs["Color"])
    bg.inputs["Strength"].default_value=.63 if dusk else .80
    light("Late sun" if dusk else "Industrial daylight","SUN",(-56,-48,22 if dusk else 74),(0,0,0),(1.,.63,.38) if dusk else (1.,.91,.78),1.07 if dusk else 2.75,2.7)
    light("Sky return","SUN",(20,50,40),(0,0,7),(.54,.72,1.),.55 if dusk else .53,12)
    far=flat("Distant fields",(.38,.44,.36) if not dusk else (.19,.23,.24))
    plane("Far terrain",[(-5000,-5000,-.32),(5000,-5000,-.32),(5000,5000,-.32),(-5000,5000,-.32)],far)
    if dusk or kind=="office":
        for ang in (-62,27,122,216):
            r=math.radians(ang)
            loc=(19*math.cos(r),19*math.sin(r),2)
            light("Architectural uplight","AREA",loc,(14*math.cos(r),14*math.sin(r),10),(1.,.63,.33),2300,4)
        light("Dock task lighting","AREA",(19,-22,4),(23,-17,1),(.78,.92,1.),820,4)
    if dusk:
        light("Blue-hour roof fill","AREA",(9,-21,49),(0,0,25),(.65,.81,1.),10500,25)
    if review:
        sys.path.insert(0,str(Path(__file__).resolve().parent))
        from review_farmland import landscape
        landscape()
        # Blue-hour skylight preserves field detail under a low raking sun.
        bg.inputs["Strength"].default_value=.82
        ramp.color_ramp.elements[0].color=(.70,.52,.43,1)
        ramp.color_ramp.elements[1].color=(.27,.39,.57,1)
        ramp.color_ramp.elements[2].color=(.040,.087,.19,1)
        late=bpy.data.lights.get("Late sun");late.energy=1.65;late.angle=math.radians(3.2)
        stretch=nt.nodes.new("ShaderNodeVectorMath");stretch.operation="MULTIPLY"
        stretch.inputs[1].default_value=(2.5,2.5,14)
        nt.links.new(tex.outputs["Generated"],stretch.inputs[0])
        cloud=nt.nodes.new("ShaderNodeTexNoise");cloud.inputs["Scale"].default_value=2.6;cloud.inputs["Detail"].default_value=4
        nt.links.new(stretch.outputs[0],cloud.inputs["Vector"])
        veil=nt.nodes.new("ShaderNodeValToRGB")
        for el,pos,col in zip(veil.color_ramp.elements,(.49,.73),((0,0,0,1),(.24,.24,.24,1))):
            el.position=pos;el.color=col
        nt.links.new(cloud.outputs["Fac"],veil.inputs[0])
        sky_mix=nt.nodes.new("ShaderNodeMixRGB");sky_mix.inputs[2].default_value=(.72,.68,.66,1)
        nt.links.new(veil.outputs[0],sky_mix.inputs[0]);nt.links.new(ramp.outputs[0],sky_mix.inputs[1]);nt.links.new(sky_mix.outputs[0],bg.inputs["Color"])
        sc.render.image_settings.quality=96
camdata=bpy.data.cameras.new("Engineering film camera")
camdata.sensor_fit="VERTICAL";camdata.sensor_height=32;camdata.clip_start=.07;camdata.clip_end=2600
cam=obj(camdata.name,camdata);sc.camera=cam
objects=[]
for i,n in enumerate(manifest["nodes"]):
    idx=n["mesh"]
    if idx<0 or idx not in mesh_meta or mesh_meta[idx]["mat"]==1:continue
    if (kind=="studio")!=(n["group"]=="IFC studio"):continue
    local=pose[i,source_first:source_last+1]
    if not np.any(np.all(np.abs(local[:,3:6])>1.e-6,axis=1)):continue
    group=n["group"]
    if kind=="studio":typ="studio"
    elif group in ("Foundation","Inner concrete wall","Outer concrete wall","Control office","Architectural finish"):typ="concrete"
    elif group in ("Landscape","Site works","Frame laydown","Power laydown"):typ="land"
    elif mesh_meta[idx]["mat"]==3:typ="machine"
    else:typ="other"
    o=obj(n["name"],read_mesh(idx,typ))
    for k,v in n.get("extras",{}).items():o[k]=v
    objects.append((i,o))

previous={}
def update(_,depsgraph=None):
    t=sc.frame_current
    if t<a.first or t>a.last:return
    source_t=min(source_last,roof+t//2) if review else t
    for idx,o in objects:
        q=pose[idx,source_t];show=bool(np.all(abs(q[3:6])>.000001))
        if review and t%2 and show and source_t<source_last:
            next_q=pose[idx,source_t+1]
            if np.all(abs(next_q[3:6])>.000001) and not np.array_equal(q,next_q):
                mid=(q+next_q)*.5
                mid[6]=q[6]+.5*((next_q[6]-q[6]+math.pi)%(2*math.pi)-math.pi)
                q=mid
        old=previous.get(idx)
        if old is not None and old[0]==show and (not show or np.array_equal(q,old[1])):continue
        o.hide_render=not show
        if show:
            o.location=q[:3];o.scale=q[3:6];o.rotation_euler=(0.,0.,float(q[6]))
        previous[idx]=(show,q.copy())
    cam.location=camera["eye"][t];aim(cam,camera["target"][t])
    camdata.lens=32/(2*math.tan(math.radians(camera["fov"][t])/2))
    # The turbine study moves from the independent rail deck into a package inspection.
    if kind=="studio":
        phase=(t-manifest["studio"])//144
        stage.location.z=-1.62 if phase==0 else -.035
        if phase==3:
            u=(t-manifest["studio"]-432)/144
            blend=min(1.,max(0.,(u-.08)/.44));blend=blend*blend*(3-2*blend)
            target=Vector(camera["target"][t])+Vector((-1.,-1.2,1.8))*blend
            cam.location=target+(cam.location-Vector(camera["target"][t]))*(1-.40*blend);aim(cam,target)

# A single process retains the scene, graphics context and compiled materials for the entire run.
camera={k:camera[k] for k in camera.files}
bpy.app.handlers.frame_change_pre.append(update)
sc.frame_start=a.first;sc.frame_end=a.last
sc.frame_set(a.first);update(sc)
sc.render.filepath=str((a.out/"f_").resolve())
sc.render.use_file_extension=True
sc.render.use_overwrite=False
sc.render.use_placeholder=False
print("READY",len(objects),"objects",len(meshes),"meshes",sc.render.engine,flush=True)
if a.stills:
    for frame in a.stills:
        sc.frame_set(frame);update(sc)
        sc.render.filepath=str((a.out/f"f_{frame:04}.jpg").resolve())
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
bpy.app.handlers.frame_change_pre.remove(update)
