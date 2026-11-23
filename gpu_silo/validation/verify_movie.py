"""Verify the frame clock, chapters and decoding of the finished movie."""
import json
from pathlib import Path
import subprocess
import sys

from .. import closing, design, film, pod_scene, render_project


def check(path):
    result = subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_chapters",
                                      "-of", "json", str(path)])
    info = json.loads(result)
    video, = [stream for stream in info["streams"] if stream["codec_type"] == "video"]
    frames = pod_scene.FRAMES
    assert video["codec_name"] == "h264" and video["pix_fmt"] == "yuv420p"
    assert (video["width"], video["height"]) == ((1920,1080) if film.SHORT else (design.MOVIE["width_px"],design.MOVIE["height_px"]))
    assert int(video["nb_frames"]) == frames and video["r_frame_rate"] == f"{pod_scene.FPS}/1"
    assert abs(float(video["duration"]) - frames / pod_scene.FPS) < .001
    chapters = info["chapters"]
    assert chapters and float(chapters[0]["start_time"]) == 0
    assert abs(float(chapters[-1]["end_time"]) - frames / pod_scene.FPS) < .002
    assert all(a["end"] == b["start"] for a, b in zip(chapters, chapters[1:]))
    sound = [stream for stream in info["streams"] if stream["codec_type"] == "audio"]
    voice = ""
    if film.SHORT:
        from .. import short_voice, short_reels
        marks=render_project.short_chapters()
        assert len(chapters)==len(marks)
        for chapter,(frame,title) in zip(chapters,marks):
            assert abs(float(chapter["start_time"])-frame/pod_scene.FPS)<.002
            assert chapter["tags"]["title"]==design.display(title)
        assert len(sound)==1 and sound[0]["codec_name"]=="aac" and abs(float(sound[0]["duration"])-frames/pod_scene.FPS)<.1
        assert any(s["codec_name"]=="mov_text" for s in info["streams"])
        assert all(any(title in c["tags"]["title"] for c in chapters) for title in short_reels.TITLES)
        import numpy as np
        raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-map","0:a:0","-ac","1","-ar","8000","-f","f32le","-"])
        wave=np.frombuffer(raw,dtype="<f4")
        for cue in json.loads(short_voice.TIMINGS.read_text(encoding="utf-8"))["lines"]:
            window=wave[round(cue["start"]*8000):round(cue["end"]*8000)]
            assert np.sqrt(np.mean(window*window))>.012, cue
        voice=", timed narration and selectable captions"
    elif render_project.NARRATION.is_file():
        assert len(sound) == 1 and sound[0]["codec_name"] == "aac", "the narration track is missing"
        assert abs(float(sound[0]["duration"]) - frames / pod_scene.FPS) < .1
        # The voice must sit inside the plan-view scene and be silent before it.
        begin = (pod_scene.FILLED + closing.PLAN) / pod_scene.FPS
        end = (pod_scene.FILLED + closing.SECTION) / pod_scene.FPS
        def peak(start, length):
            out = subprocess.run(["ffmpeg", "-v", "info", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", str(path),
                                  "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
                                 capture_output=True, text=True, check=True).stderr
            return float(out.split("max_volume:")[1].split("dB")[0])
        assert peak(begin + closing.VOICE_LEAD, closing.VOICE["duration"]) > -12, "no narration in the plan view"
        assert peak(max(0, begin - 20), 19.5) < -60 and peak(end + .5, 10) < -60, "narration outside the plan view"
        voice = ", narration in the plan view"
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0",
                    "-f", "null", "-"], check=True)
    print(f"{frames} frames at {pod_scene.FPS} fps, {len(chapters)} chapters{voice}, full MP4 decode passed")


if __name__ == "__main__":
    check(Path(sys.argv[1]))      # set GPU_SILO_FILM=short to check silo_short.mp4
