"""Render five editorial treatments onto the same three full-resolution, text-free film frames."""
import argparse
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    "sans":("segoeui.ttf","Inter-Regular.ttf","DejaVuSans.ttf"),
    "bold":("segoeuib.ttf","Inter-Bold.ttf","DejaVuSans-Bold.ttf"),
    "light":("segoeuil.ttf","Inter-Light.ttf","DejaVuSans-ExtraLight.ttf","DejaVuSans.ttf"),
    "mono":("consola.ttf","DejaVuSansMono.ttf"),
    "serif":("georgia.ttf","LiberationSerif-Regular.ttf","DejaVuSerif.ttf"),
    "italic":("georgiai.ttf","LiberationSerif-Italic.ttf","DejaVuSerif-Italic.ttf"),
}
STYLES = ("Editorial lower third","Instrument strip","Field note","Tracked callout","Open typography")
SLUGS = ("editorial-lower-third","instrument-strip","field-note","tracked-callout","open-typography")
SCENES = (
    dict(id="delivery",title="Pod receiving",section="Logistics",time="00:36.750",at=(1090,618),
         metric=(("4","Vera Rubin racks per pod"),("2","pods per delivery"),("7.16 m","cantilever")),
         hero=2),
    dict(id="turbines",title="Turbine generation",section="Power",time="01:14.500",at=(1061,397),
         metric=(("2 × 25 MW","propane design basis"),("22.7 MW","net, natural gas at ISO"),("LM2500 DLE","GE reference package")),
         hero=0),
    dict(id="shaft",title="Steel shaft",section="Structure",time="01:29.500",at=(1089,507),
         metric=(("Ø1.16 m","fixed shaft"),("24 × M56","base anchors"),("45°","carrier indexing step")),
         hero=2),
)
LIGHT=(244,242,229); MUTED=(197,211,211); BRASS=(239,181,113); SEA=(130,228,215)
SIZE=(3840,2160); SCALE=2

@lru_cache(maxsize=100)
def font(family,size):
    for name in FONTS[family]:
        try:
            return ImageFont.truetype(name,size)
        except OSError:
            continue
    raise OSError(f"Install one of the fonts for {family}: {', '.join(FONTS[family])}")

class Canvas:
    def __init__(self,im):
        self.image=im.convert("RGBA")
        self.layer=Image.new("RGBA",self.image.size)
        self.pen=ImageDraw.Draw(self.layer)
    def text(self,x,y,value,size=25,f="sans",ink=LIGHT):
        self.pen.text((round(x*SCALE),round(y*SCALE)),value,font=font(f,round(size*SCALE)),fill=ink,anchor="lt")
    def line(self,pts,color,width=1):
        self.pen.line([(round(x*SCALE),round(y*SCALE)) for x,y in pts],fill=color,width=round(width*SCALE),joint="curve")
    def box(self,l,t,r,b,fill):
        self.pen.rectangle(tuple(round(v*SCALE) for v in (l,t,r,b)),fill=fill)
    def ring(self,x,y,r,color,w):
        self.pen.ellipse(tuple(round(v*SCALE) for v in (x-r,y-r,x+r,y+r)),outline=color,width=round(w*SCALE))
    def shade(self,kind):
        x=np.linspace(0,1,480)[None,:]; y=np.linspace(0,1,270)[:,None]
        if kind=="editorial":
            a=np.clip((y-.55)/.37,0,1)**.83*np.clip((1.02-x)/.49,.19,1)*.95
        else:
            a=np.clip((x-.49)/.25,0,1)*np.clip((.90-y)/.37,.12,1)*.92
        veil=Image.new("RGBA",self.image.size,(13,23,29))
        veil.putalpha(Image.fromarray(np.uint8(255*a)).resize(self.image.size,Image.Resampling.BILINEAR))
        self.image=Image.alpha_composite(self.image,veil)
    def final(self):
        return Image.alpha_composite(self.image,self.layer).convert("RGB")

