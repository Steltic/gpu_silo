using System;
using System.Drawing;

partial class Shot {
    static readonly string[][] ProductLabels={
        new[]{"Fixed steel shaft","Base anchors","Sliding collar"},
        new[]{"Rack 02","Side truss","Coolant unit"},
        new[]{"Coil and axial fans","Carrier frame","Pump module"},
        new[]{"25 MW turbine set","Rail girder","Bearing shoe"}
    };

    void StudioGround(Frame f,int index){
        double unit=new double[]{2,.5,1,2}[index];
        double centreX=f.Target.X,centreY=f.Target.Y,ground=index==0?-2.1:-.35;
        double extent=unit*12,stroke=unit*.009;
        for(int i=-12;i<=12;i++){
            double off=i*unit;
            V a=View(new V(centreX+off,centreY-extent,ground)),b=View(new V(centreX+off,centreY+extent,ground));
            V c=View(new V(centreX+off+stroke,centreY+extent,ground)),e=View(new V(centreX+off+stroke,centreY-extent,ground));
            alpha=i==0?57:29;Clipped(a,b,c,0x82989a);Clipped(a,c,e,0x82989a);
            a=View(new V(centreX-extent,centreY+off,ground));b=View(new V(centreX+extent,centreY+off,ground));
            c=View(new V(centreX+extent,centreY+off+stroke,ground));e=View(new V(centreX-extent,centreY+off+stroke,ground));
            Clipped(a,b,c,0x82989a);Clipped(a,c,e,0x82989a);
        }
        double rx=new double[]{3,4.4,2.8,8.8}[index],ry=new double[]{2,.95,6.9,6.9}[index];
        V origin=View(new V(centreX,centreY,ground+.01));
        for(int ring=1;ring<=9;ring++){
            double k=1.25-ring*.071;
            alpha=10;
            for(int i=0;i<40;i++){
                double a=i*Math.PI/20,b=(i+1)*Math.PI/20;
                Clipped(origin,View(new V(centreX+Math.Cos(a)*rx*k,centreY+Math.Sin(a)*ry*k,ground+.01)),
                    View(new V(centreX+Math.Cos(b)*rx*k,centreY+Math.Sin(b)*ry*k,ground+.01)),0x0e242d);
            }
        }
        alpha=255;
    }

    void ProductLeaders(Graphics g,int frame,int index){
        int length=(d.SealBegin-d.Crew)/4;
        int elapsed=frame-(d.Full+d.Crew+index*length);
        if(elapsed<60 || elapsed>length-46)return;
        using(var pen=new Pen(Color.FromArgb(165,165,202,198),1))
        using(var text=new SolidBrush(Color.FromArgb(225,233,221)))
        using(var dot=new SolidBrush(Color.FromArgb(225,178,104))){
            foreach(Node n in d.Nodes){
                if(n.Kind<30 || n.Kind>32 || n.WorldPose.S.X<.5)continue;
                int label=n.Kind-30; V pos=Screen(View(n.WorldPose.T));
                float px=(float)pos.X/Factor,py=(float)pos.Y/Factor;
                if(px<UiLeft || px>1270 || py<16 || py>650)continue;
                bool left=label==1;
                float ex=left?280:1250,ey=label==0?129:label==1?515:365;
                if(index==0 && label==2)ey=88;
                float knee=left?ex+118:ex-120;
                g.DrawLines(pen,new[]{new PointF(px,py),new PointF(knee,ey),new PointF(ex,ey)});
                g.FillEllipse(dot,px-2.5f,py-2.5f,5,5);
                g.DrawString(ProductLabels[index][label],monoSmall,text,new PointF(ex,ey-16),left?leftText:rightText);
            }
        }
    }
}
