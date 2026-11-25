"""Animate flow on camera projections of the issued IFC and composite its Cycles section passes."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .review_overlays import font
from .short_song import optional_lyrics

HOT=(255,158,90); COLD=(73,219,238); SECONDARY=(218,208,252)
WHITE=(239,242,232); MUTED=(181,202,204); DARK=(12,25,31)
COLOR={"podCold":COLD,"podWarm":HOT,"coolerCold":COLD,"coolerWarm":HOT,"secondary":SECONDARY}
SHOTS={
 "store": dict(kicker="Vertical IFC section",title=("The annular","store"),size=63,
               value="6,524 m³",detail=("Water with 25% propylene","glycol by volume")),
 "pods": dict(kicker="Heat acquisition",title=("The pod circuit",),size=59,
               value="4 racks",detail=("One CDU transfers heat","from the pod’s rack loop.")),
 "coolers": dict(kicker="Heat rejection",title=("The cooler","circuit"),size=63,
                 value="30 dry coolers",detail=("Three units per frame","10 frames around the silo")),
 "risers": dict(kicker="Pipework study",title=("The tall risers",),size=58,
                value="Ø400 mm",detail=("8 pairs for pod bays","10 pairs for cooler frames")),
 "diffuser": dict(kicker="Pipe mouth detail",title=("The diffuser",),size=59,
                  value="Ø1.20 m",detail=("A circular plate spreads","the discharge sideways.")),
 "reserve": dict(kicker="Loss of heat rejection",title=("Thermal","ride-through"),size=61,
                 value="76 minutes",detail=("10 K usable temperature swing","51.25 MW design heat load","90% usable store volume")),
}
# Label anchors in the Cycles camera view, line position and two lines of copy.
LABELS={
 "store":[("upperLayer",267,"WARM UPPER LAYER","52 °C design",HOT),("lowerLayer",769,"COOL LOWER LAYER","42 °C design",COLD)],
 "pods":[("podWarm",170,"HIGH RETURN   +30.70 m","Warm to store",HOT),("cdu",590,"POD CDU","Separate rack loop",SECONDARY),
         ("podCold",866,"LOW INTAKE   +0.50 m","Cool to CDU",COLD)],
 "coolers":[("coolerWarm",163,"HIGH INTAKE   +30.70 m","Warm to coolers",HOT),("cooler",476,"DRY COOLER","Heat to outside air",WHITE),
            ("coolerCold",865,"LOW RETURN   +0.50 m","Cool to store",COLD)],
 "risers":[("studypodWarm",209,"POD HEADERS","Low draw  /  high return",HOT),
           ("studycoolerCold",794,"COOLER HEADERS","High draw  /  low return",COLD)],
 "diffuser":[("topPlate",202,"DIFFUSER PLATE","Three support legs",WHITE),("mouth",683,"OPEN PIPE","350 mm clear gap",HOT)],
 "reserve":[("upperLayer",234,"WARM INVENTORY","Expands downward",HOT),("lowerLayer",763,"COOL INVENTORY","Feeds the pod CDUs",COLD)],
}
ROUTES={"store":(),"pods":("podCold","podWarm","secondary"),"coolers":("coolerWarm","coolerCold"),
        "risers":("riserpodCold","riserpodWarm","risercoolerCold","risercoolerWarm"),
        "diffuser":("inlet",*(f"fan{i}" for i in range(8))),"reserve":()}

def smooth(t):
    t=min(1,max(0,t));return t*t*(3-2*t)

def picture(path,width):
    im=Image.open(path).convert("RGB")
    return im if im.width==width else im.resize((width,width*9//16),Image.Resampling.LANCZOS)

class Graphic:
    """All authored coordinates use a 1920-wide artboard at the film's exact aspect ratio."""
    def __init__(self,im):
        self.im=im;self.s=im.width/1920;self.draw=ImageDraw.Draw(im)
    def xy(self,p):return tuple(round(v*self.s) for v in p)
    def line(self,pts,ink,w=1):
        self.draw.line([self.xy(p) for p in pts],fill=ink,width=max(1,round(w*self.s)),joint="curve")
    def dot(self,p,r,ink,outline=False):
        x,y=p;bounds=(*self.xy((x-r,y-r)),*self.xy((x+r,y+r)))
        if outline:self.draw.ellipse(bounds,outline=ink,width=max(1,round(1.5*self.s)))
        else:self.draw.ellipse(bounds,fill=ink)
    def text(self,x,y,text,size,f="sans",ink=WHITE):
        self.draw.text(self.xy((x,y)),text,font=font(f,max(8,round(size*self.s))),anchor="lt",fill=ink)
    def rectangle(self,xy,ink):
        self.draw.rectangle((*self.xy(xy[:2]),*self.xy(xy[2:])),fill=ink)

