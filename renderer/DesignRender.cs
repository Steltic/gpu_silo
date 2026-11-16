using System;
using System.Drawing;
using System.Drawing.Drawing2D;

// Key design figures on the film. Every number is written by gpu_silo/calcs.py from design/project.json.
partial class Shot {
    void DesignStrip(Graphics g,int frame) {
        if(d.Strip.Length==0 || frame-d.Full>=d.SealBegin)return;
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
