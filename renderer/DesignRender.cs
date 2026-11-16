using System;
using System.Drawing;
using System.Drawing.Drawing2D;

// Key design figures on the film. Every number is written by gpu_silo/calcs.py from design/project.json.
partial class Shot {
    void DesignStrip(Graphics g,int frame) {
        int since=frame-d.Full;
        if(d.Strip.Length==0 || since>=d.SealBegin && since<d.Fuel)return;
        const float height=40,right=1280-22;
        float left=UiLeft+22,top=720-22-height;
        using(var back=new SolidBrush(Color.FromArgb(238,245,244,236)))g.FillRectangle(back,left,top,right-left,height);
        Rule(g,left,top,right,top,cAccent,1.6f);
        float label=118,cell=(right-left-label)/d.Strip.Length;
        g.DrawString("DESIGN BASIS",section,accent,new PointF(left+14,top+9),leftText);
        g.DrawString(d.Title.ToUpperInvariant(),section,muted,new PointF(left+14,top+22),leftText);
        for(int i=0;i<d.Strip.Length;i++){
            float x=left+label+cell*i;
            Rule(g,x,top+8,x,top+height-8,cLine,1);
            g.DrawString(d.Strip[i].Left,strong,ink,new PointF(x+12,top+4),leftText);
            g.DrawString(d.Strip[i].Right.ToUpperInvariant(),section,muted,new PointF(x+12,top+25),leftText);
        }
    }

    // Cooler service card shown beside the pod exchange.
    void ServicePanel(Graphics g,int frame) {
        int w=frame-d.Full-d.Repair;
        if(w<d.ServiceArrive+46 || w>d.ServiceDone+40)return;
        const int x=927,y=36,wide=325,high=112;
        using(var bg=new SolidBrush(Color.FromArgb(247,246,239)))g.FillRectangle(bg,x,y,wide,high);
        Rule(g,x,y,x+wide,y,cLine,1);Rule(g,x,y+high,x+wide,y+high,cLine,1);
        g.DrawString("COOLER SERVICE",section,muted,new PointF(x+14,y+12),leftText);
        g.DrawString("Frame "+(d.ServiceFrame+1).ToString("00")+", cooler "+(d.ServiceRow+1),mono,ink,new PointF(x+wide-14,y+10),rightText);
        int step=w<d.ServiceRigged?0:w<d.ServiceDown?1:w<d.ServiceOut?2:w<d.ServiceIn?3:w<d.ServiceReleased?4:5;
        string[] phases={"Rig the frame","Lower the frame to the ground","Withdraw the cooler","Fit the replacement cooler","Hang the frame back","Frame back in service"};
        g.DrawString(phases[step],strong,step==5?ink:accent,new PointF(x+14,y+36),leftText);
        float bar=(wide-28-4*4)/5f;
        for(int i=0;i<5;i++)g.FillRectangle(i<step?waterBrush:light,x+14+i*(bar+4),y+72,bar,5);
        g.DrawString("One crane: lower, swap a cooler, rehang",monoSmall,muted,new PointF(x+14,y+88),leftText);
    }

    void FuelOverlay(Graphics g,int frame) {
        const float x=24,xr=222;
        int t=frame-d.Full,landed=0;
        for(int k=0;k<d.TankCount;k++)if(t>=d.Tanks+(k+1)*d.TankStep-2)landed++;
        string phase=t<d.Tanks?"Clear the pad":landed<d.TankCount?"Place the tanks":
            t<d.Line[3]?"Run the line to the silo":t<d.Line[5]?"Up the outside wall":
            t<d.Line[7]?"Across the lid":t<d.Line[9]?"Down to the power modules":"Fuel connected";
        g.FillRectangle(accent,x,33,25,3);g.DrawString("FUEL SUPPLY",section,muted,new PointF(x,46),leftText);
        Heading(g,"Propane",x-2,73);g.DrawString("Gas for the power modules",title2,muted,new PointF(x,126),leftText);
        Rule(g,x,164,xr,164,cLine,1);g.DrawString("TANKS PLACED",section,muted,new PointF(x,183),leftText);
        g.DrawString(landed+" / "+d.TankCount,numbers,ink,new PointF(xr,169),rightText);
        float bar=(xr-x-4*(d.TankCount-1))/d.TankCount;
        for(int i=0;i<d.TankCount;i++)g.FillRectangle(i<landed?waterBrush:light,x+(bar+4)*i,212,bar,5);
        g.DrawString(phase,strong,t>=d.Line[9]?ink:accent,new PointF(x,239),leftText);
        Rule(g,x,311,xr,311,cLine,1);g.DrawString("GAS LINE",section,muted,new PointF(x,329),leftText);
        string[] legs={"Tank header","Ground run","Riser on the wall","Across the lid","Drop to the modules"};
        for(int i=0;i<5;i++){
            float y=356+i*30;bool done=t>=d.Line[2*i+1],live=t>=d.Line[2*i] && !done;
            g.FillRectangle(done?waterBrush:live?accent:light,x,y+4,8,8);
            g.DrawString(legs[i],title2,done||live?ink:muted,new PointF(x+19,y-2),leftText);
        }
        Rule(g,x,520,xr,520,cLine,1);g.DrawString("STORAGE",section,muted,new PointF(x,538),leftText);
        Rows(g,d.FuelRows,x,xr,560,24);
    }

    void DesignOverlay(Graphics g,int frame) {
        const float x=24,xr=222;
        g.FillRectangle(accent,x,33,25,3);g.DrawString("DESIGN BASIS",section,muted,new PointF(x,46),leftText);
        Heading(g,d.Title,x-2,73);
        g.DrawString("Figures from the design file",title2,muted,new PointF(x,126),leftText);
        float y=160;
        foreach(Row row in d.Summary){
            if(row.Right.Length==0){
                Rule(g,x,y+4,xr,y+4,cLine,1);
                g.DrawString(row.Left,section,accent,new PointF(x,y+13),leftText);
                y+=32;continue;
            }
            if(row.Left.Length>0)g.DrawString(row.Left,title2,muted,new PointF(x,y),leftText);
            g.DrawString(row.Right,mono,ink,new PointF(xr,y+1),rightText);
            y+=21.5f;
        }
    }
}
