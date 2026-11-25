"""Farm landscape for the full-rate review orbit. Dimensions are metres in facility world coordinates."""
import math
import random
import bpy
from mathutils import Vector

TAU = math.tau
rng = random.Random(4671)
mats = {}


def material(name, color, rough=.75, metal=0, grain=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    tree = m.node_tree
    bs = tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color,1)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if grain:
        pos=tree.nodes.new("ShaderNodeNewGeometry")
        noise=tree.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=grain
        noise.inputs["Detail"].default_value=3
        tree.links.new(pos.outputs["Position"],noise.inputs["Vector"])
        ramp=tree.nodes.new("ShaderNodeValToRGB")
        for el,fac in zip(ramp.color_ramp.elements,(.68,1.22)):
            el.color=(*(min(1,c*fac) for c in color),1)
        tree.links.new(noise.outputs["Fac"],ramp.inputs[0])
        tree.links.new(ramp.outputs[0],bs.inputs["Base Color"])
        bump=tree.nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value=min(.016,.32/grain)
        bump.inputs["Strength"].default_value=.18
        tree.links.new(noise.outputs["Fac"],bump.inputs["Height"]);tree.links.new(bump.outputs[0],bs.inputs["Normal"])
    mats[name]=m
    return m


class Geometry:
    def __init__(self):
        self.v=[]; self.f=[]; self.indices=[]; self.names=[]; self.smooth=[]
    def add(self, points, faces, mat, smooth=False):
        if mat not in self.names: self.names.append(mat)
        i=self.names.index(mat); base=len(self.v)
        self.v.extend(points)
        self.f.extend(tuple(base+k for k in face) for face in faces)
        self.indices.extend([i]*len(faces)); self.smooth.extend([smooth]*len(faces))
    def quad(self, points, mat):
        self.add(points,[(0,1,2,3)],mat)
    def box(self,x0,y0,z0,x1,y1,z1,mat):
        v=[(x,y,z) for z in (z0,z1) for y in (y0,y1) for x in (x0,x1)]
        self.add(v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],mat)
    def rod(self,p,q,r,mat,n=8,r2=None):
        p,q=Vector(p),Vector(q); d=q-p
        if d.length<.0001:return
        d.normalize(); u=d.cross(Vector((0,0,1)) if abs(d.z)<.94 else Vector((0,1,0))).normalized()
        v=d.cross(u); r2=r if r2 is None else r2
        verts=[tuple(c+(u*math.cos(TAU*i/n)+v*math.sin(TAU*i/n))*rad) for c,rad in ((p,r),(q,r2)) for i in range(n)]
        self.add(verts,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)
    def oval(self,c,scale,mat,n=12,rings=7,angle=0):
        pts=[]; co,si=math.cos(angle),math.sin(angle)
        for j in range(rings+1):
            lat=math.pi*(j/rings-.5)
            for i in range(n):
                rad=max(.006,math.cos(lat)); a=TAU*i/n
                x=scale[0]*rad*math.cos(a);y=scale[1]*rad*math.sin(a);z=scale[2]*math.sin(lat)
                pts.append((c[0]+co*x-si*z,c[1]+y,c[2]+si*x+co*z))
        self.add(pts,[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(rings) for i in range(n)],mat,True)
    def make(self,name):
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(self.v,[],self.f);mesh.update()
        for m in self.names:mesh.materials.append(mats[m])
        mesh.polygons.foreach_set("material_index",self.indices)
        mesh.polygons.foreach_set("use_smooth",self.smooth)
        return mesh


def place(name,mesh,xyz=(0,0,0)):
    o=bpy.data.objects.new(name,mesh); bpy.context.scene.collection.objects.link(o);o.location=xyz
    return o


def fence(g,x0,y0,x1,y1,steel=False):
    length=math.hypot(x1-x0,y1-y0); n=max(1,math.ceil(length/(2.35 if steel else 5.8)))
    for i in range(n+1):
        u=i/n; x=x0+(x1-x0)*u; y=y0+(y1-y0)*u
        g.rod((x,y,0),(x,y,1.52 if steel else 1.18),.067 if steel else .082,"rails" if steel else "timber",7)
    for h in ((.33,.69,1.04,1.40) if steel else (.42,.78,1.04)):
        g.rod((x0,y0,h),(x1,y1,h),.045 if steel else .014,"rails" if steel else "wire",6)


