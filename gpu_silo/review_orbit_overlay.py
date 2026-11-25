"""Composite the owner's closing specification card over the silent, graded Cycles master."""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw

from .review_overlays import SCALE, SIZE, font


def ramp(values, low, high):
    pos = np.clip((values - low) / (high - low), 0, 1)
    return pos * pos * (3 - 2 * pos)


def scrim():
    """Leave a clear window at the centre of the frame for the silo."""
    x = np.linspace(0, 1, 960)[None, :]
    y = np.linspace(0, 1, 540)[:, None]
    sides = np.maximum(1 - ramp(x, .345, .444), ramp(x, .525, .623))
    opacity = ramp(y, .605, .795) * (.055 + .872 * sides)
    mask = Image.fromarray(np.uint8(255 * opacity)).resize(SIZE, Image.Resampling.BILINEAR)
    image = Image.new("RGBA", SIZE, (13, 26, 31))
    image.putalpha(mask)
    return image


def points(*coords):
    return tuple(round(v * SCALE) for v in coords)


def heading(layer, headline):
    title, divider, link = headline.partition(" - ")
    if not divider or not link:
        raise ValueError("The closing headline must include the title and repository address")
    title_font = font("serif", 84)
    link_font = font("mono", 46)
    left = 78
    inside = left + 15
    join = inside + title_font.getlength(title) / SCALE
    right = join + link_font.getlength(divider + link) / SCALE + 15
    if right > 805:
        raise ValueError("The highlighted headline would cross the silo")
    top, bottom = 741, 797
    band = Image.new("RGBA", points(right - left, bottom - top))
    band_draw = ImageDraw.Draw(band)
    for x in range(band.width):
        u = x / (band.width - 1)
        fill = tuple(round(a + u * (b-a)) for a, b in zip((246, 211, 152), (229, 179, 111)))
        band_draw.line(((x, 0), (x, band.height)), fill=(*fill, 255))
    layer.alpha_composite(band, dest=points(left, top))
    draw = ImageDraw.Draw(layer)
    draw.text(points(inside, 781), title, font=title_font, anchor="ls", fill=(23, 36, 39))
    draw.text(points(join, 780), divider + link, font=link_font, anchor="ls", fill=(23, 36, 39))


def typeset(draw, x, baseline, line):
    for i, text in enumerate(line.split("**")):
        face = font("bold" if i % 2 else "sans", 52)
        ink = (251, 247, 234) if i % 2 else (224, 231, 226)
        draw.text(points(x, baseline), text, font=face, anchor="ls", fill=ink)
        x += face.getlength(text) / SCALE
    return x


def artwork(config):
    layer = scrim()
    heading(layer, config["headline"])
    draw = ImageDraw.Draw(layer)
    for column, start, bound in zip(config["columns"], (80, 1173), (820, 1850), strict=True):
        y = 846
        for row in column:
            for line in row:
                if typeset(draw, start, y, line) > bound:
                    raise ValueError(f"Closing copy exceeds the safe area: {line}")
                y += 32
            y += 11
        if y - 43 > 1013:
            raise ValueError("Closing copy exceeds the bottom safe area")
    return layer


def encode(master, image, out, fade_start, fade_length):
    streams = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(master)
    ]))["streams"]
    if len(streams) != 1 or (streams[0]["width"], streams[0]["height"]) != SIZE:
        raise ValueError("Use the silent 3840 × 2160 closing master")
    video = streams[0]
    if video["avg_frame_rate"] != "24/1" or int(video["nb_frames"]) != 540:
        raise ValueError("Use the 540-frame, full-rate orbit")
    filters = (f"[1:v]format=rgba,fade=t=in:s={fade_start}:n={fade_length}:alpha=1,"
               "scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuva420p[ink];"
               "[0:v][ink]overlay=shortest=1:format=yuv420,setsar=1[v]")
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-threads", "4", "-i", str(master),
        "-framerate", "24", "-loop", "1", "-i", str(image), "-filter_complex_threads", "4",
        "-filter_complex", filters, "-map", "[v]", "-map_metadata", "-1", "-map_chapters", "-1",
        "-an", "-frames:v", video["nb_frames"], "-c:v", "libx264", "-threads", "6",
        "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-color_range", "tv",
        "-color_primaries", "bt709", "-colorspace", "bt709", "-color_trc", "bt709",
        "-metadata", "title=The GPU Silo | Closing orbit with specifications", "-movflags", "+faststart", str(out)
    ], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("master", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--art-only", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config_path = Path(__file__).resolve().parents[1] / "design" / "technical_review.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))["closing_overlay"]
    card = args.out / "final_360_overlay.png"
    artwork(config).save(card, optimize=True)
    if not args.art_only:
        encode(args.master, card, args.out / "final_360_overlay.mp4",
               config["fade_start_frame"], config["fade_frames"])


if __name__ == "__main__":
    main()
