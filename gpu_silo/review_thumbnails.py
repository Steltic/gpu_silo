"""Make YouTube thumbnail proofs and the selected cover from the graded closing orbit."""
import argparse
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_STORED

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .review_overlays import SIZE

# The design grid is 1280 x 720. Each glyph is rendered at native 4K.
SCALE = 3
FRAMES = (420, 438, 456, 474, 492)
SLUGS = ("no-water-mains", "why-so-much-water", "off-the-power-grid", "electricity-bills", "gpus-on-a-farm")
LABELS = ("No water mains. No grid power.", "Why so much water?", "50 MW off the power grid?",
          "Electricity bills. What if AI went off-grid?", "18,432 GPUs on a farm?")
FACES = {
    "poster": ("impact.ttf", "Anton-Regular.ttf", "DejaVuSansCondensed-Bold.ttf"),
    "condensed": ("FRAMDCN.TTF", "BarlowCondensed-Bold.ttf", "DejaVuSansCondensed-Bold.ttf"),
    "sans": ("seguisb.ttf", "Inter-SemiBold.ttf", "DejaVuSans.ttf"),
    "bold": ("segoeuib.ttf", "Inter-Bold.ttf", "DejaVuSans-Bold.ttf"),
    "serif": ("georgiab.ttf", "LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"),
    "italic": ("georgiaz.ttf", "LiberationSerif-BoldItalic.ttf", "DejaVuSerif-BoldItalic.ttf"),
}


@lru_cache(maxsize=96)
def face(family, px):
    for name in FACES[family]:
        try:
            return ImageFont.truetype(name, round(px * SCALE))
        except OSError:
            continue
    raise OSError(f"Missing display typeface for {family}")


def text(draw, xy, copy, family, px, ink, anchor="lt", max_width=None):
    if max_width:
        measured = face(family, px).getlength(copy) / SCALE
        if measured > max_width:
            px = px * max_width / measured
    f = face(family, px)
    pos = tuple(round(u * SCALE) for u in xy)
    draw.text(pos, copy, font=f, fill=ink, anchor=anchor)
    return f.getlength(copy) / SCALE


def side_crop(still, fraction, right, shade):
    w, h = SIZE
    left = w * (1-fraction) * right
    top = h * (1-fraction) * .53
    crop = still.resize(SIZE, Image.Resampling.LANCZOS, box=(left, top, left+w*fraction, top+h*fraction))
    x = np.linspace(0, 1, 960)[None, :]
    y = np.linspace(0, 1, 540)[:, None]
    # Protect the face of the building. The vignette sits behind the side headline.
    x = 1-x if right else x
    stop = .585 + .045 * (y-.5)
    u = np.clip((stop-x)/.30, 0, 1)
    a = (u*u*(3-2*u)) * (.84+.075*np.sin(np.pi*y))
    mask = Image.fromarray(np.uint8(255*a)).resize(SIZE, Image.Resampling.BILINEAR)
    return Image.composite(Image.new("RGB", SIZE, shade), crop, mask)


def cover(still, number):
    if number == 1:
        image = side_crop(still, .775, False, (9, 23, 29))
    elif number == 4:
        image = side_crop(still, .77, True, (37, 22, 30))
    else:
        # The three floating-sky designs change only the pixels occupied by the glyphs.
        image = still.copy()
    d = ImageDraw.Draw(image)
    if number == 1:
        text(d,(53,238),"GPU DATA CENTRE","bold",34,(248,232,191))
        text(d,(50,303),"NO WATER MAINS","poster",82,(251,250,243),max_width=500)
        text(d,(50,397),"NO GRID POWER","poster",91,(255,198,91),max_width=510)
    elif number == 2:
        text(d,(60,25),"AI DATA CENTRES","bold",29,(27,46,57))
        x = 58 + text(d,(58,66),"WHY SO MUCH","poster",84,(14,32,47))
        text(d,(x+18,66),"WATER?","poster",84,(0,73,79))
    elif number == 3:
        text(d,(557,120),"50 MW","poster",117,(25,36,46),anchor="rs")
        text(d,(594,27),"OFF THE","bold",36,(40,48,51))
        text(d,(592,69),"POWER GRID?","condensed",85,(107,47,27),max_width=590)
    elif number == 4:
        text(d,(729,236),"ELECTRICITY BILLS","bold",38,(255,192,154),max_width=485)
        text(d,(724,301),"What if AI","serif",79,(252,246,229),max_width=497)
        text(d,(724,392),"went off-grid?","serif",78,(252,246,229),max_width=502)
    elif number == 5:
        end = 58 + text(d,(58,117),"18,432","serif",105,(23,51,41),anchor="ls")
        text(d,(end+14,115),"GPUs","sans",57,(23,51,41),anchor="ls")
        text(d,(1226,115),"on a farm?","italic",78,(30,46,42),anchor="rs",max_width=510)
    else:
        raise ValueError(number)
    return image


