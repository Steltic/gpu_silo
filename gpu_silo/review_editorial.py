"""Apply the selected compact editorial lower third to clean frames and timed cues."""
import argparse
from functools import lru_cache
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw

from .review_overlays import BRASS, LIGHT, MUTED, SCALE, SCENES, SIZE, Canvas, font


@lru_cache(maxsize=1)
def editorial_scrim():
    x = np.linspace(0, 1, 480)[None, :]
    y = np.linspace(0, 1, 270)[:, None]
    vertical = np.clip((y - .71) / .19, 0, 1) ** .83
    horizontal = np.clip((1.02 - x) / .49, .19, 1)
    alpha = Image.fromarray(np.uint8(255 * .95 * vertical * horizontal))
    scrim = Image.new("RGBA", SIZE, (13, 23, 29))
    scrim.putalpha(alpha.resize(SIZE, Image.Resampling.BILINEAR))
    return scrim


def graphic(section, title, metrics, reference=None):
    """Typeset once on the native 4K grid. Keep the approved type sizes."""
    card = Canvas(editorial_scrim())
    card.line(((87, 853), (154, 853)), BRASS, 4)
    card.text(171, 844, section.upper(), 21, "mono", BRASS)
    if reference:
        x = 171 + font("mono", 21 * SCALE).getlength(section.upper()) / SCALE + 32
        line = "   ·   ".join((reference["label"], reference["detail"]))
        if x + font("sans", 21 * SCALE).getlength(line) / SCALE > 1833:
            raise ValueError(f"Equipment reference exceeds the safe area for {title!r}")
        card.text(x, 844, line, 21, "sans", LIGHT)
    card.text(84, 871, title, 70, "serif")
    left = 89.0
    for index, metric in enumerate(metrics):
        secondary = index == 2
        size = 24 if secondary else 29
        ink = MUTED if secondary else LIGHT
        card.text(left, 958 if secondary else 954, metric, size, "sans", ink)
        left += font("sans", size * SCALE).getlength(metric) / SCALE
        if index + 1 < len(metrics):
            card.text(left + 18, 956, "/", 25, "sans", MUTED)
            left += 48
    if left > 1833:
        raise ValueError(f"Metrics exceed the safe area for {title!r}")
    return Image.alpha_composite(card.image, card.layer)


def sample_metrics(row):
    return tuple(f"{value} {name}" for value, name in row["metric"])


def for_cue(cue):
    title = cue["title"]
    section = {
        "GPU SILO": "Design",
        "Concrete shell": "Structure",
        "Liquid containment": "Cooling",
        "Tandem cage lift": "Construction",
        "Top guide": "Structure",
        "Pod receiving": "Logistics",
        "Radial store": "Compute",
        "Heat rejection": "Cooling",
        "Fuel supply": "Power",
        "Annular store": "Cooling",
        "Generator support": "Structure",
        "Emergency generation": "Power",
        "Propane turbine generators": "Power",
        "Normal operating envelope": "Power",
        "Steel shaft": "Structure",
        "Four-rack pod": "Compute",
        "Dry cooler": "Cooling",
        "Turbine deck": "Power",
    }[title]
    samples = {"Pod receiving": SCENES[0], "Propane turbine generators": SCENES[1], "Steel shaft": SCENES[2]}
    parts = sample_metrics(samples[title]) if title in samples else re.split(r"\s+/\s*", cue["spec"])
    return graphic(section, title, parts, cue.get("equipmentReference"))


def screenshots(source, dest):
    dest.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1696, 390), (18, 27, 30))
    labels = ImageDraw.Draw(sheet)
    for i, row in enumerate(SCENES):
        with Image.open(source / (row["id"] + ".jpg")) as still:
            if still.size != SIZE:
                raise ValueError(f"Expected original 4K frame for {row['id']}")
            card = graphic(row["section"], row["title"], sample_metrics(row))
            result = Image.alpha_composite(still.convert("RGBA"), card).convert("RGB")
        result.save(dest / f"{i + 1:02}-{row['id']}.jpg", quality=95, subsampling=0, optimize=True)
        left = 22 + 558 * i
        sheet.paste(result.resize((536, 302), Image.Resampling.LANCZOS), (left, 22))
        labels.text((left, 338), row["title"] + "   /   " + row["time"], font=font("sans", 22), fill=LIGHT)
    sheet.save(dest / "selection.jpg", quality=93, optimize=True)


def cue_images(path, cues, frame_of, total, fps, size=(1920, 1080)):
    """Produce a frame-exact still track for FFmpeg. Blank intervals show clean picture."""
    events = {0: "blank.png", total: "blank.png"}
    Image.new("RGBA", size).save(path.parent / "blank.png")
    for index, cue in enumerate(cues):
        first = min(total, max(0, frame_of(cue["start"])))
        last = min(total, max(0, frame_of(cue["end"])))
        if last <= first:
            raise ValueError(f"Empty editorial interval for {cue['title']}")
        name = f"editorial-{index:02}.png"
        card = for_cue(cue)
        if card.size != size:
            card = card.resize(size, Image.Resampling.LANCZOS)
        card.save(path.parent / name)
        events[first] = name
        events[last] = "blank.png"
    lines = ["ffconcat version 1.0"]
    starts = sorted(events)
    for first, last in zip(starts, starts[1:]):
        lines.extend([f"file '{events[first]}'", f"option framerate {fps}", f"duration {(last-first)/fps:.9f}"])
    lines.extend(["file 'blank.png'", f"option framerate {fps}"])
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clean_frames", type=Path)
    parser.add_argument("output_folder", type=Path)
    args = parser.parse_args()
    screenshots(args.clean_frames, args.output_folder)
