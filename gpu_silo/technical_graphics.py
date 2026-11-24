"""Resolution-independent postproduction graphics for the 4K short. Uses FFmpeg/libass."""
import math
from pathlib import Path

HEADER="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Film,Segoe UI,38,&H00F3F5F4,&H00FFFFFF,&H001B2525,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
NAVY="132832"; SKY="84c9ce"; WARM="f3aa69"; PALE="e7ede7"; MUTED="93a9ab"; MID="44606a"; LINE="35515a"


def color(hexcode):
    return "&H"+hexcode[4:6]+hexcode[2:4]+hexcode[:2]+"&"


def stamp(seconds):
    n=round(seconds*100)
    return f"{n//360000}:{n//6000%60:02}:{n//100%60:02}.{n%100:02}"


class Art:
    def __init__(self,start,end):
        self.start=start;self.end=end;self.events=[]

    def emit(self,layer,text,start=None,end=None):
        self.events.append(f"Dialogue: {layer},{stamp(self.start if start is None else start)},{stamp(self.end if end is None else end)},Film,,0,0,0,,{text}")

    def polygon(self,points,col,layer=1,alpha="00",motion=None):
        path="m "+" l ".join(f"{round(x)} {round(y)}" for x,y in points)
        loc=motion or r"\pos(0,0)"
        self.emit(layer,"{"+loc+r"\an7\bord0\shad0\p1\1c"+color(col)+r"\1a&H"+alpha+"&}"+path)

    def rect(self,x,y,w,h,col,layer=1,alpha="00"):
        self.polygon(((x,y),(x+w,y),(x+w,y+h),(x,y+h)),col,layer,alpha)

    def line(self,points,width,col,layer=2):
        for (x,y),(xx,yy) in zip(points,points[1:]):
            dx,dy=xx-x,yy-y
            length=math.hypot(dx,dy)
            if length<.001:continue
            u,v=-dy/length*width*.5,dx/length*width*.5
            self.polygon(((x+u,y+v),(xx+u,yy+v),(xx-u,yy-v),(x-u,y-v)),col,layer)

    def disk(self,x,y,r,col,layer=2,n=86):
        self.polygon([(x+r*math.cos(a*math.tau/n),y+r*math.sin(a*math.tau/n)) for a in range(n)],col,layer)

    def text(self,x,y,value,size,col=PALE,bold=False,layer=8,fade=False):
        tag=f"\\an7\\pos({x},{y})\\fs{size}\\b{int(bold)}\\1c{color(col)}"
        if fade:tag+=r"\fad(95,85)"
        self.emit(layer,"{"+tag+"}"+value)

    def write(self,path):
        path.write_text(HEADER+"\n".join(self.events)+"\n",encoding="utf-8-sig")


