using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Drawing.Text;

// Closing schematics, drawn to scale from the design data: the cooling loop in plan
// and a section showing power, water-glycol and gas. Moving dashes show flow direction.
partial class Shot {
    readonly Color cHot=Color.FromArgb(201,84,58),cCold=Color.FromArgb(52,122,178),cPower=Color.FromArgb(222,160,38),cGas=Color.FromArgb(98,150,70);
    readonly Color cDrawn=Color.FromArgb(92,128,132),cDiesel=Color.FromArgb(150,74,54);
    readonly Color cConcrete=Color.FromArgb(152,162,154),cSteel=Color.FromArgb(76,98,102),cBronze=Color.FromArgb(160,137,89),cGrey=Color.FromArgb(207,210,210);
    Bitmap sheet;

    static Color Blend(Color a,Color b,double t){
        t=Sat(t);return Color.FromArgb((int)(a.R+(b.R-a.R)*t),(int)(a.G+(b.G-a.G)*t),(int)(a.B+(b.B-a.B)*t));
    }

    // Dashes travel along the path from its first point to its last.
    // With fade set, the stream thins out toward its end: the liquid is dispersing into the store.
    void Stream(Graphics g,IList<PointF> path,Color from,Color to,float width,double travel,float dash=9,float period=22,bool fade=false){
        var run=new double[path.Count];
        for(int i=1;i<path.Count;i++)run[i]=run[i-1]+Math.Sqrt(Math.Pow(path[i].X-path[i-1].X,2)+Math.Pow(path[i].Y-path[i-1].Y,2));
        double total=run[path.Count-1];if(total<1)return;
        if(!fade)using(var guide=new Pen(Color.FromArgb(46,Blend(from,to,.5)),width+2.2f)){guide.LineJoin=LineJoin.Round;g.DrawLines(guide,ToArray(path));}
        Func<double,PointF> at=s=>{
            int i=1;while(i<path.Count-1 && run[i]<s)i++;
            double span=Math.Max(1e-6,run[i]-run[i-1]),q=Sat((s-run[i-1])/span);
            return new PointF((float)(path[i-1].X+(path[i].X-path[i-1].X)*q),(float)(path[i-1].Y+(path[i].Y-path[i-1].Y)*q));
        };
        double start=travel%period-period;
        for(double s=start;s<total;s+=period){
            double a=Math.Max(0,s),b=Math.Min(total,s+dash);if(b-a<1.2)continue;
            var points=new List<PointF>();points.Add(at(a));
            for(int i=1;i<path.Count-1;i++)if(run[i]>a && run[i]<b)points.Add(path[i]);
            points.Add(at(b));
            double along=(a+b)/(2*total);
            using(var pen=new Pen(Color.FromArgb(fade?(int)(255*Math.Pow(1-along,1.3)):255,Blend(from,to,along)),fade?(float)(width*(1+.6*along)):width)){
                pen.StartCap=LineCap.Round;pen.EndCap=LineCap.Round;pen.LineJoin=LineJoin.Round;
                g.DrawLines(pen,points.ToArray());
            }
        }
    }
    static PointF[] ToArray(IList<PointF> path){var a=new PointF[path.Count];path.CopyTo(a,0);return a;}

    void Arrow(Graphics g,PointF tip,double direction,Color colour,float size=6){
        var points=new PointF[3];
        points[0]=tip;
        points[1]=new PointF(tip.X-(float)(size*Math.Cos(direction-.5)),tip.Y-(float)(size*Math.Sin(direction-.5)));
        points[2]=new PointF(tip.X-(float)(size*Math.Cos(direction+.5)),tip.Y-(float)(size*Math.Sin(direction+.5)));
        using(var b=new SolidBrush(colour))g.FillPolygon(b,points);
    }

    void Note(Graphics g,string text,string second,float x,float y,PointF target,bool rightAligned=false){
        float w=Math.Max(g.MeasureString(text,title2,PointF.Empty,leftText).Width,second==null?0:g.MeasureString(second,monoSmall,PointF.Empty,leftText).Width);
        float left=rightAligned?x-w:x,anchor=target.X<left?left-6:left+w+6;
        Rule(g,anchor,y+9,target.X,target.Y,cInk,.9f);
        using(var dot=new SolidBrush(cInk))g.FillEllipse(dot,target.X-2,target.Y-2,4,4);
        g.DrawString(text,title2,ink,new PointF(left,y),leftText);
        if(second!=null)g.DrawString(second,monoSmall,muted,new PointF(left,y+18),leftText);
    }

    void Legend(Graphics g,float x,float y,Color colour,string label){
        using(var pen=new Pen(colour,3.2f)){pen.DashPattern=new float[]{2.6f,1.6f};g.DrawLine(pen,x,y+8,x+34,y+8);}
        g.DrawString(label,title2,ink,new PointF(x+44,y),leftText);
    }

    void SceneHeading(Graphics g,string kicker,string title,string subtitle){
        const float x=24;
        g.FillRectangle(paper,0,0,UiLeft,720);
        g.FillRectangle(accent,x,33,25,3);g.DrawString(kicker,section,muted,new PointF(x,46),leftText);
        Heading(g,title,x-2,73);g.DrawString(subtitle,title2,muted,new PointF(x,126),leftText);
        Rule(g,x,164,222,164,cLine,1);
    }

