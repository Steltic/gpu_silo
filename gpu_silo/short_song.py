"""Mux the song edition from the published technical picture and the stereo song master."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import struct
import subprocess
import tempfile

from . import song_score as score


def probe(path, *options):
    data = subprocess.check_output(["ffprobe", "-v", "error", *options, "-of", "json", str(path)])
    return json.loads(data)


def chapter_frame(chapter, prop):
    when = int(chapter[prop]) * Fraction(chapter["time_base"]) * score.FPS
    return round(when)


def kept_chapters(source):
    data = probe(source, "-show_streams", "-show_chapters")
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    chapters = data["chapters"]
    if (video["width"], video["height"], Fraction(video["avg_frame_rate"])) != (3840, 2160, score.FPS):
        raise ValueError("Expected the 4K, 24 fps technical short")
    if (len(chapters) < 2 or "Plan and section" not in chapters[-1]["tags"]["title"] or
            chapter_frame(chapters[-1], "start") != score.PICTURE_FRAMES or
            "360" not in chapters[-2]["tags"]["title"]):
        raise ValueError("Cannot locate the technical short's orbit-to-drawings cut")
    return chapters[:-1]


def packet_hashes(path):
    p = probe(path, "-select_streams", "v:0", "-show_packets", "-show_data_hash", "sha256",
              "-show_entries", "packet=pts,dts,duration,data_hash:stream=time_base", "-show_streams")
    base = Fraction(p["streams"][0]["time_base"])
    return [(int(v["pts"])*base, int(v["dts"])*base, int(v["duration"])*base, v["data_hash"])
            for v in p["packets"]]


def optional_lyrics(path):
    """Disable the tx3g track by default. The MOV muxer enables the first subtitle of its type."""
    streams = probe(path, "-select_streams", "s", "-show_streams")["streams"]
    if len(streams) != 1 or streams[0]["codec_name"] != "mov_text":
        raise ValueError("Expected exactly one timed lyric track")
    if not streams[0]["disposition"]["default"]:
        return
    track_id = int(streams[0]["id"], 0)
    with path.open("r+b") as file:
        def boxes(start, end):
            while start+8 <= end:
                file.seek(start)
                size, name = struct.unpack(">I4s", file.read(8))
                header = 8
                if size == 1:
                    size, = struct.unpack(">Q", file.read(8))
                    header = 16
                if size == 0:
                    size = end-start
                if size < header or start+size > end:
                    raise ValueError("Invalid MP4 box")
                yield name, start+header, start+size
                start += size
        moov = next((a,b) for name,a,b in boxes(0,path.stat().st_size) if name == b"moov")
        for name, start, end in boxes(*moov):
            if name != b"trak":
                continue
            header = next(a for name,a,_ in boxes(start,end) if name == b"tkhd")
            file.seek(header)
            version = file.read(1)[0]
            flags = int.from_bytes(file.read(3), "big")
            file.seek(header + (20 if version else 12))
            if int.from_bytes(file.read(4), "big") == track_id:
                file.seek(header+1)
                file.write((flags & ~1).to_bytes(3,"big"))
                return
    raise ValueError("Couldn't identify the MP4 lyric track")


def verify(source, output):
    original = kept_chapters(source)
    source_frames = [p for p in packet_hashes(source) if p[0] < score.DURATION]
    actual = packet_hashes(output)
    if len(actual) != score.PICTURE_FRAMES or actual != source_frames:
        raise ValueError("Song picture packets or timestamps differ from the technical master")
    data = probe(output, "-show_streams", "-show_chapters")
    visible = [s for s in data["streams"] if s["codec_type"] != "data"]
    if [s["codec_type"] for s in visible] != ["video", "audio", "subtitle"]:
        raise ValueError("Expected one picture, one music track and one optional lyric caption track")
    _, audio, subtitles = visible
    if (audio["channels"] != 2 or audio["sample_rate"] != "48000" or
            abs(Fraction(audio["time_base"])*int(audio["duration_ts"]) - score.DURATION) > Fraction(1, 48000)):
        raise ValueError("The stereo song does not run to the exact picture end")
    if subtitles["tags"].get("language") != "eng" or subtitles["disposition"]["default"]:
        raise ValueError("English lyric captions must be selectable")
    def marks(chapters):
        return [(chapter_frame(c, "start"), chapter_frame(c, "end"), c["tags"]["title"]) for c in chapters]
    if marks(original) != marks(data["chapters"]):
        raise ValueError("The song's retained chapter marks differ from the source")
    print(f"Verified all {len(actual)} original picture packets, {len(original)} chapters and stereo song.")


def write_chapters(path, chapters):
    lines = [";FFMETADATA1", "title=GPU Silo | I Want a GPU Tower"]
    for c in chapters:
        label = c["tags"]["title"]
        for char in ("\\", "=", ";", "#", "\n"):
            label = label.replace(char, "\\" + char)
        lines.extend(("[CHAPTER]", "TIMEBASE=1/24000", f"START={1000*chapter_frame(c, 'start')}",
                      f"END={1000*chapter_frame(c, 'end')}", f"title={label}"))
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")


def build(source, output, audio=None):
    source, output = map(Path, (source, output))
    music = Path(audio) if audio else score.ROOT/"audio"/"short_song"/"short_song.flac"
    music = music.resolve()
    if source.resolve() == output.resolve():
        raise ValueError("Use a separate file for the song edition")
    chapters = kept_chapters(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        work = Path(tmp)
        picture = work/"picture.mp4"
        subs, meta = work/"lyrics.srt", work/"chapters.txt"
        subs.write_text(score.captions(score.read()), encoding="utf-8")
        write_chapters(meta, chapters)
        # Finish stream-copying the picture separately so the AAC encoder can flush its last samples.
        cli = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        subprocess.run([*cli, "-i", str(source), "-map", "0:v:0", "-frames:v", str(score.PICTURE_FRAMES),
                        "-c:v", "copy", "-map_chapters", "-1", "-map_metadata", "-1", str(picture)], check=True)
        track = probe(music, "-select_streams", "a:0", "-show_streams")["streams"][0]
        if Fraction(track["time_base"])*int(track["duration_ts"]) != score.DURATION or track["channels"] != 2:
            raise ValueError("Supply the complete stereo song master")
        master = work/"short_song.mp4"
        subprocess.run([*cli, "-i", str(picture), "-i", str(music), "-i", str(subs),
                        "-f", "ffmetadata", "-i", str(meta), "-map", "0:v:0", "-map", "1:a:0",
                        "-map", "2:s:0", "-map_metadata", "3", "-map_chapters", "3",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-c:s", "mov_text",
                        "-metadata", "comment=Original English song. English tenor: Kokoro (am_michael). Vocal: Chiaki. Instruments: GeneralUser GS by S. Christian Collins.",
                        "-metadata:s:a:0", "language=eng", "-metadata:s:a:0", "handler_name=I Want a GPU Tower",
                        "-metadata:s:s:0", "language=eng", "-metadata:s:s:0", "handler_name=English lyrics",
                        "-disposition:s:0", "0", "-movie_timescale", "6000000",
                        "-movflags", "+faststart", str(master)], check=True)
        optional_lyrics(master)
        verify(source, master)
        master.replace(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("picture", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--audio", type=Path)
    args = parser.parse_args()
    print(build(args.picture, args.output, args.audio))