def paint(frame,row,style):
    c=Canvas(frame);m=row["metric"]
    if style==0:
        c.shade("editorial")
        c.line(((87,796),(154,796)),BRASS,4)
        c.text(171,783,row["section"].upper(),21,"mono",BRASS)
        c.text(84,818,row["title"],70,"serif")
        c.text(89,925,"    /    ".join(v+" "+u for v,u in m[:2]),29,"sans")
        c.text(90,980,m[2][0]+" "+m[2][1],24,"sans",MUTED)
    elif style==1:
        c.box(0,845,1920,1080,(13,29,34,241))
        c.line(((0,846),(1920,846)),(80,132,136),1)
        c.line(((85,846),(352,846)),SEA,4)
        c.text(87,877,row["title"],36,"bold")
        c.text(88,941,row["section"].upper(),19,"mono",SEA)
        for i,(v,u) in enumerate(m):
            x=(562,997,1432)[i]
            c.line(((x-28,889),(x-28,1015)),(78,105,111),1)
            c.text(x,889,v,48 if len(v)<9 else 39,"light")
            c.text(x,973,u,21,"sans",MUTED)
    elif style==2:
        c.box(80,67,605,480,(0,0,0,45))
        c.box(73,60,598,473,(245,241,224,252))
        c.box(73,60,83,473,(80,114,87))
        c.text(106,91,row["section"].upper(),22,"mono",(43,88,66))
        c.text(104,143,row["title"],41,"serif",(33,48,42))
        c.line(((106,209),(561,209)),(125,143,121),1.5)
        for i,(v,u) in enumerate(m):
            y=241+66*i
            c.text(106,y,v,26 if len(v)<10 else 23,"bold",(36,56,44))
            c.text(286,y+2,u,20,"sans",(45,66,55))
    elif style==3:
        x,y=row["at"]; left=75;right=613; top=90
        c.line(((right,top+191),(right+105,top+191),(x-52,y),(x-10,y)),(15,35,40,235),6)
        c.line(((right,top+191),(right+105,top+191),(x-52,y),(x-10,y)),SEA,2)
        c.ring(x,y,10,(12,36,42),4);c.ring(x,y,9,SEA,2)
        c.box(left,top,right,top+236,(14,32,42,237))
        c.box(left,top,right,top+4,SEA)
        c.text(left+26,top+27,row["title"],35,"bold")
        for i,(v,u) in enumerate(m):
            c.text(left+27,top+88+42*i,v+"  "+u,22,"sans",LIGHT if i==0 else MUTED)
    else:
        c.shade("open")
        x=1380;c.text(x,102,row["title"].upper(),23,"mono",BRASS)
        i=row["hero"];v,u=m[i]
        c.text(x-5,164,v,78 if len(v)>6 else 96,"light")
        c.text(x+2,287,u,29,"italic")
        c.line(((x+2,355),(1808,355)),(203,193,167),1.5)
        for j,(value,caption) in enumerate([r for k,r in enumerate(m) if k!=i]):
            y=396+j*90
            c.text(x,y,value,33,"bold")
            c.text(x+1,y+43,caption,21,"sans",MUTED)
    return c.final()

def make(source,dest):
    dest.mkdir(parents=True,exist_ok=True)
    frames=[Image.open(source/(row["id"]+".jpg")).convert("RGB") for row in SCENES]
    if any(im.size!=SIZE for im in frames):raise ValueError("Use native 4K source frames")
    overview=Image.new("RGB",(2312,2424),(18,27,30)); d=ImageDraw.Draw(overview)
    d.text((42,22),"Technical short  /  Overlay studies",font=font("serif",42),fill=LIGHT)
    for k,row in enumerate(SCENES):
        d.text((43+k*747,86),row["title"]+"  /  "+row["time"],font=font("sans",25),fill=MUTED)
    files=[]
    for j,style in enumerate(STYLES):
        folder=dest/"overlays"/f"{j+1:02}-{SLUGS[j]}";folder.mkdir(parents=True,exist_ok=True)
        top=140+j*453
        d.text((42,top),f"{j+1:02}   {style}",font=font("bold",27),fill=LIGHT)
        for k,(row,base) in enumerate(zip(SCENES,frames)):
            pic=paint(base,row,j)
            out=folder/f"{k+1:02}-{row['id']}.jpg"
            pic.save(out,quality=95,subsampling=0,optimize=True);files.append(out)
            thumb=pic.resize((732,412),Image.Resampling.LANCZOS)
            overview.paste(thumb,(42+k*747,top+35))
    overview_file=dest/"overlay_options.jpg"
    overview.save(overview_file,quality=91,optimize=True)
    with ZipFile(dest/"overlay_options.zip","w",ZIP_STORED) as z:
        for file in [overview_file,*files]:z.write(file,file.relative_to(dest))
    print(f"{len(files)} full-resolution designs at 3840 × 2160",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("out",type=Path)
    a=p.parse_args();make(a.source,a.out)