def drawings(start,end):
    """Plan and longitudinal section use the same shell proportions and eight storage levels."""
    a=Art(start,end)
    for x in range(0,1920,48):a.rect(x,0,1,1080,"1c353c",0)
    for y in range(0,1080,48):a.rect(0,y,1920,1,"1c353c",0)
    a.rect(960,215,1,663,LINE,1)
    cx,cy=494,558
    for radius,col in ((277,"718687"),(267,"325c66"),(199,"6b999a"),(192,"172f37"),(173,"375662"),(171,"192f37")):
        a.disk(cx,cy,radius,col,2)
    def basis(angle,x,y):
        c,s=math.cos(angle),math.sin(angle)
        return (cx+c*x-s*y,cy+s*x+c*y)
    def local(angle,x,y,w,h,col,layer=3):
        a.polygon([basis(angle,xx,yy) for xx,yy in ((x,y),(x+w,y),(x+w,y+h),(x,y+h))],col,layer)
    for bay in range(8):
        ang=(bay*45-16)*math.pi/180
        local(ang,24,-13,159,26,"81969a")
        local(ang,26,-10,154,20,"263e48",4)
        for rack in range(4):
            local(ang,30+25*rack,-9,22,18,"b4c6c2",5)
            local(ang,33+25*rack,-5,13,4,"68858a",6)
        local(ang,134,-8,32,16,"78b2b3",5)
        for off in (-7,7):a.line([basis(ang,172,off),basis(ang,202,off)],4,SKY if off>0 else WARM,6)
    for bay in range(10):
        ang=(bay*36-18)*math.pi/180
        local(ang,278,-40,32,80,"91a4a5")
        local(ang,280,-37,27,74,"243e49",4)
        for j in range(3):
            x,y=basis(ang,295,-22+j*22)
            a.disk(x,y,9,"688e93",5,24);a.disk(x,y,5,"2c474f",6,16)
    a.disk(cx,cy,22,"c5ceca",7,48);a.disk(cx,cy,14,"4e696c",8,48)
    # Section at matching datum. Roof plant and thermal layers are shown schematically.
    sx,sy=1409,837
    scale=15.1
    a.rect(sx-208,sy,416,31,"abb9b7",2)
    for i in range(39):a.line([(sx-205+i*10,sy+29),(sx-188+i*10,sy+3)],1.4,"758d91",3)
    zinc=sy-32*scale
    for sign in (-1,1):
        left=sx-12.5*scale if sign==-1 else sx+8.5*scale
        w=4*scale
        a.rect(left,zinc,w,sy-zinc,"547e86",2)
        for j in range(18):
            t=j/17
            c=tuple(round((1-t)*u+t*v) for u,v in zip((159,105,73),(64,139,157)))
            a.rect(left+6,zinc+j*(sy-zinc)/18,w-12,(sy-zinc)/18+1,"%02x%02x%02x"%c,3)
        a.rect(left,zinc,6,sy-zinc,"b0bfbd",4);a.rect(left+w-6,zinc,6,sy-zinc,"b0bfbd",4)
    a.rect(sx-8,sy-28*scale,16,28*scale,"96a9aa",4)
    for level in range(8):
        base=sy-11-level*2.77*scale
        a.rect(sx-128,base,256,3,"7b9297",5)
        for sign in (-1,1):
            start=sx+sign*16
            for rack in range(4):
                x=start+sign*(7+rack*20)
                a.rect(x-(16 if sign<0 else 0),base-27,16,26,"9fbbbd",5)
                for j in range(4):a.rect(x-(15 if sign<0 else -1),base-23+j*5,12,1,"617e86",6)
            x=sx+sign*111
            a.rect(x-7,base-27,14,25,SKY,5)
    for deck in (23.8,27.6):
        y=sy-deck*scale
        a.rect(sx-130,y,260,7,"9caeae",5)
        for sign in (-1,1):
            a.rect(sx+sign*63-41,y-23,82,22,"718c90",5)
            for k in range(7):a.rect(sx+sign*63-37+10*k,y-20,4,16,"3b5963",6)
    a.rect(sx-190,zinc-5,380,8,"b6c3c2",6)
    for x in (sx-75,sx+69):a.rect(x,zinc-34,11,30,"86a0a3",5)
    for side in (-1,1):
        x=sx+side*211
        for unit in range(3):
            y=zinc+83+unit*43
            a.rect(x-17,y,34,39,"8b9c9c",5)
            a.disk(x,y+18,13,"365561",6,24);a.disk(x,y+18,6,"87a6a9",7,20)
        a.line([(x,zinc+170),(x,zinc+195),(sx+side*159,zinc+195),(sx+side*159,sy-33)],4,SKY,7)
        a.line([(sx+side*148,zinc+15),(x,zinc+15),(x,zinc+78)],4,WARM,7)
        for j in range(4):
            a.line([(sx+side*150,sy-80-j*77),(sx+side*121,sy-80-j*77)],3,SKY,7)
    # A small train of fluid markers traverses the supply and return paths.
    for x,y1,y2,col in ((sx+159,zinc+200,sy-36,SKY),(sx-148,sy-50,zinc+17,WARM)):
        duration=2.1
        for i in range(math.ceil((end-start)/duration)):
            at=start+i*duration;until=min(end,at+duration)
            final=y1+(y2-y1)*(until-at)/duration
            path="m -4 -4 l 4 -4 l 4 4 l -4 4"
            a.emit(8,"{\\an7\\p1\\bord0\\1c"+color(col)+f"\\move({x},{y1:.0f},{x},{final:.0f})"+"}"+path,at,until)
    return a


def overlays(script,section_start,end):
    out=Art(0,end)
    for cue in script["cues"]:
        a=Art(round(cue["start"]*24)/24,round(cue["end"]*24)/24)
        lines=cue["spec"].split("   /   ")
        length=max(len(cue["title"])*16.1,max(len(t) for t in lines)*15.8)
        # Fit the compact card to its type. Ordinary labels do not occupy the entire screen.
        w=max(240,min(734,length+57))
        h=67+len(lines)*32
        a.rect(58,47,w,h,NAVY,3,"18");a.rect(58,47,4,h,"82c4c8",4)
        a.text(81,55,cue["title"],35,PALE,True,fade=True)
        for j,t in enumerate(lines):a.text(82,103+j*30,t,25,"c1d7d7",fade=True)
        out.events+=a.events
    for ref in script.get("equipmentReferences",[]):
        a=Art(round(ref["start"]*24)/24,round(ref["end"]*24)/24)
        width=max(len(ref["label"])*14,len(ref["detail"])*13.1)+48
        a.rect(58,914,width,91,NAVY,3,"18")
        a.rect(58,914,4,91,WARM,4)
        a.text(81,921,ref["label"],23,"efb984",True,fade=True)
        a.text(81,951,ref["detail"],26,PALE,fade=True)
        out.events+=a.events
    d=Art(section_start,end)
    d.text(91,202,"TYPICAL STORAGE LEVEL",24,MUTED,True)
    d.text(1036,202,"LONGITUDINAL SECTION",24,MUTED,True)
    d.text(290,894,"Ø25 m shell   /   Ø17 m bore",28,PALE)
    d.text(1199,894,"32 m shell   /   2 m raft",28,PALE)
    d.rect(1063,973,22,7,SKY,7);d.text(1096,951,"Cool supply",25,SKY)
    d.rect(1320,973,22,7,WARM,7);d.text(1353,951,"Warm return",25,WARM)
    out.events+=d.events
    return out
