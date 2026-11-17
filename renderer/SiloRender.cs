using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Drawing.Text;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;

// Small depth-buffer renderer. The movie reads exactly the mesh instances and
// transform curves used to create the editable glTF animation.
struct V {
    public double X,Y,Z;
    public V(double x,double y,double z) { X=x;Y=y;Z=z; }
    public static V operator +(V a,V b) {return new V(a.X+b.X,a.Y+b.Y,a.Z+b.Z);}
    public static V operator -(V a,V b) {return new V(a.X-b.X,a.Y-b.Y,a.Z-b.Z);}
    public static V operator *(V a,double b) {return new V(a.X*b,a.Y*b,a.Z*b);}
    public double Dot(V b) {return X*b.X+Y*b.Y+Z*b.Z;}
    public V Cross(V b) {return new V(Y*b.Z-Z*b.Y,Z*b.X-X*b.Z,X*b.Y-Y*b.X);}
    public V Unit() {double n=Math.Sqrt(Dot(this)); return n>1e-12 ? this*(1/n) : new V(0,0,1);}
}
struct Tri {public V A,B,C,N;public Color Co;}
class Mesh {public Tri[] Ts;public bool Land;public int Mat;}
struct Pose {public V T,S;public double A;}
class Node {public int M,Parent,Kind;public double Sin,Cos;public Pose[] Transform;public Pose WorldPose;}
class Frame {public V Eye,Target;public double Fov,Height,Plan,U,Theta,Bunch,PodZ,Feed,HookZ,RackZ,Liquid,Dock;
    public int Lift,Pod,Level,Stored,Ports,Online,Fixings;public bool End;public string Phase,LoadPhase;public int[] Loads;}
class Row {public string Left,Right;}
class Caption {public int First,Last;public string Text;}
class Tag {public int First,Last;public string Day,Title,Note;public int[] Counters;}
class Bar {public string Name;public int First,Last;}
class Scene {public int First,Last,Kind,Card;}
class Step {public int At;public string Text;}
class Card {public string Kicker,Heading,Sub;public Row[] Rows;public Step[] Steps;}
class Data {
    public Mesh[] Meshes;public Node[] Nodes;public Frame[] Frames;public int Fps;
    public float Outer,OuterInside,InnerOutside,Inner,Height,Lift;
    public int Count,LastPour,Closed,RevealEnd;
    public int BuildEnd,Ghost,FirstPod,Full,Fast,Pick1,Pick2,PickDuration,VentBegin,VentEnd,LidBegin,LidEnd;
    public int SealBegin,SealEnd,OrbitBegin,OrbitEnd;
    public int Crew,Repair,Fault,FaultLevel,FaultBay;
    public int Levels,Bays,Total,CrewCount;
    public float Pitch,BaseZ,CoreLength,FrameWidth,FrameHeight,OpeningWidth,OpeningHeight,FastRate,RootRadius,PowerWidth,PowerHeight,PowerLength,StackX;
    public float ShaftRadius,PowerBase0,PowerBase1,VentTop,LidZ,PortZ,PowerYaw,Entry;
    public float[] Lengths; public string UnitName,Title; public int[] WorkLevels;
    // Dry cooler frames: installation clock, geometry and the order in which they are placed.
    public int StoreStart,StoreFillBegin,StoreFillEnd,Terminal,CoolerStart,CoolerFirst,CoolerEnd,CoolerFrames,CoolerRows,CoolerFans;
    // Cooler service during the pod exchange, and the closing scenes.
    public int ServiceFrame,ServiceRow,ServiceArrive,ServiceRigged,ServiceDown,ServiceOut,ServiceIn,ServiceReleased,ServiceDone;
    public int Fuel,Tanks,TankStep,FuelEnd,Plan,PlanFrames,Section,SectionFrames,Fade,TankCount;
    public int Enc0,Enc1,Enc2,Enc3,FinalBegin,FinalEnd,DieselSets;
    public float ModuleMW,SetY,GenL,GenH,Level0,ExhaustR,InletL,InletH,InletX,DieselStackH,DieselEnd,DropR,ShaftCore;
    public Row[] TurbineRows,BackupRows,CrewRows,DockRows;public Tag[] Tags;public Bar[] Programme;
    public int ProgrammeDays,LiftCrew,Cradles,PodsPerTruck,TankSettle,Counters;
    public bool Short;public Scene[] Scenes;public Card[] Cards;public Color Liner;
    public int[] Line=new int[10];
    public float FuelBearing,FarmRadius,TankLength,TankDiameter,TankPitch,RiserRadius,GasTop,DropRadius,DropEnd;
    public Row[] FuelRows,PlanRows,SectionRows;public Caption[] Captions;
    public float CoolerFrameWidth,CoolerFrameHeight,CoolerFrameDepth,CoolLength,PumpLength,CoolerBack,CoolerMW;
    public int[] FrameOrder;public int[,] FrameTimes;public float[] FrameBase,FrameBearing;
    public float Crown,LiquidTop;
    public Row[] Strip,Summary,StoreRows,FrameRows;
    static V Vec(BinaryReader r){return new V(r.ReadSingle(),r.ReadSingle(),r.ReadSingle());}
    static string Str(BinaryReader r){return System.Text.Encoding.UTF8.GetString(r.ReadBytes(r.ReadInt32()));}
    static Row[] Rows(BinaryReader r){
        var rows=new Row[r.ReadInt32()];
        for(int i=0;i<rows.Length;i++){rows[i]=new Row();rows[i].Left=Str(r);rows[i].Right=Str(r);}
        return rows;
    }
    static void Set(Node n,int i,int prop,V val){
        if(prop==0)n.Transform[i].T=val;
        else if(prop==1)n.Transform[i].S=val;
        else n.Transform[i].A=val.X;
    }
    static void ReadCurve(BinaryReader r,Node n,int nf,int prop){
        int count=r.ReadInt32();if(count==0)return;
        int prev=r.ReadInt32();V v=prop==2?new V(r.ReadSingle(),0,0):Vec(r);
        for(int i=0;i<=prev;i++)Set(n,i,prop,v);
        for(int j=1;j<count;j++){
            int next=r.ReadInt32();V w=prop==2?new V(r.ReadSingle(),0,0):Vec(r);
            for(int i=prev+1;i<=next;i++)Set(n,i,prop,v+(w-v)*((i-prev)/(double)(next-prev)));
            prev=next;v=w;
        }
        for(int i=prev+1;i<nf;i++)Set(n,i,prop,v);
    }
    public Data(string file){
        using(var r=new BinaryReader(File.OpenRead(file))){
            if (System.Text.Encoding.ASCII.GetString(r.ReadBytes(8))!="GSILO06\0") throw new InvalidDataException("Unknown scene");
            int nm=r.ReadInt32(),nn=r.ReadInt32(),nf=r.ReadInt32(); Fps=r.ReadInt32();
            Outer=r.ReadSingle();OuterInside=r.ReadSingle();InnerOutside=r.ReadSingle();Inner=r.ReadSingle();
            Height=r.ReadSingle();Lift=r.ReadSingle();
            Count=r.ReadInt32();LastPour=r.ReadInt32();Closed=r.ReadInt32();RevealEnd=r.ReadInt32();
            BuildEnd=r.ReadInt32();Ghost=r.ReadInt32();FirstPod=r.ReadInt32();Full=r.ReadInt32();Fast=r.ReadInt32();
            Pick1=r.ReadInt32();Pick2=r.ReadInt32();PickDuration=r.ReadInt32();VentBegin=r.ReadInt32();VentEnd=r.ReadInt32();
            LidBegin=r.ReadInt32();LidEnd=r.ReadInt32();
            SealBegin=r.ReadInt32();SealEnd=r.ReadInt32();OrbitBegin=r.ReadInt32();OrbitEnd=r.ReadInt32();
            Crown=r.ReadSingle();LiquidTop=r.ReadSingle();
            Crew=r.ReadInt32();Repair=r.ReadInt32();
            Fault=r.ReadInt32();FaultLevel=r.ReadInt32();FaultBay=r.ReadInt32();
            Levels=r.ReadInt32(); Bays=r.ReadInt32(); Total=r.ReadInt32();
            Pitch=r.ReadSingle(); BaseZ=r.ReadSingle(); CoreLength=r.ReadSingle(); FrameWidth=r.ReadSingle(); FrameHeight=r.ReadSingle();
            OpeningWidth=r.ReadSingle(); OpeningHeight=r.ReadSingle(); FastRate=r.ReadSingle();
            Lengths=new float[Total]; for(int j=0;j<Total;j++)Lengths[j]=r.ReadSingle();
            UnitName=Str(r); RootRadius=r.ReadSingle(); PowerWidth=r.ReadSingle(); PowerHeight=r.ReadSingle();
            PowerLength=r.ReadSingle(); StackX=r.ReadSingle();
            ShaftRadius=r.ReadSingle();PowerBase0=r.ReadSingle();PowerBase1=r.ReadSingle();VentTop=r.ReadSingle();
            LidZ=r.ReadSingle();PortZ=r.ReadSingle();PowerYaw=r.ReadSingle();Entry=r.ReadSingle(); CrewCount=r.ReadInt32();
            WorkLevels=new int[Bays]; for(int j=0;j<Bays;j++)WorkLevels[j]=r.ReadInt32();
            StoreStart=r.ReadInt32();StoreFillBegin=r.ReadInt32();StoreFillEnd=r.ReadInt32();Terminal=r.ReadInt32();
            CoolerStart=r.ReadInt32();CoolerFirst=r.ReadInt32();CoolerEnd=r.ReadInt32();
            CoolerFrames=r.ReadInt32();CoolerRows=r.ReadInt32();CoolerFans=r.ReadInt32();
            CoolerFrameWidth=r.ReadSingle();CoolerFrameHeight=r.ReadSingle();CoolerFrameDepth=r.ReadSingle();
            CoolLength=r.ReadSingle();PumpLength=r.ReadSingle();CoolerBack=r.ReadSingle();CoolerMW=r.ReadSingle();
            FrameOrder=new int[CoolerFrames];FrameTimes=new int[CoolerFrames,8];FrameBase=new float[CoolerFrames];FrameBearing=new float[CoolerFrames];
            for(int i=0;i<CoolerFrames;i++){
                FrameOrder[i]=r.ReadInt32();for(int k=0;k<8;k++)FrameTimes[i,k]=r.ReadInt32();
                FrameBase[i]=r.ReadSingle();FrameBearing[i]=r.ReadSingle();
            }
            ServiceFrame=r.ReadInt32();ServiceRow=r.ReadInt32();ServiceArrive=r.ReadInt32();ServiceRigged=r.ReadInt32();ServiceDown=r.ReadInt32();
            ServiceOut=r.ReadInt32();ServiceIn=r.ReadInt32();ServiceReleased=r.ReadInt32();ServiceDone=r.ReadInt32();
            Fuel=r.ReadInt32();Tanks=r.ReadInt32();TankStep=r.ReadInt32();for(int k=0;k<10;k++)Line[k]=r.ReadInt32();
            FuelEnd=r.ReadInt32();Plan=r.ReadInt32();PlanFrames=r.ReadInt32();Section=r.ReadInt32();SectionFrames=r.ReadInt32();
            Fade=r.ReadInt32();TankCount=r.ReadInt32();
            FuelBearing=r.ReadSingle();FarmRadius=r.ReadSingle();TankLength=r.ReadSingle();TankDiameter=r.ReadSingle();TankPitch=r.ReadSingle();
            RiserRadius=r.ReadSingle();GasTop=r.ReadSingle();DropRadius=r.ReadSingle();DropEnd=r.ReadSingle();
            Enc0=r.ReadInt32();Enc1=r.ReadInt32();Enc2=r.ReadInt32();Enc3=r.ReadInt32();FinalBegin=r.ReadInt32();FinalEnd=r.ReadInt32();DieselSets=r.ReadInt32();
            ModuleMW=r.ReadSingle();SetY=r.ReadSingle();GenL=r.ReadSingle();GenH=r.ReadSingle();Level0=r.ReadSingle();ExhaustR=r.ReadSingle();InletL=r.ReadSingle();
            InletH=r.ReadSingle();InletX=r.ReadSingle();DieselStackH=r.ReadSingle();DieselEnd=r.ReadSingle();DropR=r.ReadSingle();ShaftCore=r.ReadSingle();
            Title=Str(r);Strip=Rows(r);Summary=Rows(r);StoreRows=Rows(r);FrameRows=Rows(r);
            FuelRows=Rows(r);PlanRows=Rows(r);SectionRows=Rows(r);TurbineRows=Rows(r);BackupRows=Rows(r);
            Captions=new Caption[r.ReadInt32()];
            for(int i=0;i<Captions.Length;i++){Captions[i]=new Caption();Captions[i].First=r.ReadInt32();Captions[i].Last=r.ReadInt32();Captions[i].Text=Str(r);}
            CrewRows=Rows(r);DockRows=Rows(r);
            ProgrammeDays=r.ReadInt32();LiftCrew=r.ReadInt32();Cradles=r.ReadInt32();PodsPerTruck=r.ReadInt32();
            Programme=new Bar[r.ReadInt32()];
            for(int i=0;i<Programme.Length;i++){Programme[i]=new Bar();Programme[i].Name=Str(r);Programme[i].First=r.ReadInt32();Programme[i].Last=r.ReadInt32();}
            Tags=new Tag[r.ReadInt32()];
            for(int i=0;i<Tags.Length;i++){
                Tag tag=Tags[i]=new Tag();tag.First=r.ReadInt32();tag.Last=r.ReadInt32();tag.Day=Str(r);tag.Title=Str(r);tag.Note=Str(r);
                tag.Counters=new int[r.ReadInt32()];for(int k=0;k<tag.Counters.Length;k++)tag.Counters[k]=r.ReadInt32();
            }
            Short=r.ReadInt32()!=0;TankSettle=r.ReadInt32();Counters=r.ReadInt32();
            Scenes=new Scene[r.ReadInt32()];
            for(int i=0;i<Scenes.Length;i++){Scenes[i]=new Scene();Scenes[i].First=r.ReadInt32();Scenes[i].Last=r.ReadInt32();Scenes[i].Kind=r.ReadInt32();Scenes[i].Card=r.ReadInt32();}
            Cards=new Card[r.ReadInt32()];
            for(int i=0;i<Cards.Length;i++){
                Card card=Cards[i]=new Card();card.Kicker=Str(r);card.Heading=Str(r);card.Sub=Str(r);card.Rows=Rows(r);
                card.Steps=new Step[r.ReadInt32()];
                for(int k=0;k<card.Steps.Length;k++){card.Steps[k]=new Step();card.Steps[k].At=r.ReadInt32();card.Steps[k].Text=Str(r);}
            }
            Liner=ColorTranslator.FromHtml(Str(r));
            Meshes=new Mesh[nm];Nodes=new Node[nn];Frames=new Frame[nf];
            for(int i=0;i<nm;i++){
                Mesh m=Meshes[i]=new Mesh();m.Ts=new Tri[r.ReadInt32()]; m.Land=r.ReadInt32()!=0;m.Mat=r.ReadInt32();
                for(int j=0;j<m.Ts.Length;j++){
                    Tri t=new Tri(); t.A=Vec(r); t.B=Vec(r); t.C=Vec(r);
                    t.N=(t.B-t.A).Cross(t.C-t.A).Unit();
                    t.Co=Color.FromArgb(r.ReadByte(),r.ReadByte(),r.ReadByte());m.Ts[j]=t;
                }
            }
            for(int i=0;i<nn;i++){
                Node n=Nodes[i]=new Node();n.M=r.ReadInt32();n.Parent=r.ReadInt32();n.Kind=r.ReadInt32();
                Pose rest=new Pose{T=Vec(r),S=Vec(r),A=r.ReadSingle()};
                n.Transform=new Pose[nf];
                for(int j=0;j<nf;j++)n.Transform[j]=rest;
                for(int p=0;p<3;p++)ReadCurve(r,n,nf,p);
            }
            for(int i=0;i<nf;i++){
                Frame f=Frames[i]=new Frame();f.Eye=Vec(r);f.Target=Vec(r);f.Fov=r.ReadSingle();
                f.Height=r.ReadSingle();f.Plan=r.ReadSingle();f.Lift=r.ReadInt32();f.End=r.ReadInt32()!=0;
                f.Phase=Str(r);
                f.Pod=r.ReadInt32();f.Level=r.ReadInt32();f.Stored=r.ReadInt32();
                f.U=r.ReadSingle();f.Theta=r.ReadSingle();f.Bunch=r.ReadSingle();f.PodZ=r.ReadSingle();
                f.Feed=r.ReadSingle();f.HookZ=r.ReadSingle();f.RackZ=r.ReadSingle();f.LoadPhase=Str(r);
                f.Liquid=r.ReadSingle();f.Dock=r.ReadSingle();f.Ports=r.ReadInt32();f.Online=r.ReadInt32();
                f.Fixings=r.ReadInt32();
                f.Loads=new int[Counters];for(int k=0;k<Counters;k++)f.Loads[k]=r.ReadInt32();
            }
        }
    }
}