def selected_cover(still):
    if still.size != SIZE:
        raise ValueError("Use the uncropped 4K closing frame")
    image = still.convert("RGB")
    draw = ImageDraw.Draw(image)
    ink = (18, 43, 52)
    text(draw, (49, 103), "NO WATER MAINS", "poster", 55, ink, anchor="ls")
    text(draw, (640, 103), "GPU data centre", "poster", 60, (90, 43, 27), anchor="ms")
    text(draw, (1231, 103), "NO GRID POWER", "poster", 55, ink, anchor="rs")
    return image


def extract(master, folder, frames=FRAMES, pattern="orbit-%02d.png"):
    folder.mkdir(parents=True, exist_ok=True)
    select = "+".join(f"eq(n,{frame})" for frame in frames)
    filters = f"select='{select}',scale=in_range=limited:in_color_matrix=bt709:out_range=full,format=rgb24"
    subprocess.run(["ffmpeg","-hide_banner","-v","error","-y","-threads","4","-i",str(master),
                    "-vf",filters,"-frames:v",str(len(frames)),"-fps_mode","passthrough",
                    "-compression_level","2","-threads","2",str(folder / pattern)],check=True)


def save_jpg(image, path):
    for quality in (95, 93, 91, 89, 87):
        data = BytesIO()
        image.save(data, "JPEG", quality=quality, subsampling=0, optimize=True)
        if data.tell() < 2_000_000:
            path.write_bytes(data.getvalue())
            return
    raise ValueError(f"Thumbnail exceeds the delivery target: {path}")


def present(master, work, out):
    out.mkdir(parents=True,exist_ok=True)
    clean = out / "clean"
    clean.mkdir(exist_ok=True)
    extract(master,work)
    files = []
    width, height, margin, gutter = 704,396,24,24
    sheet = Image.new("RGB",(2*width+2*margin+gutter,3*(height+63)+margin),(16,26,31))
    pen = ImageDraw.Draw(sheet)
    for index, (frame, slug, label) in enumerate(zip(FRAMES, SLUGS, LABELS, strict=True),1):
        with Image.open(work/f"orbit-{index:02}.png") as raw:
            if raw.size!=SIZE:
                raise ValueError("Use the 4K closing master")
            original = raw.convert("RGB")
        seconds = frame / 24
        source = clean/f"{index:02}-orbit-{seconds:05.2f}s.jpg"
        target = out/f"{index:02}-{slug}.jpg"
        save_jpg(original, source)
        image = cover(original,index)
        save_jpg(image,target)
        files.extend((target,source))
        x = (sheet.width-width)//2 if index==5 else margin+(index-1)%2*(width+gutter)
        y = margin+(index-1)//2*(height+63)
        sheet.paste(image.resize((width,height), Image.Resampling.LANCZOS),(x,y))
        caption = f"{index:02}   {label}"
        pen.text((x,y+height+10),caption,font=face("sans",6.8),fill=(241,240,227),anchor="lt")
        pen.text((x+width,y+height+11),f"00:{seconds:05.2f}",font=face("sans",6.4),fill=(181,198,193),anchor="rt")
    sheet.save(out/"thumbnail_choices.jpg",quality=93,subsampling=0,optimize=True)
    with ZipFile(out/"five_youtube_thumbnails.zip","w",ZIP_STORED) as archive:
        for file in files:
            archive.write(file, file.relative_to(out).as_posix())


def make_selected(master, work, out):
    # Proof 04 was selected for its camera angle. Decode the master before adding type.
    extract(master, work, (FRAMES[3],), pattern="selected-%02d.png")
    out.mkdir(parents=True, exist_ok=True)
    with Image.open(work / "selected-01.png") as still:
        save_jpg(selected_cover(still), out / "final_thumbnail.jpg")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("master","work","out"):
        p.add_argument(name,type=Path)
    p.add_argument("--final-only", action="store_true", help="Build the selected frame 04 cover")
    args=p.parse_args()
    if args.final_only:
        make_selected(args.master, args.work, args.out)
    else:
        present(args.master, args.work, args.out)
