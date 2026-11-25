"""Record the standalone thermal film and the revised technical narration without rebuilding the film."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from . import narrate, technical_voice

def record(models,out):
    config=json.loads((narrate.ROOT/"design"/"technical_review.json").read_text(encoding="utf-8"))
    out.mkdir(parents=True,exist_ok=True)
    speaker=Kokoro(str(models/narrate.MODEL),str(models/narrate.VOICES))
    def take(cue,key,speed):
        name=out/f"raw-{key}.wav"
        source=out/f"raw-{key}.txt"
        if source.exists() and name.exists() and source.read_text(encoding="utf-8")==cue["say"]+str(speed):
            return sf.read(name,dtype="float32")[0]
        wave,hz=speaker.create(cue["say"],voice="am_eric",speed=speed,lang="en-us")
        assert hz==24000
        result=narrate.trim(np.asarray(wave,dtype=np.float32),hz,keep=.045)
        sf.write(name,result,hz,subtype="FLOAT")
        source.write_text(cue["say"]+str(speed),encoding="utf-8")
        return result
    rate=24000; at=0; shots=[]; timed=[]; parts=[]
    for cue in config["thermal"]:
        w=take(cue,cue["id"],1.02)
        gap=.46 if at else .55
        frames=int(np.ceil((gap+len(w)/rate+(.55 if cue["id"]!="reserve" else 1.05))*24))
        segment=np.zeros(frames*1000,np.float32);index=round(gap*rate)
        segment[index:index+len(w)]=w
        first=at/24+gap; last=first+len(w)/rate
        shots.append({**cue,"first":at,"last":at+frames,"voiceStart":first,"voiceEnd":last})
        timed.append(dict(start=first,end=last,text=cue["caption"]))
        at+=frames;parts.append(segment)
    wave=np.concatenate(parts);wave*=.87/max(.001,abs(wave).max())
    sf.write(out/"thermal.flac",wave,rate,subtype="PCM_16")
    technical_voice.captions(out/"thermal.srt",timed,wave,rate)
    (out/"thermal.json").write_text(json.dumps(shots,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Thermal",at,"frames",round(at/24,3),"seconds",flush=True)
    edits=[]
    for i,cue in enumerate(config["revised_cues"]):
        w=take(cue,f"edit{i}",1.10)
        window=cue.get("voiceWindow",(cue["start"],cue["end"]))
        start=round(window[0]*24)/24+.055
        room=window[1]-start-.11
        factor=max(1,len(w)/rate/room)
        if factor>1:
            path=out/f"fitted{i}.wav"
            subprocess.run(["ffmpeg","-y","-v","error","-i",str(out/f"raw-edit{i}.wav"),"-af",f"atempo={factor*1.005}",str(path)],check=True)
            w,_=sf.read(path,dtype="float32")
        w*=.87/max(.001,abs(w).max()); sf.write(out/f"cue{i}.flac",w,rate,subtype="PCM_16")
        end=start+len(w)/rate
        if end>window[1]:raise ValueError(cue["title"])
        edits.append(dict(**cue,voiceStart=round(start,5),voiceEnd=round(end,5),fit=round(factor,3)))
        print(cue["title"],round(start,3),round(end,3),"fit",round(factor,3),flush=True)
    assert edits[-1]["voiceEnd"]<config["shaft_entry_frame"]/24
    (out/"edits.json").write_text(json.dumps(edits,indent=2,ensure_ascii=False),encoding="utf-8")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("models",type=Path);p.add_argument("out",type=Path)
    a=p.parse_args();record(a.models,a.out)
