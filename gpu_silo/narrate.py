"""Record the plan-view narration with Kokoro and write its caption timings.

The audio and the timings are committed, so building the movie does not need the speech model.
Run this again only after editing design/narration.json:

    pip install kokoro-onnx soundfile
    python -m gpu_silo narrate --models DIRECTORY

DIRECTORY holds kokoro-v1.0.onnx and voices-v1.0.bin from the kokoro-onnx model release.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"design"/"narration.json"
AUDIO=ROOT/"audio"
MODEL,VOICES="kokoro-v1.0.onnx","voices-v1.0.bin"


def trim(samples,rate,keep=.06,floor=.004):
    """Drop the silence the model leaves at each end of a line."""
    import numpy as np
    loud=np.flatnonzero(np.abs(samples)>floor)
    if not len(loud):return samples
    pad=round(keep*rate)
    return samples[max(0,loud[0]-pad):min(len(samples),loud[-1]+pad)]


def record(models,name="plan_view"):
    try:
        import numpy as np
        import soundfile
        from kokoro_onnx import Kokoro
    except ImportError as error:
        raise SystemExit(f"{error}. Install the narration tools: pip install kokoro-onnx soundfile")
    models=Path(models)
    for file in (MODEL,VOICES):
        if not (models/file).is_file():raise SystemExit(f"{models/file} not found. See CONTRIBUTING.md, 'Narration'.")
    script=json.loads(SCRIPT.read_text(encoding="utf-8"))[name]
    voice=Kokoro(str(models/MODEL),str(models/VOICES))
    pieces,lines,clock,rate=[],[],0.,None
    for line in script["lines"]:
        samples,rate=voice.create(line["say"],voice=script["voice"],speed=script["speed"],lang="en-us")
        samples=trim(np.asarray(samples,dtype=np.float32),rate)
        length=len(samples)/rate
        lines.append({"start":round(clock,3),"end":round(clock+length,3),"text":line["show"]})
        gap=np.zeros(round(script["pause_seconds"]*rate),dtype=np.float32)
        pieces+=[samples,gap];clock+=length+len(gap)/rate
    sound=np.concatenate(pieces[:-1])
    sound*=.89/max(1e-6,float(np.abs(sound).max()))
    AUDIO.mkdir(exist_ok=True)
    soundfile.write(AUDIO/f"{name}.flac",sound,rate,subtype="PCM_16")
    timing={"voice":script["voice"],"model":"Kokoro v1.0","sample_rate":rate,
            "duration":round(len(sound)/rate,3),"lines":lines}
    (AUDIO/f"{name}.json").write_text(json.dumps(timing,indent=2)+"\n",encoding="utf-8",newline="\n")
    return AUDIO/f"{name}.flac",timing["duration"]
