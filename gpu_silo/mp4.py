"""Read film metadata and keep the English MP4 captions selectable."""
import json
import struct
import subprocess


def probe(path, *options):
    data = subprocess.check_output(["ffprobe", "-v", "error", *options, "-of", "json", str(path)])
    return json.loads(data)


def _boxes(file, start, end):
    while start + 8 <= end:
        file.seek(start)
        size, name = struct.unpack(">I4s", file.read(8))
        header_size = 8
        if size == 1:
            size, = struct.unpack(">Q", file.read(8))
            header_size = 16
        if size == 0:
            size = end - start
        if size < header_size or start + size > end:
            raise ValueError("Invalid MP4 box")
        yield name, start + header_size, start + size
        start += size


def optional_captions(path):
    """Clear the subtitle track's default-enabled flag set by the MOV muxer."""
    streams = probe(path, "-select_streams", "s", "-show_streams")["streams"]
    if len(streams) != 1 or streams[0]["codec_name"] != "mov_text":
        raise ValueError("Expected exactly one timed caption track")
    if not streams[0]["disposition"]["default"]:
        return
    track_id = int(streams[0]["id"], 0)
    with path.open("r+b") as file:
        moov = next((a, b) for name, a, b in _boxes(file, 0, path.stat().st_size) if name == b"moov")
        for name, start, end in _boxes(file, *moov):
            if name != b"trak":
                continue
            header = next(a for name, a, _ in _boxes(file, start, end) if name == b"tkhd")
            file.seek(header)
            version = file.read(1)[0]
            flags = int.from_bytes(file.read(3), "big")
            file.seek(header + (20 if version else 12))
            if int.from_bytes(file.read(4), "big") == track_id:
                file.seek(header + 1)
                file.write((flags & ~1).to_bytes(3, "big"))
                return
    raise ValueError("Could not identify the MP4 caption track")
