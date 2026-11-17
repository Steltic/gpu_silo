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
from . import clock
from . import closing
from . import service

NARRATION = Path(__file__).resolve().parents[1] / "audio" / "plan_view.flac"

MOVIE = "GPU_Silo.mp4"
MODEL = "GPU_Silo.glb"
SOURCES = ("SiloRender.cs", "CoolerFrameRender.cs", "DesignRender.cs", "FlowRender.cs")


def chapters():
    care, plant, yard = p.care, p.plant, p.yard
    first = frames.times(0)
    full, repair = p.FILLED, p.FILLED+care.REPAIR
    marks = [(0,"Cast the pod service sleeves into the inner wall"),(12,"Cast the cooler-frame anchors and conduits"),
            (123,"Seal the ground opening"),
            (p.C,"Begin the water-glycol fill and install the steel pod cage"),
            (clock.STORE_FILL[0],"Fill the water-glycol store to the top"),
            (yard.INSERT_AT,"Flatbed unloads three framed pods at the rail terminal"),
            (p.FIRST_POD,"Lift the first pod into the store"),
            (p.FIRST_POD+round(.91*p.motion_ticks(0)),"Dock the pod and connect it to the store"),
            (first[0],f"Crawler hangs the first of {frames.N} screened cooler frames while pods load"),
            (first[4],"Boom-lift crew connects the coolers and pumps"),
            (frames.times(1)[0],f"The other {frames.N-1} frames follow round the silo"),
            (p.SPEED_FRAME,f"Lower {p.LEVELS-2} levels of pods at {p.FAST_RATE:g}x"),
            (full,f"{p.TOTAL} pods installed | backup diesel level through the open top"),
            (full+plant.PICK_STARTS[1],"Turbine level | two in-line 25 MW gas turbine sets side by side"),
            (full+care.LID[0],"Lower the lid with its exhaust stacks and air inlet houses"),
            (full+care.CREW,f"Board the {p.BAYS} wedge work platforms"),
            (full+care.CREW+248,"Service the pods on their assigned levels"),
            (full+clock.ENCLOSURE_OPEN[0],f"Fold down the side of turbine set A | {cfg.POWER['module_output_mw']:g} MW gas turbine"),
            (full+clock.ENCLOSURE_CLOSE[0],"Close the enclosure and return to grade"),
            (full+care.SOLID_BEGIN,"Finished silo | design basis and 360-degree exterior sweep"),
            (full+closing.FUEL,f"Place {cfg.PROJECT['fuel']['tanks']} propane tanks and the diesel tank, and run the fuel lines to the power levels"),
            (full+closing.PLAN,"Plan view | hot and cold water-glycol dispersing into the store (narrated)"),
            (full+closing.SECTION,"Section | power, cooling and fuel"),
            (repair,f"Replacement | fault in pod {care.BAD+1:03} on Level {care.LEVEL}"),
            (repair+65,"Disconnect and clear the vertical bay"),
            (repair+service.RIG[0],f"Wide shot | crawler lowers cooler frame {service.K+1:02} while the pod comes out"),
            (repair+service.SLIDE[0],f"Withdraw one {frames.D['cooler_capacity_mw']:g} MW cooler and fit its replacement"),
            (repair+649,f"Feed replacement pod {p.TOTAL+1:03} | hang the cooler frame back"),
            (repair+1151,f"Reconnect the {p.TOTAL} service positions"),
            (full+closing.FINAL[0],"Finished silo")]
    if any(a[0]>=b[0] for a,b in zip(marks,marks[1:])):
        raise ValueError("Chapters are out of order: "+str([f for f,_ in marks]))
    return marks


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
    # The narration is placed at the start of the plan view and padded with silence to the film's length.
    start=round(1000*((p.FILLED+closing.PLAN)/p.FPS+closing.VOICE_LEAD))
    sound=["-i",str(NARRATION),"-filter_complex",
           f"[2:a]aresample=48000,adelay={start}:all=1,apad=whole_dur={p.FRAMES/p.FPS:.6f},pan=stereo|c0=c0|c1=c0[voice]",
           "-map","[voice]","-c:a","aac","-b:a","128k"] if NARRATION.is_file() else []
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(playlist),
        "-f","ffmetadata","-i",str(metadata),*sound[:2],"-map","0:v:0",*sound[2:],"-map_metadata","1","-map_chapters","1",
        "-c:v","copy","-video_track_timescale","12288","-t",f"{p.FRAMES/p.FPS:.6f}","-movflags","+faststart",str(out)],check=True)


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
