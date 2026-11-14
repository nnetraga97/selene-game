import bpy, sys, collections
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:]; outblend=a[0]; H_KNEE=float(a[1]); H_ELB=float(a[2]); SHIFT=float(a[3]) if len(a)>3 else 0.0
arm=bpy.data.objects["Armature"]
mesh=[o for o in bpy.data.objects if o.type=="MESH" and o.name!="Icosphere"][0]
ico=bpy.data.objects.get("Icosphere")
if ico: bpy.data.objects.remove(ico)
W=arm.matrix_world; MW=mesh.matrix_world
hd=lambda n: W@arm.data.bones[n].head_local
vg=mesh.vertex_groups; gi={g.name:g.index for g in vg}
def sm(x): x=max(0.0,min(1.0,x)); return x*x*x*(x*(6*x-15)+10)
def fix(par,chi,joint,end,h,R=0.14,rad=0.10,bend=None):
    P=[gi[n] for n in par]; C=[gi[n] for n in chi]; PC=set(P+C)
    j=hd(joint); d=(hd(end)-j).normalized()
    verts=[]
    refP=collections.Counter(); refC=collections.Counter()
    for v in mesh.data.vertices:
        p=MW@v.co; t=(p-j).dot(d); r=(p-j-d*t)
        if abs(t)>R or r.length>rad: continue
        w={g.group:g.weight for g in v.groups}
        wpc=sum(w.get(i,0) for i in PC)
        if wpc<0.5: continue
        if -0.09<t<-0.05:
            for i in P: refP[i]+=w.get(i,0)
        if 0.09<t<0.13:
            for i in C: refC[i]+=w.get(i,0)
        verts.append((v.index,t,r,w,wpc))
    def norm(c):
        s=sum(c.values()); return {k:x/s for k,x in c.items() if x/s>0.02}
    refP=norm(refP); refC=norm(refC)
    n=0
    for idx,t,r,w,wpc in verts:
        # optional tilt: shift blend centre along the bend direction (front of knee keeps parent a bit longer)
        tt=t-SHIFT
        if bend is not None and r.length>1e-6: tt-= 0.25*h*(r.normalized().dot(bend))
        f=1.0-sm((tt+h)/(2*h))      # parent fraction
        # fade the correction in at the region edge so nothing pops
        k=sm((R-abs(t))/0.03)
        curP=sum(w.get(i,0) for i in P)/wpc
        f=curP+(f-curP)*k
        def dist(ids,ref):
            s=sum(w.get(i,0) for i in ids)
            if s>0.05*wpc:
                top=sorted(ids,key=lambda i:-w.get(i,0))[:2]; s2=sum(w.get(i,0) for i in top)
                return {i:w.get(i,0)/s2 for i in top if w.get(i,0)>0}
            top=sorted(ref,key=lambda i:-ref[i])[:2]; s2=sum(ref[i] for i in top)
            return {i:ref[i]/s2 for i in top}
        new={}
        if f>0.001:
            for i,x in dist(P,refP).items(): new[i]=wpc*f*x
        if f<0.999:
            for i,x in dist(C,{C[0]:1.0}).items(): new[i]=wpc*(1-f)*x
        for i in PC:
            if i in w: vg[i].remove([idx])
        for i,x in new.items():
            if x>0.001: vg[i].add([idx],x,'REPLACE')
        n+=1
    print("FIXED",joint,n,"refP",{vg[i].name:round(x,2) for i,x in refP.items()},"refC",{vg[i].name:round(x,2) for i,x in refC.items()})
fwd=Vector((0,-1,0))
for s in "lr":
    fix([f"thigh_{s}",f"thigh_twist_01_{s}",f"thigh_twist_02_{s}"],[f"calf_{s}",f"calf_twist_01_{s}",f"calf_twist_02_{s}"],f"calf_{s}",f"foot_{s}",H_KNEE,bend=fwd)
    fix([f"upperarm_{s}",f"upperarm_twist_01_{s}",f"upperarm_twist_02_{s}"],[f"lowerarm_{s}",f"lowerarm_twist_01_{s}",f"lowerarm_twist_02_{s}"],f"lowerarm_{s}",f"hand_{s}",H_ELB,R=0.11,rad=0.07,bend=Vector((0,1,0)))
# limit to 4 influences and normalise
mx=0
for v in mesh.data.vertices:
    gs=sorted(v.groups,key=lambda g:-g.weight)
    for g in gs[4:]: vg[g.group].remove([v.index])
    gs=[g for g in v.groups]; s=sum(g.weight for g in gs)
    for g in gs: g.weight=g.weight/s
    mx=max(mx,len(gs))
print("MAX_INFL",mx)
bpy.ops.wm.save_as_mainfile(filepath=outblend)
bpy.ops.export_scene.gltf(filepath=outblend.replace('.blend','.glb'),export_format='GLB',export_yup=True,export_skins=True,export_animations=False)