def color_for(key):
    if key.startswith("fan") or key=="inlet":return HOT
    return COLOR[key.removeprefix("riser")]

class Trail:
    def __init__(self,projected,color,short=False,diffusing=False):
        p=np.array(projected)*[1920,1080]
        if diffusing:
            control=np.vstack((p[0],p,p[-1]));smoothed=[]
            for a,b,c,d in zip(control,control[1:],control[2:],control[3:]):
                for t in np.linspace(0,1,12,endpoint=False):
                    smoothed.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3))
            p=np.vstack((smoothed,p[-1]))
        keep=np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>.01]
        self.p=p[keep];self.color=color
        delta=np.diff(self.p,axis=0);self.lengths=np.linalg.norm(delta,axis=1)
        self.dirs=delta/self.lengths[:,None];self.ends=np.cumsum(self.lengths)
        self.length=self.ends[-1];self.short=short;self.diffusing=diffusing
    def at(self,d):
        i=min(len(self.dirs)-1,int(self.ends.searchsorted(d)))
        start=self.ends[i]-self.lengths[i]
        return self.p[i]+(d-start)*self.dirs[i],self.dirs[i]
    def base(self,g):
        if self.diffusing:
            previous=None
            for u in np.linspace(0,1,29):
                point,direction=self.at(u*self.length)
                normal=np.array([-direction[1],direction[0]])*(2+11*u)
                sides=(point+normal,point-normal)
                if previous is not None:
                    g.draw.polygon([g.xy(p) for p in (previous[0],sides[0],sides[1],previous[1])],
                                   fill=(*self.color,round(103*(1-u)**.75)))
                previous=sides
            return
        g.line(self.p,(*self.color,46),14 if not self.short else 9)
        g.line(self.p,(*self.color,104),8 if not self.short else 5)
        g.line(self.p,(*self.color,200),3 if not self.short else 2)
    def moving(self,g,t,phase):
        pitch=52 if self.short else 73
        speed=60 if self.short else 96
        for distance in np.arange((t*speed+phase)%pitch,self.length,pitch):
            if self.diffusing:
                u=distance/self.length
                distance=self.length*(1-(1-u)**1.55)
                p,direction=self.at(distance)
                tail=p-direction*(9-5*u)
                lit=tuple(round(c*(1-.48*u)) for c in self.color)
                g.line((tail,p),lit,3.6-1.5*u)
                g.dot(p,2.3-1.1*u,tuple(round(v*.73+60) for v in lit))
                continue
            p,tangent=self.at(distance); side=np.array([-tangent[1],tangent[0]])
            size=5.2 if self.short else 6.2
            tip=p+size*tangent;back=p-size*.82*tangent
            ink=tuple(round(c*.47+255*.53) for c in self.color)
            tail,_=self.at(max(0,distance-13))
            g.line((tail,p),self.color,4)
            chevron=[back+size*.57*side,tip,back-size*.57*side]
            g.line(chevron,self.color,6);g.line(chevron,ink,3)