    // ---------------------------------------------------------------- plan
    void PlanScene(Graphics g,int tick){
        bool duo=d.Short;
        if(!duo)using(var ground=new SolidBrush(Color.FromArgb(233,235,221)))g.FillRectangle(ground,UiLeft,0,1280-UiLeft,720);
        float cx=duo?516:752,cy=duo?352:322,m=duo?11.4f:17.2f;
        double turn=-Math.PI/2-d.Entry;
        Func<double,double,PointF> polar=(r,a)=>new PointF(cx+(float)(m*r*Math.Cos(a+turn)),cy-(float)(m*r*Math.Sin(a+turn)));
        Func<double,double,double,PointF> local=(a,x,y)=>new PointF(
            cx+(float)(m*(x*Math.Cos(a+turn)-y*Math.Sin(a+turn))),cy-(float)(m*(x*Math.Sin(a+turn)+y*Math.Cos(a+turn))));
        Action<double,Brush> disc=(r,b)=>g.FillEllipse(b,cx-(float)(m*r),cy-(float)(m*r),(float)(2*m*r),(float)(2*m*r));
        Color warm=Color.FromArgb(232,170,138),pale=Color.FromArgb(206,226,214),cool=Color.FromArgb(142,190,214);
        // Cooler frames behind the wall line: the lower tier first, the upper tier over it.
        for(int pass=0;pass<2;pass++)for(int i=0;i<d.CoolerFrames;i++){
            bool upper=d.FrameBase[i]>d.Height/2;if(upper!=(pass==1) || duo && upper)continue;
            double a=d.FrameBearing[i];float half=d.CoolerFrameWidth/2;
            PointF[] box={local(a,d.CoolerBack,-half),local(a,d.CoolerBack+d.CoolerFrameDepth,-half),local(a,d.CoolerBack+d.CoolerFrameDepth,half),local(a,d.CoolerBack,half)};
            using(var fill=new SolidBrush(upper?Color.FromArgb(214,217,210):Color.FromArgb(196,200,193)))g.FillPolygon(fill,box);
            using(var edge=new Pen(cSteel,1.3f))g.DrawPolygon(edge,box);
            PointF[] cooler={local(a,d.CoolerBack+.45,-half+.3),local(a,d.CoolerBack+d.CoolerFrameDepth-.35,-half+.3),
                             local(a,d.CoolerBack+d.CoolerFrameDepth-.35,half-d.PumpLength-.1),local(a,d.CoolerBack+.45,half-d.PumpLength-.1)};
            using(var fill=new SolidBrush(Color.FromArgb(upper?150:255,96,124,124)))g.FillPolygon(fill,cooler);
            PointF[] pump={local(a,d.CoolerBack+.6,half-d.PumpLength+.1),local(a,d.CoolerBack+d.CoolerFrameDepth-.6,half-d.PumpLength+.1),
                           local(a,d.CoolerBack+d.CoolerFrameDepth-.6,half-.15),local(a,d.CoolerBack+.6,half-.15)};
            using(var fill=new SolidBrush(Color.FromArgb(163,168,168)))g.FillPolygon(fill,pump);
        }
        // Walls and the store. The tint runs from warm at the inner wall to cool at the outer wall.
        using(var concrete=new SolidBrush(cConcrete))disc(d.Outer,concrete);
        int bands=26;
        for(int k=0;k<bands;k++){
            double q=k/(double)(bands-1),r=d.OuterInside-(d.OuterInside-d.InnerOutside)*k/(double)bands;
            Color tint=q<.5?Blend(cool,pale,q*2):Blend(pale,warm,q*2-1);
            using(var b=new SolidBrush(tint))disc(r,b);
        }
        using(var concrete=new SolidBrush(cConcrete))disc(d.InnerOutside,concrete);
        using(var bore=new SolidBrush(Color.FromArgb(244,243,235)))disc(d.Inner,bore);
        // Pods on one level, each with its grey CDU and pump section at the wall end.
        for(int j=0;j<d.Bays;j++){
            double a=d.Entry+(j+.5)*2*Math.PI/d.Bays;float half=d.FrameWidth/2-.04f,tip=d.RootRadius+d.Lengths[0],body=d.RootRadius+d.CoreLength;
            PointF[] rack={local(a,d.RootRadius,-half),local(a,body,-half),local(a,body,half),local(a,d.RootRadius,half)};
            PointF[] cdu={local(a,body,-half),local(a,tip,-half),local(a,tip,half),local(a,body,half)};
            using(var b=new SolidBrush(cBronze))g.FillPolygon(b,rack);
            using(var b=new SolidBrush(cGrey))g.FillPolygon(b,cdu);
            using(var edge=new Pen(Color.FromArgb(70,74,78),1)){g.DrawPolygon(edge,rack);g.DrawPolygon(edge,cdu);}
            using(var sleeve=new Pen(Color.FromArgb(150,120,84),3.2f))g.DrawLine(sleeve,local(a,tip,0),local(a,d.InnerOutside+.45,0));
        }
        using(var deck=new SolidBrush(Color.FromArgb(226,228,216)))disc(d.RootRadius-.08,deck);
        using(var rim=new Pen(cSteel,1))g.DrawEllipse(rim,cx-m*(d.RootRadius-.08f),cy-m*(d.RootRadius-.08f),2*m*(d.RootRadius-.08f),2*m*(d.RootRadius-.08f));
        using(var steel=new SolidBrush(cSteel))disc(d.ShaftCore+.2,steel);
        // Flow. Hot water-glycol leaves each CDU through the inner wall and disperses into the store.
        double travel=tick*1.5;
        for(int j=0;j<d.Bays;j++){
            double a=d.Entry+(j+.5)*2*Math.PI/d.Bays;float mouth=d.InnerOutside+.42f;
            for(int k=-1;k<=1;k++){
                var plume=new List<PointF>();
                plume.Add(local(a,d.RootRadius+d.Lengths[0]-.25,.14));plume.Add(local(a,mouth,.14));
                for(int q=1;q<=6;q++){double u=q/6.0;plume.Add(local(a,mouth+2.5*u,.14+k*1.75*u*u+.25*u));}
                Stream(g,plume,cHot,Blend(cHot,warm,.55),3.0f,travel+k*5,8,19,true);
            }
            // The same CDU pump draws its supply from the store.
            var supply=new List<PointF>();
            supply.Add(local(a,mouth+1.5,-1.25));supply.Add(local(a,mouth+.1,-.2));supply.Add(local(a,d.RootRadius+d.Lengths[0]-.25,-.16));
            Stream(g,supply,cDrawn,cDrawn,1.9f,travel,5,14);
        }
        // Each cooler pump draws from the store. The cooled liquid returns at the outer wall and disperses.
        for(int i=0;i<d.CoolerFrames;i++){
            if(duo && d.FrameBase[i]>d.Height/2)continue;
            double a=d.FrameBearing[i];float end=d.CoolerFrameWidth/2-d.PumpLength/2;
            double wall=Math.Sqrt(d.OuterInside*d.OuterInside-end*end);
            var suction=new List<PointF>();
            suction.Add(local(a,wall-1.5,end-1.0));suction.Add(local(a,wall-.15,end));suction.Add(local(a,d.CoolerBack+.75,end));
            Stream(g,suction,cDrawn,cHot,1.9f,travel,5,14);
            var through=new List<PointF>();
            through.Add(local(a,d.CoolerBack+.75,end));through.Add(local(a,d.CoolerBack+1.5,end));
            through.Add(local(a,d.CoolerBack+1.5,-end));through.Add(local(a,d.CoolerBack+.75,-end));
            Stream(g,through,cHot,cCold,2.6f,travel,8,20);
            for(int k=-1;k<=1;k++){
                var plume=new List<PointF>();
                plume.Add(local(a,d.CoolerBack+.75,-end));plume.Add(local(a,wall-.1,-end));
                for(int q=1;q<=6;q++){double u=q/6.0;plume.Add(local(a,wall-.1-2.4*u,-end+k*1.7*u*u+.9*u));}
                Stream(g,plume,cCold,Blend(cCold,cool,.5),3.0f,travel+k*5,8,19,true);
            }
        }
        PointF door=polar(d.CoolerBack+d.CoolerFrameDepth+1.0,d.Entry);
        Rule(g,door.X-5,door.Y+10,door.X,door.Y+3,cAccent,1.4f);Rule(g,door.X+5,door.Y+10,door.X,door.Y+3,cAccent,1.4f);
        g.DrawString("GROUND ENTRY",section,muted,new PointF(door.X,door.Y+14),middleText);
        if(duo)return;
        // Labels
        {
            double hot=d.Entry+(PodNear(-.4)+.5)*2*Math.PI/d.Bays;
            Note(g,"Hot water-glycol enters the store","from "+d.Total+" CDUs, and disperses",1052,70,local(hot,d.InnerOutside+1.5,.5));
            int f=IndexNear(-1.25);float e=d.CoolerFrameWidth/2-d.PumpLength/2;
            Note(g,"Cold water-glycol enters the store","from "+(d.CoolerFrames*d.CoolerRows)+" dry coolers, and disperses",1052,206,
                local(d.FrameBearing[f],Math.Sqrt(d.OuterInside*d.OuterInside-e*e)-1.2,-e+.5));
            Note(g,"Dry cooler frame",d.CoolerRows+" coolers, "+d.CoolerRows+" pumps",1070,470,local(d.FrameBearing[IndexNear(-2.0)],d.CoolerBack+d.CoolerFrameDepth,-1.5));
        }
        Note(g,d.UnitName+" pod","4 racks, CDU and pump",452,96,local(d.Entry+(PodNear(.4)+.5)*2*Math.PI/d.Bays,d.RootRadius+3.2,0),true);
        Note(g,"Water-glycol store","between the two walls",452,470,polar((d.InnerOutside+d.OuterInside)/2,d.Entry+Math.PI+1.96),true);
        SceneHeading(g,"COOLING LOOP","Plan view","Looking down on one pod level");
        Legend(g,24,186,cHot,"Hot water-glycol");Legend(g,24,214,cCold,"Cold water-glycol");
        Legend(g,24,242,cDrawn,"Drawn from the store");
        string[] words={"Hot and cold streams both","disperse into the stored","liquid. Nothing is piped","from a cooler to a pod."};
        for(int i=0;i<words.Length;i++)g.DrawString(words[i],title2,muted,new PointF(24,286+20*i),leftText);
        Rule(g,24,382,222,382,cLine,1);g.DrawString("AT FULL LOAD",section,muted,new PointF(24,400),leftText);
        Rows(g,d.PlanRows,24,222,422,27);
    }
    // Frame nearest a bearing measured anticlockwise from straight up on the drawing, in radians.
    int IndexNear(double fromTop){
        double want=d.Entry+Math.PI+fromTop;int best=0;double score=-2;
        for(int i=0;i<d.CoolerFrames;i++){double c=Math.Cos(d.FrameBearing[i]-want);if(c>score){score=c;best=i;}}
        return best;
    }
    int PodNear(double fromTop){
        double want=d.Entry+Math.PI+fromTop;int best=0;double score=-2;
        for(int j=0;j<d.Bays;j++){double c=Math.Cos(d.Entry+(j+.5)*2*Math.PI/d.Bays-want);if(c>score){score=c;best=j;}}
        return best;
    }

