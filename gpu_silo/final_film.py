"""Assemble gpu_silo from the native construction frames, reviewed IFC study and closing orbit."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess

from . import narrate, review_editorial, technical_voice
from .final_voice import FPS, body_cues, read_json
from .review_overlays import SIZE
from .mp4 import optional_captions, probe


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", *map(str, args)], check=True)


def picture_info(path, expected):
    stream = probe(path, "-select_streams", "v:0", "-show_streams")["streams"][0]
    if (stream["width"], stream["height"]) != SIZE or stream["codec_name"] != "h264":
        raise ValueError(f"{path} must be a 4K AVC stream")
    if (Fraction(stream["avg_frame_rate"]) != FPS or int(stream["nb_frames"]) != expected
            or Fraction(stream["duration_ts"]) * Fraction(stream["time_base"]) != Fraction(expected, FPS)):
        raise ValueError(f"Unexpected frame count or duration for {path}")
    return stream


def assembly():
    original = read_json(technical_voice.SCRIPT)
    review = read_json(narrate.ROOT / "design" / "technical_review.json")
    cues = body_cues(original["cues"], review)
    references = {ref["start"]: ref for ref in original["equipmentReferences"]}
    for cue in cues:
        # The approved turbine card already includes the GE model and its ISO rating.
        if cue["start"] in references and cue["title"] != "Propane turbine generators":
            cue["equipmentReference"] = references[cue["start"]]
    office = round(review["remove_narration_start"] * FPS)
    shaft = review["shaft_entry_frame"]
    end = round(review["move_narration_start"] * FPS)
    return cues, {"construction": (0, office), "office": (office, shaft), "studies": (shaft, end)}


def body_part(name, frames, work):
    from PIL import Image

    cues, ranges = assembly()
    first, last = ranges[name]
    selected = [c for c in cues if round(c["start"] * FPS) < last and round(c["end"] * FPS) > first]
    for number in range(first, last):
        with Image.open(frames / f"f_{number:04}.jpg") as image:
            if image.size != SIZE:
                raise ValueError(f"Expected native 4K photography at frame {number}")
    cards = work / name
    cards.mkdir(parents=True, exist_ok=True)
    overlays = cards / "cards.ffconcat"
    review_editorial.cue_images(overlays, selected, lambda t: round(t * FPS) - first,
                                last - first, FPS, size=SIZE)
    output = work / f"{name}.mp4"
    filters = ("[0:v]scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p[plate];"
               "[1:v]fps=24,scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuva420p[type];"
               "[plate][type]overlay=shortest=1,setsar=1[v]")
    ffmpeg("-threads", 3, "-framerate", FPS, "-start_number", first, "-i", frames / "f_%04d.jpg",
           "-threads", 2, "-f", "concat", "-safe", 0, "-i", overlays, "-filter_complex_threads", 4,
           "-filter_complex", filters, "-map", "[v]", "-an", "-sn", "-frames:v", last-first,
           "-c:v", "libx264", "-threads:v", 6, "-preset", "veryfast", "-crf", 16, "-pix_fmt", "yuv420p",
           "-color_range", "tv", "-color_primaries", "bt709", "-colorspace", "bt709", "-color_trc", "bt709",
           "-video_track_timescale", 12288, "-movflags", "+faststart", output)
    picture_info(output, last-first)
    print(f"Finished {name}: {last-first} native frames.", flush=True)


def chapters(path, timing, thermal_shots):
    marks = [(0, "The GPU silo")]
    cues, _ = assembly()
    marks.extend((timing["intro"] + round(c["start"] * FPS), c["title"]) for c in cues)
    thermal_at = timing["intro"] + timing["body"]
    marks.extend((thermal_at + s["first"], s["title"]) for s in thermal_shots)
    marks.append((thermal_at + timing["thermal"], "Closing orbit"))
    rows = [";FFMETADATA1"]
    for (start, title), end in zip(marks, [x for x, _ in marks[1:]] + [timing["total"]], strict=True):
        rows.extend(("[CHAPTER]", "TIMEBASE=1/24", f"START={start}", f"END={end}", f"title={title}"))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def master_audio(work, frames):
    source = work / "dialogue.flac"
    target = "I=-16:TP=-1.5:LRA=8"
    measurement = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(source), "-af",
                                  f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                                 capture_output=True, text=True, check=True).stderr
    m = json.loads(measurement[measurement.rindex("{"):measurement.rindex("}")+1])
    normalize = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                 f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = work / "master-dialogue.flac"
    ffmpeg("-i", source, "-af", f"{normalize},aresample=48000,apad,atrim=end_sample={frames*2000}",
           "-c:a", "flac", "-sample_fmt", "s32", out)
    return out


def mux(picture, sound, captions, out, frames, title, chapter_file=None):
    args = ["-i", picture, "-i", sound, "-i", captions]
    if chapter_file:
        args.extend(("-f", "ffmetadata", "-i", chapter_file))
    ffmpeg(*args, "-map", "0:v:0", "-map", "1:a:0", "-map", "2:s:0", "-map_metadata", 3 if chapter_file else -1,
           "-map_chapters", 3 if chapter_file else -1, "-c:v", "copy", "-af", f"atrim=end_sample={frames*2000}",
           "-c:a", "aac", "-ar", 48000, "-b:a", "160k", "-c:s", "mov_text", "-disposition:s:0", "0",
           "-metadata:s:a:0", "language=eng", "-metadata:s:a:0", "title=Technical narration",
           "-metadata:s:s:0", "language=eng", "-metadata:s:s:0", "title=English captions",
           "-metadata", f"title={title}", "-movie_timescale", 6000000, "-movflags", "+faststart", out)
    optional_captions(out)
    picture_info(out, frames)


def assemble(orbit, thermal, reviewed, work, out):
    timing = read_json(work / "timeline.json")
    picture_info(orbit, timing["closing"])
    picture_info(thermal, timing["thermal"])
    out.mkdir(parents=True, exist_ok=True)
    cut = timing["intro"]
    if "intro_orbit_frames" in timing:
        opening = orbit.with_name("wide_intro_picture.mp4")
    else:
        # Earlier edit manifests used the first closed GOPs of the closing orbit.
        opening = work / "intro-picture.mp4"
        stream = probe(orbit, "-select_streams", "v:0", "-show_streams", "-show_packets")
        packets = stream["packets"]
        base = Fraction(stream["streams"][0]["time_base"]) * FPS
        if ("K" not in packets[cut]["flags"] or
                sorted(int(p["pts"]) * base for p in packets[:cut]) != list(range(cut))):
            raise ValueError(f"Encode the closing overlay with --intro-frames {cut} before assembling")
        ffmpeg("-i", orbit, "-map", "0:v:0", "-frames:v", cut, "-c:v", "copy", "-map_chapters", -1, opening)
    picture_info(opening, cut)
    thermal_picture = work / "thermal-picture.mp4"
    ffmpeg("-i", thermal, "-map", "0:v:0", "-map_metadata", -1, "-map_chapters", -1, "-c:v", "copy", thermal_picture)
    _, ranges = assembly()
    parts = [(opening, cut), *((work / f"{name}.mp4", end-start) for name, (start, end) in ranges.items()),
             (thermal_picture, timing["thermal"]), (orbit, timing["closing"])]
    manifest = ["ffconcat version 1.0"]
    for path, length in parts:
        picture_info(path, length)
        name = path.resolve().as_posix().replace("'", "'\\''")
        manifest.extend((f"file '{name}'", f"duration {length/FPS:.9f}"))
    concat = work / "pictures.ffconcat"
    concat.write_text("\n".join(manifest) + "\n", encoding="utf-8")
    joined = work / "whole-picture.mp4"
    ffmpeg("-f", "concat", "-safe", 0, "-i", concat, "-map", "0:v:0", "-c:v", "copy",
           "-map_metadata", -1, "-map_chapters", -1, "-video_track_timescale", 12288, joined)
    picture_info(joined, timing["total"])
    chapter_file = work / "chapters.ffmetadata"
    chapters(chapter_file, timing, read_json(reviewed / "thermal.json"))
    mixed = master_audio(work, timing["total"])
    mux(opening, mixed, work / "intro.srt", out / "gpu_silo_intro.mp4", cut, "The GPU silo | Introduction")
    mux(joined, mixed, work / "gpu_silo.srt", out / "gpu_silo.mp4", timing["total"], "The GPU silo", chapter_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    body = sub.add_parser("body")
    body.add_argument("name", choices=("construction", "office", "studies"))
    body.add_argument("frames", type=Path)
    body.add_argument("work", type=Path)
    final = sub.add_parser("assemble")
    for argument in ("orbit", "thermal", "reviewed", "work", "out"):
        final.add_argument(argument, type=Path)
    args = parser.parse_args()
    if args.action == "body":
        body_part(args.name, args.frames, args.work)
    else:
        assemble(args.orbit, args.thermal, args.reviewed, args.work, args.out)