class Study:
    def __init__(self,plates,projection,shot,width):
        self.shot=shot;self.id=shot["id"];self.width=width;self.height=width*9//16
        row=projection[self.id]
        self.anchors={k:np.array(v)*[1920,1080] for k,v in row["anchors"].items()}
        lines=dict(row["routes"])
        lines["secondary"]=[*lines["secondary"],lines["secondary"][0]]
        lines["inlet"]=lines["fan0"][:2]
        for k in range(4):lines[f"fan{k}"]=lines[f"fan{k}"][1:]
        centre=(np.array(lines["fan0"])+lines["fan1"])/2
        for j,(a,b) in enumerate(((0,2),(2,1),(1,3),(3,0)),4):
            lines[f"fan{j}"]=centre+(np.array(lines[f"fan{a}"])+lines[f"fan{b}"]-2*centre)/math.sqrt(2)
        self.trails=[Trail(lines[k],color_for(k),k=="secondary",k.startswith("fan")) for k in ROUTES[self.id]]
        self.base=picture(plates/(("reserve_cold" if self.id=="reserve" else self.id)+".png"),width)
        if self.id=="diffuser":
            # Reapply the neutral metal facing the camera so the rear discharge
            # streams disappear behind the photographed plate and its three legs.
            self.clean=self.base
            rgb=np.asarray(self.base).astype(np.int16)
            lo=rgb.min(axis=2);hi=rgb.max(axis=2)
            matte=np.clip((lo-86)/42,0,1)*np.clip((67-(hi-lo))/27,0,1)
            matte[:round(self.height*.16)]=0;matte[round(self.height*.55):]=0
            self.front_matte=Image.fromarray(np.uint8(255*matte))
        if self.id=="store":
            self.inset=picture(plates/"store_inset.png",width)
            self.inset_trails=[Trail(lines[k],COLOR[k]) for k in ("podCold","podWarm","coolerCold","coolerWarm")]
            ink=Image.new("RGBA",self.base.size);g=Graphic(ink)
            for trail in self.inset_trails:trail.base(g)
            self.inset=Image.alpha_composite(self.inset.convert("RGBA"),ink).convert("RGB")
        if self.id=="reserve":
            self.warm=picture(plates/"reserve_warm.png",width)
            self.mask=picture(plates/"reserve_z.png",width).convert("L")
        self.strokes=Image.new("RGBA",self.base.size);g=Graphic(self.strokes)
        for trail in self.trails:trail.base(g)
        if self.id=="diffuser":self.strokes=self.strokes.filter(ImageFilter.GaussianBlur(width/1580))
        if self.trails:self.base=Image.alpha_composite(self.base.convert("RGBA"),self.strokes).convert("RGB")
        self.card=Image.new("RGBA",self.base.size);g=Graphic(self.card)
        spec=SHOTS[self.id];left=80; y=128
        g.line(((left,88),(left+42,88)),(236,182,123),3)
        g.text(left+56,79,spec["kicker"].upper(),21,"mono",(236,182,123))
        for line in spec["title"]:
            g.text(left-2,y,line,spec["size"],"serif");y+=spec["size"]+8
        y+=36
        g.line(((left,y),(left+278,y)),(118,142,146,190),1)
        g.text(left,y+28,spec["value"],46,"light")
        for i,v in enumerate(spec["detail"]):g.text(left+1,y+94+34*i,v,24,"sans",MUTED)
        if self.id=="risers":
            g.text(left,910,"Header spacing expanded for this view.",20,"sans",MUTED)
        if self.id=="reserve":
            g.text(left,802,"MODEL TIME",20,"mono",MUTED)
            g.text(left,943,"Circulation maintained",24,"sans",WHITE)
        self.notes=Image.new("RGBA",self.base.size);g=Graphic(self.notes)
        for anchor,y,title,detail,ink in LABELS[self.id]:
            g.rectangle((1476,y-14,1894,y+69),(12,28,34,206))
            g.rectangle((1476,y-14,1480,y+69),(*ink,255))
            g.text(1497,y,title,20,"mono",ink)
            g.text(1497,y+30,detail,24,"sans",WHITE)
    def render(self,frame):
        count=self.shot["last"]-self.shot["first"];t=frame/24;u=frame/max(1,count-1)
        # A gradual editorial push moves all world-anchored callouts together with the Cycles plate.
        zoom=1+.030*smooth(u); px,py=.575,.5
        if self.id in ("pods","coolers"):
            # Inspect the active exchanger during its narration, then reacquire both openings.
            close=smooth((u-.115)/.28)*(1-smooth((u-.62)/.30))
            target=self.anchors["cdu" if self.id=="pods" else "cooler"]
            px,py=target/[1920,1080]
            zoom+=(.74 if self.id=="pods" else .58)*close
        if self.id=="reserve":
            elapsed=smooth((u-.06)/.85)
            # In this straight annulus, a front traversing 90% of the liquid depth
            # represents the report's 90% usable-volume allowance at constant load.
            boundary=31.75*(.95-.90*elapsed)
            values=np.arange(256)
            z=(values/255-.05)*32/.9
            w=np.clip((z-boundary+1.0)/2.,0,1);w=w*w*(3-2*w)
            lut=np.uint8(np.where(values<8,0,255*w))
            im=Image.composite(self.warm,self.base,self.mask.point(lut.tolist()))
        elif self.id=="store":
            show=smooth((u-.28)/.32)
            if show:
                explanation=self.inset.copy()
                pen=Graphic(explanation)
                for i,trail in enumerate(self.inset_trails):trail.moving(pen,t,17*i)
                im=Image.blend(self.base,explanation,show) if show<1 else explanation
            else:im=self.base.copy()
        else:im=self.base.copy()
        g=Graphic(im)
        for i,trail in enumerate(self.trails):trail.moving(g,t,13*i)
        if self.id=="diffuser":im.paste(self.clean,(0,0),self.front_matte)
        if zoom>1.00001:
            w,h=im.size; dx=(w-w/zoom)*px;dy=(h-h/zoom)*py
            im=im.resize(im.size,Image.Resampling.BICUBIC,box=(dx,dy,dx+w/zoom,dy+h/zoom))
        im=im.convert("RGBA")
        def pushed(p):
            return (p[0]*zoom-1920*px*(zoom-1),p[1]*zoom-1080*py*(zoom-1))
        # Do not project a line behind an opaque label. The end ring marks the physical part.
        g=Graphic(im)
        for anchor,y,title,detail,ink in LABELS[self.id]:
            place=self.anchors[anchor]
            if self.id=="reserve":
                # Keep each callout inside the named layer as the interface descends.
                height=(boundary+31.75)*.5 if anchor=="upperLayer" else boundary*.5
                place=self.anchors["lowerLayer"]+(height-6.2)/19.6*(self.anchors["upperLayer"]-self.anchors["lowerLayer"])
            target=pushed(place);end=(1476,y+19)
            offscreen=target[1]<12 or target[1]>1068
            if offscreen:target=(target[0],max(12,min(1068,target[1])))
            elbow=(max(target[0]+43,1404),y+19)
            line=[target,elbow,end]
            g.line(line,(20,40,44),4);g.line(line,tuple(int(v*.8+30) for v in ink),1.25)
            if offscreen:
                sign=1 if target[1]<540 else -1
                g.line(((target[0]-5,target[1]+sign*8),target,(target[0]+5,target[1]+sign*8)),ink,2.5)
            else:
                g.dot(target,4.5,DARK);g.dot(target,4.5,ink,True)
        im.alpha_composite(self.card);im.alpha_composite(self.notes)
        if self.id=="reserve":
            g=Graphic(im)
            seconds=round(76*60*elapsed)
            g.text(78,843,f"{seconds//60:02}:{seconds%60:02}",61,"light",HOT)
            g.text(308,877,"min : sec",20,"mono",MUTED)
        return im.convert("RGB")

