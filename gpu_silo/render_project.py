"""Rebuild the animated GLB and the 720p movie from this project."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import pod_scene as p
from . import silo_model as silo
from . import design as cfg
from . import cooler_frames as frames
from . import calcs

MOVIE = "GPU_Silo.mp4"
MODEL = "GPU_Silo.glb"
SOURCES = ("SiloRender.cs", "CoolerFrameRender.cs", "DesignRender.cs")


def chapters():
    care, plant, yard = p.care, p.plant, p.yard
    first = frames.times(0)
    return [(0,"Position the pod service conduits"),(12,"Cast the cooler-frame anchors and conduits"),
            (123,"Seal the ground opening"),
            (p.C,"Begin the water-glycol fill and install the steel pod cage"),
            (frames.START,f"Retained crawler tracks round the silo with {frames.N} dry cooler frames"),
            (first[3],"Seat the first frame on its cast-in anchors"),
            (first[4],"Boom-lift crew connects the coolers and pumps"),
            (frames.times(1)[0],f"Place the remaining {frames.N-1} frames"),
            (frames.END,"Fill the water-glycol store to the rim"),
            (yard.INSERT_AT,"Flatbed unloads three framed pods at the rail terminal"),
            (p.FIRST_POD,"Lift the first pod into the store"),
            (p.FIRST_POD+round(.91*p.motion_ticks(0)),"Dock the liquid, power and data connection"),
            (p.SPEED_FRAME,f"Lower {p.LEVELS-2} levels of pods at {p.FAST_RATE:g}x"),
            (p.FILLED,f"{p.TOTAL} pods installed | lower power module through the open top"),
            (p.FILLED+plant.PICK_STARTS[1],"Upper power module at 90 degrees"),
            (p.FILLED+plant.VENT_START,"Extend four exhausts to the rim"),
            (p.FILLED+care.CREW,f"Board the {p.BAYS} wedge work platforms"),
            (p.FILLED+care.CREW+248,"Service the pods on their assigned levels"),
            (p.FILLED+care.CREW+420,"Service the underside of the lower power unit"),
            (p.FILLED+care.REPAIR,f"Fault in pod {care.BAD+1:03} on Level {care.LEVEL}"),
            (p.FILLED+care.REPAIR+65,"Disconnect and clear the vertical bay"),
            (p.FILLED+care.REPAIR+434,f"Lower pod {care.BAD+1:03} and transfer it out through the door"),
            (p.FILLED+care.REPAIR+649,f"Feed replacement {p.TOTAL+1:03} and hoist it to Level {care.LEVEL}"),
            (p.FILLED+care.REPAIR+1151,f"Reconnect the {p.TOTAL} service positions"),
            (p.FILLED+care.SOLID_BEGIN,"Finished silo | design basis and 360-degree exterior sweep")]


def ffmeta(path):
    def ms(frame): return round(1000*frame/p.FPS)
    marks=chapters()
    data=[";FFMETADATA1",f"title={cfg.TITLE} | {calcs.C['racks']} GPU racks in {calcs.C['pods']} {cfg.NAME} pods"]
    for (fr,title),end in zip(marks,[f for f,_ in marks[1:]]+[p.FRAMES]):
        data+=["[CHAPTER]","TIMEBASE=1/1000","START="+str(ms(fr)),"END="+str(ms(end)),"title="+cfg.display(title)]
    path.write_text("\n".join(data)+"\n",encoding="utf-8")


def compile_renderer(source,target):
    """Build the reference renderer with .NET Framework on Windows or Mono elsewhere. Returns its command line."""
    files=[str(source/name) for name in SOURCES]
    if sys.platform=="win32":
        compiler=Path(os.environ["WINDIR"])/"Microsoft.NET/Framework64/v4.0.30319/csc.exe"
        if not compiler.is_file():
            raise SystemExit("Install the .NET Framework 4.x 64-bit C# compiler for the movie.")
        subprocess.run([str(compiler),"/nologo","/optimize+","/codepage:65001","/reference:System.Drawing.dll",
                        "/out:"+str(target),*files],check=True)
        return [str(target)]
    compiler,runtime=shutil.which("mcs"),shutil.which("mono")
    if not compiler or not runtime:
        raise SystemExit("Install Mono (mono-mcs, libmono-system-drawing4.0-cil and libgdiplus) for the movie.")
    subprocess.run([compiler,"-nologo","-optimize+","-codepage:65001","-r:System.Drawing.dll","-out:"+str(target),*files],check=True)
    return [runtime,str(target)]


def encode(renderer,scene,video,begin,end):
    command=["ffmpeg","-hide_banner","-loglevel","error","-nostats","-y","-f","rawvideo",
        "-pix_fmt","bgr0","-video_size","1920x1080","-framerate",str(p.FPS),"-i","pipe:0",
        "-an","-vf",f"scale={cfg.MOVIE['width_px']}:{cfg.MOVIE['height_px']}:flags=lanczos:out_color_matrix=bt709,format=yuv420p",
        "-c:v","libx264","-preset","fast","-crf","22","-maxrate","1800k","-bufsize","3600k","-colorspace","bt709",
        "-color_primaries","bt709","-color_trc","bt709","-video_track_timescale","12288",str(video)]
    run=subprocess.Popen([*renderer,str(scene),"stream",str(begin),str(end)],stdout=subprocess.PIPE)
    write=subprocess.Popen(command,stdin=run.stdout)
    run.stdout.close()
    return run,write


def render(renderer,scene,out,work,jobs):
    """Render equal spans of the film side by side, then join them without re-encoding."""
    jobs=max(1,min(jobs,p.FRAMES//240))
    cuts=[round(p.FRAMES*j/jobs) for j in range(jobs+1)]
    parts=[work/f"part{j:02}.mp4" for j in range(jobs)]
    running=[encode(renderer,scene,part,a,b) for part,a,b in zip(parts,cuts,cuts[1:])]
    failed=[(run.wait(),write.wait()) for run,write in running]
    if any(a or b for a,b in failed):raise SystemExit(f"Renderer and FFmpeg returned {failed}")
    def quote(path):
        return "'"+Path(path).resolve().as_posix().replace("'","'\\''")+"'"
    playlist=work/"join.ffconcat";metadata=work/"chapters.txt"
    lines=["ffconcat version 1.0"]
    for part,a,b in zip(parts,cuts,cuts[1:]):lines+=["file "+quote(part),f"duration {(b-a)/p.FPS:.9f}"]
    playlist.write_text("\n".join(lines)+"\n",encoding="utf-8")
    ffmeta(metadata)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(playlist),
        "-f","ffmetadata","-i",str(metadata),"-map","0:v:0","-map_metadata","1","-map_chapters","1",
        "-c:v","copy","-video_track_timescale","12288","-movflags","+faststart",str(out)],check=True)


def stills(output,ticks,scene_data=None):
    """Write full-resolution PNG frames for review."""
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).resolve().parents[1]/"renderer"
    with tempfile.TemporaryDirectory(prefix="silo-",dir=output) as tmp:
        work=Path(tmp);data=work/"scene.bin"
        p.render_data(p.build(),data)
        renderer=compile_renderer(source,work/"SiloRender.exe")
        subprocess.run([*renderer,str(data),"frame",str(output),*map(str,ticks)],check=True)


def build_project(output, *, movie=True, jobs=None):
    output = Path(output).resolve()
    source = Path(__file__).resolve().parents[1] / "renderer"
    if movie and not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg with libx264 is required for the movie.")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="silo-",dir=output) as tmp:
        work=Path(tmp)
        scene=p.build();silo.glb_file(scene,output/MODEL)
        print(output/MODEL)
        if not movie:return
        data=work/"scene.bin";p.render_data(scene,data)
        renderer=compile_renderer(source,work/"SiloRender.exe")
        render(renderer,data,output/MOVIE,work,jobs or os.cpu_count() or 1)
        print(output/MOVIE)
