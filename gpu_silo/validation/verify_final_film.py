"""Decode the final cut and check every picture against its source segment."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess

import numpy as np

from .. import narrate
from ..final_film import assembly, picture_info
from ..final_voice import FPS, read_json
from ..short_song import probe


def frame_hashes(path):
    checks = subprocess.check_output([
        "ffmpeg", "-hide_banner", "-v", "error", "-xerror", "-threads", "4", "-i", str(path),
        "-map", "0:v:0", "-vf", "scale=192:108:flags=area,format=gray", "-threads", "2",
        "-fps_mode", "passthrough", "-f", "framemd5", "-"
    ], text=True)
    return [line.rsplit(",", 1)[1].strip() for line in checks.splitlines() if line.strip() and not line.startswith("#")]


def small_frames(path):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-xerror", "-threads", "4", "-i", str(path), "-map", "0:v:0",
        "-vf", "scale=160:90:flags=area,format=gray", "-threads", "2", "-fps_mode", "passthrough",
        "-f", "rawvideo", "-"
    ])
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, 90, 160)


def check_wide_excerpt(opening, orbit, first, stop):
    old = small_frames(orbit).astype(np.int16)
    new = small_frames(opening).astype(np.int16)
    if not 0 < first < stop <= len(old) or len(new) != stop-first:
        raise ValueError("The opening must use the selected wide orbit frames")
    error = np.abs(new - old[first:stop])
    # The upper half is clear of both graphics throughout the orbit. The lower half
    # should match too once the opening's independently timed title has faded in.
    config = read_json(narrate.ROOT / "design" / "technical_review.json")["closing_overlay"]
    visible = config["fade_start_frame"] + config["fade_frames"]
    held = error[visible:]
    if error[:, :45].mean(axis=(1, 2)).max() > 1.5 or (len(held) and held.mean(axis=(1, 2)).max() > 1.5):
        raise ValueError("The wide opening differs from its source camera frames")
    if first >= visible and error[0, 65:, :60].mean() < 5:
        raise ValueError("The opening should begin on the clean silo, before its title appears")


def check_sound_and_captions(path, frames, captions):
    media = probe(path, "-show_streams", "-show_chapters")
    visible = [s for s in media["streams"] if s["codec_type"] != "data"]
    if [s["codec_type"] for s in visible] != ["video", "audio", "subtitle"]:
        raise ValueError(f"Unexpected media streams in {path}")
    _, audio, sub = visible
    duration = int(audio["duration_ts"]) * Fraction(audio["time_base"])
    if audio["channels"] != 1 or audio["sample_rate"] != "48000" or duration != Fraction(frames, FPS):
        raise ValueError(f"Dialogue length or format differs from picture in {path}")
    if sub["tags"].get("language") != "eng" or sub["disposition"]["default"]:
        raise ValueError("The English dialogue captions must be selectable")
    embedded = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:s",
                                        "-c:s", "srt", "-f", "srt", "-"]).decode("utf-8-sig")
    if embedded.split() != captions.read_text(encoding="utf-8-sig").split():
        raise ValueError(f"Embedded caption text or timing differs in {path}")
    return media["chapters"]


def verify(work, out, thermal, orbit):
    timing = read_json(work / "timeline.json")
    film = out / "gpu_silo.mp4"
    opening = out / "gpu_silo_intro.mp4"
    picture_info(film, timing["total"])
    picture_info(opening, timing["intro"])
    chapter_list = check_sound_and_captions(film, timing["total"], work / "gpu_silo.srt")
    check_sound_and_captions(opening, timing["intro"], work / "intro.srt")
    expected = probe(work / "chapters.ffmetadata", "-f", "ffmetadata", "-show_chapters")["chapters"]
    def marks(chapters):
        return [(c["tags"]["title"], round(float(c["start_time"]) * FPS), round(float(c["end_time"]) * FPS))
                for c in chapters]
    if len(chapter_list) != len(assembly()[0]) + 6 or marks(chapter_list) != marks(expected):
        raise ValueError("Film chapter titles or boundaries differ from the edit")
    closing_start = timing["total"] - timing["closing"]
    if chapter_list[-1]["tags"]["title"] != "Closing orbit" or round(float(chapter_list[-1]["start_time"]) * FPS) != closing_start:
        raise ValueError("The closing chapter must start on the first silent orbit frame")

    orbit_hashes = frame_hashes(orbit)
    intro_hashes = frame_hashes(opening)
    if "intro_orbit_frames" in timing:
        check_wide_excerpt(opening, orbit, *timing["intro_orbit_frames"])
        if intro_hashes != frame_hashes(orbit.with_name("wide_intro_picture.mp4")):
            raise ValueError("Standalone introduction differs from its wide picture master")
    elif intro_hashes != orbit_hashes[:timing["intro"]]:
        raise ValueError("Opening pictures differ from the original orbit prefix")
    pictures = intro_hashes.copy()
    for name in assembly()[1]:
        pictures.extend(frame_hashes(work / f"{name}.mp4"))
    pictures.extend(frame_hashes(thermal))
    pictures.extend(orbit_hashes)
    actual = frame_hashes(film)
    if len(actual) != timing["total"] or actual != pictures:
        raise ValueError("A source picture was changed, dropped or repeated during assembly")

    sound = np.frombuffer(subprocess.check_output([
        "ffmpeg", "-v", "error", "-xerror", "-i", str(film), "-map", "0:a", "-c:a", "pcm_f32le", "-f", "f32le", "-"
    ]), dtype="<f4")
    for line in timing["dialogue"]:
        samples = sound[round(line["start"]*48000):round(line["end"]*48000)]
        if np.sqrt(np.mean(samples**2)) < .015:
            raise ValueError(f"Missing dialogue for {line['text']}")
    if np.abs(sound[closing_start*2000:]).max() > .0001:
        raise ValueError("Unexpected sound in the closing orbit")
    print(json.dumps(dict(frames=len(actual), seconds=len(actual)/FPS, matchingIntroFrames=len(intro_hashes),
                          introOrbitFrames=timing.get("intro_orbit_frames", [0, timing["intro"]]),
                          closingSilentFrames=len(orbit_hashes), chapters=len(chapter_list),
                          dialogueCues=len(timing["dialogue"])), indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("work", "out", "thermal", "orbit"):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    verify(args.work, args.out, args.thermal, args.orbit)
