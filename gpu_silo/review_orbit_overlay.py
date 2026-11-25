"""Composite the specification card over the full rural orbit and its wide opening excerpt."""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from .review_overlays import SIZE
from .review_thumbnails import SCALE, text


def ramp(values, low, high):
    pos = np.clip((values - low) / (high - low), 0, 1)
    return pos * pos * (3 - 2 * pos)


def scrim():
    """Leave a clear window at the centre of the frame for the silo."""
    x = np.linspace(0, 1, 960)[None, :]
    y = np.linspace(0, 1, 540)[:, None]
    sides = np.maximum(1 - ramp(x, .369, .445), ramp(x, .535, .603))
    opacity = ramp(y, .602, .792) * .907 * sides
    mask = Image.fromarray(np.uint8(255 * opacity)).resize(SIZE, Image.Resampling.BILINEAR)
    image = Image.new("RGBA", SIZE, (13, 26, 31))
    image.putalpha(mask)
    return image


def artwork(config):
    # The title and metrics use the selected thumbnail's Impact face on the same 1280-wide grid.
    layer = scrim()
    draw = ImageDraw.Draw(layer)
    left, right = 51, 767
    gold, ivory = (255, 203, 111), (249, 246, 234)
    for line, baseline in zip(config["headline"], (539, 577), strict=True):
        text(draw, (left, baseline), line, "poster", 34, gold, anchor="ls", max_width=446)
    positions = ((left, 624), (left, 661), (right, 575), (right, 614))
    for line, position in zip(config["specs"], positions, strict=True):
        text(draw, position, line, "poster", 27, ivory, anchor="ls", max_width=461)

    # Treat the repository as a credit below the specifications, with a lighter condensed cut.
    draw.line((right * SCALE, 634 * SCALE, 1228 * SCALE, 634 * SCALE),
              fill=(149, 158, 148, 200), width=SCALE)
    text(draw, (right, 661), config["credit"], "condensed", 25, (235, 224, 194),
         anchor="ls", max_width=461)
    return layer


def encode(master, image, out, fade_start, fade_length, intro_frames=None, source_span=None):
    streams = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(master)
    ]))["streams"]
    if len(streams) != 1 or (streams[0]["width"], streams[0]["height"]) != SIZE:
        raise ValueError("Use the silent 3840 × 2160 closing master")
    video = streams[0]
    if video["avg_frame_rate"] != "24/1" or int(video["nb_frames"]) != 540:
        raise ValueError("Use the 540-frame, full-rate orbit")
    count = int(video["nb_frames"])
    first, stop = source_span if source_span is not None else (0, count)
    if not 0 <= first < stop <= count:
        raise ValueError(f"Orbit source frames must be inside [0, {count})")
    seek = ["-ss", f"{first/24:.9f}"] if first else []
    title = "Wide opening" if source_span is not None else "Closing orbit with specifications"
    keyframe = []
    if intro_frames is not None:
        if not 0 < intro_frames < stop - first:
            raise ValueError("The opening must end inside the closing orbit")
        # Older full-orbit editions used a closed GOP at the end of their opening.
        keyframe = ["-force_key_frames", f"expr:eq(n,{intro_frames})", "-x264-params", "open-gop=0"]
    filters = (f"[1:v]format=rgba,fade=t=in:s={fade_start}:n={fade_length}:alpha=1,"
               "scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuva420p[ink];"
               "[0:v][ink]overlay=shortest=1:format=yuv420,setsar=1[v]")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "4", *seek, "-i", str(master),
        "-framerate", "24", "-loop", "1", "-i", str(image), "-filter_complex_threads", "4",
        "-filter_complex", filters, "-map", "[v]", "-map_metadata", "-1", "-map_chapters", "-1",
        "-an", "-frames:v", str(stop - first), "-c:v", "libx264", "-threads", "6",
        "-preset", "medium", "-crf", "16", *keyframe, "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-color_primaries", "bt709", "-colorspace", "bt709", "-color_trc", "bt709",
        "-metadata", f"title=The GPU Silo | {title}", "-movflags", "+faststart", str(out)
    ], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("master", type=Path)
    parser.add_argument("out", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--art-only", action="store_true")
    mode.add_argument("--intro-only", action="store_true", help="Create only the wide opening from the clean orbit")
    parser.add_argument("--intro-frames", type=int, help="Place a closed keyframe for an earlier prefix edit")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config_path = Path(__file__).resolve().parents[1] / "design" / "technical_review.json"
    review = json.loads(config_path.read_text(encoding="utf-8"))
    config = review["closing_overlay"]
    card = args.out / "final_360_overlay.png"
    artwork(config).save(card, optimize=True)
    if args.art_only:
        return
    if not args.intro_only:
        encode(args.master, card, args.out / "final_360_overlay.mp4",
               config["fade_start_frame"], config["fade_frames"], args.intro_frames)
    encode(args.master, card, args.out / "wide_intro_picture.mp4", config["fade_start_frame"],
           config["fade_frames"], source_span=review["intro_orbit_frames"])


if __name__ == "__main__":
    main()
