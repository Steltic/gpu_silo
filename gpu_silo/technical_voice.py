"""Record the 2× cut from its own technical script, with captions on the recorded syllables."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from . import narrate

SCRIPT = narrate.ROOT / "design" / "technical_short.json"


def stamp(t):
    ms = round(t * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


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
    (out / "technical_short.srt").write_text("\n\n".join(f"{i}\n{stamp(r['start'])} --> {stamp(r['end'])}\n{r['text']}" for i,r in enumerate(lines,1)) + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("models", type=Path)
    args.add_argument("out", type=Path)
    a = args.parse_args()
    record(a.models, a.out)
