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
    stop=[0,m["office"],m["studio"],m["roof"],m["drawing"]]
    samples=(6,6,8,8)
    for i,(first,end) in enumerate(zip(stop,stop[1:])):
        if all((frames/f"f_{f:04}.jpg").is_file() for f in range(first,end)):continue
        call=[str(blender),"-b","--python-exit-code","9","-P",str(root/"renderer"/"technical_blender.py"),"--",
              str(cache),str(frames),str(first),str(end-1),"--samples",str(samples[i])]
        if cpu:call.append("--cpu")
        subprocess.run(call,check=True,env=env)
    technical_model.export(cache,output/"silo_short.glb")
    from .validation.verify_technical import check
    check(cache,output/"silo_short.glb")
    finish.encode(cache,post,frames,output)
    finish.excerpts(cache,post,output)
    finish.verify(output,cache)
