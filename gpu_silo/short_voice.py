"""Place documentary narration against the short film's chapter clock."""
import json
from pathlib import Path

from . import clock, closing, narrate, pod_scene as p

ROOT=Path(__file__).resolve().parents[1]
AUDIO=ROOT/"audio"/"short_build.flac"
TIMINGS=AUDIO.with_suffix(".json")
SCRIPT=ROOT/"design"/"short_narration.json"


def cues():
    base=p.FILLED
    anchor={"build":0,"orbit":base+clock.ORBIT,"drawings":base+closing.PLAN}
    for i,name in enumerate(("shaft","pod","cooler","turbine")):
        anchor[name]=base+clock.DETAIL_START+i*clock.DETAIL_LENGTH
    script=json.loads(SCRIPT.read_text(encoding="utf-8"))
    return script,[(anchor[row["cue"]]/p.FPS+row["offset"],row) for row in script["lines"]]


def record(models):
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    script,lines=cues()
    speaker=Kokoro(str(Path(models)/narrate.MODEL),str(Path(models)/narrate.VOICES))
    rate=24000
    track=np.zeros(round(p.FRAMES/p.FPS*rate),dtype=np.float32)
    captions=[]
    for i,(at,line) in enumerate(lines):
        samples,freq=speaker.create(line["text"],voice=script["voice"],speed=script["speed"],lang="en-us")
        if freq!=rate:raise ValueError(freq)
        samples=narrate.trim(np.asarray(samples,dtype=np.float32),freq)
        end=at+len(samples)/freq
        next_at=lines[i+1][0] if i+1<len(lines) else len(track)/rate
        if end+.10>next_at:raise ValueError(f"Voice cue at {at:.2f} s ends at {end:.2f}; next cue at {next_at:.2f}")
        first=round(at*rate)
        track[first:first+len(samples)]=samples
        captions.append(dict(start=round(at,3),end=round(end,3),text=line["text"].replace("four S U","4SU")))
    track*=.87/max(abs(track).max(),1e-6)
    sf.write(AUDIO,track,rate,subtype="PCM_16")
    TIMINGS.write_text(json.dumps(dict(voice=script["voice"],rate=rate,lines=captions),indent=2)+"\n",encoding="utf-8")
    print(f"{len(lines)} timed cues, {len(track)/rate:.2f} seconds")


def subtitles(path,begin=0.,end=float("inf")):
    def stamp(seconds):
        msec=round(seconds*1000)
        return f"{msec//3600000:02}:{msec//60000%60:02}:{msec//1000%60:02},{msec%1000:03}"
    captions=json.loads(TIMINGS.read_text(encoding="utf-8"))["lines"]
    selected=[c for c in captions if c["end"]>begin and c["start"]<end]
    path.write_text("\n\n".join(f"{i}\n{stamp(max(c['start'],begin)-begin)} --> {stamp(min(end,c['end'])-begin)}\n{c['text']}" for i,c in enumerate(selected,1))+"\n",encoding="utf-8")


if __name__=="__main__":
    import sys
    record(sys.argv[1])
