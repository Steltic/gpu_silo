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
    readonly Color cDiesel=Color.FromArgb(150,74,54);
    readonly Color cConcrete=Color.FromArgb(152,162,154),cSteel=Color.FromArgb(76,98,102),cBronze=Color.FromArgb(160,137,89),cGrey=Color.FromArgb(207,210,210);
    Bitmap sheet;

    static Color Blend(Color a,Color b,double t){
        t=Sat(t);return Color.FromArgb((int)(a.R+(b.R-a.R)*t),(int)(a.G+(b.G-a.G)*t),(int)(a.B+(b.B-a.B)*t));
    }

    // Dashes travel along the path from its first point to its last.
    void Stream(Graphics g,IList<PointF> path,Color from,Color to,float width,double travel,float dash=9,float period=22){
        var run=new double[path.Count];
        for(int i=1;i<path.Count;i++)run[i]=run[i-1]+Math.Sqrt(Math.Pow(path[i].X-path[i-1].X,2)+Math.Pow(path[i].Y-path[i-1].Y,2));
        double total=run[path.Count-1];if(total<1)return;
        using(var guide=new Pen(Color.FromArgb(55,Blend(from,to,.5)),width+2.2f)){guide.LineJoin=LineJoin.Round;g.DrawLines(guide,ToArray(path));}
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
            using(var pen=new Pen(Blend(from,to,along),width)){
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

    void RiserMark(Graphics g,PointF p,Color colour){
        using(var fill=new SolidBrush(Color.White))g.FillEllipse(fill,p.X-3,p.Y-3,6,6);
        using(var edge=new Pen(colour,1.8f))g.DrawEllipse(edge,p.X-3,p.Y-3,6,6);
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
        Color store=Color.FromArgb(213,226,221);
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
        // The plan locates riser pairs. The temperature layers are shown in section.
        using(var concrete=new SolidBrush(cConcrete))disc(d.Outer,concrete);
        using(var water=new SolidBrush(store))disc(d.OuterInside,water);
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
        double travel=tick*1.5;
        for(int j=0;j<d.Bays;j++){
            double a=d.Entry+(j+.5)*2*Math.PI/d.Bays,tip=d.RootRadius+d.Lengths[0]-.25;
            PointF take=local(a,d.PodRiser,-d.PodOffset),give=local(a,d.PodRiser,d.PodOffset);
            Stream(g,new[]{take,local(a,tip,-.18)},cCold,cCold,2.2f,travel,5,12);
            Stream(g,new[]{local(a,tip,.18),give},cHot,cHot,2.2f,travel,5,12);
            RiserMark(g,take,cCold);RiserMark(g,give,cHot);
        }
        for(int i=0;i<d.CoolerFrames;i++){
            if(duo && d.FrameBase[i]>d.Height/2)continue;
            double a=d.FrameBearing[i],end=d.CoolerFrameWidth/2-d.PumpLength/2;
            PointF take=polar(d.CoolerRiser,a+d.CoolerSuctionAngle),give=polar(d.CoolerRiser,a+d.CoolerReturnAngle);
            PointF inlet=local(a,d.CoolerBack+1.5,end),outlet=local(a,d.CoolerBack+1.5,-end);
            Stream(g,new[]{take,inlet},cHot,cHot,2.2f,travel,6,14);
            Stream(g,new[]{inlet,outlet},cHot,cCold,2.5f,travel,8,18);
            Stream(g,new[]{outlet,give},cCold,cCold,2.2f,travel,6,14);
            RiserMark(g,take,cHot);RiserMark(g,give,cCold);
        }
        PointF door=polar(d.CoolerBack+d.CoolerFrameDepth+1.0,d.Entry);
        Rule(g,door.X-5,door.Y+10,door.X,door.Y+3,cAccent,1.4f);Rule(g,door.X+5,door.Y+10,door.X,door.Y+3,cAccent,1.4f);
        g.DrawString("GROUND ENTRY",section,muted,new PointF(door.X,door.Y+14),middleText);
        if(duo)return;
        // Labels
        {
            double hot=d.Entry+(PodNear(-.4)+.5)*2*Math.PI/d.Bays;
            Note(g,"Pod return riser","warm liquid to the top",1052,70,local(hot,d.PodRiser,d.PodOffset));
            int f=IndexNear(-1.25);
            Note(g,"Cooler return riser","cool liquid to the bottom",1052,206,
                polar(d.CoolerRiser,d.FrameBearing[f]+d.CoolerReturnAngle));
            Note(g,"Dry cooler frame",d.CoolerRows+" coolers, "+d.CoolerRows+" pumps",1070,470,local(d.FrameBearing[IndexNear(-2.0)],d.CoolerBack+d.CoolerFrameDepth,-1.5));
        }
        Note(g,d.UnitName+" pod","4 racks, CDU and pump",452,96,local(d.Entry+(PodNear(.4)+.5)*2*Math.PI/d.Bays,d.RootRadius+3.2,0),true);
        Note(g,"Water-glycol store","between the two walls",452,470,polar((d.InnerOutside+d.OuterInside)/2,d.Entry+Math.PI+1.96),true);
        SceneHeading(g,"COOLING LOOP","Plan view","Looking down on one pod level");
        Legend(g,24,186,cHot,"Hot water-glycol");Legend(g,24,214,cCold,"Cold water-glycol");
        RiserMark(g,new PointF(40,250),cSteel);g.DrawString("Vertical pipe",title2,ink,new PointF(68,242),leftText);
        string[] words={"Each pod bay and cooler","frame has two risers.","One opens at the top,","one at the bottom."};
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
        using(var water=new LinearGradientBrush(at(0,liquid),at(0,0),Color.White,Color.White))
        using(var steel=new SolidBrush(cSteel))
        using(var bronze=new SolidBrush(cBronze))
        using(var grey=new SolidBrush(cGrey))
        using(var edge=new Pen(Color.FromArgb(70,74,78),1)){
            Color warm=Color.FromArgb(233,177,149),cool=Color.FromArgb(151,195,218);
            water.InterpolationColors=new ColorBlend{Colors=new[]{warm,warm,cool,cool},Positions=new[]{0f,.45f,.55f,1f}};
            for(int side=-1;side<=1;side+=2){
                box(water,side*d.InnerOutside,0,side*d.OuterInside,liquid);
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
        // Project the two pipes of each pair slightly apart so that both paths can be followed.
        double podCold=d.PodRiser-.23,podHot=d.PodRiser+.23,coolerCold=d.CoolerRiser-.23,coolerHot=d.CoolerRiser+.23;
        for(int side=-1;side<=1;side+=2){
            Func<double,double,PointF> wall=(r,z)=>at(side*r,z);
            double first=d.PortZ,last=first+(d.Levels-1)*d.Pitch;
            double lowTap=lowTier+rowHeight*.28,highTap=lowTier+(d.CoolerRows-1+.72)*rowHeight;
            Stream(g,new[]{wall(podCold,d.BottomMouth),wall(podCold,last-.35)},cCold,cCold,2,travel);
            Stream(g,new[]{wall(podHot,first+.35),wall(podHot,d.TopMouth)},cHot,cHot,2,travel);
            Stream(g,new[]{wall(coolerHot,d.TopMouth),wall(coolerHot,lowTier+rowHeight*.72)},cHot,cHot,2,travel);
            Stream(g,new[]{wall(coolerCold,highTap-rowHeight*.44),wall(coolerCold,d.BottomMouth)},cCold,cCold,2,travel);
            // Horizontal plates at the open ends discharge or collect sideways.
            foreach(double r in new[]{podHot,coolerHot,podCold,coolerCold}){
                bool upper=r==podHot || r==coolerHot;
                double height=upper?d.TopMouth+d.DiffuserGap:d.BottomMouth-d.DiffuserGap;
                using(var plate=new Pen(cSteel,1.8f))g.DrawLine(plate,wall(r-d.Diffuser,height),wall(r+d.Diffuser,height));
            }
            for(int level=0;level<d.Levels;level++){
                double z=d.BaseZ+level*d.Pitch,tip=d.RootRadius+d.Lengths[0]-.15,port=first+level*d.Pitch;
                double rack=d.RootRadius+.5;
                var loop=new[]{wall(podCold,port-.35),wall(tip,port-.35),wall(tip,z+.42),wall(rack,z+.42),
                               wall(rack,z+d.FrameHeight-.42),wall(tip,z+d.FrameHeight-.42),wall(tip,port+.35),wall(podHot,port+.35)};
                Stream(g,loop,cCold,cHot,duo?1.5f:2.3f,travel,7,18);
            }
            for(int k=0;k<d.CoolerRows;k++){
                double low=lowTap+k*rowHeight,high=low+rowHeight*.44,fan=d.CoolerBack+d.CoolerFrameDepth-.7;
                Stream(g,new[]{wall(coolerHot,high),wall(fan,high),wall(fan,low),wall(coolerCold,low)},cHot,cCold,2.3f,travel,7,18);
            }
        }
        // Medium voltage drops down the shaft to grade. Transformers feed the fixed bay risers.
        var spine=new List<PointF>();spine.Add(at(4.2,d.PowerBase1+1.6));spine.Add(at(0,d.PowerBase1+1.6));spine.Add(at(0,-.6));
        var standby=new List<PointF>();standby.Add(at(-3.2,d.PowerBase0+1.4));standby.Add(at(0,d.PowerBase0+1.4));
        Stream(g,standby,cPower,cPower,2.0f,travel,5,16);
        Stream(g,spine,cPower,cPower,3.4f,travel,9,20);
        for(int side=-1;side<=1;side+=2){
            double riser=side*(d.Outer+.35);
            Stream(g,new[]{at(0,-.6),at(riser,-.6),at(riser,d.BaseZ+(d.Levels-1)*d.Pitch+d.FrameHeight/2-.42)},cPower,cPower,2.1f,travel,6,18);
            for(int level=0;level<d.Levels;level++){
                double z=d.BaseZ+level*d.Pitch+d.FrameHeight/2-.42;
                var end=at(side*(d.RootRadius+d.CoreLength-.2),z);
                Stream(g,new[]{at(riser,z),end},cPower,cPower,2.1f,travel,6,18);
                Arrow(g,end,side>0?Math.PI:0,cPower,6);
            }
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
        float pipeY=ground+(float)(m*1.4);
        if(!duo){
            g.DrawString(d.TankCount+" propane tanks",title2,ink,new PointF(farm,ground-2*tank-52),middleText);
            g.DrawString(d.TankLength.ToString("0.#")+" m long, "+d.FarmRadius.ToString("0.#")+" m from the silo",monoSmall,muted,new PointF(farm,ground-2*tank-34),middleText);
            var gas=new List<PointF>();
            gas.Add(new PointF(farm+(d.TankCount-1)/2f*pitch+tank+3,pipeY));gas.Add(new PointF(breakAt-8,pipeY));
            Stream(g,gas,cGas,cGas,3.0f,travel);
        }
        using(var slash=new Pen(cInk,1.2f)){g.DrawLine(slash,breakAt-6,pipeY+9,breakAt+2,pipeY-9);g.DrawLine(slash,breakAt+2,pipeY+9,breakAt+10,pipeY-9);}
        var line=new List<PointF>();
        line.Add(new PointF(breakAt+14,pipeY));line.Add(at(-d.RiserRadius,-1.4));line.Add(at(-d.RiserRadius,d.GasTop));
        line.Add(at(-d.DropR,d.GasTop));line.Add(at(-d.DropR,d.DropEnd));line.Add(at(-2.4,d.DropEnd));
        Stream(g,line,cGas,cGas,3.0f,travel+6);
        // Diesel: from the bulk tank beside the propane, along the same route, down to the day tanks.
        var oil=new List<PointF>();
        oil.Add(new PointF(breakAt+14,pipeY+7));oil.Add(at(-d.RiserRadius-.35,-1.4));oil.Add(at(-d.RiserRadius-.35,d.GasTop+.35));
        oil.Add(at(-d.DropR-.35,d.GasTop+.35));oil.Add(at(-d.DropR-.35,d.DieselEnd));oil.Add(at(-5.6,d.DieselEnd));
        Stream(g,oil,cDiesel,cDiesel,1.8f,travel*.5,4,15);
        if(duo)return;
        // Labels
        Note(g,"Gas turbine sets","2 x "+d.ModuleMW.ToString("0.#")+" MW, in line",1098,86,at(d.PowerLength/2-.6,d.PowerBase1+d.PowerHeight/2));
        Note(g,"Turbine exhaust stack",null,1098,40,at(d.StackX+d.ExhaustR,d.VentTop-.6));
        Note(g,"Backup diesel sets",d.DieselSets+" sets and day tanks",1098,268,at(5.0+d.GenL/2*.62,d.PowerBase0+d.GenH/2));
        Note(g,"Air inlet house","filtered air for a turbine",560,64,at(d.InletX-d.InletL/2,d.LidZ+.24+d.InletH/2),true);
        Note(g,"13.8 kV down the shaft","via grade transformers",1098,146,at(d.Outer+.35,d.BaseZ+7*d.Pitch+d.FrameHeight/2-.42));
        Note(g,"Water-glycol over the racks","cold in, hot out",1098,206,at(d.RootRadius+3.4,d.BaseZ+6*d.Pitch+d.FrameHeight-.42));
        Note(g,"Dry coolers","draw hot, return cold",1098,360,at(d.CoolerBack+d.CoolerFrameDepth-.7,lowTier+2.5*rowHeight));
        Note(g,"Cool lower layer","warm liquid above",1098,500,at((d.InnerOutside+d.OuterInside)/2,3.2));
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
            string[] notes={"Pod pumps draw from the cool lower layer and return warm liquid to the upper layer.",
                            "Dry coolers draw from the upper layer and return cooled liquid to the bottom.",
                            "Diffuser plates spread the flow sideways at each pipe opening."};
            for(int i=0;i<notes.Length;i++)g.DrawString(notes[i],title2,i==2?muted:ink,new PointF(764,y+20*i),middleText);
            SceneHeading(g,"HOW IT WORKS","Plan and section","Cooling, power and fuel");
            Legend(g,24,186,cHot,"Hot water-glycol");Legend(g,24,214,cCold,"Cold water-glycol");
            RiserMark(g,new PointF(40,250),cSteel);g.DrawString("Vertical pipe",title2,ink,new PointF(68,242),leftText);
            Legend(g,24,270,cPower,"Electrical power");
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