    void CaptionLine(Graphics g,int frame){
        foreach(Caption line in d.Captions){
            if(frame<line.First || frame>line.Last+6)continue;
            float width=g.MeasureString(line.Text,strong,PointF.Empty,leftText).Width;
            float cx=(UiLeft+1280)/2f,y=664;
            using(var back=new SolidBrush(Color.FromArgb(236,245,244,236)))g.FillRectangle(back,cx-width/2-16,y-7,width+32,34);
            Rule(g,cx-width/2-16,y-7,cx+width/2+16,y-7,cAccent,1.4f);
            g.DrawString(line.Text,strong,ink,new PointF(cx,y),middleText);
            return;
        }
    }

    // ------------------------------------------------------------- section
    void SectionScene(Graphics g,int tick){
        bool duo=d.Short;
        if(!duo)using(var sky=new SolidBrush(Color.FromArgb(236,238,226)))g.FillRectangle(sky,UiLeft,0,1280-UiLeft,720);
        float cx=duo?1012:822,ground=duo?606:646,m=duo?11.4f:15.0f,west=duo?806:UiLeft;
        Func<double,double,PointF> at=(x,z)=>new PointF(cx+(float)(m*x),ground-(float)(m*z));
        Action<Brush,double,double,double,double> box=(b,x0,z0,x1,z1)=>g.FillRectangle(b,cx+(float)(m*Math.Min(x0,x1)),ground-(float)(m*Math.Max(z0,z1)),(float)(m*Math.Abs(x1-x0)),(float)(m*Math.Abs(z1-z0)));
        using(var soil=new SolidBrush(Color.FromArgb(206,202,176)))g.FillRectangle(soil,west,ground,1280-west,duo?26:720-ground);
        Rule(g,west,ground,1280,ground,Color.FromArgb(120,124,104),1.4f);
        double travel=tick*1.5,liquid=d.LiquidTop;
        using(var concrete=new SolidBrush(cConcrete))
        using(var water=new SolidBrush(Color.FromArgb(178,214,214)))
        using(var steel=new SolidBrush(cSteel))
        using(var bronze=new SolidBrush(cBronze))
        using(var grey=new SolidBrush(cGrey))
        using(var edge=new Pen(Color.FromArgb(70,74,78),1)){
            for(int side=-1;side<=1;side+=2){
                box(water,side*d.InnerOutside,0,side*d.OuterInside,liquid);
                if(duo){
                    // As in the plan: warm at the inner wall where the pods return, cool at the outer wall where the coolers return.
                    int bands=14;
                    for(int k=0;k<bands;k++){
                        double q=(k+.5)/bands;
                        Color tint=q<.5?Blend(Color.FromArgb(232,170,138),Color.FromArgb(206,226,214),q*2):Blend(Color.FromArgb(206,226,214),Color.FromArgb(142,190,214),q*2-1);
                        using(var b=new SolidBrush(tint))box(b,side*(d.InnerOutside+(d.OuterInside-d.InnerOutside)*k/bands),0,side*(d.InnerOutside+(d.OuterInside-d.InnerOutside)*(k+1.02)/bands),liquid);
                    }
                }
                box(concrete,side*d.Inner,0,side*d.InnerOutside,d.Height);
                box(concrete,side*d.OuterInside,0,side*d.Outer,d.Height);
            }
            // Lid, shaft and the two power levels: diesel sets below, turbine sets above.
            using(var lid=new SolidBrush(Color.FromArgb(150,158,154)))box(lid,-d.Outer-.14,d.LidZ,d.Outer+.14,d.LidZ+.24);
            box(steel,-d.ShaftCore,0,d.ShaftCore,d.Crown);
            // Walkway rings between the shaft and the pod roots.
            using(var walk=new SolidBrush(Color.FromArgb(150,160,150)))
                for(int level=0;level<d.Levels;level++)box(walk,-d.RootRadius,d.BaseZ+level*d.Pitch-.16,d.RootRadius,d.BaseZ+level*d.Pitch-.04);
            using(var floor=new SolidBrush(Color.FromArgb(96,116,118))){
                box(floor,-d.Inner+.2,d.PowerBase0-.5,d.Inner-.2,d.PowerBase0);
                box(floor,-d.Inner+.2,d.PowerBase1-.5,d.Inner-.2,d.PowerBase1);
            }
            using(var diesel=new SolidBrush(Color.FromArgb(194,165,72)))
            using(var edge2=new Pen(Color.FromArgb(90,84,60),1))
            foreach(double x in new[]{-5.0,0.0,5.0}){
                box(diesel,x-d.GenL/2*.62,d.PowerBase0,x+d.GenL/2*.62,d.PowerBase0+d.GenH);
                PointF a=at(x-d.GenL/2*.62,d.PowerBase0+d.GenH);g.DrawRectangle(edge2,a.X,a.Y,(float)(m*d.GenL*.62),(float)(m*d.GenH));
            }
            using(var set=new SolidBrush(Color.FromArgb(158,146,122)))box(set,-d.PowerLength/2,d.PowerBase1,d.PowerLength/2,d.PowerBase1+d.PowerHeight);
            using(var gen=new SolidBrush(Color.FromArgb(95,127,154)))box(gen,1.8,d.PowerBase1+.3,d.PowerLength/2-.5,d.PowerBase1+d.PowerHeight-.9);
            using(var hot=new SolidBrush(Color.FromArgb(201,138,75)))box(hot,-2.7,d.PowerBase1+.5,-.1,d.PowerBase1+d.PowerHeight-1.2);
            using(var vent=new SolidBrush(Color.FromArgb(168,184,181))){
                box(vent,d.StackX-d.ExhaustR,d.LidZ+.24,d.StackX+d.ExhaustR,d.VentTop);
                box(vent,2.6,d.LidZ+.24,3.2,d.LidZ+.24+d.DieselStackH);
            }
            using(var house=new SolidBrush(Color.FromArgb(213,216,207)))box(house,d.InletX-d.InletL/2,d.LidZ+.24,d.InletX+d.InletL/2,d.LidZ+.24+d.InletH);
            // Cooler frames: the tier on the section in full, the other tier beyond it in outline.
            float lowBase=d.Height,highBase=0;
            for(int i=0;i<d.CoolerFrames;i++){lowBase=Math.Min(lowBase,d.FrameBase[i]);highBase=Math.Max(highBase,d.FrameBase[i]);}
            float row=d.CoolerFrameHeight/d.CoolerRows;
            for(int side=-1;side<=1;side+=2){
                double x0=side*d.CoolerBack,x1=side*(d.CoolerBack+d.CoolerFrameDepth);
                using(var beyond=new Pen(Color.FromArgb(150,cSteel),1.1f)){
                    beyond.DashPattern=new float[]{4,3};
                    PointF a=at(Math.Min(x0,x1),highBase+d.CoolerFrameHeight);
                    g.DrawRectangle(beyond,a.X,a.Y,m*d.CoolerFrameDepth,m*d.CoolerFrameHeight);
                }
                using(var screen=new SolidBrush(Color.FromArgb(205,208,201)))box(screen,x0,lowBase,x1,lowBase+d.CoolerFrameHeight);
                for(int k=0;k<d.CoolerRows;k++){
                    double z=lowBase+k*row;
                    using(var cooler=new SolidBrush(Color.FromArgb(96,124,124)))box(cooler,x0+side*.35,z+.2,x1-side*.3,z+row-.2);
                    PointF fan=at(x1-side*.05,z+row/2);
                    using(var blade=new Pen(Color.FromArgb(60,84,86),2.2f))g.DrawLine(blade,fan.X,fan.Y-m*row*.33f,fan.X,fan.Y+m*row*.33f);
                }
                PointF c=at(Math.Min(x0,x1),lowBase+d.CoolerFrameHeight);
                using(var frame=new Pen(cSteel,1.4f))g.DrawRectangle(frame,c.X,c.Y,m*d.CoolerFrameDepth,m*d.CoolerFrameHeight);
            }
            // Pods on every level, both sides of the shaft.
            for(int level=0;level<d.Levels;level++)for(int side=-1;side<=1;side+=2){
                double z=d.BaseZ+level*d.Pitch,tip=d.RootRadius+d.Lengths[0],body=d.RootRadius+d.CoreLength;
                box(bronze,side*d.RootRadius,z+.05,side*body,z+d.FrameHeight-.05);
                box(grey,side*body,z+.05,side*tip,z+d.FrameHeight-.05);
                PointF a=at(side>0?d.RootRadius:-tip,z+d.FrameHeight-.05);
                g.DrawRectangle(edge,a.X,a.Y,(float)(m*(tip-d.RootRadius)),(float)(m*(d.FrameHeight-.1)));
                for(int k=1;k<4;k++){PointF p=at(side*(d.RootRadius+d.CoreLength*k/4),z+.05),q=at(side*(d.RootRadius+d.CoreLength*k/4),z+d.FrameHeight-.05);g.DrawLine(edge,p,q);}
                double port=d.PortZ+level*d.Pitch;
                using(var sleeve=new SolidBrush(Color.FromArgb(150,120,84)))box(sleeve,side*tip,port-.1,side*(d.InnerOutside+.45),port+.1);
            }
        }
        float lowTier=d.Height;for(int i=0;i<d.CoolerFrames;i++)lowTier=Math.Min(lowTier,d.FrameBase[i]);
        float rowHeight=d.CoolerFrameHeight/d.CoolerRows;
        if(duo){
            // Hot water-glycol leaves each pod through the inner wall and disperses. Cold returns at the outer wall and disperses.
            Color warm=Color.FromArgb(232,170,138),cool=Color.FromArgb(142,190,214);
            for(int level=0;level<d.Levels;level++)for(int side=-1;side<=1;side+=2){
                double tip=d.RootRadius+d.Lengths[0],port=d.PortZ+level*d.Pitch,mouth=d.InnerOutside+.42;
                for(int k=-1;k<=1;k++){
                    var plume=new List<PointF>();
                    plume.Add(at(side*(tip-.2),port+.12));plume.Add(at(side*mouth,port+.12));
                    for(int q=1;q<=6;q++){double u=q/6.0;plume.Add(at(side*(mouth+2.3*u),port+.12+k*.75*u*u+.55*u));}
                    Stream(g,plume,cHot,Blend(cHot,warm,.55),2.4f,travel+k*5,7,17,true);
                }
                var supply=new List<PointF>();
                supply.Add(at(side*(mouth+1.3),port-.95));supply.Add(at(side*(mouth+.05),port-.3));supply.Add(at(side*(tip-.2),port-.3));
                Stream(g,supply,cDrawn,cDrawn,1.6f,travel,5,14);
            }
            for(int k=0;k<d.CoolerRows;k++)for(int side=-1;side<=1;side+=2){
                double z=lowTier+k*rowHeight,wall=d.OuterInside-.1,far=d.CoolerBack+d.CoolerFrameDepth-.7;
                var suction=new List<PointF>();
                suction.Add(at(side*(wall-1.4),z+rowHeight*.72+.6));suction.Add(at(side*wall,z+rowHeight*.72));suction.Add(at(side*far,z+rowHeight*.72));
                Stream(g,suction,cDrawn,cHot,1.8f,travel,5,14);
                var through=new List<PointF>();
                through.Add(at(side*far,z+rowHeight*.72));through.Add(at(side*far,z+rowHeight*.28));through.Add(at(side*wall,z+rowHeight*.28));
                Stream(g,through,cHot,cCold,2.2f,travel,7,18);
                for(int j=-1;j<=1;j++){
                    var plume=new List<PointF>();
                    plume.Add(at(side*wall,z+rowHeight*.28));
                    for(int q=1;q<=6;q++){double u=q/6.0;plume.Add(at(side*(wall-2.3*u),z+rowHeight*.28+j*.7*u*u-.55*u));}
                    Stream(g,plume,cCold,Blend(cCold,cool,.5),2.4f,travel+j*5,7,17,true);
                }
            }
        }
        // Water-glycol: cold in from the store, over the racks, hot back out. Then out to the coolers and back cold.
        if(!duo)for(int level=0;level<d.Levels;level++)for(int side=-1;side<=1;side+=2){
            double z=d.BaseZ+level*d.Pitch,tip=d.RootRadius+d.Lengths[0],port=d.PortZ+level*d.Pitch;
            var loop=new List<PointF>();
            loop.Add(at(side*(d.InnerOutside+.9),port-.42));loop.Add(at(side*(tip-.15),port-.42));
            loop.Add(at(side*(tip-.15),z+.42));loop.Add(at(side*(d.RootRadius+.5),z+.42));
            loop.Add(at(side*(d.RootRadius+.5),z+d.FrameHeight-.42));loop.Add(at(side*(tip-.15),z+d.FrameHeight-.42));
            loop.Add(at(side*(tip-.15),port+.42));loop.Add(at(side*(d.InnerOutside+.9),port+.42));
            Stream(g,loop,cCold,cHot,2.3f,travel,7,18);
        }
        if(!duo)for(int k=0;k<d.CoolerRows;k++)for(int side=-1;side<=1;side+=2){
            double z=lowTier+k*rowHeight;
            var loop=new List<PointF>();
            loop.Add(at(side*(d.OuterInside-.9),z+rowHeight*.72));loop.Add(at(side*(d.CoolerBack+d.CoolerFrameDepth-.7),z+rowHeight*.72));
            loop.Add(at(side*(d.CoolerBack+d.CoolerFrameDepth-.7),z+rowHeight*.28));loop.Add(at(side*(d.OuterInside-.9),z+rowHeight*.28));
            Stream(g,loop,cHot,cCold,2.3f,travel,7,18);
        }
        // Convection in the store: hot rises at the inner wall, cold sinks at the outer wall.
        if(!duo)for(int side=-1;side<=1;side+=2){
            var rise=new List<PointF>();rise.Add(at(side*(d.InnerOutside+.55),1.2));rise.Add(at(side*(d.InnerOutside+.55),lowTier+d.CoolerFrameHeight-.6));
            Stream(g,rise,cHot,cHot,1.8f,travel*.7,5,26);
            var sink=new List<PointF>();sink.Add(at(side*(d.OuterInside-.5),lowTier+d.CoolerFrameHeight-.6));sink.Add(at(side*(d.OuterInside-.5),1.2));
            Stream(g,sink,cCold,cCold,1.8f,travel*.7,5,26);
        }
        // Power: from the modules down the steel shaft and out to every pod.
        var spine=new List<PointF>();spine.Add(at(4.2,d.PowerBase1+1.6));spine.Add(at(0,d.PowerBase1+1.6));spine.Add(at(0,d.BaseZ+d.FrameHeight/2));
        var standby=new List<PointF>();standby.Add(at(-3.2,d.PowerBase0+1.4));standby.Add(at(0,d.PowerBase0+1.4));
        Stream(g,standby,cPower,cPower,2.0f,travel,5,16);
        Stream(g,spine,cPower,cPower,3.4f,travel,9,20);
        for(int level=0;level<d.Levels;level++)for(int side=-1;side<=1;side+=2){
            double z=d.BaseZ+level*d.Pitch+d.FrameHeight/2;
            var feed=new List<PointF>();feed.Add(at(0,z));feed.Add(at(side*(d.RootRadius+d.CoreLength-.3),z));
            Stream(g,feed,cPower,cPower,2.4f,travel,7,18);
            Arrow(g,at(side*(d.RootRadius+d.CoreLength-.1),z),side>0?0:Math.PI,cPower,6);
        }
        // Gas: from the tanks along the ground, up the outside wall behind a cooler frame, over the lid and down.
        float farm=412,breakAt=duo?cx-m*(d.Outer+6.5f):574,tank=17,pitch=38;
        using(var shell=new SolidBrush(Color.FromArgb(233,231,220)))
        using(var edge=new Pen(Color.FromArgb(120,124,110),1.2f))
        using(var band=new Pen(Color.FromArgb(200,86,60),2))
        for(int k=0;k<(duo?0:d.TankCount);k++){
            float r=tank,x=farm+(k-(d.TankCount-1)/2f)*pitch,y=ground-r-7;
            g.FillEllipse(shell,x-r,y-r,2*r,2*r);g.DrawEllipse(edge,x-r,y-r,2*r,2*r);g.DrawArc(band,x-r+3,y-r+3,2*r-6,2*r-6,200,140);
            g.FillRectangle(Brushes.Gray,x-r*.7f,ground-7,r*1.4f,7);
        }
        float pipeY=ground-(float)(m*.45);
        if(!duo){
            g.DrawString(d.TankCount+" propane tanks",title2,ink,new PointF(farm,ground-2*tank-52),middleText);
            g.DrawString(d.TankLength.ToString("0.#")+" m long, "+d.FarmRadius.ToString("0.#")+" m from the silo",monoSmall,muted,new PointF(farm,ground-2*tank-34),middleText);
            var gas=new List<PointF>();
            gas.Add(new PointF(farm+(d.TankCount-1)/2f*pitch+tank+3,pipeY));gas.Add(new PointF(breakAt-8,pipeY));
            Stream(g,gas,cGas,cGas,3.0f,travel);
        }
        using(var slash=new Pen(cInk,1.2f)){g.DrawLine(slash,breakAt-6,pipeY+9,breakAt+2,pipeY-9);g.DrawLine(slash,breakAt+2,pipeY+9,breakAt+10,pipeY-9);}
        var line=new List<PointF>();
        line.Add(new PointF(breakAt+14,pipeY));line.Add(at(-d.RiserRadius,.45));line.Add(at(-d.RiserRadius,d.GasTop));
        line.Add(at(-d.DropR,d.GasTop));line.Add(at(-d.DropR,d.DropEnd));line.Add(at(-2.4,d.DropEnd));
        Stream(g,line,cGas,cGas,3.0f,travel+6);
        // Diesel: from the bulk tank beside the propane, along the same route, down to the day tanks.
        var oil=new List<PointF>();
        oil.Add(new PointF(breakAt+14,pipeY+7));oil.Add(at(-d.RiserRadius-.35,.2));oil.Add(at(-d.RiserRadius-.35,d.GasTop+.35));
        oil.Add(at(-d.DropR-.35,d.GasTop+.35));oil.Add(at(-d.DropR-.35,d.DieselEnd));oil.Add(at(-5.6,d.DieselEnd));
        Stream(g,oil,cDiesel,cDiesel,1.8f,travel*.5,4,15);
        if(duo)return;
        // Labels
        Note(g,"Gas turbine sets","2 x "+d.ModuleMW.ToString("0.#")+" MW, in line",1098,86,at(d.PowerLength/2-.6,d.PowerBase1+d.PowerHeight/2));
        Note(g,"Turbine exhaust stack",null,1098,40,at(d.StackX+d.ExhaustR,d.VentTop-.6));
        Note(g,"Backup diesel sets",d.DieselSets+" sets and day tanks",1098,268,at(5.0+d.GenL/2*.62,d.PowerBase0+d.GenH/2));
        Note(g,"Air inlet house","filtered air for a turbine",560,64,at(d.InletX-d.InletL/2,d.LidZ+.24+d.InletH/2),true);
        Note(g,"Power down the steel shaft","out to all "+d.Total+" pods",1098,146,at(d.RootRadius+2.2,d.BaseZ+7*d.Pitch+d.FrameHeight/2));
        Note(g,"Water-glycol over the racks","cold in, hot out",1098,206,at(d.RootRadius+3.4,d.BaseZ+6*d.Pitch+d.FrameHeight-.42));
        Note(g,"Dry coolers","draw hot, return cold",1098,360,at(d.CoolerBack+d.CoolerFrameDepth-.7,lowTier+2.5*rowHeight));
        Note(g,"Water-glycol store",null,1098,500,at((d.InnerOutside+d.OuterInside)/2+.3,3.2));
        Note(g,"Gas line","up the wall, over the lid",560,150,at(-d.RiserRadius,lowTier+d.CoolerFrameHeight+4.2),true);
        SceneHeading(g,"HOW IT WORKS","Section","Power, cooling and fuel");
        Legend(g,24,186,cPower,"Electrical power");Legend(g,24,214,cCold,"Cold water-glycol");
        Legend(g,24,242,cHot,"Hot water-glycol");Legend(g,24,270,cGas,"Propane gas");
        Legend(g,24,298,cDiesel,"Backup diesel");
        Rule(g,24,340,222,340,cLine,1);g.DrawString("AT FULL LOAD",section,muted,new PointF(24,358),leftText);
        Rows(g,d.SectionRows,24,222,380,27);
        g.DrawString("Section turned to show a",monoSmall,muted,new PointF(24,560),leftText);
        g.DrawString("lower cooler frame each side.",monoSmall,muted,new PointF(24,575),leftText);
        g.DrawString("Tank farm not to scale.",monoSmall,muted,new PointF(24,598),leftText);
    }

