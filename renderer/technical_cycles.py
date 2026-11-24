"""Keep the Cycles device and its compiled kernels available across the three lighting setups."""
import argparse
import gc
import json
from pathlib import Path
import runpy
import sys

cli=argparse.ArgumentParser()
cli.add_argument("bake",type=Path);cli.add_argument("out",type=Path)
cli.add_argument("--cpu",action="store_true")
args=cli.parse_args(sys.argv[sys.argv.index("--")+1:])
info=json.loads((args.bake/"scene.json").read_text(encoding="utf-8"))
script=Path(__file__).with_name("technical_blender.py")
# Begin with the smaller IFC stage to warm the device before the facility is loaded.
for start,end,samples in ((info["studio"],info["roof"],8),(info["office"],info["studio"],6),(info["roof"],info["drawing"],8)):
    if all((args.out/f"f_{i:04}.jpg").is_file() for i in range(start,end)):continue
    sys.argv=[str(script),"--",str(args.bake),str(args.out),str(start),str(end-1),"--samples",str(samples)]
    if args.cpu:sys.argv.append("--cpu")
    runpy.run_path(str(script),run_name="__main__")
    gc.collect()
