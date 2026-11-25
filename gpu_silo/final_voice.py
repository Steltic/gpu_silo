"""Record the opening and conform the technical short's dialogue to its final picture."""
import argparse
import json
import math
from pathlib import Path
import re

import numpy as np

from . import narrate, technical_voice

FPS = 24
RATE = 24_000
SAMPLES_PER_FRAME = RATE // FPS


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_take(path):
    import soundfile as sf

    wave, rate = sf.read(path, dtype="float32")
    if rate != RATE or wave.ndim != 1:
        raise ValueError(f"Expected a mono {RATE} Hz recording in {path}")
    return wave


def record_intro(models, out):
    import soundfile as sf
    from kokoro_onnx import Kokoro

    cues = read_json(narrate.ROOT / "design" / "technical_review.json")["intro_narration"]
    voice = read_json(technical_voice.SCRIPT)["voice"]
    speaker = Kokoro(str(models / narrate.MODEL), str(models / narrate.VOICES))
    pieces = []
    timed = []
    cursor = 0
    for index, cue in enumerate(cues):
        raw, rate = speaker.create(cue["say"], voice=voice, speed=1.08, lang="en-us")
        if rate != RATE:
            raise ValueError(f"Unexpected speech sample rate {rate}")
        take = narrate.trim(np.asarray(raw, dtype=np.float32), rate, keep=.04)
        pause = round((.15 if index == 0 else .19) * rate)
        pieces.extend((np.zeros(pause, dtype=np.float32), take))
        cursor += pause
        timed.append(dict(start=cursor / rate, end=(cursor + len(take)) / rate, text=cue["caption"]))
        cursor += len(take)
    frames = math.ceil((cursor + .10 * RATE) / SAMPLES_PER_FRAME)
    if frames >= 540:
        raise ValueError(f"The {frames}-frame reading exceeds the closing orbit")
    wave = np.concatenate([*pieces, np.zeros(frames * SAMPLES_PER_FRAME - cursor, dtype=np.float32)])
    wave *= .87 / np.abs(wave).max()
    out.mkdir(parents=True, exist_ok=True)
    sf.write(out / "gpu_silo_intro.flac", wave, RATE, subtype="PCM_16")
    timing = dict(voice=voice, frames=frames, fps=FPS, lines=timed)
    (out / "gpu_silo_intro.json").write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
    print(f"Opening orbit: {frames} frames, {frames/FPS:.3f} s; last word ends at {timed[-1]['end']:.3f} s.")


def body_cues(originals, config):
    edits = config["revised_cues"]
    replacements = {c["title"] for c in edits}
    body_frames = round(config["move_narration_start"] * FPS)
    keep = [c for c in originals if c["title"] not in replacements
            and c["start"] != config["remove_narration_start"] and round(c["start"] * FPS) < body_frames]
    return sorted([*keep, *edits], key=lambda c: c["start"])


def conform(source, reviewed, intro, out):
    import soundfile as sf

    config = read_json(narrate.ROOT / "design" / "technical_review.json")
    edits = read_json(reviewed / "edits.json")
    edit_index = {cue["title"]: i for i, cue in enumerate(edits)}
    body_frames = round(config["move_narration_start"] * FPS)
    old_voice = read_take(source / "technical_voice.flac")
    old_times = {c["text"]: c for c in read_json(source / "technical_voice.json")}
    body = np.zeros(body_frames * SAMPLES_PER_FRAME, np.float32)
    timed_body = []
    for cue in body_cues(read_json(technical_voice.SCRIPT)["cues"], config):
        if cue["title"] in edit_index:
            index = edit_index[cue["title"]]
            wave = read_take(reviewed / f"cue{index}.flac")
            start = round(edits[index]["voiceStart"] * RATE)
        else:
            line = old_times[cue["caption"]]
            start = round(line["start"] * RATE)
            wave = old_voice[start:round(line["end"] * RATE)]
        end = start + len(wave)
        if end > len(body) or (timed_body and start < round(timed_body[-1]["end"] * RATE)):
            raise ValueError(f"Dialogue does not fit at {cue['title']}")
        body[start:end] = wave
        timed_body.append(dict(start=start/RATE, end=end/RATE, text=cue["caption"]))

    opening = read_take(intro / "gpu_silo_intro.flac")
    opening_times = read_json(intro / "gpu_silo_intro.json")
    thermal = read_take(reviewed / "thermal.flac")
    shots = read_json(reviewed / "thermal.json")
    closing_frames = config["silent_closing_source_frames"][1] - config["silent_closing_source_frames"][0]
    if len(opening) != opening_times["frames"] * SAMPLES_PER_FRAME or len(thermal) != shots[-1]["last"] * SAMPLES_PER_FRAME:
        raise ValueError("Picture and dialogue frame counts disagree")
    thermal_at = len(opening) + len(body)
    intro_lines = opening_times["lines"]
    for line in intro_lines:
        if len(line["text"]) > 90:
            # Keep the power rating and the concrete enclosure in separate caption cues.
            clauses = re.split(r"(?<=,)\s+", line["text"])
            if len(clauses) > 1:
                line["parts"] = clauses
    timeline = list(intro_lines)
    for line in timed_body:
        timeline.append(dict(start=line["start"] + len(opening)/RATE, end=line["end"] + len(opening)/RATE, text=line["text"]))
    for shot in shots:
        timeline.append(dict(start=shot["voiceStart"] + thermal_at/RATE,
                             end=shot["voiceEnd"] + thermal_at/RATE, text=shot["caption"]))
    whole = np.concatenate((opening, body, thermal, np.zeros(closing_frames * SAMPLES_PER_FRAME, np.float32)))
    out.mkdir(parents=True, exist_ok=True)
    sf.write(out / "dialogue.flac", whole, RATE, subtype="PCM_16")
    technical_voice.captions(out / "gpu_silo.srt", timeline, whole, RATE)
    technical_voice.captions(out / "intro.srt", intro_lines, opening, RATE)
    manifest = dict(intro=opening_times["frames"], body=body_frames, thermal=shots[-1]["last"],
                    closing=closing_frames, total=len(whole)//SAMPLES_PER_FRAME, dialogue=timeline)
    (out / "timeline.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Dialogue and captions: {len(timeline)} cues across {manifest['total']} frames.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    record = commands.add_parser("record")
    record.add_argument("models", type=Path)
    record.add_argument("out", type=Path)
    assemble = commands.add_parser("conform")
    for argument in ("source", "reviewed", "intro", "out"):
        assemble.add_argument(argument, type=Path)
    args = parser.parse_args()
    if args.action == "record":
        record_intro(args.models, args.out)
    else:
        conform(args.source, args.reviewed, args.intro, args.out)
