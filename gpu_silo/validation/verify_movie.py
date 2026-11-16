"""Verify the frame clock, chapters and decoding of the finished movie."""
import json
from pathlib import Path
import subprocess
import sys

from .. import design, pod_scene


def check(path):
    result = subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_chapters",
                                      "-of", "json", str(path)])
    info = json.loads(result)
    video, = [stream for stream in info["streams"] if stream["codec_type"] == "video"]
    frames = pod_scene.FRAMES
    assert video["codec_name"] == "h264" and video["pix_fmt"] == "yuv420p"
    assert (video["width"], video["height"]) == (design.MOVIE["width_px"], design.MOVIE["height_px"])
    assert int(video["nb_frames"]) == frames and video["r_frame_rate"] == f"{pod_scene.FPS}/1"
    assert abs(float(video["duration"]) - frames / pod_scene.FPS) < .001
    chapters = info["chapters"]
    assert chapters and float(chapters[0]["start_time"]) == 0
    assert abs(float(chapters[-1]["end_time"]) - frames / pod_scene.FPS) < .002
    assert all(a["end"] == b["start"] for a, b in zip(chapters, chapters[1:]))
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0",
                    "-f", "null", "-"], check=True)
    print(f"{frames} frames at {pod_scene.FPS} fps, {len(chapters)} chapters, full MP4 decode passed")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