def roof(g,x,y,w,d,h,rise,mat):
    for sign in (-1,1):
        edge=x+sign*(w/2+.5)
        g.quad([(x,y-.56,h+rise),(edge,y-.56,h),(edge,y+d+.56,h),(x,y+d+.56,h+rise)],mat)
        g.rod((edge,y-.52,h-.045),(edge,y+d+.52,h-.045),.075,"rails")
        for j in range(math.ceil(d/.77)+1):
            yy=y-.45+j*.77
            g.rod((x,yy,h+rise+.022),(edge,yy,h+.022),.025,mat,5)
    g.rod((x,y-.63,h+rise+.06),(x,y+d+.63,h+rise+.06),.075,mat)
    for yy in (y,y+d):
        for sign in (-1,1):
            g.rod((x+sign*w/2,yy,h-.17),(x,yy,h+rise-.12),.085,"timber")
            g.rod((x+sign*w/2,yy,h-.17),(x,yy,h-.17),.077,"timber")


def shed(g,x,y,w,d,h,open_load=False,green=False):
    g.box(x-w/2-.3,y-.25,.018,x+w/2+.3,y+d+.25,.16,"slab")
    for j in range(4):
        yy=y+d*j/3
        for sign in (-1,1):
            xx=x+sign*w/2
            g.box(xx-.095,yy-.105,.14,xx+.095,yy+.105,h,"timber" if open_load else "rails")
            g.rod((xx,yy,h-1),(xx-sign*.9,yy,h),.07,"timber")
    roof(g,x,y,w,d,h,w*.16,"green roof" if green else "zinc")
    if open_load:return
    for side in (-1,1):
        xx=x+side*w/2
        g.box(xx-.07,y,.18,xx+.07,y+d,h-.10,"siding")
        for j in range(round(d/.67)):
            g.box(xx-.084,y+j*.67,.26,xx+.084,y+j*.67+.04,h-.16,"wall rib")
    g.box(x-w/2,y+d-.08,.18,x+w/2,y+d,h-.12,"siding")
    for side in (-1,1):
        a=x+side*w/2;b=x+side*w*.24
        g.box(min(a,b),y-.04,.18,max(a,b),y+.08,h-.10,"siding")
    g.box(x-w*.25,y-.07,h*.73,x+w*.25,y+.08,h-.11,"siding")


def stockyard(g,x,y,sign):
    # The reversing apron and race are on farm land north of the public carriageway.
    g.box(x-14,y-7,.017,x+14,y+11,.045,"gravel")
    shed(g,x,y+1.5,7,8.8,4.1,True,sign==1)
    centre=x+sign*.0
    # High truck end faces the road. The low end feeds from the holding pens.
    a,b=y+1.65,y+9.25; w=1.0
    g.quad([(centre-w,a,1.43),(centre+w,a,1.43),(centre+w,b,.20),(centre-w,b,.20)],"ramp")
    for j in range(17):
        u=j/16; yy=a+(b-a)*u; z=1.43-1.23*u
        g.rod((centre-w,yy,z+.025),(centre+w,yy,z+.025),.028,"rails",5)
    for side in (-1,1):
        xx=centre+side*w
        for j in range(5):
            u=j/4; yy=a+(b-a)*u; zz=1.43-1.23*u
            g.rod((xx,yy,.15),(xx,yy,zz+1.43),.065,"rails")
        for d in (.20,.62,1.04,1.42):
            g.rod((xx,a,1.43+d),(xx,b,.20+d),.045,"rails")
    g.box(x-13,y+10.5,.024,x+13,y+29,.052,"yard")
    fence(g,x-13,y+11,x-1,y+11,True);fence(g,x+1,y+11,x+13,y+11,True)
    for xx in (x-13,x+13): fence(g,xx,y+11,xx,y+29,True)
    fence(g,x-13,y+29,x+13,y+29,True)
    fence(g,x,y+14.5,x,y+29,True)
    for dx in (-1,1):fence(g,x+dx,y+9.4,x+4.2*dx,y+14,True)
    for dx in (-9,9):
        xx=x+dx; g.box(xx-.93,y+26.5,.07,xx+.93,y+27.1,.63,"slab")


