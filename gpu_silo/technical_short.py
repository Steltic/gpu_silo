"""Assemble the 4K, double-speed technical edition of the short film."""
import json
import os
from pathlib import Path
import shutil
import subprocess


def build(blender,work,output,models=None,cpu=False):
    from . import technical_finish as finish, technical_model, technical_scene, technical_voice
    root=Path(__file__).resolve().parents[1]
    work=work.resolve();output=output.resolve()
    cache=work/"bake";frames=work/"frames";post=work/"post"
    output.mkdir(parents=True,exist_ok=True)
    if not (cache/"scene.json").is_file():technical_scene.prepare(cache)
    m=json.loads((cache/"scene.json").read_text(encoding="utf-8"))
    if models:
        technical_voice.record(models,output)
    else:
        for name in ("technical_voice.flac","technical_voice.json","technical_short.srt"):
            shutil.copyfile(root/"audio"/name,output/name)
    finish.prepare(cache,post,frames)
    env=os.environ.copy()
    profile=work/"blender-profile";profile.mkdir(exist_ok=True)
    env["BLENDER_USER_RESOURCES"]=str(profile)
    kernels=work/"cycles-device-cache";kernels.mkdir(exist_ok=True)
    env.update(SYCL_CACHE_PERSISTENT="1",SYCL_CACHE_DIR=str(kernels))
    head=[str(blender),"-b","--python-exit-code","9","-P"]
    if not all((frames/f"f_{f:04}.jpg").is_file() for f in range(m["office"])):
        subprocess.run([*head,str(root/"renderer"/"technical_blender.py"),"--",str(cache),str(frames),
                        "0",str(m["office"]-1),"--samples","6"],check=True,env=env)
    call=[*head,str(root/"renderer"/"technical_cycles.py"),"--",str(cache),str(frames)]
    if cpu:call.append("--cpu")
    subprocess.run(call,check=True,env=env)
    technical_model.export(cache,output/"silo_short.glb")
    from .validation.verify_technical import check
    check(cache,output/"silo_short.glb")
    finish.encode(cache,post,frames,output)
    finish.excerpts(cache,post,output)
    shutil.copyfile(cache/"traffic.json",output/"traffic_schedule.json")
    shutil.copyfile(root/"design"/"technical_short.md",output/"production_notes.md")
    finish.verify(output,cache)
