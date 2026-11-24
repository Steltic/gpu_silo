"""Composite the text-free Blender photography, recorded VO and retimed engineering graphics."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
os.environ["GPU_SILO_FILM"]="short"
from . import technical_graphics as art, technical_voice as voice


def run(args,cwd=None):
    subprocess.run([str(s) for s in args],cwd=cwd,check=True)


def chapters(path,frames):
    from . import render_project
    marks=[((f+1)//2,title) for f,title in render_project.short_chapters()]
    lines=[";FFMETADATA1","title=GPU Silo | Technical short"]
    for (frame,title),end in zip(marks,[f for f,_ in marks[1:]]+[frames]):
        lines+=["[CHAPTER]","TIMEBASE=1/24000",f"START={frame*1000}",f"END={end*1000}",f"title={title}"]
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")


def prepare(bake,scratch,framesdir,draw=True):
    scratch.mkdir(parents=True,exist_ok=True)
    framesdir.mkdir(parents=True,exist_ok=True)
    m=json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    script=json.loads(voice.SCRIPT.read_text(encoding="utf-8"))
    n=m["frames"]-m["drawing"]
    art.drawings(0,n/24).write(scratch/"draw.ass")
    art.overlays(script,m["drawing"]/24,m["frames"]/24).write(scratch/"titles.ass")
    chapters(scratch/"chapters.txt",m["frames"])
    if draw:
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","lavfi","-i","color=c=0x162c35:s=3840x2160:r=24",
             "-vf","ass=draw.ass","-frames:v",n,"-threads","2","-q:v","2","-start_number",m["drawing"],
             str((framesdir/"f_%04d.jpg").resolve())],scratch)


def encode(bake,work,framesdir,out):
    m=json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    missing=[n for n in range(m["frames"]) if not (framesdir/f"f_{n:04}.jpg").is_file()]
    if missing:raise ValueError(f"{len(missing)} missing frames, first is {missing[0]}")
    work=work.resolve();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    clean=out/"silo_short_clean.mp4"
    final=out/"silo_short.mp4"
    # Image sequences use full-range JPEG. Give both H.264 streams explicit video-range BT.709 metadata.
    video=["-c:v","libx264","-threads:v","5","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",
           "-color_primaries","bt709","-colorspace","bt709","-color_trc","bt709","-movflags","+faststart"]
    convert="scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p"
    raw=["ffmpeg","-hide_banner","-loglevel","error","-y","-framerate","24","-start_number","0","-i",str((framesdir/"f_%04d.jpg").resolve())]
    run([*raw,"-vf",convert,"-frames:v",m["frames"],*video,clean],work)
    # Composite from the original clean frames to avoid a lossy intermediate generation.
    run([*raw,"-i",out/"technical_voice.flac","-i",out/"technical_short.srt","-f","ffmetadata","-i","chapters.txt",
         "-filter_threads","3","-vf",convert+",ass=titles.ass","-frames:v",m["frames"],"-map","0:v:0","-map","1:a:0",
         "-force_key_frames",",".join(str((m["studio"]+144*k)/24) for k in range(5)),
         "-map","2:s:0","-map_chapters","3","-map_metadata","3",*video,"-af","loudnorm=I=-16:TP=-1.5:LRA=8","-ar","48000",
         "-c:a","aac","-b:a","160k","-c:s","mov_text","-metadata:s:s:0","language=eng","-disposition:s:0","0",
         "-metadata:s:a:0","language=eng","-metadata:s:a:0","title=Technical narration",final],work)
    shutil.copyfile(voice.SCRIPT,out/"technical_script.json")


def excerpts(bake,work,out):
    m=json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    lines=json.loads((out/"technical_voice.json").read_text(encoding="utf-8"))
    for name,first,last in (("shaft",0,1),("pod",1,2),("cooler",2,3),("turbines",3,4),("highlights",0,4)):
        start=(m["studio"]+first*144)/24
        end=(m["studio"]+last*144)/24
        # The master has a keyframe on every study cut. Remux picture and trim audio sample-accurately.
        sub=work/f"{name}.srt"
        active=[l for l in lines if start<l["end"] and l["start"]<end]
        sub.write_text("\n\n".join(f"{i}\n{voice.stamp(max(start,c['start'])-start)} --> {voice.stamp(min(end,c['end'])-start)}\n{c['text']}"
                                   for i,c in enumerate(active,1))+"\n",encoding="utf-8")
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",f"{start:.9f}","-i",out/"silo_short.mp4",
             "-ss",f"{start:.9f}","-i",out/"technical_voice.flac","-i",sub,"-t",f"{end-start:.9f}",
             "-map","0:v:0","-map","1:a:0","-map","2:s:0","-map_metadata","-1","-map_chapters","-1","-c:v","copy",
             "-af","loudnorm=I=-16:TP=-1.5:LRA=8","-ar","48000","-c:a","aac","-b:a","160k","-c:s","mov_text",
             "-metadata:s:s:0","language=eng","-disposition:s:0","0","-movflags","+faststart",out/f"IFC_{name}.mp4"])


def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_chapters","-show_format","-of","json",str(path)]))


def verify(out,bake):
    m=json.loads((bake/"scene.json").read_text(encoding="utf-8"))
    lines=json.loads((out/"technical_voice.json").read_text(encoding="utf-8"))
    if len(lines)!=20 or any(a["end"]>b["start"] for a,b in zip(lines,lines[1:])):raise ValueError("Voice cue overlap")
    for file,expected in (("silo_short.mp4",{"video","audio","subtitle","data"}),("silo_short_clean.mp4",{"video"})):
        p=probe(out/file);v=p["streams"][0]
        if (v["width"],v["height"],v["avg_frame_rate"],int(v["nb_frames"]))!=(3840,2160,"24/1",m["frames"]):
            raise ValueError(f"Invalid frame clock in {file}")
        if {s["codec_type"] for s in p["streams"]}!=expected:raise ValueError(f"Wrong streams in {file}")
        if file=="silo_short.mp4":
            if len(p["chapters"])!=23:raise ValueError("Missing source chapters")
            if abs(float(p["streams"][1]["duration"])-m["frames"]/24)>.060:raise ValueError("Narration end differs from picture end")
        run(["ffmpeg","-v","error","-xerror","-threads","4","-i",out/file,"-map","0:v","-map","0:a?","-f","null","-"])
    hashes={}
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name!="SHA256SUMS.txt":
            with path.open("rb") as f:hashes[path.name]=hashlib.file_digest(f,"sha256").hexdigest()
    (out/"SHA256SUMS.txt").write_text("".join(f"{v}  {k}\n" for k,v in hashes.items()),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["graphics","encode","excerpts","verify"])
    for arg in ("bake","scratch","frames","out"):parser.add_argument(arg,type=Path)
    a=parser.parse_args()
    if a.action=="graphics":prepare(a.bake,a.scratch,a.frames)
    if a.action=="encode":encode(a.bake,a.scratch,a.frames,a.out)
    if a.action=="excerpts":excerpts(a.bake,a.scratch,a.out)
    if a.action=="verify":verify(a.out,a.bake)