def grain_silo(g,x,y,r,h):
    g.rod((x,y,.04),(x,y,.36),r+.30,"slab",72)
    g.rod((x,y,.36),(x,y,h),r,"zinc",80)
    g.rod((x,y,h),(x,y,h+r*.67),r+.13,"bright zinc",80,.17)
    for j in range(1,int(h/.28)):
        z=.35+j*.28
        for k in range(56):
            a=TAU*k/56;b=TAU*(k+1)/56
            g.rod((x+r*math.cos(a),y+r*math.sin(a),z),(x+r*math.cos(b),y+r*math.sin(b),z),.035,"bright zinc",4)
    for i in range(20):
        a=TAU*i/20
        g.rod((x+(r+.10)*math.cos(a),y+(r+.1)*math.sin(a),h+.02),(x+.17*math.cos(a),y+.17*math.sin(a),h+r*.67+.02),.038,"bright zinc",5)
    for dx in (-.25,.25):
        g.rod((x+dx,y-r-.25,.40),(x+dx,y-r-.25,h+.9),.046,"rails")
    for j in range(int(h/.38)):
        z=.6+j*.38;g.rod((x-.25,y-r-.25,z),(x+.25,y-r-.25,z),.033,"rails")
    g.rod((x+r+3,y-1,.28),(x+.4,y+.5,h+r*.67),.105,"rails",12)
    g.rod((x,y,h+r*.67),(x,y,h+r*.67+.35),.44,"bright zinc",24)


def cow_parts(colour):
    g=Geometry()
    g.oval((-.12,0,1.05),(.88,.35,.45),colour,20,10)
    g.oval((-.70,0,1.10),(.37,.37,.43),colour,14,8)
    g.oval((.45,0,1.16),(.40,.32,.41),colour,14,8)
    g.oval((-.52,0,.79),(.22,.19,.19),"udder",12,7)
    for end in (-1,1):
        for side in (-1,1):
            x=-.67 if end<0 else .45;y=.228*side
            dx=(.10 if end<0 else -.06)+.05*side
            g.rod((x,y,1.08),(x+dx,y,.58),.135,colour,9,.083)
            g.rod((x+dx,y,.59),(x-.065*side,y,.14),.081,"stocking",8,.052)
            g.oval((x-.065*side+.034,y,.075),(.107,.075,.068),"hoof",9,5)
    g.rod((-.93,.07,1.33),(-1.02,.14,.53),.026,colour,6,.018)
    g.oval((-1.02,.15,.47),(.045,.045,.11),"hoof",8,6)
    body=g.make("Grazing cow body "+colour)
    g=Geometry()
    g.oval((.24,0,-.22),(.43,.25,.23),colour,15,8,-.68)
    g.oval((.54,0,-.54),(.30,.21,.19),colour,15,8,-.85)
    g.oval((.68,0,-.73),(.15,.17,.105),"muzzle",13,7,-.30)
    for side in (-1,1):
        g.oval((.39,.24*side,-.37),(.145,.12,.068),colour,10,6,-.13)
        g.oval((.52,.177*side,-.48),(.037,.022,.032),"hoof",9,5)
        g.oval((.40,.30*side,-.406),(.038,.019,.048),"tag",6,5)
    return body,g.make("Grazing cow neck and head "+colour)


def herd():
    variants=[cow_parts(m) for m in ("Holstein","Hereford","Angus")]
    groups=[(67,39,12,19,10),(-69,-53,16,12,11),(65,83,17,10,8),(-44,156,12,5,6),(48,157,10,5,6)]
    for k,(x,y,dx,dy,count) in enumerate(groups):
        for j in range(count):
            body,head=variants[(j+k)%3];m=place(f"Grazing cow {k+1}.{j+1}",body,(x+rng.uniform(-dx,dx),y+rng.uniform(-dy,dy),.055))
            m.rotation_euler.z=rng.uniform(0,TAU);s=rng.uniform(.88,1.10);m.scale=(s,s,s)
            h=place("Grazing neck",head);h.parent=m;h.location=(.48,0,1.25)
            # Independent neck movement: muzzle reaches the pasture while the feet stay planted.
            phase=rng.uniform(0,TAU)
            for f in range(1,570,24):
                h.rotation_euler.y=.24+.18*math.sin(f*.027+phase)+.075*math.sin(f*.071+phase)
                h.keyframe_insert(data_path="rotation_euler",frame=f)


