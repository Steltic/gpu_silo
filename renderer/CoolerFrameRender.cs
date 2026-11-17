using System;
using System.Drawing;
using System.Drawing.Drawing2D;

// Panels for the dry cooler frames, the water-glycol store and the pod terminal.
partial class Shot {
    int SeatedFrames(int frame) {
        int seated=0;
        for(int i=0;i<d.CoolerFrames;i++)if(frame>=d.FrameTimes[i,4])seated++;
        return seated;
    }

    void Rows(Graphics g,Row[] rows,float x,float xr,float y,float pitch) {
        foreach(Row row in rows){
            if(row.Left.Length>0)g.DrawString(row.Left,title2,muted,new PointF(x,y),leftText);
            g.DrawString(row.Right,mono,ink,new PointF(xr,y+1),rightText);
            y+=pitch;
        }
    }

    void FrameElevation(Graphics g,int connectedRows) {
        const float left=49,top=356,size=148;
        float row=size/d.CoolerRows,pump=size*d.PumpLength/d.CoolerFrameWidth;
        using(var steel=new Pen(Color.FromArgb(76,98,102),2.2f))
        using(var cool=new SolidBrush(Color.FromArgb(69,99,99)))
        using(var fan=new SolidBrush(Color.FromArgb(176,190,184)))
        using(var hub=new SolidBrush(Color.FromArgb(69,99,99)))
        using(var grey=new SolidBrush(Color.FromArgb(163,168,168)))
        using(var live=new SolidBrush(teal)){
            for(int j=0;j<d.CoolerRows;j++){
                float y=top+size-(j+1)*row;
                g.FillRectangle(cool,left+3,y+3,size-pump-5,row-6);
                float pitch=(size-pump-5)/d.CoolerFans,radius=Math.Min(row/2-6,pitch/2-3);
                for(int k=0;k<d.CoolerFans;k++){
                    float cx=left+3+pitch*(k+.5f),cy=y+row/2;
                    g.FillEllipse(fan,cx-radius,cy-radius,2*radius,2*radius);
                    g.FillEllipse(hub,cx-radius*.28f,cy-radius*.28f,radius*.56f,radius*.56f);
                }
                g.FillRectangle(grey,left+size-pump,y+5,pump-3,row-10);
                if(j<connectedRows)g.FillRectangle(live,left+size+4,y+row/2-2,7,4);
                g.DrawLine(steel,left,y,left+size,y);
            }
            g.DrawRectangle(steel,left,top,size,size);
            g.DrawLine(steel,left+size-pump-1,top,left+size-pump-1,top+size);
        }
        g.DrawString(d.CoolerFrameWidth.ToString("0.#")+" m across  ×  "+d.CoolerFrameHeight.ToString("0.#")+" m high",monoSmall,ink,new PointF(left+size/2,top+size+8),middleText);
        g.DrawString(d.CoolerFrameDepth.ToString("0.#")+" m off the wall",monoSmall,muted,new PointF(left+size/2,top+size+23),middleText);
    }

    void CoolerFrameOverlay(Graphics g,int frame) {
        const float x=24,xr=222;
        int active=0,landed=SeatedFrames(frame),count=d.CoolerFrames;
        while(active+1<count && frame>=d.FrameTimes[active+1,0])active++;
        string phase=frame<d.FrameTimes[active,1]?(active==0?"Rig the first frame":"Rig the next frame"):
            frame<d.FrameTimes[active,2]?"Hoist from laydown":
            frame<d.FrameTimes[active,3]?"Move in to the wall":
            frame<d.FrameTimes[active,4]?"Seat on cast-in anchors":
            frame<d.FrameTimes[active,6]?"Boom-lift crew connects":
            landed==count?"All frames connected":"Track to the next frame";
        g.FillRectangle(accent,x,33,25,3);Text(g,"HEAT REJECTION",section,muted,x,46);
        Heading(g,"Cooler frames",x-2,73);Text(g,"Retained crawler and boom lift",title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);Text(g,"FRAMES SEATED",section,muted,x,183);
        g.DrawString(landed+" / "+count,numbers,ink,new PointF(xr,169),rightText);
        float bar=(xr-x-4*(count-1))/count;
        for(int i=0;i<count;i++)g.FillRectangle(i<landed?waterBrush:light,x+(bar+4)*i,212,bar,5);
        Text(g,phase,strong,accent,x,239);
        float low=d.FrameBase[active];
        Text(g,"Frame "+(d.FrameOrder[active]+1).ToString("00"),title2,muted,x,277);
        g.DrawString("RL "+low.ToString("0.#")+" to "+(low+d.CoolerFrameHeight).ToString("0.#")+" m",mono,ink,new PointF(xr,277),rightText);
        Rule(g,x,311,xr,311,cLine,1);Text(g,"ONE FRAME, SEEN FROM OUTSIDE",section,muted,x,329);
        double joined=(frame-d.FrameTimes[active,4])/(double)Math.Max(1,d.FrameTimes[active,6]-d.FrameTimes[active,4]);
        FrameElevation(g,(int)Math.Round(Sat(joined)*d.CoolerRows));
        Rule(g,x,557,xr,557,cLine,1);
        Rows(g,d.FrameRows,x,xr,571,26);
        if(active==0 && frame>=d.FrameTimes[0,2] && frame<d.FrameTimes[0,7])CoolerPanel(g,frame);
    }

