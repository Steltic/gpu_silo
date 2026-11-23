"""Object-level excerpts from the issued IFC for the narrated build film.

Refresh the small offline mesh cache with python -m gpu_silo.short_reels PATH/TO/GPU_Silo.ifc.
The cache stores each group in assembly-local coordinates with its IFC product tags and GlobalIds.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path

from . import silo_model as s

CACHE = Path(__file__).with_name("short_ifc_geometry.json.gz")
SOURCE = "891dac77a0a1de577bf8da9c6e3301cef85eed5dc9f379a6a4a01bbb74bb7764"
STUDIO = (600., 600., 0.)
OFF, ON = (0., 0., 0.), (1., 1., 1.)
# The colour and the distance a product travels in the exploded view are editorial.
STEEL, LIGHT, COPPER, COOL, INK = "587279", "c3cdca", "cd8b54", "509e9c", "354c57"
TITLES = ("The steel shaft", "Inside a 4SU", "The dry cooler", "The turbine deck")
SUBS = ("Base anchors and sliding guide", "Four racks on twin trusses", "Coil, fan bank and pump", "Two independent generator sets")
ROWS = (
    [("Shaft diameter","1.16 m"),("Wall","50.8 mm"),("Base anchors","24 × M56"),("Guide","Four sliding pads")],
    [("Rack positions","4"),("Structure","Twin side trusses"),("Wall end","CDU and pump"),("Services","Liquid and power")],
    [("Thermal duty","2 MW per cooler"),("Frame","Three units"),("Discharge","Outward"),("Pump","One per unit")],
    [("Normal supply","2 × 25 MW"),("Fuel","Propane"),("Rails","4 box girders"),("Support","Independent ring")],
)
STEPS = (
    ("Fix the shaft base","Locate the guide arms","Seat the sliding collar"),
    ("Expose the trusses","Space the four racks","Dock cooling services"),
    ("Isolate one bay","Withdraw the cooler","Return to the frame"),
    ("Lift the covers","Locate the rail girders","Seat both generators"),
)
LOCATORS = (
    ("SHAFT","F-AN-01","Diesel/Sliding shaft collar and four replaceable guide pads"),
    ("POD-06-01-R2","POD-06-01-FRAME","POD-06-01-CDU"),
    ("Dry coolers/Cooler frame 01 | cooler 1","Cooler frames/Cooler frame 01 | steel frame","Pump units/Cooler frame 01 | pump unit 1"),
    ("Power modules/Turbine set A | gas turbine and generator","Turbines/Rail girder 01","Turbines/Bearing shoe 01"),
)


def selections():
    """IFC tag, colour, exploded offset in local metres, and whether the part drops away."""
    shaft = [("SHAFT", LIGHT, (0,0,0), False),
             ("Diesel/Sliding shaft collar and four replaceable guide pads", COPPER, (0,0,2.5), False),
             ("Diesel/Open ring beam", STEEL, (0,0,0), True)]
    for i in range(4):
        a=i*math.pi/2
        shaft.append((f"Diesel/Collar drag arm {i+1:02}", COOL, (2*math.cos(a),2*math.sin(a),1),False))
    shaft.extend((f"F-AN-{i:02}", COPPER, (0,0,-1.3),False) for i in range(1,25))
    prefix="POD-06-01-"
    pod=[(prefix+"FRAME",STEEL,(0,0,0),False)]
    pod.extend((prefix+f"R{i+1}",LIGHT,(.14*(i-1.5),0,.75+.23*i),False) for i in range(4))
    pod.extend([(prefix+"CDU",COOL,(.70,0,.45),False),(prefix+"P",COPPER,(1.30,0,.35),False),
                ("Steel shoes/L06B01 shaft root lock",STEEL,(-.13,0,0),True)])
    cooler=[("Cooler frames/Cooler frame 01 | steel frame",STEEL,(0,0,0),False),
            ("Cooler screens/Cooler frame 01 | mesh screen",LIGHT,(2,0,0),True)]
    for i in range(1,4):
        cooler.extend([(f"Dry coolers/Cooler frame 01 | cooler {i}",LIGHT,(2.4,0,.35),i!=1),
                       (f"Pump units/Cooler frame 01 | pump unit {i}",COOL,(3.5,.6,.35),i!=1)])
    turbine=[("Turbines/Open ring beam",STEEL,(0,0,0),False)]
    turbine.extend((f"Turbines/Rail girder {i:02}",COOL,(0,0,1.0),False) for i in range(1,5))
    turbine.extend((f"Turbines/Bearing shoe {i:02}",COPPER,(0,0,0),False) for i in range(1,17))
    for i,side in enumerate("AB"):
        turbine.extend([(f"Power modules/Turbine set {side} | gas turbine and generator",LIGHT,(0,(1 if i==0 else -1)*2.1,3.4+.8*i),False),
                        (f"ENC-{i+1}",INK,(0,0,5.5),True)])
    return shaft,pod,cooler,turbine


def extract(path):
    import ifcopenshell
    import ifcopenshell.geom as geom
    import ifcopenshell.util.placement
    import numpy as np
    from . import cooler_frames,plant
    path=Path(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=SOURCE:
        raise ValueError("Use the issued revision K exchange. Its SHA-256 is "+SOURCE)
    model=ifcopenshell.open(str(path))
    elements={e.Tag:e for e in model.by_type("IfcElement") if e.Tag and e.Representation}
    settings=geom.settings()
    settings.set("use-world-coords",True)
    groups=[]
    reference=("SHAFT","POD-06-01-R1","Cooler frames/Cooler frame 01 | steel frame","Power modules/Turbine set A | gas turbine and generator")
    for index,items in enumerate(selections()):
        ref=reference[index]
        matrix=ifcopenshell.util.placement.get_local_placement(elements[ref].ObjectPlacement)
        yaw=math.atan2(matrix[1,0],matrix[0,0])
        axes=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1]])
        meshes=[]
        for tag,_,_,_ in items:
            entity=elements[tag]
            shape=geom.create_shape(settings,entity)
            points=np.asarray(shape.geometry.verts).reshape(-1,3) @ axes
            faces=np.asarray(shape.geometry.faces).reshape(-1,3)
            meshes.append((tag,entity.GlobalId,points,faces))
        all_points=np.vstack([m[2] for m in meshes])
        lo,hi=all_points.min(axis=0),all_points.max(axis=0)
        datum=np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]])
        products=[]
        for tag,guid,v,idx in meshes:
            product=dict(tag=tag,guid=guid,mm=np.rint((v-datum)*1000).astype(int).tolist(),faces=idx.tolist())
            # The exchange combines the faces into one styled representation per product.
            # Recover the illustration colours on matching triangles, preserving every IFC vertex.
            reference_mesh=None
            if tag.startswith("Dry coolers/"):reference_mesh=cooler_frames.cooler_mesh()
            if tag.startswith("Pump units/"):reference_mesh=cooler_frames.pump_mesh()
            if tag.startswith("Power modules/"):reference_mesh=plant.turbine_mesh(-1 if "set A" in tag else 1)
            if reference_mesh:
                tris=np.array([t[:3] for t in reference_mesh.tris])
                align=v.min(axis=0)-tris.min(axis=(0,1))
                centers=np.rint((tris.mean(axis=1)+align)*1000).astype(int)
                palette={tuple(c):list(t[3]) for c,t in zip(centers,reference_mesh.tris)}
                colours=[palette.get(tuple(c)) for c in np.rint(v[idx].mean(axis=1)*1000).astype(int)]
                product["colours"]=colours
            products.append(product)
        groups.append(products)
    raw=json.dumps(dict(sha256=digest,groups=groups),separators=(",",":")).encode()
    CACHE.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))


def camera(p,frame):
    elapsed=frame-p.FILLED-p.clock.DETAIL_START
    index,offset=divmod(elapsed,p.clock.DETAIL_LENGTH)
    u=offset/p.clock.DETAIL_LENGTH
    # Each product is in its own IFC local axes.
    az,el,dist,z=[(-64,12,69,13.5),(-67,17,17.8,1.6),(-32,17,33,4.1),(-64,30,42,3.7)][index]
    return p.camera((STUDIO[0],STUDIO[1],z),az+13*s.step(0,1,u),el,dist)


def install(scene,node,p):
    data=json.loads(gzip.decompress(CACHE.read_bytes()))
    if data["sha256"]!=SOURCE:raise ValueError("Incorrect IFC source for the short film")
    for j,(spec,assets) in enumerate(zip(selections(),data["groups"],strict=True)):
        start=p.FILLED+p.clock.DETAIL_START+j*p.clock.DETAIL_LENGTH
        stop=start+p.clock.DETAIL_LENGTH
        root=node("IFC study | "+TITLES[j],-1,"IFC studio",t=STUDIO,
                  tracks={"scale":[(0,OFF),(start-.02,OFF),(start,ON),(stop-.02,ON),(stop,OFF)]})
        for n,((tag,col,delta,context),asset) in enumerate(zip(spec,assets,strict=True)):
            if asset["tag"]!=tag:raise ValueError(tag)
            mesh=s.Mesh(tag);mesh.material=3
            points=[tuple(v*.001 for v in vertex) for vertex in asset["mm"]]
            colour=s.rgb(col)
            colours=asset.get("colours") or [None]*len(asset["faces"])
            for (a,b,c),tint in zip(asset["faces"],colours,strict=True):
                mesh.tris.append((points[a],points[b],points[c],tint or colour))
            start_motion=start+12+(n%4)*4
            full=start+106
            keys={"translation":[(0,(0,0,0)),(start_motion,(0,0,0)),(full,delta),(stop-76,delta),(stop-14,(0,0,0))]}
            if context:
                # Context clears early, then returns to its installed location at the end.
                keys["scale"]=[(0,ON),(start+44,ON),(start+59,OFF),(stop-32,OFF),(stop-18,ON)]
            holder=node("IFC detail | "+tag,scene.mesh(mesh),"IFC studio",root,tracks=keys)
            scene.nodes[holder]["extras"]={"ifcGlobalId":asset["guid"],"ifcTag":tag}
            lo=[min(v[i] for v in points) for i in range(3)]
            hi=[max(v[i] for v in points) for i in range(3)]
            if tag.startswith("POD-06-01-") and not tag.endswith("FRAME"):
                from . import short_art
                fascia=short_art.rack_fascia(tag,lo,hi)
                node("Illustrative finish | "+tag,scene.mesh(fascia),"IFC studio",holder)
            if tag in LOCATORS[j]:
                mid=tuple((a+b)/2 for a,b in zip(lo,hi))
                if tag.endswith("FRAME"):mid=(lo[0]+.4,lo[1],lo[2]+.4)
                if tag.endswith("steel frame"):mid=(hi[0],lo[1],hi[2]-.8)
                node("Locator | "+tag,-1,"Detail locator "+str(LOCATORS[j].index(tag)),holder,t=mid)
    scene.project_info["shortFilmIfcSourceSHA256"]=SOURCE


def clips(master,output):
    """Export the four narrated chapters and their continuous 48-second reel from the verified master."""
    import subprocess
    import tempfile
    from . import short_voice
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_chapters","-of","json",str(master)]))
    selected=[c for c in info["chapters"] if c["tags"]["title"].startswith("IFC detail | ")]
    if [c["tags"]["title"].split(" | ",1)[1] for c in selected]!=list(TITLES):raise ValueError("Unexpected short-film chapters")
    names=("shaft","4su","cooler","turbines")
    spans=[(name,c,c) for name,c in zip(names,selected)]+[("highlights",selected[0],selected[-1])]
    for name,first,last in spans:
        begin=float(first["start_time"]);end=float(last["end_time"])
        path=output/("IFC_"+name+".mp4")
        with tempfile.TemporaryDirectory(dir=output) as tmp:
            subt=Path(tmp)/"captions.srt"
            short_voice.subtitles(subt,begin,end)
            subprocess.run(["ffmpeg","-v","error","-y","-ss",str(begin),"-i",str(master),"-i",str(subt),"-t",f"{end-begin:.3f}",
                "-map","0:v:0","-map","0:a:0","-map","1:s:0","-map_chapters","-1","-map_metadata","-1","-c:v","libx264",
                "-threads","4","-preset","fast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k","-c:s","mov_text",
                "-metadata:s:s:0","language=eng","-disposition:s:0","0","-movflags","+faststart",str(path)],check=True)
        print(path,flush=True)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path",type=Path,help="issued IFC, or the finished MP4 when exporting clips")
    parser.add_argument("--clips",type=Path,metavar="DIRECTORY",help="export component films into this directory")
    args=parser.parse_args()
    if args.clips:clips(args.path,args.clips)
    else:extract(args.path)