def crops(g):
    fields=[(40,-93,104,-67,"wheat"),(-98,-105,-44,-80,"corn"),(79,-37,126,2,"corn"),
            (26,50,82,65,"corn"),(14,166,61,192,"wheat"),(93,134,151,163,"wheat"),
            (-153,137,-95,166,"corn"),(-162,-47,-131,-7,"wheat")]
    for xa,ya,xb,yb,kind in fields:
        g.box(xa,ya,.012,xb,yb,.065,"soil")
        spacing=.85 if kind=="corn" else .54
        for i in range(int((xb-xa)/spacing)):
            x=xa+(i+.5)*spacing
            shade=("leaf1","leaf2","leaf3")[i%3] if kind=="corn" else ("grain1","grain2","grain3")[i%3]
            h=(1.22 if kind=="corn" else .68)*rng.uniform(.89,1.15)
            # Continuous row volume carries the field at distance; individual blades break the silhouette.
            g.quad([(x-.22,ya,.06),(x-.20,yb,.06),(x+.03,yb,h*.61),(x+.03,ya,h*.61)],shade)
            for j in range(int((yb-ya)/(.72 if kind=="corn" else .79))):
                y=ya+(j+.4)*(.72 if kind=="corn" else .79)+rng.uniform(-.10,.10)
                ht=h*rng.uniform(.78,1.16); side=(-1)**j
                if kind=="corn":
                    g.add([(x,y,.09),(x+.07,y+.035,ht*.57),(x+.015,y,ht),
                           (x+side*.32,y+.09,ht*.65),(x+side*.43,y+.17,ht*.49),
                           (x-side*.27,y-.14,ht*.81),(x-side*.38,y-.17,ht*.66)],
                          [(0,1,3),(1,4,3),(1,2,5),(2,6,5)],shade)
                else:
                    g.add([(x-.025,y,.12),(x+.038,y,.12),(x+.12,y+.14,ht),(x+.076,y+.08,ht*.70)],
                          [(0,1,2),(0,2,3)],shade)
    for xa,ya,xb,yb in ((49,24,85,53),(-89,-68,-49,-37),(44,70,86,98)):
        g.box(xa,ya,.018,xb,yb,.037,"pasture")
        for (a,b,c,d) in ((xa,ya,xb,ya),(xa,yb,xb,yb),(xa,ya,xa,yb),(xb,ya,xb,yb)):
            fence(g,a,b,c,d)