    void StoreOverlay(Graphics g,int frame) {
        Frame f=d.Frames[frame];
        const float x=24,xr=222;
        bool full=f.Liquid>=d.LiquidTop-.01;
        g.FillRectangle(accent,x,33,25,3);Text(g,"THERMAL STORE",section,muted,x,46);
        Heading(g,"Water-glycol",x-2,73);Text(g,"Between the concrete walls",title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);Text(g,"FILL LEVEL",section,muted,x,183);
        g.DrawString(f.Liquid.ToString("0.0")+" m",numbers,ink,new PointF(xr,169),rightText);
        g.FillRectangle(light,x,212,xr-x,5);g.FillRectangle(waterBrush,x,212,(float)((xr-x)*Sat(f.Liquid/d.LiquidTop)),5);
        Text(g,full?"Store full to the rim":"Fill to the rim",strong,full?ink:accent,x,239);
        Text(g,"Separate tank",title2,muted,x,277);g.DrawString("None",mono,ink,new PointF(xr,277),rightText);
        Rule(g,x,311,xr,311,cLine,1);Text(g,"WALL SECTION",section,muted,x,329);
        // One side of the silo. Horizontal scale is three times the vertical scale.
        const float top=362,bottom=530,inner=58;
        float metre=(bottom-top)/d.Height,wide=metre*3;
        float skinIn=(d.InnerOutside-d.Inner)*wide,gap=(d.OuterInside-d.InnerOutside)*wide,skinOut=(d.Outer-d.OuterInside)*wide;
        using(var concrete=new SolidBrush(Color.FromArgb(169,179,168))){
            g.FillRectangle(concrete,inner,top,skinIn,bottom-top);g.FillRectangle(concrete,inner+skinIn+gap,top,skinOut,bottom-top);
        }
        g.FillRectangle(light,inner+skinIn,top,gap,bottom-top);
        float level=(float)(f.Liquid*metre);
        g.FillRectangle(waterBrush,inner+skinIn,bottom-level,gap,level);
        Rule(g,inner-8,bottom,inner+skinIn+gap+skinOut+8,bottom,cInk,1);
        float edge=inner+skinIn+gap+skinOut;
        Rule(g,edge+3,top,edge+16,top,cLine,1);
        Text(g,d.Height.ToString("0.00")+" m",mono,ink,edge+20,top-7);Text(g,"Silo rim",monoSmall,muted,edge+20,top+10);
        Rule(g,edge+3,bottom-level,edge+16,bottom-level,teal,1);
        if(level>34 && level<bottom-top-30){Text(g,f.Liquid.ToString("0.00")+" m",mono,ink,edge+20,bottom-level-7);Text(g,"Liquid",monoSmall,muted,edge+20,bottom-level+10);}
        g.DrawString("bore",monoSmall,muted,new PointF(inner-6,(top+bottom)/2-6),rightText);
        Rule(g,x,557,xr,557,cLine,1);
        Rows(g,d.StoreRows,x,xr,569,24);
    }

    void TerminalOverlay(Graphics g,int frame) {
        const int x=24,xr=222;
        int t=frame-d.Terminal,landed=Math.Min(d.Cradles,d.Frames[frame].Loads[4]);
        g.FillRectangle(accent,x,33,25,3);Text(g,"GROUND LOGISTICS",section,muted,x,46);
        Heading(g,"Pod dock",x-2,73);Text(g,d.PodsPerTruck+" a truck, limited by weight",title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);Text(g,"PODS ON RAIL",section,muted,x,183);
        g.DrawString(landed+" / "+d.Cradles,numbers,ink,new PointF(xr,169),rightText);
        g.FillRectangle(light,x,211,xr-x,5);g.FillRectangle(waterBrush,x,211,(xr-x)*landed/d.Cradles,5);
        string phase=t<50?"Truck backing in":landed<d.Cradles?"Gantry unloading":"Rail transfer ready";
        Text(g,phase,strong,accent,x,239);
        Rule(g,x,300,xr,300,cLine,1);Text(g,"RECEIVING CRADLES",section,muted,x,320);
        for(int j=0;j<d.Cradles;j++){
            int y=349+30*j;
            g.FillRectangle(j<landed?waterBrush:light,x,y+2,8,8);
            Text(g,"Pod "+(j+1).ToString("000"),mono,ink,x+19,y-3);
            g.DrawString(j<landed?"On rail":"On truck",monoSmall,muted,new PointF(xr,y-1),rightText);
        }
        Rows(g,d.DockRows,x,xr,349+30*d.Cradles+6,19);
        Rule(g,x,491,xr,491,cLine,1);g.DrawString("ONE "+d.UnitName+" POD",section,muted,new PointF(x,512),leftText);
        g.DrawString(d.Lengths[0].ToString("0.00")+" m long",strong,ink,new PointF(x,538),leftText);
        g.DrawString(d.CoreLength.ToString("0.00")+" m housing, 4 GPU racks",title2,muted,new PointF(x,577),leftText);
        if(d.Lengths[0]>d.CoreLength)g.DrawString((d.Lengths[0]-d.CoreLength).ToString("0.00")+" m grey CDU and pump",title2,muted,new PointF(x,603),leftText);
        using(var bronze=new SolidBrush(Color.FromArgb(160,137,89)))
        using(var grey=new SolidBrush(Color.FromArgb(207,210,210)))
        using(var edge=new Pen(cInk,1)){
            float w=xr-x,core=w*d.CoreLength/d.Lengths[0];
            g.FillRectangle(bronze,x,640,core,22);g.FillRectangle(grey,x+core,640,w-core,22);g.DrawRectangle(edge,x,640,w,22);
            for(int k=1;k<4;k++)g.DrawLine(edge,x+core*k/4,640,x+core*k/4,662);
        }
        g.DrawString("shaft end",monoSmall,muted,new PointF(x,668),leftText);
        g.DrawString("wall end",monoSmall,muted,new PointF(xr,668),rightText);
    }
}