partial class Shot {
    public const int W=1920,H=1080;
    const int Left=369;
    const int UiLeft=246;
    const float Factor=1.5f;
    const double Near=.15;
    readonly Data d; readonly int[] pixels=new int[W*H]; readonly float[] depth=new float[W*H];
    readonly int[] alternate=new int[W*H];
    readonly int[] underEquipment=new int[W*H];
    int alpha=255;
    readonly List<int> podNodes=new List<int>();
    readonly List<int> serviceNodes=new List<int>();
    readonly List<int> coolers=new List<int>();
    readonly List<int> decks=new List<int>();
    int replacement,hook,replacementPlug;
    readonly List<Node> nearEquipment=new List<Node>();
    Bitmap coolerInset;
    readonly Color teal=Color.FromArgb(46,110,102);
    readonly Brush waterBrush=new SolidBrush(Color.FromArgb(62,146,151));
    int cachedFrame=-2;
    int[] siteColors;float[] siteDepth;
    bool softShadow,cachedSoft;
    V eye,forward,up,right;double focal,centerX,centerY;
    double shadowHeight;
    readonly V sun=new V(-.52,-.47,.79).Unit();
    readonly Bitmap bmp=new Bitmap(W,H,PixelFormat.Format32bppRgb);
    // The first installed family in each list is used, so the film keeps its layout on Windows, Linux and macOS.
    static readonly string[] Serif={"Georgia","Gelasio","Liberation Serif","Times New Roman","DejaVu Serif"};
    static readonly string[] Sans={"Segoe UI","Inter","Helvetica Neue","Liberation Sans","DejaVu Sans"};
    static readonly string[] SansBold={"Segoe UI Semibold","Inter SemiBold","Inter Semi Bold","Inter","Liberation Sans","DejaVu Sans"};
    static readonly string[] Figures={"Bahnschrift","Inter Display","Inter","Liberation Sans","DejaVu Sans"};
    static readonly string[] Fixed={"Consolas","DejaVu Sans Mono","Liberation Mono","Menlo","Courier New"};
    static Font Face(string[] names,float size,FontStyle style=FontStyle.Regular){
        foreach(string name in names){
            try{
                var family=new FontFamily(name);
                if(string.Equals(family.Name,name,StringComparison.OrdinalIgnoreCase) && family.IsStyleAvailable(style))
                    return new Font(family,size,style,GraphicsUnit.Pixel);
            }catch(ArgumentException){}
        }
        return new Font(FontFamily.GenericSansSerif,size,style,GraphicsUnit.Pixel);
    }
    readonly Font title1=Face(Serif,32);
    readonly Font title2=Face(Sans,14);
    readonly Font section=Face(Sans,10,FontStyle.Bold);
    readonly Font strong=Face(SansBold,18);
    readonly Font numbers=Face(Figures,27);
    readonly Font mono=Face(Fixed,13);
    readonly Font monoSmall=Face(Fixed,11);
    readonly Brush paper=new SolidBrush(Color.FromArgb(245,244,236)),
        ink=new SolidBrush(Color.FromArgb(42,53,45)), muted=new SolidBrush(Color.FromArgb(88,101,88)),
        accent=new SolidBrush(Color.FromArgb(172,91,45)), light=new SolidBrush(Color.FromArgb(231,230,216)),
        white=new SolidBrush(Color.FromArgb(247,247,238));
    readonly Color cInk=Color.FromArgb(57,70,59),cLine=Color.FromArgb(201,205,188),
        cAccent=Color.FromArgb(175,95,48);
    readonly StringFormat leftText=(StringFormat)StringFormat.GenericTypographic.Clone();
    readonly StringFormat rightText=(StringFormat)StringFormat.GenericTypographic.Clone();
    readonly StringFormat middleText=(StringFormat)StringFormat.GenericTypographic.Clone();
    public Shot(Data data){
        d=data;rightText.Alignment=StringAlignment.Far;middleText.Alignment=StringAlignment.Center;
        for(int i=0;i<d.Nodes.Length;i++)if(d.Nodes[i].Kind==2)podNodes.Add(i);
        for(int i=0;i<d.Nodes.Length;i++)if(d.Nodes[i].Kind==3)serviceNodes.Add(i);
        for(int i=0;i<d.Nodes.Length;i++)if(d.Nodes[i].Kind==4)coolers.Add(i);
        for(int i=0;i<d.Nodes.Length;i++){
            if(d.Nodes[i].Kind==6)decks.Add(i);
            if(d.Nodes[i].Kind==7)replacement=i;
            if(d.Nodes[i].Kind==11)hook=i;
            if(d.Nodes[i].Kind==12)replacementPlug=i;
        }
    }
    static int Clamp(int a,int b,int c){return Math.Min(c,Math.Max(b,a));}
    static double Sat(double c){return Math.Min(1,Math.Max(0,c));}
    static int Pack(int r,int g,int b){return (r<<16)|(g<<8)|b;}
    static int MixColor(int original,int tint,double t){
        int r=(original>>16)&255,g=(original>>8)&255,b=original&255;
        return Pack((int)(r+(((tint>>16)&255)-r)*t),(int)(g+(((tint>>8)&255)-g)*t),
                    (int)(b+((tint&255)-b)*t));
    }
    V World(V p,Node n,Pose pose){
        double x=p.X*pose.S.X,y=p.Y*pose.S.Y;
        return new V(pose.T.X+x*n.Cos-y*n.Sin,pose.T.Y+x*n.Sin+y*n.Cos,pose.T.Z+p.Z*pose.S.Z);
    }
    void UpdateWorld(int frame){
        foreach(Node n in d.Nodes){
            Pose p=n.Transform[frame];
            if(n.Parent>=0){
                Node parent=d.Nodes[n.Parent];Pose q=parent.WorldPose;
                p.T=World(p.T,parent,q);p.A+=q.A;p.S=new V(p.S.X*q.S.X,p.S.Y*q.S.Y,p.S.Z*q.S.Z);
            }
            n.WorldPose=p;n.Sin=Math.Sin(p.A);n.Cos=Math.Cos(p.A);
        }
    }
    V View(V p){V v=p-eye;return new V(v.Dot(right),v.Dot(up),v.Dot(forward));}
    V Screen(V v){double iz=1/v.Z;return new V(centerX+focal*v.X*iz,centerY-focal*v.Y*iz,iz);}
    static V Intersect(V a,V b){return a+(b-a)*((Near-a.Z)/(b.Z-a.Z));}
    void Clipped(V a,V b,V c,int col){
        bool ai=a.Z>=Near,bi=b.Z>=Near,ci=c.Z>=Near;
        if(ai && bi && ci){Raster(Screen(a),Screen(b),Screen(c),col);return;}
        if(!ai && !bi && !ci) return;
        if(bi && !ai && !ci){Clipped(b,c,a,col);return;}
        if(ci && !bi && !ai){Clipped(c,a,b,col);return;}
        if(ai && !bi && !ci){Raster(Screen(a),Screen(Intersect(a,b)),Screen(Intersect(a,c)),col);return;}
        if(!ai && bi && ci){Clipped(b,c,a,col);return;}
        if(ai && !bi && ci){Clipped(c,a,b,col);return;}
        V e1=Screen(Intersect(b,c)),e2=Screen(Intersect(a,c)),sa=Screen(a),sb=Screen(b);
        Raster(sa,sb,e1,col);Raster(sa,e1,e2,col);
    }
    void Raster(V a,V b,V c,int col){
        double miny=Math.Min(a.Y,Math.Min(b.Y,c.Y)),maxy=Math.Max(a.Y,Math.Max(b.Y,c.Y));
        double minx=Math.Min(a.X,Math.Min(b.X,c.X)),maxx=Math.Max(a.X,Math.Max(b.X,c.X));
        if(maxy<0 || miny>=H || maxx<Left || minx>=W) return;
        double det=(b.X-a.X)*(c.Y-a.Y)-(c.X-a.X)*(b.Y-a.Y);
        if(Math.Abs(det)<1e-7)return;
        double izx=((b.Z-a.Z)*(c.Y-a.Y)-(c.Z-a.Z)*(b.Y-a.Y))/det;
        double izy=((b.X-a.X)*(c.Z-a.Z)-(c.X-a.X)*(b.Z-a.Z))/det;
        if(a.Y>b.Y){V t=a;a=b;b=t;} if(b.Y>c.Y){V t=b;b=c;c=t;} if(a.Y>b.Y){V t=a;a=b;b=t;}
        if(c.Y-a.Y<1e-8)return;
        double dxlong=(c.X-a.X)/(c.Y-a.Y);
        double dxupper=(b.X-a.X)/Math.Max(1e-9,b.Y-a.Y),dxlower=(c.X-b.X)/Math.Max(1e-9,c.Y-b.Y);
        int lo=Clamp((int)Math.Ceiling(a.Y-.5),0,H),hi=Clamp((int)Math.Ceiling(c.Y-.5),0,H);
        for(int y=lo;y<hi;y++){
            double yy=y+.5,xx1=a.X+(yy-a.Y)*dxlong;
            double xx2=yy<b.Y ? a.X+(yy-a.Y)*dxupper : b.X+(yy-b.Y)*dxlower;
            if(xx2<xx1){double t=xx1;xx1=xx2;xx2=t;}
            int x0=Clamp((int)Math.Ceiling(xx1-.5),Left,W),x1=Clamp((int)Math.Ceiling(xx2-.5),Left,W);
            double z=a.Z+izx*(x0+.5-a.X)+izy*(yy-a.Y);
            int offset=y*W;
            for(int x=x0;x<x1;x++,z+=izx){
                int i=offset+x;
                if(z>depth[i]){
                    if(alpha==255){depth[i]=(float)z;pixels[i]=col;}
                    else pixels[i]=MixColor(pixels[i],col,alpha/255.0);
                }
            }
        }
    }
    int Shade(Tri t,Node node,double dist){
        double nx=t.N.X*node.Cos-t.N.Y*node.Sin,ny=t.N.X*node.Sin+t.N.Y*node.Cos,nz=t.N.Z;
        double direct=Math.Max(0,nx*sun.X+ny*sun.Y+nz*sun.Z);
        double value=.72+.34*direct+.06*Math.Max(0,nz);
        int rr=Clamp((int)(t.Co.R*value*1.017),0,255);
        int gg=Clamp((int)(t.Co.G*value*1.013),0,255);
        int bb=Clamp((int)(t.Co.B*(.93*value+.07)),0,255);
        int color=Pack(rr,gg,bb);
        double haze=Math.Min(.91,Math.Max(0,(dist-60)/335));
        return haze>0?MixColor(color,Pack(219,224,209),haze):color;
    }
    void DrawNode(Node n,int frame){
        Pose pose=n.WorldPose;if(n.M<0 || pose.S.X<.0001 || pose.S.Z<.0001)return;
        foreach(Tri q in d.Meshes[n.M].Ts){
            V a=World(q.A,n,pose),b=World(q.B,n,pose),c=World(q.C,n,pose);
            // Skip camera-backfacing polygons for all opaque closed pieces.
            double nx=q.N.X*n.Cos-q.N.Y*n.Sin,ny=q.N.X*n.Sin+q.N.Y*n.Cos;
            if(nx*(eye.X-a.X)+ny*(eye.Y-a.Y)+q.N.Z*(eye.Z-a.Z)<-.00001) continue;
            V va=View(a),vb=View(b),vc=View(c);
            if(va.Z<Near && vb.Z<Near && vc.Z<Near)continue;
            Clipped(va,vb,vc,Shade(q,n,(va.Z+vb.Z+vc.Z)/3));
        }
    }
    void Shadows(){
        double height=Math.Max(.2,shadowHeight);
        double sx=-sun.X/sun.Z*height,sy=-sun.Y/sun.Z*height;
        double len2=sx*sx+sy*sy;
        for(int y=0;y<H;y++){
            double py=(centerY-y-.5)/focal;
            double rz=forward.Z+up.Z*py;
            if(rz>-.003)continue;
            double t=-eye.Z/rz;
            if(t>170)continue;
            double shift=(Left+.5-centerX)/focal;
            double dx=right.X*t/focal,dy=right.Y*t/focal;
            double gx=eye.X+t*(forward.X+up.X*py+right.X*shift);
            double gy=eye.Y+t*(forward.Y+up.Y*py+right.Y*shift);
            for(int x=Left;x<W;x++,gx+=dx,gy+=dy){
                double extent=d.Outer+2;
                if(gx< -extent||gy< -extent||gx>sx+extent||gy>sy+extent)continue;
                double u=Sat((gx*sx+gy*sy)/Math.Max(len2,.01));
                double px=gx-u*sx,py2=gy-u*sy,dist=Math.Sqrt(px*px+py2*py2);
                double dark=(softShadow?.12:.27)*Sat((d.Outer+.85-dist)/1.40);
                if(dark>0){int i=y*W+x;pixels[i]=MixColor(pixels[i],Pack(50,63,59),dark);}
            }
        }
    }
    void Sky(){
        Array.Clear(depth,0,depth.Length);
        double horizon=centerY+focal*forward.Z/up.Z;
        for(int y=0;y<H;y++){
            double k=Math.Exp(-Math.Max(0,horizon-y)*11/H);
            int col=MixColor(Pack(143,177,186),Pack(220,225,211),k);
            int start=y*W+Left;
            for(int i=start;i<(y+1)*W;i++)pixels[i]=col;
        }
    }
    void Text(Graphics g,string label,Font font,Brush brush,float x,float y){
        label=System.Text.RegularExpressions.Regex.Replace(label,@"\bpod(s?)\b",m=>d.UnitName+(m.Groups[1].Length>0?"s":""),System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        g.DrawString(label,font,brush,new PointF(x,y),leftText);
    }
    // Panel headings shrink to the panel width when a fallback typeface runs wider than the reference one.
    void Heading(Graphics g,string label,float x,float y){
        label=System.Text.RegularExpressions.Regex.Replace(label,@"\bpod(s?)\b",m=>d.UnitName+(m.Groups[1].Length>0?"s":""),System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        float width=g.MeasureString(label,title1,PointF.Empty,leftText).Width,room=UiLeft-x-14;
        if(width<=room){g.DrawString(label,title1,ink,new PointF(x,y),leftText);return;}
        using(var smaller=new Font(title1.FontFamily,title1.Size*room/width,title1.Style,GraphicsUnit.Pixel))
            g.DrawString(label,smaller,ink,new PointF(x,y+(title1.Size-smaller.Size)*.62f),leftText);
    }
    void Rule(Graphics g,float x0,float y0,float x1,float y1,Color co,float width){
        using(var pen=new Pen(co,width)){g.DrawLine(pen,x0,y0,x1,y1);}
    }
    void Plan(Graphics g){
        float cx=122,cy=445,r=66;
        using(var brush1=new SolidBrush(cInk)){
            float[] walls={d.Outer,d.OuterInside,d.InnerOutside,d.Inner};
            for(int j=0;j<4;j+=2){
                float rr=r*walls[j]/d.Outer;
                g.FillEllipse(brush1,cx-rr,cy-rr,rr*2,rr*2);
                float r2=r*walls[j+1]/d.Outer;
                g.FillEllipse(paper,cx-r2,cy-r2,2*r2,2*r2);
            }
        }
        // Dashed centrelines and a dimension witness for the outside diameter.
        using(var p=new Pen(Color.FromArgb(183,190,170),.72f)){
            p.DashPattern=new float[]{4f,4f};
            g.DrawLine(p,cx-r-7,cy,cx+r+7,cy);g.DrawLine(p,cx,cy-r-7,cx,cy+r+7);
        }
        float angle=-.77f,cs=(float)Math.Cos(angle),ss=(float)Math.Sin(angle);
        float a=r*d.OuterInside/d.Outer,b=r*d.InnerOutside/d.Outer;
        Rule(g,cx+cs*a,cy+ss*a,cx+cs*b,cy+ss*b,cAccent,2.0f);
        float midR=(a+b)/2,ex=cx+cs*midR,ey=cy+ss*midR;
        Rule(g,ex,ey,182,384,cAccent,1);
        Rule(g,181.5f,384,211,384,cAccent,1);
        g.DrawString((d.OuterInside-d.InnerOutside).ToString("0.##")+" m clear",monoSmall,accent,new PointF(216,369),rightText);
        float yd=527;
        Rule(g,cx-r,cy+r*.38f,cx-r,yd+4,cLine,.8f);
        Rule(g,cx+r,cy+r*.38f,cx+r,yd+4,cLine,.8f);
        Rule(g,cx-r,yd,cx+r,yd,cInk,.8f);
        Rule(g,cx-r-2.7f,yd+3,cx-r+2.7f,yd-3,cInk,1);
        Rule(g,cx+r-2.7f,yd+3,cx+r+2.7f,yd-3,cInk,1);
        g.DrawString((2*d.Outer).ToString("0.##")+" m OD",mono,ink,new PointF(cx,yd+6),middleText);
    }
    PointF Project(V world){
        V p=Screen(View(world));return new PointF((float)p.X/Factor,(float)p.Y/Factor);
    }
    void Dimensions(Graphics g,int frame){
        Frame f=d.Frames[frame];
        if(f.End && f.Plan>.93){
            V horizontal=new V(forward.X,forward.Y,0).Unit();
            V radial=(right*.87+horizontal*.50).Unit();
            PointF a=Project(radial*d.InnerOutside+new V(0,0,d.Height));
            PointF b=Project(radial*d.OuterInside+new V(0,0,d.Height));
            float mx=(a.X+b.X)*.5f,my=(a.Y+b.Y)*.5f;
            Rule(g,a.X,a.Y,b.X,b.Y,cAccent,1.5f);
            Rule(g,a.X-1.5f,a.Y-3,a.X+1.5f,a.Y+3,cAccent,1.4f);
            Rule(g,b.X-1.5f,b.Y-3,b.X+1.5f,b.Y+3,cAccent,1.4f);
            Rule(g,mx,my,mx+35,my-36,cAccent,1.2f);
            Rule(g,mx+35,my-36,mx+54,my-36,cAccent,1.2f);
            g.FillRectangle(paper,mx+54,my-49,104,25);
            Text(g,(d.OuterInside-d.InnerOutside).ToString("0.00")+" m clear",mono,ink,mx+62,my-44);
        }
        if(f.Lift==1 && (f.Phase=="Jump the forms" || f.Phase=="Reset for next pour")){
            V at=right*(d.Outer+1.85);
            PointF a=Project(at),b=Project(at+new V(0,0,d.Lift));
            Rule(g,a.X,a.Y,b.X,b.Y,cInk,1.35f);
            Rule(g,b.X,b.Y,b.X-3,b.Y+6,cInk,1.35f);
            Rule(g,b.X,b.Y,b.X+3,b.Y+6,cInk,1.35f);
            Rule(g,a.X-3,a.Y,a.X+3,a.Y,cInk,1.35f);
            float mid=(a.Y+b.Y)*.5f;
            g.FillRectangle(paper,b.X+7,mid-11,95,24);
            Text(g,d.Lift.ToString("0.0")+" m jump",mono,ink,b.X+14,mid-6);
        }
    }
    void LevelPlan(Graphics g,int frame,int level,bool installation){
        Frame f=d.Frames[frame];float cx=122,cy=448,rad=80;
        int first=(d.Levels-level)*d.Bays;double angle=-37*Math.PI/180;
        Func<double,double,PointF> plan=(u,v)=>new PointF(cx+(float)((-Math.Sin(angle)*u+Math.Cos(angle)*v)*rad/d.Inner),
            cy+(float)((Math.Cos(angle)*u+Math.Sin(angle)*v)*rad/d.Inner));
        using(var pen=new Pen(Color.FromArgb(139,160,146),1))g.DrawEllipse(pen,cx-rad,cy-rad,2*rad,2*rad);
        using(var pen=new Pen(Color.FromArgb(188,199,181),.92f))g.DrawEllipse(pen,cx-rad-4,cy-rad-4,2*rad+8,2*rad+8);
        double actualPitch=(d.Nodes[podNodes[first+1]].WorldPose.A-d.Nodes[podNodes[first]].WorldPose.A)*180/Math.PI;
        if(!installation && level>f.Level && actualPitch<44.8 && frame<d.Full){
            double pitch=actualPitch*Math.PI/180;
            double corridor=(2*Math.PI-7*pitch)*.5-.345;
            double mid=d.Nodes[podNodes[first]].WorldPose.A-(Math.PI-3.5*pitch);
            var lane=new List<PointF>();lane.Add(new PointF(cx,cy));
            for(int i=0;i<=28;i++){
                double a=mid-corridor+2*corridor*i/28;
                lane.Add(plan(5.88*Math.Cos(a),5.88*Math.Sin(a)));
            }
            using(var br=new SolidBrush(Color.FromArgb(218,232,215)))g.FillPolygon(br,lane.ToArray());
        }
        using(var track=new Pen(Color.FromArgb(204,206,185),.8f)){
            g.DrawEllipse(track,cx-rad*.137f,cy-rad*.137f,rad*.274f,rad*.274f);
            g.DrawEllipse(track,cx-rad*.966f,cy-rad*.966f,rad*1.932f,rad*1.932f);
        }
        for(int k=0;k<d.Bays;k++){
            int index=first+k;Node pod=d.Nodes[podNodes[index]];
            double a=installation?angle+Math.PI*2*k/d.Bays:pod.WorldPose.A;
            double ca=Math.Cos(a),sa=Math.Sin(a);
            bool stored=!installation && index<f.Stored;
            bool moving=!installation && index==f.Pod && f.Stored==index && f.Feed>.995;
            double root=d.RootRadius,tip=root+d.Lengths[index],half=d.FrameWidth/2; double[] xs={root,tip,tip,root},ys={-half,-half,half,half};
            PointF[] points=new PointF[4];
            for(int i=0;i<4;i++)points[i]=plan(xs[i]*ca-ys[i]*sa,xs[i]*sa+ys[i]*ca);
            if(stored || moving){
                using(var br=new SolidBrush(stored?Color.FromArgb(111,128,125):Color.FromArgb(182,138,87)))
                    g.FillPolygon(br,points);
            }
            using(var pen=new Pen(stored?Color.FromArgb(68,90,87):moving?cAccent:Color.FromArgb(202,205,188),.9f))g.DrawPolygon(pen,points);
        }
        for(int j=0;j<d.Bays;j++){
            double a=angle+(j+.5)*2*Math.PI/d.Bays;
            PointF socket=plan(d.Inner*Math.Cos(a),d.Inner*Math.Sin(a));
            bool live=false;
            for(int k=0;k<d.Bays;k++){
                Node svc=d.Nodes[serviceNodes[first+k]];
                if(svc.WorldPose.S.X>.995 && Math.Cos(svc.WorldPose.A-a)>.99995)live=true;
            }
            using(var br=new SolidBrush(live?teal:Color.FromArgb(177,177,145)))
                g.FillEllipse(br,socket.X-2.0f,socket.Y-2.0f,4,4);
        }
        using(var br=new SolidBrush(Color.FromArgb(58,83,78)))g.FillEllipse(br,cx-7.7f,cy-7.7f,15.4f,15.4f);
        if(!installation && frame<d.Full){
            double a=angle+f.Theta;
            PointF p=plan(1.65*Math.Cos(a),1.65*Math.Sin(a)),q=plan(5.05*Math.Cos(a),5.05*Math.Sin(a));
            Rule(g,p.X,p.Y,q.X,q.Y,cAccent,1.5f);
            using(var br=new SolidBrush(cAccent))foreach(PointF pt in new[]{p,q})g.FillEllipse(br,pt.X-2.1f,pt.Y-2.1f,4.2f,4.2f);
        }
        Rule(g,cx-4,cy+rad+7,cx,cy+rad+3,cAccent,1.3f);
        Rule(g,cx+4,cy+rad+7,cx,cy+rad+3,cAccent,1.3f);
        g.DrawString("GROUND ENTRY",section,muted,new PointF(cx,cy+rad+13),middleText);
    }
    void UtilityReadouts(Graphics g,Frame f,bool construction,int frame){
        Text(g,"WATER-GLYCOL STORE",section,muted,24,580);
        g.DrawString(f.Liquid.ToString("0.0")+" m",mono,ink,new PointF(222,577),rightText);
        g.FillRectangle(light,24,601,198,5);g.FillRectangle(waterBrush,24,601,(float)(198*f.Liquid/d.LiquidTop),5);
        if(construction){
            Text(g,"Pod service sleeves",title2,ink,24,633);
            g.DrawString(f.Ports.ToString("00")+" / "+d.Total,mono,ink,new PointF(222,633),rightText);
            Text(g,"Frame fixings",title2,ink,24,662);
            g.DrawString(f.Fixings+" / "+d.Frames[d.Frames.Length-1].Fixings,mono,ink,new PointF(222,662),rightText);
        }else{
            Text(g,"Service links",title2,ink,24,633);
            g.DrawString(f.Online.ToString("00")+" / "+d.Total,mono,ink,new PointF(222,633),rightText);
            Text(g,"Cooler frames seated",title2,ink,24,662);
            g.DrawString(SeatedFrames(frame)+" / "+d.CoolerFrames,mono,ink,new PointF(222,662),rightText);
        }
    }
    void StorePlan(Graphics g){
        float cx=122,cy=445,r=66;
        using(var pn=new Pen(Color.FromArgb(78,156,159,143),r/7.5f)){
            g.DrawArc(pn,cx-r*.9f,cy-r*.9f,r*1.8f,r*1.8f,7,346);
        }
        for(int j=0;j<d.Bays;j++){
            double a=(j+.5)*2*Math.PI/d.Bays-.65;
            float cs=(float)Math.Cos(a),sn=(float)Math.Sin(a);
            Rule(g,cx+cs*r*.79f,cy+sn*r*.79f,cx+cs*r*1.04f,cy+sn*r*1.04f,cAccent,1.8f);
        }
    }
    void DetailPanel(Graphics g,int frame,bool doorway,bool cast){
        Frame f=d.Frames[frame];
        const float bx=927,by=36,bw=325,bh=173;
        using(var bg=new SolidBrush(Color.FromArgb(247,246,239)))g.FillRectangle(bg,bx,by,bw,bh);
        Rule(g,bx,by,bx+bw,by,cLine,1);Rule(g,bx,by+bh,bx+bw,by+bh,cLine,1);
        if(doorway){
            Text(g,"DOOR BLOCKOUT",section,muted,bx+14,by+12);
            float x=bx+44,y=by+42,w=181,h=103;
            using(var br=new SolidBrush(f.Liquid>0?Color.FromArgb(188,218,208):Color.FromArgb(223,224,208)))g.FillRectangle(br,x,y,w,h);
            using(var br=new SolidBrush(Color.FromArgb(101,135,124))){
                g.FillRectangle(br,x+57,y+20,12,h-20);g.FillRectangle(br,x+91,y+20,12,h-20);
                g.FillRectangle(br,x+57,y+11,46,12);g.FillRectangle(br,x+57,y+h-6,46,6);
            }
            g.FillRectangle(paper,x+69,y+23,22,h-29);
            Rule(g,x+102,y+17,bx+206,by+50,cInk,1);
            Text(g,"Lintel",monoSmall,ink,bx+212,by+43);
            Rule(g,x+103,y+65,bx+205,by+101,cInk,1);
            Text(g,"Sealed jamb",monoSmall,ink,bx+208,by+94);
            Text(g,"Jambs and lintel seal the liquid store",monoSmall,ink,bx+14,by+151);
            return;
        }
        double extension=cast?0:d.Nodes[serviceNodes[f.Pod]].WorldPose.S.X;
        bool active=extension>.995;
        Text(g,cast?"CAST-IN POD SERVICE SLEEVE":"POD SERVICE COUPLING",section,muted,bx+14,by+12);
        if(!cast)g.DrawString(active?"LATCHED":"",section,waterBrush,new PointF(bx+bw-15,by+12),rightText);
        float cy=by+90;float inner=bx+130,outer=bx+262,stub=inner+14+34;
        using(var liquid=new SolidBrush(f.Liquid>0?Color.FromArgb(179,217,210):Color.FromArgb(232,231,218)))
            g.FillRectangle(liquid,inner+14,by+40,outer-inner-14,85);
        using(var concrete=new SolidBrush(Color.FromArgb(169,179,168))){
            g.FillRectangle(concrete,inner,by+40,14,85);g.FillRectangle(concrete,outer,by+40,14,85);
        }
        g.DrawString(f.Liquid>0?"Water-glycol store":"Dry gap",monoSmall,muted,new PointF((stub+outer)/2+8,by+45),middleText);
        // The sleeve passes through the inner wall only and opens into the store.
        using(var sleeve=new Pen(Color.FromArgb(135,117,89),16))g.DrawLine(sleeve,inner,cy,stub,cy);
        Rule(g,inner,cy-4,stub+2,cy-4,teal,3);
        Rule(g,inner,cy+4,stub+2,cy+4,Color.FromArgb(80,130,156),2.7f);
        Rule(g,stub+2,cy-4,stub+2,cy-20,teal,3);
        Rule(g,stub+2,cy+4,stub+2,cy+22,Color.FromArgb(80,130,156),3);
        g.DrawString("inner",monoSmall,muted,new PointF(inner+7,by+127),middleText);
        g.DrawString("outer",monoSmall,muted,new PointF(outer+7,by+127),middleText);
        float podFace=bx+81;
        if(!cast){
            using(var br=new SolidBrush(Color.FromArgb(155,165,162)))g.FillRectangle(br,bx+15,cy-24,66,48);
            g.DrawString(d.UnitName,mono,ink,new PointF(bx+44,cy-8),middleText);
            using(var slide=new SolidBrush(active?teal:Color.FromArgb(160,142,110)))
                g.FillRectangle(slide,podFace,cy-4,(float)((inner-podFace)*extension),8);
            if(active){using(var br=new SolidBrush(Color.FromArgb(126,202,154)))g.FillEllipse(br,podFace-10,cy-17,5,5);}
        }else Text(g,"Bore",monoSmall,ink,bx+35,cy-8);
        Text(g,"CDU supply and return open into the store",monoSmall,ink,bx+15,by+142);
        Text(g,"Power and data arrive down the shaft",monoSmall,muted,bx+15,by+155);
    }
    void StorageOverlay(Graphics g,int frame){
        Frame f=d.Frames[frame];bool installing=frame<d.StoreStart,full=frame>=d.Full;
        float x=24,xr=UiLeft-24;int stage=frame-d.BuildEnd;
        using(var sw=new SolidBrush(cAccent))g.FillRectangle(sw,x,33,25,3);
        Text(g,installing?"STEEL INSTALLATION":"STORAGE SEQUENCE",section,muted,x,46);
        Heading(g,installing?"Steel module":"Pod storage",x-2,73);
        Text(g,installing?"Tandem crawler cranes":"Ground-fed pod installation",title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);
        Text(g,installing?"MODULE BASE":"PODS STORED",section,muted,x,182);
        g.DrawString(installing?f.RackZ.ToString("0.0")+" m":f.Stored.ToString("00")+" / "+d.Total,numbers,ink,new PointF(xr,169),rightText);
        float w=(xr-x-4*(d.Levels-1))/d.Levels;
        for(int i=0;i<d.Levels;i++){
            float left=x+i*(w+4);g.FillRectangle(light,left,212,w,5);
            double frac=installing?Sat((stage-42-i*32)/32.0):Sat((f.Stored-i*d.Bays)/(double)d.Bays);
            if(frac>.001)g.FillRectangle(frac>.999?ink:accent,left,212,w*(float)frac,5);
        }
        string phase=installing?(stage<40?"Rig the module":stage<118?"Hoist above rim":stage<194?"Slew over silo":
            stage<299?"Lower onto base":"Release the rigging"):full?"Storage complete":f.LoadPhase;
        Text(g,phase,strong,full?ink:accent,x,236);
        Text(g,installing?"Shaft and crown":full?"Occupied levels":"Destination",title2,muted,x,275);
        g.DrawString(installing?d.Crown.ToString("0.0")+" m":full?d.Levels+" / "+d.Levels:"Level "+f.Level.ToString("00"),mono,ink,new PointF(xr,275),rightText);
        Rule(g,x,312,xr,312,cLine,1);
        int planLevel=installing||full?d.Levels:Math.Min(d.Levels,f.Level+1);
        Text(g,installing?"RADIAL STORAGE PLAN":"PLAN  /  LEVEL "+planLevel.ToString("00"),section,muted,x,333);
        LevelPlan(g,frame,planLevel,installing);
        UtilityReadouts(g,f,false,frame);
        string badge=installing?(stage<56?"TANDEM PICK":"TRANSLUCENT SILO"):full?"ALL LEVELS FILLED":"TRANSLUCENT SILO";
        g.FillRectangle(paper,UiLeft+23,22,badge=="TANDEM PICK"?105:149,27);
        using(var pen=new Pen(cInk,1.2f))g.DrawEllipse(pen,UiLeft+32,30,9,9);
        Text(g,badge,section,ink,UiLeft+48,29);
        if(frame>=d.Fast && !full){
            using(var br=new SolidBrush(teal))g.FillRectangle(br,UiLeft+23,56,138,27);
            Text(g,d.FastRate.ToString("0.##")+"\u00d7   LOWER "+(d.Levels-2)+" TIERS",section,white,UiLeft+33,63);
        }
        if(!installing && f.Pod==0 && f.U>=.90)DetailPanel(g,frame,false,false);
        if(full)DetailPanel(g,frame,false,false);
        if(!installing && f.Pod==0 && f.U<.29){
            double a=-37*Math.PI/180;PointF p=Project(new V((d.Outer+.01)*Math.Cos(a),(d.Outer+.01)*Math.Sin(a),1.98));
            float ty=p.Y+23;
            Rule(g,p.X,p.Y,p.X+38,ty,cAccent,1);
            g.FillRectangle(paper,p.X+37,ty-3,132,24);Text(g,d.OpeningWidth.ToString("0.00")+" × "+d.OpeningHeight.ToString("0.00")+" m",mono,ink,p.X+44,ty+1);
        }
        if(full){
            PointF a=Project(new V(d.Inner-.10,0,d.Levels*d.Pitch)),b=Project(new V(d.Inner-.10,0,d.BaseZ));
            float lx=Math.Max(a.X,b.X)+40;
            Rule(g,lx,a.Y,lx,b.Y,cInk,1);
            Rule(g,lx-4,a.Y,lx+4,a.Y,cInk,1);Rule(g,lx-4,b.Y,lx+4,b.Y,cInk,1);
            g.FillRectangle(paper,lx+6,(a.Y+b.Y)/2-12,111,40);
            Text(g,d.Levels+" × "+d.Pitch.ToString("0.00")+" m",mono,ink,lx+13,(a.Y+b.Y)/2-8);
            Text(g,"storage tiers",monoSmall,muted,lx+13,(a.Y+b.Y)/2+10);
        }
    }
    Bitmap CoolerDetail(){
        // A fixed view of the same mesh that is hoisted in the main scene.
        var im=new Bitmap(624,238,PixelFormat.Format32bppRgb);
        V direction=new V(.91,-.47,.37).Unit(),side=new V(-direction.Y,direction.X,0).Unit(),vertical=direction.Cross(side).Unit();
        double zoom=Math.Min(105,540/d.CoolLength);V middle=new V(d.CoolerFrameDepth/2,0,d.CoolerFrameHeight/d.CoolerRows/2-.15);
        Func<V,PointF> project=v=>new PointF(312+(float)(zoom*(v-middle).Dot(side)),119-(float)(zoom*(v-middle).Dot(vertical)));
        Tri[] triangles=d.Meshes[d.Nodes[coolers[0]].M].Ts;
        int width=im.Width,height=im.Height;
        int[] rgb=new int[width*height];
        double[] zbuf=new double[rgb.Length];
        for(int i=0;i<rgb.Length;i++){rgb[i]=Pack(247,246,239);zbuf[i]=Double.NegativeInfinity;}
        V lamp=new V(.42,-.65,.82).Unit();
        foreach(Tri t in triangles){
            if(t.N.Dot(direction)<.0001)continue;
            PointF a=project(t.A),b=project(t.B),c=project(t.C);
            double bx=b.X-a.X,by=b.Y-a.Y,cx=c.X-a.X,cy=c.Y-a.Y,det=bx*cy-by*cx;
            if(Math.Abs(det)<1e-8)continue;
            int l=Clamp((int)Math.Floor(Math.Min(a.X,Math.Min(b.X,c.X))),0,width-1);
            int r=Clamp((int)Math.Ceiling(Math.Max(a.X,Math.Max(b.X,c.X))),0,width-1);
            int top=Clamp((int)Math.Floor(Math.Min(a.Y,Math.Min(b.Y,c.Y))),0,height-1);
            int bottom=Clamp((int)Math.Ceiling(Math.Max(a.Y,Math.Max(b.Y,c.Y))),0,height-1);
            double lightness=.78+.24*Math.Max(0,t.N.Dot(lamp));
            int col=Pack(Clamp((int)(t.Co.R*lightness),0,255),Clamp((int)(t.Co.G*lightness),0,255),
                         Clamp((int)(t.Co.B*lightness),0,255));
            double z=t.A.Dot(direction),zb=t.B.Dot(direction)-z,zc=t.C.Dot(direction)-z;
            for(int y=top;y<=bottom;y++)for(int x=l;x<=r;x++){
                double dx=x+.5-a.X,dy=y+.5-a.Y;
                double u=(dx*cy-dy*cx)/det,v=(bx*dy-by*dx)/det;
                if(u<-.000001 || v<-.000001 || u+v>1.000001)continue;
                int i=y*width+x;double zz=z+u*zb+v*zc;
                if(zz>zbuf[i]){zbuf[i]=zz;rgb[i]=col;}
            }
        }
        BitmapData bits=im.LockBits(new Rectangle(0,0,width,height),ImageLockMode.WriteOnly,PixelFormat.Format32bppRgb);
        Marshal.Copy(rgb,0,bits.Scan0,rgb.Length);im.UnlockBits(bits);
        return im;
    }
    void CoolerPanel(Graphics g,int frame){
        if(coolerInset==null)coolerInset=CoolerDetail();
        const int x=927,y=36,w=325,h=177;
        using(var bg=new SolidBrush(Color.FromArgb(247,246,239)))g.FillRectangle(bg,x,y,w,h);
        Rule(g,x,y,x+w,y,cLine,1);Rule(g,x,y+h,x+w,y+h,cLine,1);
        Text(g,d.CoolerMW.ToString("0.#")+" MW DRY COOLER",section,muted,x+14,y+12);
        g.DrawImage(coolerInset,x+6,y+29,312,119);
        Text(g,d.CoolLength.ToString("0.00")+" m long",mono,ink,x+15,y+147);
        g.DrawString(d.CoolerFans+" outward fans, own pump unit",monoSmall,muted,new PointF(x+w-14,y+149),rightText);
    }
    void PowerPlan(Graphics g,int count,bool vents){
        const float cx=123,cy=447,r=76;
        using(var pen=new Pen(Color.FromArgb(133,153,141),1))g.DrawEllipse(pen,cx-r,cy-r,2*r,2*r);
        using(var pen=new Pen(cLine,1))g.DrawEllipse(pen,cx-r-7,cy-r-7,2*r+14,2*r+14);
        for(int j=0;j<2;j++){
            double a=(12+j*90)*Math.PI/180,cs=Math.Cos(a),sn=Math.Sin(a);
            Func<double,double,PointF> pt=(x,y)=>new PointF(cx+(float)((x*cs-y*sn)*r/d.Inner),cy-(float)((x*sn+y*cs)*r/d.Inner));
            PointF[] corners={pt(-d.PowerLength/2,-d.PowerWidth/2),pt(d.PowerLength/2,-d.PowerWidth/2),pt(d.PowerLength/2,d.PowerWidth/2),pt(-d.PowerLength/2,d.PowerWidth/2)};
            if(j<count){using(var b=new SolidBrush(j==0?Color.FromArgb(124,150,139):Color.FromArgb(181,162,125)))g.FillPolygon(b,corners);}
            using(var pn=new Pen(j<count?cInk:cLine,1)){if(j>=count)pn.DashStyle=DashStyle.Dash;g.DrawPolygon(pn,corners);}
            if(j<count)foreach(double x in new[]{-(double)d.StackX,(double)d.StackX}){
                var v=pt(x,0);using(var b=new SolidBrush(vents?teal:cInk))g.FillEllipse(b,v.X-4.5f,v.Y-4.5f,9,9);
            }
        }
        using(var pn=new Pen(Color.FromArgb(145,88,50),1.7f))g.DrawEllipse(pn,cx-6,cy-6,12,12);
        g.DrawString("CENTRAL SHAFT",section,muted,new PointF(cx,cy+r+16),middleText);
    }
    void PowerOverlay(Graphics g,int frame){
        int t=frame-d.Full;
        int firstSeat=d.Pick1+d.PickDuration,secondSeat=d.Pick2+d.PickDuration;
        int count=t>=secondSeat?2:t>=firstSeat?1:0;
        bool vents=t>=d.VentBegin,done=t>=d.VentEnd,second=t>=d.Pick2;
        int elapsed=t-(second?d.Pick2:d.Pick1);
        float x=24,xr=UiLeft-24;
        g.FillRectangle(accent,x,33,25,3);
        Text(g,"POWER INSTALLATION",section,muted,x,46);
        Heading(g,"Power plant",x-2,73);
        Text(g,"Diesel level, then turbine level",title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);
        Text(g,"LEVELS SEATED",section,muted,x,182);
        g.DrawString(count+" / 2",numbers,ink,new PointF(xr,169),rightText);
        for(int i=0;i<2;i++){g.FillRectangle(i<count?ink:light,x+101*i,212,97,5);}
        string phase=t>=d.LidEnd?"Silo closed":t>=d.LidBegin+8?"Lower the lid and its vents":done?"Rig the lid":vents?"Release the rigging":
            count==2?"Release the rigging":t>=firstSeat && !second?"Hook the turbine level":
            elapsed<5?"Rig the level":elapsed<55?"Hoist above rim":elapsed<91?"Slew over bore":
            second?"Seat the turbine sets":"Seat the diesel sets";
        Text(g,phase,strong,done?ink:accent,x,236);
        Text(g,"Turbine set",title2,muted,x,275);
        g.DrawString(d.PowerLength.ToString("0.0")+" x "+d.PowerWidth.ToString("0.0")+" m",mono,ink,new PointF(xr,275),rightText);
        Rule(g,x,312,xr,312,cLine,1);
        Text(g,"TURBINE LEVEL",section,muted,x,333);
        Rows(g,d.TurbineRows,x,xr,356,22);
        Rule(g,x,478,xr,478,cLine,1);
        Text(g,"DIESEL LEVEL",section,muted,x,497);
        Rows(g,d.BackupRows,x,xr,520,22);
        Rule(g,x,620,xr,620,cLine,1);
        Text(g,"Roof stacks",title2,muted,x,640);
        g.DrawString("to "+d.VentTop.ToString("0.#")+" m",mono,ink,new PointF(xr,639),rightText);
        Text(g,"Lid",title2,muted,x,693);
        g.DrawString(t>=d.LidEnd?"Closed":"Open",mono,ink,new PointF(xr,692),rightText);
    }
    void EmbedPanel(Graphics g,int frame){
        const int bx=916,by=35,w=336,h=185;
        using(var bg=new SolidBrush(Color.FromArgb(248,247,239)))g.FillRectangle(bg,bx,by,w,h);
        Rule(g,bx,by,bx+w,by,cLine,1);Rule(g,bx,by+h,bx+w,by+h,cLine,1);
        Text(g,"CAST-IN FRAME ANCHOR",section,muted,bx+15,by+12);
        float lo=by+41,hi=by+144,back=bx+59,face=bx+143;
        g.FillRectangle(light,back,lo,face-back,hi-lo);
        double zTop=Math.Max(d.Frames[frame].Height-(frame>=196?5.01:0),0);
        float at=(float)Math.Max(0,Math.Min(hi-lo,(hi-lo)*(zTop-.015)/.71));
        using(var concrete=new SolidBrush(Color.FromArgb(171,179,164)))g.FillRectangle(concrete,back,hi-at,face-back,at);
        Rule(g,back,lo,back,hi,cLine,1);Rule(g,face+5,lo,face+5,hi,cLine,1);
        float lift=(float)(9*(1-Sat((frame-8)/25.0)));
        int platePos=(int)(lo+7-lift);
        using(var steel=new SolidBrush(Color.FromArgb(154,116,77)))g.FillRectangle(steel,face-5,platePos,7,89);
        foreach(float yy in new[]{lo+24-lift,lo+80-lift}){
            Rule(g,back+17,yy,face-4,yy,cInk,4.2f);
            Rule(g,back+17,yy-7,back+17,yy+7,cInk,4.5f);
            using(var b=new SolidBrush(cInk))g.FillRectangle(b,face-4,yy-3,6,6);
        }
        Rule(g,back+21,lo+25-lift,bx+31,lo+12,cInk,.9f);
        Rule(g,face+1,lo+47-lift,bx+195,lo+23,cAccent,.9f);
        Text(g,"Flush steel plate",monoSmall,ink,bx+199,lo+14);
        Rule(g,back+37,lo+80-lift,bx+192,lo+72,cInk,.9f);
        Text(g,"Headed studs",monoSmall,ink,bx+197,lo+64);
        Text(g,"Each cooler frame bolts to 20 of these",monoSmall,muted,bx+15,by+157);
    }
    void WorkLeader(Graphics g,V pt,string label){
        PointF q=Project(pt);
        if(q.X<UiLeft+55 || q.X>1198 || q.Y<70 || q.Y>641)return;
        float w=label.Length*6.8f+19;
        float x=q.X+31,y=q.Y-28;
        if(x+w>1253)x=q.X-31-w;
        Rule(g,q.X,q.Y,x>q.X?x:x+w,y+10,cAccent,1.15f);
        g.FillRectangle(paper,x,y,w,22);Text(g,label,monoSmall,ink,x+7,y+4);
    }
    void CrewPlan(Graphics g,int frame){
        const float cx=122,cy=446,r=81;
        using(var pn=new Pen(cLine,1))g.DrawEllipse(pn,cx-r-4,cy-r-4,2*r+8,2*r+8);
        Func<double,double,PointF> plan=(rad,ang)=>new PointF(cx+(float)(rad*Math.Cos(ang)),cy-(float)(rad*Math.Sin(ang)));
        for(int j=0;j<d.Bays;j++){
            double a=(-37+j*360.0/d.Bays)*Math.PI/180;
            PointF[] pod={plan(14,a+.3927-.18),plan(78,a+.3927-.037),plan(78,a+.3927+.037),plan(14,a+.3927+.18)};
            using(var b=new SolidBrush(Color.FromArgb(126,142,137)))g.FillPolygon(b,pod);
            var v=new List<PointF>();
            for(int k=0;k<=9;k++)v.Add(plan(74,a+(-.324+.648*k/9)));
            for(int k=9;k>=0;k--)v.Add(plan(31,a+(-.245+.490*k/9)));
            double z=d.Nodes[decks[j]].WorldPose.T.Z;
            using(var b=new SolidBrush(z>1?Color.FromArgb(165,136,80):Color.FromArgb(213,199,160)))g.FillPolygon(b,v.ToArray());
            using(var pn=new Pen(Color.FromArgb(138,120,83),.7f))g.DrawPolygon(pn,v.ToArray());
            PointF mark=plan(53.5,a);
            g.DrawString(d.WorkLevels[j]==0?"P":d.WorkLevels[j].ToString(),section,z>1?white:ink,new PointF(mark.X,mark.Y-6),middleText);
        }
        using(var br=new SolidBrush(cInk))g.FillEllipse(br,cx-8,cy-8,16,16);
        g.DrawString("P  TURBINE LEVEL",section,muted,new PointF(cx,544),middleText);
    }
    void CrewOverlay(Graphics g,int frame){
        int w=frame-d.Full-d.Crew;
        const float x=24,xr=222;
        g.FillRectangle(accent,x,33,25,3);Text(g,"PERSONNEL ACCESS",section,muted,x,46);
        Heading(g,"Work decks",x-2,73);Text(g,"Crews in the radial voids",title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);
        int at=0;
        for(int j=0;j<d.Bays;j++){
            double set=d.WorkLevels[j]==0?d.PowerBase1+.054:d.BaseZ-.025+d.Pitch*(d.WorkLevels[j]-1);
            if(Math.Abs(d.Nodes[decks[j]].WorldPose.T.Z-set)<.03)at++;
        }
        Text(g,"DECKS AT WORK",section,muted,x,182);g.DrawString(at+" / "+d.Bays,numbers,ink,new PointF(xr,169),rightText);
        float bar=(xr-x-4*(d.Bays-1))/d.Bays;
        for(int j=0;j<d.Bays;j++)g.FillRectangle(j<at?accent:light,x+j*(bar+4),212,bar,5);
        int e0=d.Enc0-d.Crew,e1=d.Enc1-d.Crew,e2=d.Enc2-d.Crew,e3=d.Enc3-d.Crew;
        string phase=w<104?"Board at ground":w<241?"Rise between pods":w<e0-30?"Service the pods":
            w<e1?"Open the turbine enclosure":w<e2-30?"Service the gas turbine":w<e3?"Close the enclosure":
            w<700?"Return to grade":w<775?"Crews disembark":"Stow the decks";
        if(w>=e0-6 && w<e3+10)TurbinePanel(g);
        Text(g,phase,strong,accent,x,236);
        Text(g,"Destinations",title2,muted,x,276);
        g.DrawString("See plan",mono,ink,new PointF(xr,275),rightText);
        Rule(g,x,312,xr,312,cLine,1);Text(g,"PLATFORM DESTINATIONS",section,muted,x,333);
        CrewPlan(g,frame);
        Rule(g,x,571,xr,571,cLine,1);
        Text(g,"Maintenance crew",title2,muted,x,596);
        g.DrawString(d.CrewCount+" people",mono,ink,new PointF(xr,595),rightText);
        Text(g,"Power-unit deck",title2,muted,x,633);
        g.DrawString(d.Nodes[decks[1]].WorldPose.T.Z<.01?"Ground":d.Nodes[decks[1]].WorldPose.T.Z.ToString("0.0")+" m",mono,ink,new PointF(xr,632),rightText);
        if(w>276 && w<370){
            V pt=World(new V(4.55,1.02,1.15),d.Nodes[decks[0]],d.Nodes[decks[0]].WorldPose);
            WorkLeader(g,pt,"Level 04 service");
        }
        if(w>449 && w<535){
            V pt=World(new V(3.68,.10,1.64),d.Nodes[decks[1]],d.Nodes[decks[1]].WorldPose);
            WorkLeader(g,pt,"Gas turbine set A");
        }
    }
    string RepairPhase(int w){
        if(w<34)return "Reveal the storage";
        if(w<65)return "Identify the fault";
        if(w<112)return "Unplug the bay";
        if(w<157)return "Move the column aside";
        if(w<204)return "Align the cable crane";
        if(w<300)return "Index to the doorway";
        if(w<434)return "Lower twin pickups";
        if(w<466)return "Release the shaft lock";
        if(w<508)return "Lower the faulty pod";
        if(w<586)return "Extract at grade";
        if(w<647)return "Park the faulty pod";
        if(w<711)return "Align the new pod";
        if(w<805)return "Feed the replacement";
        if(w<931)return "Hoist the new pod";
        if(w<995)return "Seat and release";
        if(w<1149)return "Return to the ports";
        if(w<1195)return "Reconnect services";
        return "Replacement online";
    }
    void SwapPlan(Graphics g,int frame){
        int w=frame-d.Full-d.Repair;
        const float cx=115,bottom=544;
        float scale=7.85f;
        Rule(g,38,bottom+1,198,bottom+1,cLine,1);
        double orig=(-37+22.5+45*(d.FaultBay-1))*Math.PI/180;
        double reg=d.Nodes[d.Nodes[podNodes[d.Fault]].Parent].WorldPose.A-orig;
        double lane=orig+reg;
        for(int lev=1;lev<=d.Levels;lev++){
            int idx=(d.Levels-lev)*d.Bays+d.FaultBay-1;
            Node n=d.Nodes[podNodes[idx]];
            float y=bottom-(float)((d.BaseZ+(lev-1)*d.Pitch+d.FrameHeight/2)*scale);
            Rule(g,46,y,180,y,cLine,.65f);
            Text(g,"L"+lev.ToString("00"),monoSmall,muted,26,y-8);
            if(lev==d.FaultLevel)continue;
            double delta=n.WorldPose.A-lane;
            float x=cx+(float)(68*Math.Sin(delta));
            bool live=d.Nodes[serviceNodes[idx]].WorldPose.S.X>.995;
            using(var b=new SolidBrush(live?Color.FromArgb(111,143,133):Color.FromArgb(164,151,123)))g.FillRectangle(b,x-14,y-5,28,10);
        }
        float top=bottom-(float)(Math.Max(.05,d.Nodes[hook].WorldPose.T.Z)*scale);
        Rule(g,cx,371,cx,top,cAccent,1.5f);
        if(w<503 || w>=805){
            Node m=w<503?d.Nodes[podNodes[d.Fault]]:d.Nodes[replacement];
            float y=bottom-(float)((m.WorldPose.T.Z+1.15)*scale);
            using(var br=new SolidBrush(w<503?cAccent:teal))g.FillRectangle(br,cx-16,y-6,32,12);
        }
        using(var p=new Pen(cLine,1))g.DrawRectangle(p,97,bottom-3,36,10);
    }
    void SwapOverlay(Graphics g,int frame){
        int w=frame-d.Full-d.Repair,links=0,direct=0;
        const float x=24,xr=222;
        foreach(int id in serviceNodes)if(d.Nodes[id].WorldPose.S.X>.995)links++;
        if(d.Nodes[replacementPlug].WorldPose.S.X>.995)links++;
        for(int lev=1;lev<=d.Levels;lev++){
            int j=(d.Levels-lev)*d.Bays+d.FaultBay-1;
            if(j!=d.Fault && d.Nodes[serviceNodes[j]].WorldPose.S.X<.02)direct++;
        }
        g.FillRectangle(accent,x,33,25,3);Text(g,"POD REPLACEMENT",section,muted,x,46);
        Heading(g,"Pod swap",x-2,73);Text(g,"Level "+d.FaultLevel.ToString("00")+"  /  Bay "+d.FaultBay.ToString("00"),title2,muted,x,126);
        Rule(g,x,164,xr,164,cLine,1);Text(g,"LIVE LINKS",section,muted,x,182);
        g.DrawString(links+" / "+d.Total,numbers,ink,new PointF(xr,169),rightText);
        g.FillRectangle(light,x,212,xr-x,5);g.FillRectangle(waterBrush,x,212,(xr-x)*links/d.Total,5);
        Text(g,RepairPhase(w),strong,w>=1195?waterBrush:accent,x,236);
        Text(g,"Column released",title2,muted,x,276);g.DrawString(direct+" / "+(d.Levels-1),mono,ink,new PointF(xr,275),rightText);
        Rule(g,x,312,xr,312,cLine,1);Text(g,"CABLE LANE  /  ELEVATION",section,muted,x,333);
        SwapPlan(g,frame);Rule(g,x,570,xr,570,cLine,1);
        using(var a=new SolidBrush(cAccent))g.FillRectangle(a,x,601,9,9);
        Text(g,"Faulty pod",title2,muted,x+17,594);g.DrawString((d.Fault+1).ToString("000"),mono,ink,new PointF(xr,595),rightText);
        using(var a=new SolidBrush(teal))g.FillRectangle(a,x,638,9,9);
        Text(g,"Replacement",title2,muted,x+17,631);g.DrawString((d.Total+1).ToString("000"),mono,ink,new PointF(xr,632),rightText);
        if(w>36 && w<70 || w>458 && w<574 || w>598 && w<637){
            Node pod=d.Nodes[podNodes[d.Fault]];V pt=World(new V(3.8,0,1.85),pod,pod.WorldPose);
            WorkLeader(g,pt,(d.Fault+1).ToString("000")+"  FAULT");
        }
        if(w>724 && w<930 || w>1197){
            Node pod=d.Nodes[replacement];V pt=World(new V(3.8,0,1.85),pod,pod.WorldPose);
            WorkLeader(g,pt,(d.Total+1).ToString("000")+(w>1197?"  ONLINE":"  REPLACEMENT"));
        }
    }
    void Overlay(int frame){
        Frame f=d.Frames[frame];
        using(Graphics g=Graphics.FromImage(bmp)){
            g.ScaleTransform(Factor,Factor);
            g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
            g.FillRectangle(paper,0,0,UiLeft,H/Factor);
            if(d.Short && frame>=d.BuildEnd){ShortOverlay(g,frame);return;}
            if(frame>=d.Terminal && frame<d.FirstPod-8){TerminalOverlay(g,frame);ProgrammeTag(g,frame);DesignStrip(g,frame);return;}
            if(frame>=d.BuildEnd){
                int t=frame-d.Full;
                if(Ghosted(frame) && (t<d.SealBegin || t>=d.Repair && t<d.FinalBegin))ShellEdges(g);
                if(t>=d.FinalBegin)DesignOverlay(g,frame);
                else if(t>=d.Repair){SwapOverlay(g,frame);ServicePanel(g,frame);}
                else if(t>=d.Fuel)FuelOverlay(g,frame);
                else if(t>=d.SealBegin)DesignOverlay(g,frame);
                else if(t>=d.Crew)CrewOverlay(g,frame);
                else if(frame>=d.Full)PowerOverlay(g,frame);
                else if(frame>=d.FrameTimes[0,0] && frame<d.FrameTimes[0,7])CoolerFrameOverlay(g,frame);
                else if(frame>=d.StoreStart && frame<d.Terminal)StoreOverlay(g,frame);
                else StorageOverlay(g,frame);
                if(t>=d.SealBegin && t<d.Fuel)ProgrammeChart(g);
                ProgrammeTag(g,frame);
                DesignStrip(g,frame);
                return;
            }
            float x=24,xr=UiLeft-24;
            using(var sb=new SolidBrush(cAccent))g.FillRectangle(sb,x,33,25,3);
            Text(g,"CONSTRUCTION SEQUENCE",section,muted,x,46);
            Heading(g,"Jumpforming",x-2,72);
            Text(g,"Double-wall concrete silo",title2,muted,x,126);
            Rule(g,x,164,xr,164,cLine,1);
            Text(g,"LIFT",section,muted,x,183);
            g.DrawString(f.Lift.ToString("00")+" / "+d.Count.ToString("00"),mono,ink,new PointF(xr,179),rightText);
            float width=(xr-x-4*(d.Count-1))/d.Count;
            for(int i=0;i<d.Count;i++){
                Brush b=i<f.Lift-1 || f.End ? ink : i==f.Lift-1 ? accent : light;
                g.FillRectangle(b,x+i*(width+4),208,width,5);
            }
            Text(g,frame>=12 && frame<=33?"Set frame anchors":frame>=5 && frame<12?"Set pod service sleeves":f.Phase,strong,f.End?ink:accent,x,229);
            Text(g,"Wall height",title2,muted,x,274);
            g.DrawString(f.Height.ToString("0.0",CultureInfo.InvariantCulture)+" m",numbers,ink,
                         new PointF(xr,264),rightText);
            Rule(g,x,312,xr,312,cLine,1);
            Text(g,"WALL PLAN",section,muted,x,333);
            Plan(g);
            if(frame>25)StorePlan(g);
            UtilityReadouts(g,f,true,frame);
            if(frame>=4 && frame<12 || frame>=106 && frame<123)DetailPanel(g,frame,false,true);
            if(frame>=12 && frame<=105 || frame>=196 && frame<=259)EmbedPanel(g,frame);
            if(frame>=123 && frame<=190)DetailPanel(g,frame,true,false);
            // The crossfade clearly signals the return to the full cylinder.
            bool full=frame>=d.Closed;
            string view=full?"FULL WALLS":"CUTAWAY VIEW";
            int labelW=full?101:122;
            g.FillRectangle(paper,UiLeft+23,22,labelW,28);
            using(var pen=new Pen(cInk,1.35f)){
                int lx=UiLeft+37, ly=36;
                if(full)g.DrawEllipse(pen,lx-5,ly-5,10,10);
                else {
                    g.DrawArc(pen,lx-5,ly-5,10,10,32,288);
                    g.DrawLine(pen,lx,ly,lx+5,ly+3);g.DrawLine(pen,lx,ly,lx+4,ly-3);
                }
            }
            Text(g,view,section,ink,UiLeft+49,29);
            Dimensions(g,frame);
            if(frame<d.Closed)CrewPanel(g,frame);
            ProgrammeTag(g,frame);
            DesignStrip(g,frame);
        }
    }
    void ToBitmap(){
        var rect=new Rectangle(0,0,W,H);
        BitmapData bit=bmp.LockBits(rect,ImageLockMode.WriteOnly,PixelFormat.Format32bppRgb);
        Marshal.Copy(pixels,0,bit.Scan0,pixels.Length);bmp.UnlockBits(bit);
    }
    void ShellEdges(Graphics g){
        double az=Math.Atan2(eye.Y,eye.X),rh=Math.Sqrt(eye.X*eye.X+eye.Y*eye.Y);
        GraphicsState sectionClip=g.Save();
        g.SetClip(new RectangleF(UiLeft,0,1280-UiLeft,720));
        foreach(double radius in new[]{(double)d.Outer,(double)d.Inner}){
            double tang=Math.Acos(radius/rh);
            foreach(double a in new[]{az-tang,az+tang}){
                PointF bottom=Project(new V(radius*Math.Cos(a),radius*Math.Sin(a),0));
                PointF top=Project(new V(radius*Math.Cos(a),radius*Math.Sin(a),d.Height));
                using(var pen=new Pen(Color.FromArgb(radius==d.Outer?138:70,87,119,123),radius==d.Outer?1.20f:.8f))
                    g.DrawLine(pen,bottom,top);
            }
            foreach(double z in new[]{(double)d.Height,0.0}){
                for(int j=0;j<72;j++){
                    double a=j*Math.PI/36,b=(j+1)*Math.PI/36;
                    bool near=Math.Cos((a+b)/2-az)>radius/rh;
                    if(z==0 && !near)continue;
                    PointF p=Project(new V(radius*Math.Cos(a),radius*Math.Sin(a),z));
                    PointF q=Project(new V(radius*Math.Cos(b),radius*Math.Sin(b),z));
                    using(var pen=new Pen(Color.FromArgb(near?140:91,79,117,123),radius==d.Outer?1.3f:1.0f))
                        g.DrawLine(pen,p,q);
                }
            }
        }
        g.Restore(sectionClip);
    }
    // In a cutaway the concrete is removed altogether. Its outline is drawn by ShellEdges.
    bool Ghosted(int frame){
        int t=frame-d.Full;
        return frame>=d.Ghost+17 && t<d.SealEnd || t>=d.Repair && t<d.FinalEnd;
    }
    // The lid is shown while it is placed, cleared for the cutaways and solid again for the closing scenes.
    int LidAlpha(int frame){
        int t=frame-d.Full;
        if(d.Short)return 255;
        if(t<d.Crew)return 255;
        if(t<d.Crew+30)return (int)(255*(1-(t-d.Crew)/30.0));
        return t<d.SealEnd?0:t<d.Repair?255:t<d.FinalEnd?0:255;
    }
    // A cooler frame facing the camera is ghosted only once it is connected and on its seats.
    bool Seated(Node n,int frame){
        double radius=Math.Sqrt(n.WorldPose.T.X*n.WorldPose.T.X+n.WorldPose.T.Y*n.WorldPose.T.Y);
        if(radius>d.CoolerBack+2.2)return false;
        double bearing=Math.Atan2(n.Sin,n.Cos);
        for(int i=0;i<d.CoolerFrames;i++)
            if(Math.Cos(bearing-d.FrameBearing[i])>.9995)return frame>=d.FrameTimes[i,6];
        return true;
    }
    void WorldFrame(int poseFrame,int wallMode=0){
        UpdateWorld(poseFrame);alpha=255;
        int t=poseFrame-d.Full;
        bool access=!d.Short && (t>=d.Crew && t<d.SealEnd || t>=d.Repair && t<d.FinalEnd);
        softShadow=wallMode==2 || (wallMode==0 && Ghosted(poseFrame));
        Frame f=d.Frames[poseFrame];
        bool same=cachedFrame>=0 && siteColors!=null && softShadow==cachedSoft &&
            (d.Frames[cachedFrame].Eye-f.Eye).Dot(d.Frames[cachedFrame].Eye-f.Eye)<1e-10 &&
            (d.Frames[cachedFrame].Target-f.Target).Dot(d.Frames[cachedFrame].Target-f.Target)<1e-10;
        if(same){
            Array.Copy(siteColors,pixels,pixels.Length);Array.Copy(siteDepth,depth,depth.Length);
        }else{
            Sky();DrawNode(d.Nodes[0],poseFrame);
            DrawNode(d.Nodes[2],poseFrame);Shadows();DrawNode(d.Nodes[1],poseFrame);DrawNode(d.Nodes[3],poseFrame);
            cachedFrame=-2;
            if(poseFrame>=d.BuildEnd && poseFrame+1<d.Frames.Length && !(t>=d.SealBegin && t<=d.SealEnd) && !(t>=d.FinalBegin && t<=d.FinalEnd)){
                Frame next=d.Frames[poseFrame+1];
                if((next.Eye-f.Eye).Dot(next.Eye-f.Eye)<1e-10){
                    if(siteColors==null){siteColors=new int[pixels.Length];siteDepth=new float[depth.Length];}
                    Array.Copy(pixels,siteColors,pixels.Length);Array.Copy(depth,siteDepth,depth.Length);
                    cachedFrame=poseFrame;cachedSoft=softShadow;
                }
            }
        }
        nearEquipment.Clear();
        for(int i=4;i<d.Nodes.Length;i++){
            Node n=d.Nodes[i];if(n.M<0)continue;
            if(n.Kind==1){
                if(wallMode==2)continue;
                if(wallMode==1)n.WorldPose.S=new V(1,1,1);
            }
            int mat=d.Meshes[n.M].Mat;
            bool powerDetail=n.Kind==13 && t>=d.Enc0-58 && t<d.Enc3+30;
            if(access && softShadow && powerDetail){nearEquipment.Add(n);continue;}
            if(n.Kind==16 || n.Kind==17)continue;
            if(d.Short && softShadow){
                // In the short film a cutaway clears everything in or on the walls, and the cooler frames facing the camera.
                if(n.Kind==18)continue;
                if((n.Kind==4 || n.Kind==5) && n.WorldPose.S.X>.999 && Seated(n,poseFrame) &&
                   new V(n.Cos,n.Sin,0).Dot(new V(eye.X,eye.Y,0).Unit())>.15)continue;
            }
            if((n.Kind==4 || n.Kind==5) && (poseFrame>=d.FirstPod && poseFrame<d.Full+d.VentEnd || access && softShadow) && n.WorldPose.S.X>.999 && Seated(n,poseFrame)){
                V az=new V(n.Cos,n.Sin,0);
                if(az.Dot(new V(eye.X,eye.Y,0).Unit())>(access?-.12:.48) ){
                    nearEquipment.Add(n);continue;
                }
            }
            if(mat!=1 && mat!=2 && mat!=4 && mat!=5 && mat!=6)DrawNode(n,poseFrame);
        }
        foreach(Node n in d.Nodes){
            if(n.M<0)continue;int mat=d.Meshes[n.M].Mat;
            if(mat==4 || mat==5){alpha=mat==4?(access?17:42):(access?55:159);DrawNode(n,poseFrame);}
            if(mat==6){alpha=104;DrawNode(n,poseFrame);}
        }
        alpha=wallMode==1?255:wallMode==2?0:LidAlpha(poseFrame);
        if(alpha>0)foreach(Node n in d.Nodes)if(n.Kind==16 && n.M>=0){
            if(poseFrame>=d.Full+d.LidEnd)n.WorldPose.S=new V(1,1,1);
            DrawNode(n,poseFrame);
        }
        if(alpha>0)foreach(Node n in d.Nodes)if(n.Kind==17 && n.M>=0){
            if(t>=d.Repair && t<d.FinalEnd)n.WorldPose.S=new V(1,1,1);
            if(n.WorldPose.S.X>.5)DrawNode(n,poseFrame);
        }
        alpha=255;
        if(nearEquipment.Count>0){
            // Blend the complete front bank once, retaining the opacity of the unit in transit.
            Array.Copy(pixels,underEquipment,pixels.Length);
            foreach(Node n in nearEquipment)DrawNode(n,poseFrame);
            for(int y=0;y<H;y++)for(int x=Left;x<W;x++){
                int i=y*W+x;if(underEquipment[i]!=pixels[i])pixels[i]=MixColor(underEquipment[i],pixels[i],access?.075:poseFrame<d.Full?.55:.18);
            }
        }
    }
    // The closing schematics replace the 3-D view. Each one fades in over the picture before it.
    public Bitmap Render(int frame){
        int t=frame-d.Full;
        if(d.Short){
            // The short film closes on the plan and the section side by side.
            if(t<d.Plan)return Render3D(frame);
            int into=t-d.Plan;
            if(into<d.Fade)Render3D(d.Full+d.Plan-1);
            Closing(frame,into<d.Fade?(into+1f)/(d.Fade+1):1);
            return bmp;
        }
        if(t<d.Plan)return Render3D(frame);
        if(t>=d.Repair){
            // The replacement scene fades in over the section drawing.
            Render3D(frame);
            if(t-d.Repair<d.Fade)Schematic(d.Full+d.Repair-1,true,1-(t-d.Repair+1f)/(d.Fade+1));
            return bmp;
        }
        bool section=t>=d.Section;
        int since=t-(section?d.Section:d.Plan);
        if(since<d.Fade){
            if(section)Schematic(d.Full+d.Section-1,false,1);else Render3D(d.Full+d.Plan-1);
            Schematic(frame,section,(since+1f)/(d.Fade+1));
        }else Schematic(frame,section,1);
        return bmp;
    }
    Bitmap Render3D(int frame){
        Frame f=d.Frames[frame];
        eye=f.Eye;forward=(f.Target-f.Eye).Unit();right=forward.Cross(new V(0,0,1)).Unit();up=right.Cross(forward);
        double solid=Sat((frame-d.Full-d.SealBegin)/(double)(d.SealEnd-d.SealBegin));
        solid=solid*solid*(3-2*solid);
        focal=H*.5/Math.Tan(f.Fov*Math.PI/360);centerX=(W+Left)*.5;centerY=H*.515;
        shadowHeight=f.End?f.Height:Math.Min(d.Height+1,Math.Max(f.Height,d.Lift*f.Lift));
        if(frame>d.LastPour+2 && frame<d.RevealEnd){
            WorldFrame(d.Closed-1);Array.Copy(pixels,alternate,pixels.Length);WorldFrame(d.Closed);
            double t=(frame-d.LastPour-2.0)/(d.RevealEnd-d.LastPour-2.0);
            t=t*t*(3-2*t);
            for(int i=0;i<pixels.Length;i++)pixels[i]=MixColor(alternate[i],pixels[i],t);
        } else if(frame>=d.Ghost && frame<d.Ghost+34){
            WorldFrame(frame,1);Array.Copy(pixels,alternate,pixels.Length);WorldFrame(frame,2);
            double t=(frame-d.Ghost)/34.0;t=t*t*(3-2*t);
            for(int i=0;i<pixels.Length;i++)pixels[i]=MixColor(alternate[i],pixels[i],t);
            UpdateWorld(frame);
        } else if(frame>=d.Full+d.SealBegin && frame<d.Full+d.SealEnd){
            WorldFrame(frame,2);Array.Copy(pixels,alternate,pixels.Length);WorldFrame(frame,1);
            for(int i=0;i<pixels.Length;i++)pixels[i]=MixColor(alternate[i],pixels[i],solid);
        } else if(frame>=d.Full+d.FinalBegin && frame<d.Full+d.FinalEnd){
            double last=Sat((frame-d.Full-d.FinalBegin)/(double)(d.FinalEnd-d.FinalBegin));last=last*last*(3-2*last);
            WorldFrame(frame,2);Array.Copy(pixels,alternate,pixels.Length);WorldFrame(frame,1);
            for(int i=0;i<pixels.Length;i++)pixels[i]=MixColor(alternate[i],pixels[i],last);
        } else WorldFrame(frame);
        ToBitmap();Overlay(frame);return bmp;
    }
    public void Raw(Stream output,byte[] bgr){
        BitmapData data=bmp.LockBits(new Rectangle(0,0,W,H),ImageLockMode.ReadOnly,PixelFormat.Format32bppRgb);
        Marshal.Copy(data.Scan0,bgr,0,bgr.Length);bmp.UnlockBits(data);output.Write(bgr,0,bgr.Length);
    }
    public static void Main(string[] args){
        CultureInfo.CurrentCulture=CultureInfo.InvariantCulture;
        var d=new Data(args[0]);var shot=new Shot(d);
        if(args.Length<2){Console.Error.WriteLine("usage: SiloRender scene.bin frame DIR N... | stream [BEGIN END]");return;}
        if(args[1]=="frame"){
            Directory.CreateDirectory(args[2]);
            for(int j=3;j<args.Length;j++){
                int i=int.Parse(args[j]);
                shot.Render(i).Save(Path.Combine(args[2],"silo_"+i.ToString("000")+".png"),ImageFormat.Png);
            }
        } else {
            var bgr=new byte[W*H*4];
            using(Stream s=Console.OpenStandardOutput()){
                int begin=args.Length>2?int.Parse(args[2]):0,end=args.Length>3?int.Parse(args[3]):d.Frames.Length;
                for(int i=begin;i<end;i++){
                    shot.Render(i);shot.Raw(s,bgr);
                    if(i%100==0)Console.Error.WriteLine("Frame "+i+" / "+d.Frames.Length);
                }
            }
        }
    }
}