def landscape():
    for n,c,r,m,q in (("slab",(.35,.34,.285),.88,0,2),("asphalt",(.100,.109,.108),.84,0,21),
     ("gravel",(.39,.34,.25),.93,0,5),("white line",(.76,.73,.59),.8,0,5),("ditch",(.105,.19,.089),.96,0,1.5),
     ("timber",(.19,.139,.081),.86,0,3),("rails",(.29,.33,.32),.38,.68,0),("wire",(.24,.28,.25),.51,.67,0),
     ("zinc",(.42,.48,.50),.33,.72,6),("bright zinc",(.62,.66,.66),.31,.7,0),("green roof",(.14,.23,.195),.49,.51,4),
     ("siding",(.31,.33,.265),.68,.22,3),("wall rib",(.24,.26,.21),.69,.25,0),("yard",(.29,.229,.142),.92,0,3),
     ("ramp",(.29,.31,.29),.64,.30,7),("soil",(.14,.105,.068),.96,0,4),("pasture",(.136,.26,.09),.97,0,1.3),
     ("leaf1",(.102,.22,.071),.81,0,0),("leaf2",(.16,.29,.076),.81,0,0),("leaf3",(.184,.32,.09),.81,0,0),
     ("grain1",(.50,.395,.135),.88,0,0),("grain2",(.57,.465,.166),.88,0,0),("grain3",(.40,.348,.12),.88,0,0),
     ("Holstein",(.19,.13,.085),.82,0,0),("Hereford",(.29,.115,.060),.83,0,0),("Angus",(.077,.062,.05),.83,0,4),
     ("stocking",(.42,.38,.31),.87,0,0),("hoof",(.034,.034,.029),.78,0,0),("udder",(.45,.26,.18),.81,0,0),
     ("muzzle",(.22,.16,.14),.68,0,0),("tag",(.83,.49,.052),.65,0,0),("ridge1",(.18,.24,.21),.98,0,.016),
     ("ridge2",(.23,.29,.29),.98,0,.012)):material(n,c,r,m,q)
    for n,dark,light in (("Holstein",(.052,.050,.047),(.68,.66,.57)),("Hereford",(.23,.067,.034),(.65,.57,.44))):
        tree=mats[n].node_tree; tex=tree.nodes.new("ShaderNodeTexNoise");tex.inputs["Scale"].default_value=3.1
        coord=tree.nodes.new("ShaderNodeTexCoord");tree.links.new(coord.outputs["Object"],tex.inputs[0])
        ramp=tree.nodes.new("ShaderNodeValToRGB")
        for el,p,col in zip(ramp.color_ramp.elements,(.45,.52),(dark,light)):el.position=p;el.color=(*col,1)
        tree.links.new(tex.outputs["Fac"],ramp.inputs[0]);tree.links.new(ramp.outputs[0],tree.nodes.get("Principled BSDF").inputs["Base Color"])
    g=Geometry();crops(g)
    for centre,half,zz,col in ((116,6.0,.030,"gravel"),(116,3.9,.048,"asphalt")):
        g.box(-700,centre-half,.016,700,centre+half,zz,col)
    for y in (112.40,119.60):
        g.box(-700,y-.06,.051,700,y+.06,.057,"white line")
    for x in range(-692,700,12):
        g.box(x,115.94,.052,x+5.2,116.06,.06,"white line")
    for x in range(-250,251,17):
        if -120<x<-65 or 20<x<65 or -53<x<-25:continue
        for y in (109.55,122.35):
            g.box(x-.065,y-.065,.015,x+.065,y+.065,.80,"white line")
            g.box(x-.069,y-.069,.64,x+.069,y+.069,.74,"timber")
    for x in (-44,48):
        g.quad([(x-13,119.55,.066),(x+13,119.55,.066),(x+7,133,.068),(x-7,133,.068)],"gravel")
        stockyard(g,x,127,1 if x>0 else -1)
    shed(g,-68,139,9.8,16.5,4.3,False,True);shed(g,70,142,13,18,5.0)
    shed(g,103,-59,12,17,4.6,False,True);shed(g,-108,-74,10,14,4)
    grain_silo(g,79.5,132.6,3.6,11.2);grain_silo(g,-83,135.5,4.25,13.8)
    for j in range(7):
        x=-91+(j%4)*4.5;y=-74+(j//4)*3
        g.rod((x,y,.99),(x+2.3,y,.99),.94,"grain1",24)
    for y in (109.35,122.7):
        for xa,xb in ((-300,-124),(-64,-58),(-30,34),(63,85),(104,310)):
            g.quad([(xa,y-.62,.019),(xb,y-.62,.019),(xb,y+.62,.019),(xa,y+.62,.019)],"ditch")
    for name,c in (("foliage light",(.14,.225,.085)),("foliage deep",(.077,.15,.075)),("foliage sage",(.17,.24,.13))):
        material(name,c,.92,0,1.2)
    def tree(x,y,h):
        g.rod((x,y,.0),(x+.1,y,h*.75),h*.047,"timber",8,h*.016)
        for k in range(7):
            a=TAU*k/7+rng.uniform(-.3,.3); d=h*rng.uniform(.14,.28)
            cx,cy=x+math.cos(a)*d,y+math.sin(a)*d
            crown=h*rng.uniform(.20,.30)
            g.rod((x,y,h*.4),(cx,cy,h*.75),max(.05,h*.019),"timber",5)
            g.oval((cx,cy,h*rng.uniform(.66,.89)),(crown,crown*.91,crown*1.12),rng.choice(("foliage light","foliage deep","foliage sage")),9,5)
    for yy,xa,xb in ((163,-240,215),(77,94,240),(-111,-220,72),(31,115,262),(105,-185,-120),(215,-306,288),(-178,-151,146)):
        for j in range(int((xb-xa)/8)):
            x=xa+j*8+rng.uniform(-2,2)
            if rng.random()>.19:
                tree(x,yy+rng.uniform(-3.7,3.7),rng.uniform(4,9.5))
            if rng.random()>.31:
                g.oval((x+1,yy+.3,rng.uniform(.8,1.4)),(rng.uniform(3.1,5.3),rng.uniform(1.3,2.6),rng.uniform(.8,1.8)),"foliage sage",9,5)
    for j in range(21):
        tree(-127+rng.uniform(-2,2),-98+j*8.8,rng.uniform(4.5,7.2))
    place("Farmland • crops, livestock yards, two grain silos and public road",g.make("Rural ground and structures"))
    g=Geometry()
    for ring,mat in ((0,"ridge1"),(1,"ridge2")):
        n=260; pts=[];profiles=((0,0),(36,.18),(75,.57),(121,.91),(150,1),(191,.88))
        for distance,frac in profiles:
            for i in range(n):
                a=TAU*i/n;r=720+ring*420+distance+41*math.sin(a*5+.6)
                h=16+ring*21+7*math.sin(a*7+.4)+5*math.sin(a*13+ring)+3*math.cos(a*23)
                pts.append((r*math.cos(a),r*math.sin(a),-.35+h*frac))
        g.add(pts,[(k*n+i,(k+1)*n+i,(k+1)*n+(i+1)%n,k*n+(i+1)%n) for k in range(len(profiles)-1) for i in range(n)],mat,True)
        bs=mats[mat].node_tree.nodes.get("Principled BSDF")
        bs.inputs["Emission Color"].default_value=(.29,.32,.34,1) if ring==0 else (.39,.40,.42,1)
        bs.inputs["Emission Strength"].default_value=.49 if ring==0 else .56
    place("Beyond the farm • distant ridgelines",g.make("Low agricultural ridges"))
    herd()
