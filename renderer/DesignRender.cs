using System;
using System.Drawing;
using System.Drawing.Drawing2D;

// Key design figures on the film. Every number is written by gpu_silo/calcs.py from design/project.json.
partial class Shot {
    void DesignStrip(Graphics g,int frame) {
        int since=frame-d.Full;
        if(d.Strip.Length==0 || since>=d.SealBegin && since<d.Fuel || since>=d.FinalBegin)return;
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

    // The short film names the panel for each scene instead of working it out from the long film's clock.
    void ShortOverlay(Graphics g,int frame) {
        int kind=3,card=0;
        foreach(Scene scene in d.Scenes)if(frame>=scene.First && frame<scene.Last){kind=scene.Kind;card=scene.Card;}
        if(Ghosted(frame))ShellEdges(g);
        if(kind==2)TerminalOverlay(g,frame);
        else if(kind==4)CoolerFrameOverlay(g,frame);
        else if(kind==5)FuelOverlay(g,frame);
        else if(kind==6)CardOverlay(g,frame,d.Cards[card]);
        else if(kind==8)PowerOverlay(g,frame);
        else if(kind==11){DesignOverlay(g,frame);ProgrammeChart(g);}
        else StorageOverlay(g,frame);
        ProgrammeTag(g,frame);
        if(kind!=11)DesignStrip(g,frame);
    }

    // A plain panel for a scene: what it is, the step in hand and a few figures.
    void CardOverlay(Graphics g,int frame,Card card) {
        const float x=24,xr=222;
        g.FillRectangle(accent,x,33,25,3);g.DrawString(card.Kicker,section,muted,new PointF(x,46),leftText);
        Heading(g,card.Heading,x-2,73);g.DrawString(card.Sub,title2,muted,new PointF(x,126),leftText);
        Rule(g,x,164,xr,164,cLine,1);
        int now=0;
        for(int i=0;i<card.Steps.Length;i++)if(frame>=card.Steps[i].At)now=i;
        float bar=(xr-x-4*(card.Steps.Length-1))/card.Steps.Length;
        for(int i=0;i<card.Steps.Length;i++)g.FillRectangle(i<now?waterBrush:i==now?accent:light,x+(bar+4)*i,186,bar,5);
        g.DrawString(card.Steps[now].Text,strong,now==card.Steps.Length-1?ink:accent,new PointF(x,206),leftText);
        Rule(g,x,262,xr,262,cLine,1);
        Rows(g,card.Rows,x,xr,282,27);
        UtilityReadouts(g,d.Frames[frame],false,frame);
    }

    // Where the scene falls in the 28-day programme, with the running truck counts.
    void ProgrammeTag(Graphics g,int frame) {
        Tag tag=null;
        foreach(Tag item in d.Tags)if(frame>=item.First && frame<item.Last)tag=item;
        if(tag==null)return;
        string note=tag.Note;
        if(tag.Counters.Length>0)note=note.Replace("{a}",d.Frames[frame].Loads[tag.Counters[0]].ToString());
        if(tag.Counters.Length>1)note=note.Replace("{b}",d.Frames[frame].Loads[tag.Counters[1]].ToString());
        string day=tag.Day.StartsWith("DAY")?tag.Day+" OF "+d.ProgrammeDays:tag.Day;
        const float x=UiLeft+185,y=22;
        float wide=Math.Max(g.MeasureString(tag.Title,title2,PointF.Empty,leftText).Width,g.MeasureString(note,monoSmall,PointF.Empty,leftText).Width);
        wide=Math.Max(wide,g.MeasureString(day,section,PointF.Empty,leftText).Width)+26;
        float high=note.Length>0?58:42;
        using(var back=new SolidBrush(Color.FromArgb(238,245,244,236)))g.FillRectangle(back,x,y,wide,high);
        g.FillRectangle(accent,x,y,3,high);
        g.DrawString(day,section,accent,new PointF(x+13,y+6),leftText);
        g.DrawString(tag.Title,title2,ink,new PointF(x+13,y+19),leftText);
        if(note.Length>0)g.DrawString(note,monoSmall,muted,new PointF(x+13,y+39),leftText);
    }

    // The crew on a typical lift and the concrete it places.
    void CrewPanel(Graphics g,int frame) {
        const int x=1016,wide=236;
        int high=44+d.CrewRows.Length*16,y=720-22-40-12-high;
        using(var bg=new SolidBrush(Color.FromArgb(247,246,239)))g.FillRectangle(bg,x,y,wide,high);
        Rule(g,x,y,x+wide,y,cLine,1);Rule(g,x,y+high,x+wide,y+high,cLine,1);
        g.DrawString("CREW ON A TYPICAL LIFT",section,muted,new PointF(x+14,y+12),leftText);
        g.DrawString(d.LiftCrew.ToString(),mono,ink,new PointF(x+wide-14,y+10),rightText);
        float row=y+33;
        foreach(Row item in d.CrewRows){
            g.DrawString(item.Left,monoSmall,muted,new PointF(x+14,row),leftText);
            g.DrawString(item.Right,monoSmall,ink,new PointF(x+wide-14,row),rightText);
            row+=16;
        }
    }

    // The programme as a bar chart, shown with the finished silo.
    void ProgrammeChart(Graphics g) {
        const int x=862,y=36,wide=390,label=200;
        int first=0,last=d.ProgrammeDays;
        foreach(Bar bar in d.Programme)first=Math.Min(first,bar.First);
        int high=62+d.Programme.Length*16;
        using(var bg=new SolidBrush(Color.FromArgb(247,246,239)))g.FillRectangle(bg,x,y,wide,high);
        Rule(g,x,y,x+wide,y,cLine,1);Rule(g,x,y+high,x+wide,y+high,cLine,1);
        g.DrawString(d.ProgrammeDays+"-DAY PROGRAMME",section,muted,new PointF(x+14,y+12),leftText);
        g.DrawString("Day 0 is the last pour",monoSmall,muted,new PointF(x+wide-14,y+11),rightText);
        float left=x+14+label,right=x+wide-16,scale=(right-left)/(last-first+1);
        float top=y+48;
        foreach(int day in new[]{0,7,14,21,d.ProgrammeDays}){
            float at=left+(day-first)*scale;
            Rule(g,at,top-6,at,top+d.Programme.Length*16,day==0?cInk:cLine,day==0?1.1f:.8f);
            g.DrawString(day.ToString(),monoSmall,muted,new PointF(at,top-20),middleText);
        }
        float row=top;
        foreach(Bar bar in d.Programme){
            g.DrawString(bar.Name,monoSmall,ink,new PointF(x+14,row),leftText);
            float a=left+(bar.First-first)*scale,b=left+(bar.Last-first+1)*scale;
            g.FillRectangle(bar.Last<=0?(Brush)muted:bar.First>=d.ProgrammeDays?accent:waterBrush,a,row+3,Math.Max(3,b-a),8);
            row+=16;
        }
    }

    // The gas turbine inside the lower power module, shown while its side is folded down.
    void TurbinePanel(Graphics g) {
        const int x=927,y=36,wide=325,high=150;
        using(var bg=new SolidBrush(Color.FromArgb(247,246,239)))g.FillRectangle(bg,x,y,wide,high);
        Rule(g,x,y,x+wide,y,cLine,1);Rule(g,x,y+high,x+wide,y+high,cLine,1);
        g.DrawString("TURBINE SET A",section,muted,new PointF(x+14,y+12),leftText);
        g.DrawString(d.ModuleMW.ToString("0.#")+" MW gas turbine",strong,accent,new PointF(x+14,y+34),leftText);
        Rows(g,d.TurbineRows,x+14,x+wide-14,y+66,16);
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
        for(int k=0;k<d.TankCount;k++)if(t>=d.Tanks+k*d.TankStep+d.TankSettle)landed++;
        string phase=t<d.Tanks?"Clear the pad":landed<d.TankCount?"Place the tanks":
            t<d.Line[3]?"Run the line to the silo":t<d.Line[5]?"Up the outside wall":
            t<d.Line[7]?"Across the lid":t<d.Line[9]?"Down to the power levels":"Fuel connected";
        g.FillRectangle(accent,x,33,25,3);g.DrawString("FUEL SUPPLY",section,muted,new PointF(x,46),leftText);
        Heading(g,"Fuel",x-2,73);g.DrawString("Propane and backup diesel",title2,muted,new PointF(x,126),leftText);
        Rule(g,x,164,xr,164,cLine,1);g.DrawString("TANKS PLACED",section,muted,new PointF(x,183),leftText);
        g.DrawString(landed+" / "+d.TankCount,numbers,ink,new PointF(xr,169),rightText);
        float bar=(xr-x-4*(d.TankCount-1))/d.TankCount;
        for(int i=0;i<d.TankCount;i++)g.FillRectangle(i<landed?waterBrush:light,x+(bar+4)*i,212,bar,5);
        g.DrawString(phase,strong,t>=d.Line[9]?ink:accent,new PointF(x,239),leftText);
        Rule(g,x,311,xr,311,cLine,1);g.DrawString("FUEL LINES",section,muted,new PointF(x,329),leftText);
        string[] legs={"Tank header","Buried crossing","Riser on the wall","Across the lid","Drops to the power levels"};
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