    // The short film's closing scene: the plan and the section side by side, with no voice-over.
    void Closing(int frame,float opacity){
        if(sheet==null)sheet=new Bitmap(W,H,PixelFormat.Format32bppArgb);
        int tick=frame-d.Full-d.Plan;
        using(Graphics g=Graphics.FromImage(sheet)){
            g.ScaleTransform(Factor,Factor);
            g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
            using(var ground=new SolidBrush(Color.FromArgb(234,236,223)))g.FillRectangle(ground,UiLeft,0,1280-UiLeft,720);
            PlanScene(g,tick);SectionScene(g,tick);
            g.DrawString("PLAN",section,accent,new PointF(516,34),middleText);
            g.DrawString("One pod level and the lower tier of cooler frames",title2,muted,new PointF(516,50),middleText);
            g.DrawString("SECTION",section,accent,new PointF(1012,34),middleText);
            g.DrawString("Power, cooling and fuel",title2,muted,new PointF(1012,50),middleText);
            float y=648;
            string[] notes={"Hot water-glycol leaves each pod through the inner wall and disperses into the store.",
                            "Each cooler pump draws from the store. The cooled liquid returns at the outer wall and disperses.",
                            "Nothing is piped from a cooler to a pod. Power comes down the steel shaft from the turbine sets."};
            for(int i=0;i<notes.Length;i++)g.DrawString(notes[i],title2,i==2?muted:ink,new PointF(764,y+20*i),middleText);
            SceneHeading(g,"HOW IT WORKS","Plan and section","Cooling, power and fuel");
            Legend(g,24,186,cHot,"Hot water-glycol");Legend(g,24,214,cCold,"Cold water-glycol");
            Legend(g,24,242,cDrawn,"Drawn from the store");Legend(g,24,270,cPower,"Electrical power");
            Legend(g,24,298,cGas,"Propane gas");Legend(g,24,326,cDiesel,"Backup diesel");
            Rule(g,24,368,222,368,cLine,1);g.DrawString("AT FULL LOAD",section,muted,new PointF(24,386),leftText);
            Rows(g,d.PlanRows,24,222,408,27);
            Rows(g,d.SectionRows,24,222,408+27*d.PlanRows.Length,27);
        }
        using(Graphics g=Graphics.FromImage(bmp))
        using(var attributes=new ImageAttributes()){
            var matrix=new ColorMatrix();matrix.Matrix33=opacity;
            attributes.SetColorMatrix(matrix);
            g.DrawImage(sheet,new Rectangle(0,0,W,H),0,0,W,H,GraphicsUnit.Pixel,attributes);
        }
    }

    // Draw a schematic over the frame already in bmp, at the given opacity.
    void Schematic(int frame,bool section,float opacity){
        if(sheet==null)sheet=new Bitmap(W,H,PixelFormat.Format32bppArgb);
        int tick=frame-d.Full-d.Plan;
        using(Graphics g=Graphics.FromImage(sheet)){
            g.ScaleTransform(Factor,Factor);
            g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
            if(section)SectionScene(g,tick);else{PlanScene(g,tick);CaptionLine(g,frame);}
        }
        using(Graphics g=Graphics.FromImage(bmp))
        using(var attributes=new ImageAttributes()){
            var matrix=new ColorMatrix();matrix.Matrix33=opacity;
            attributes.SetColorMatrix(matrix);
            g.DrawImage(sheet,new Rectangle(0,0,W,H),0,0,W,H,GraphicsUnit.Pixel,attributes);
        }
    }
}
