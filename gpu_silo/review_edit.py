"""Proof the revised cues against the photographed cut points without assembling the final short."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
from . import review_editorial, technical_voice
from .mp4 import optional_captions

FPS=24
RANGES=((802,974),(1337,2215))
OFFICE=(1993,2071)

def source_to_proof(t):
    earlier=0
    for first,last in RANGES:
        if first/24-.025<=t<=last/24+.025:return earlier+(t*24-first)/24
        earlier+=(last-first)/24
    raise ValueError(f"Time {t} is outside the excerpts")

def prepare(config_dir,source,voice,out):
    cfg=json.loads((config_dir/"technical_review.json").read_text(encoding="utf-8"))
    original=json.loads((config_dir/"technical_short.json").read_text(encoding="utf-8"))
    cues=json.loads((voice/"edits.json").read_text(encoding="utf-8"))
    shaft=next(c for c in original["cues"] if c["title"]=="Steel shaft")
    shaft_take=next(c for c in json.loads((source/"technical_voice.json").read_text(encoding="utf-8")) if c["text"]==shaft["caption"])
    full,rate=sf.read(source/"technical_voice.flac",dtype="float32")
    if rate!=24000:raise ValueError("Unexpected original recording rate")
    total=sum(b-a for a,b in RANGES)
    proof=np.zeros(total*1000,np.float32);timed=[]
    def mix(w,t,text):
        start=round(source_to_proof(t)*rate);stop=start+len(w)
        if not(0<=start<stop<=len(proof)) or np.any(proof[start:stop]):raise ValueError("VO overlap or clipping")
        proof[start:stop]=w
        timed.append(dict(start=start/rate,end=stop/rate,text=text))
    for i,cue in enumerate(cues):
        w,hz=sf.read(voice/f"cue{i}.flac",dtype="float32");assert hz==rate
        mix(w,cue["voiceStart"],cue["caption"])
    s0,s1=[round(shaft_take[k]*rate) for k in ("start","end")]
    mix(full[s0:s1],s0/rate,shaft["caption"])
    sf.write(voice/"edit-proof.flac",proof,rate,subtype="PCM_16")
    technical_voice.captions(voice/"edit-proof.srt",timed,proof,rate)
    review_editorial.cue_images(voice/"edit-proof.ffconcat", [*cues, shaft],
                               lambda t: round(source_to_proof(t)*FPS), total, FPS)
    thermal=json.loads((voice/"thermal.json").read_text(encoding="utf-8"))
    first=round(cfg["move_narration_start"]*FPS);end=first+thermal[-1]["last"]
    notes={
        "fps":FPS,"status":"Component review with compact editorial lower thirds and a four-shot thermal study. Full short pending assembly.",
        "revisedCues":cues,"removeOldCueAt":cfg["remove_narration_start"],
        "officePictureFrames":list(OFFICE),"officeSign":"STELTICAI.COM",
        "steelShaftPictureStart":OFFICE[1]/FPS,"clearBeforeSteelShaftSeconds":round(OFFICE[1]/FPS-cues[-1]["voiceEnd"],5),
        "timingProofSourceFrameRangesEndExclusive":RANGES,
        "proposedClosingPictureIfThermalIsUsedInFull":[
            {"picture":"Existing assembly and four IFC studies","frames":[0,first]},
            {"picture":cfg["picture_order_after_turbine_ifc"][0],"frames":[first,end],"sound":"Standalone narrated thermal study"},
            {"picture":cfg["picture_order_after_turbine_ifc"][1],"frames":[end,end+540],"sourceFrames":cfg["silent_closing_source_frames"],"sound":"Silent"}],
        "thermalStudy":thermal}
    (out/"technical_review_edit.json").write_text(json.dumps(notes,indent=2,ensure_ascii=False),encoding="utf-8")

def render(source,voice,office,out):
    for frame in range(*OFFICE):
        if not (office/f"f_{frame:04}.jpg").is_file():raise FileNotFoundError(f"Office frame {frame}")
    cmd=["ffmpeg","-v","error","-y","-filter_complex_threads","3"]
    parts=[(RANGES[0][0],RANGES[0][1]),(RANGES[1][0],OFFICE[0]),OFFICE,(OFFICE[1],RANGES[1][1])]
    filters=[]
    for i,(first,last) in enumerate(parts):
        if i==2:
            cmd+=["-threads","2","-framerate","24","-start_number",str(first),"-i",str((office/"f_%04d.jpg").resolve())]
            scale="scale=1920:1080:in_range=full:out_range=limited:out_color_matrix=bt709"
        else:
            cmd+=["-threads","2","-ss",f"{first/FPS:.9f}","-i",str((source/"silo_short_clean.mp4").resolve())]
            scale="scale=1920:1080:flags=lanczos:out_color_matrix=bt709"
        filters.append(f"[{i}:v]trim=end_frame={last-first},{scale},format=yuv420p,setsar=1,setpts=N/(24*TB)[p{i}]")
    filters.append("[p0][p1][p2][p3]concat=n=4:v=1:a=0[base]")
    filters.append("[6:v]fps=24,format=yuva420p[lowerthird]")
    filters.append("[base][lowerthird]overlay=shortest=1,format=yuv420p[v]")
    cmd+=["-i","edit-proof.flac","-i","edit-proof.srt","-f","concat","-safe","0","-i","edit-proof.ffconcat","-filter_complex",";".join(filters),"-map","[v]","-map","4:a","-map","5:s",
          "-map_chapters","-1","-map_metadata","-1","-c:v","libx264","-threads","4","-crf","16","-preset","veryfast",
          "-r","24","-color_primaries","bt709","-color_trc","bt709","-colorspace","bt709",
          "-c:a","aac","-b:a","128k","-c:s","mov_text","-metadata:s:s:0","language=eng",
          "-metadata","title=Technical short | Revised narration and sign","-movflags","+faststart",str((out/"VO_edit_review.mp4").resolve())]
    subprocess.run(cmd,cwd=voice,check=True);optional_captions(out/"VO_edit_review.mp4")

if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    for field in ("source","voice","office","out"):ap.add_argument(field,type=Path)
    ap.add_argument("--prepare-only",action="store_true")
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    prepare(Path(__file__).resolve().parents[1]/"design",a.source,a.voice,a.out)
    if not a.prepare_only:render(a.source,a.voice,a.office,a.out)
