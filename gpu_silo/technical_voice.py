"""Record the 2× cut from its own technical script, with captions on the recorded syllables."""
import argparse
import json
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

from . import narrate

SCRIPT = narrate.ROOT / "design" / "technical_short.json"


def stamp(t):
    ms = round(t * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def caption_parts(text):
    pieces=[]
    for sentence in re.split(r"(?<=[.!?])\s+",text):
        if len(sentence)<=82:
            pieces.append(sentence)
            continue
        words=sentence.split()
        allowed=[i for i in range(1,len(words)) if words[i] not in ("MW","MW.","kW","m³","K","Hz","mm","m","°C.")]
        def penalty(i):
            left=" ".join(words[:i]);right=" ".join(words[i:])
            boundary=8 if words[i] in ("with","at","and","after","on","for","in") or left.endswith(",") else 0
            return abs(len(left)-len(right))-boundary
        split=min(allowed,key=penalty)
        pieces.extend((" ".join(words[:split])," ".join(words[split:])))
    return pieces


def captions(out,lines,samples,rate):
    import numpy as np
    entries=[]
    for line in lines:
        parts=line.get("parts") or caption_parts(line["text"])
        total=sum(len(t) for t in parts)
        elapsed=0;bounds=[line["start"]]
        for part in parts[:-1]:
            elapsed+=len(part)
            expected=line["start"]+(line["end"]-line["start"])*elapsed/total
            # Prefer a real gap close to the written clause boundary.
            nearby=np.arange(expected-.22,expected+.221,.01)
            quiet=[float(np.mean(abs(samples[round((t-.015)*rate):round((t+.015)*rate)])))+.007*abs(t-expected) for t in nearby]
            bounds.append(float(nearby[int(np.argmin(quiet))]))
        bounds.append(line["end"])
        for start,end,part in zip(bounds,bounds[1:],parts):
            entries.append((start,end,"\n".join(textwrap.wrap(part,width=44,break_long_words=False))))
    out.write_text("\n\n".join(f"{i}\n{stamp(start)} --> {stamp(end)}\n{text}" for i,(start,end,text) in enumerate(entries,1))+"\n",encoding="utf-8")


def record(models, out):
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    speaker = Kokoro(str(models / narrate.MODEL), str(models / narrate.VOICES))
    rate = 24000
    film = np.zeros(((script["sourceFrames"] + 1) // 2) * rate // 24, np.float32)
    lines = []
    for i, cue in enumerate(script["cues"]):
        start = round(cue["start"] * 24) / 24 + .13
        limit = cue["end"] - start - .13
        raw, hz = speaker.create(cue["say"], voice=script["voice"], speed=1.08, lang="en-us")
        samples = narrate.trim(np.asarray(raw, np.float32), hz)
        if hz != rate:
            raise ValueError(hz)
        tempo = max(1., len(samples) / (rate * limit))
        if tempo > 1.35:
            raise ValueError(f"Shorten cue {i+1}: {tempo:.2f}")
        if tempo > 1.001:
            with tempfile.TemporaryDirectory(dir=out) as tmp:
                a, b = (Path(tmp) / name for name in ("a.wav", "b.wav"))
                sf.write(a, samples, rate)
                subprocess.run(["ffmpeg", "-v", "error", "-i", str(a), "-af", f"atempo={tempo*1.008}", str(b)], check=True)
                samples, _ = sf.read(b, dtype="float32")
        first = round(start * rate)
        film[first:first+len(samples)] = samples
        end = (first + len(samples)) / rate
        if end > cue["end"]:
            raise ValueError(f"Cue overruns shot: {cue['title']}")
        lines.append(dict(start=start,end=end,text=cue["caption"],tempo=round(tempo,3)))
        print(i+1, cue["title"], round(end-start,2), round(tempo,2), flush=True)
    film *= .87 / max(.001, np.abs(film).max())
    sf.write(out / "technical_voice.flac", film, rate, subtype="PCM_16")
    (out / "technical_voice.json").write_text(json.dumps(lines, indent=2, ensure_ascii=False), encoding="utf-8")
    captions(out/"technical_short.srt",lines,film,rate)


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("models", type=Path)
    args.add_argument("out", type=Path)
    a = args.parse_args()
    record(a.models, a.out)