def chapters(path,shots):
    lines=[";FFMETADATA1"]
    for shot in shots:lines+=["[CHAPTER]","TIMEBASE=1/24",f"START={shot['first']}",f"END={shot['last']}",f"title={shot['title']}"]
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")

def build(plates,voice,out,width,stills):
    shots=json.loads((voice/"thermal.json").read_text(encoding="utf-8"))
    coords=json.loads((plates/"projection.json").read_text(encoding="utf-8"))
    if stills:
        stills.mkdir(parents=True,exist_ok=True)
        for shot in shots:
            study=Study(plates,coords,shot,width);length=shot["last"]-shot["first"]
            for f in ([0,length//2,length-1] if shot["id"]=="reserve" else [length//2]):
                study.render(f).save(stills/f"{shot['id']}-{f:03}.jpg",quality=94)
        return
    out.parent.mkdir(parents=True,exist_ok=True);meta=voice/"thermal.ffmetadata";chapters(meta,shots)
    cmd=["ffmpeg","-hide_banner","-v","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",
         f"{width}x{width*9//16}","-framerate","24","-i","pipe:0","-i",str(voice/"thermal.flac"),"-i",str(voice/"thermal.srt"),
         "-f","ffmetadata","-i",str(meta),"-map","0:v","-map","1:a","-map","2:s","-map_metadata","3","-map_chapters","3",
         "-metadata","title=Thermal ride-through | GPU Silo","-metadata:s:s:0","language=eng","-metadata:s:a:0","language=eng",
         "-disposition:s:0","0","-c:v","libx264","-threads","5","-preset","veryfast","-crf","17","-pix_fmt","yuv420p",
         "-vf","scale=in_range=full:out_range=limited:out_color_matrix=bt709","-color_primaries","bt709","-colorspace","bt709","-color_trc","bt709",
         "-c:a","aac","-b:a","128k","-c:s","mov_text","-movie_timescale","6000000","-movflags","+faststart",str(out)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for shot in shots:
            print("Compositing",shot["id"],shot["first"],shot["last"],flush=True)
            study=Study(plates,coords,shot,width)
            for frame in range(shot["last"]-shot["first"]):process.stdin.write(study.render(frame).tobytes())
        process.stdin.close()
        if process.wait():raise RuntimeError("FFmpeg did not finish the thermal film")
    except BaseException:
        process.kill();process.wait();raise
    optional_lyrics(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("plates",type=Path);p.add_argument("voice",type=Path);p.add_argument("out",type=Path)
    p.add_argument("--width",type=int,default=3840);p.add_argument("--stills",type=Path)
    a=p.parse_args();build(a.plates,a.voice,a.out,a.width,a.stills)
