"""Grade the full-rate Cycles JPEG sequence for a silent blue-hour closing shot."""
import argparse
from pathlib import Path
import subprocess
import numpy as np

def blue_hour(rgb):
    """Display-referred grade. Cool the ambient light and preserve warm architectural uplighting."""
    luma=rgb@np.array([.2126,.7152,.0722])
    curve=np.interp(luma,[0,.07,.20,.40,.60,.80,1],[.009,.055,.166,.385,.626,.837,.985])
    warm=np.clip((rgb[...,0]-rgb[...,2]-.028)*5.2,0,1)
    mids=np.sin(np.clip(luma,0,1)*np.pi)**.6
    color=curve[...,None]+(rgb-luma[...,None])*(1.17+.045*warm[...,None])
    color+=(mids*(1-warm*.88))[...,None]*np.array([-.039,.0015,.060])
    color+=(mids*warm)[...,None]*np.array([.035,.009,-.016])
    return np.clip(rgb+(color-rgb)*1.07,0,1)

def write_lut(path):
    axis=np.linspace(0,1,49)
    b,g,r=np.meshgrid(axis,axis,axis,indexing="ij")
    mapped=blue_hour(np.stack((r,g,b),axis=-1)).reshape(-1,3)
    with path.open("w",encoding="ascii") as lut:
        lut.write('TITLE "GPU Silo blue hour"\nLUT_3D_SIZE 49\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        np.savetxt(lut,mapped,fmt="%.6f")

def encode(frames,work,out,first,count):
    work.mkdir(parents=True,exist_ok=True)
    if not all((frames/f"f_{i:04}.jpg").is_file() for i in range(first,first+count)):
        raise ValueError("The requested Cycles frame range is incomplete")
    out=out.resolve();frames=frames.resolve()
    lut=work/"blue-hour.cube";write_lut(lut)
    filters=("scale=in_range=full:out_range=full:in_color_matrix=bt601,format=gbrp16le,"
             "lut3d=file=blue-hour.cube:interp=tetrahedral,"
             "scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p")
    subprocess.run(["ffmpeg","-v","error","-y","-framerate","24","-start_number",str(first),"-i",str(frames/"f_%04d.jpg"),
                    "-frames:v",str(count),"-an","-map_metadata","-1","-vf",filters,"-filter_threads","4",
                    "-c:v","libx264","-threads","6","-preset","medium","-crf","17","-pix_fmt","yuv420p",
                    "-color_primaries","bt709","-colorspace","bt709","-color_trc","bt709",
                    "-metadata","title=GPU Silo | Blue-hour closing orbit","-movflags","+faststart",str(out)],
                   cwd=work,check=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ("frames","work","out"):parser.add_argument(field,type=Path)
    parser.add_argument("--first",type=int,default=0);parser.add_argument("--count",type=int,default=540)
    a=parser.parse_args();encode(a.frames,a.work,a.out,a.first,a.count)
