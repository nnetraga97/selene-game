import bpy
from mathutils import Vector
arm=bpy.data.objects["Armature"]
mesh=[o for o in bpy.data.objects if o.type=="MESH" and o.name!="Icosphere"][0]
W=arm.matrix_world; MW=mesh.matrix_world
hd=lambda n: W@arm.data.bones[n].head_local
gn={g.index:g.name for g in mesh.vertex_groups}
def report(label,parent_prefix,child_joint,axis_child_end,rad=0.06):
    j=hd(child_joint); e=hd(axis_child_end); d=(e-j).normalized()
    import collections
    bins=collections.OrderedDict()
    for v in mesh.data.vertices:
        p=MW@v.co; t=(p-j).dot(d)
        if (p-j-d*t).length>0.09 or t<-0.08 or t>0.12: continue
        b=round(t/0.02)*0.02
        wp=sum(g.weight for g in v.groups if gn[g.group].startswith(parent_prefix))
        s=bins.setdefault(b,[0,0.0,0,0]); s[0]+=1; s[1]+=wp; s[2]+= wp>0.9; s[3]+= wp<0.1
    print(label,"(t = metres past joint along child; mean parent-side weight; n fully parent; n fully child)")
    for b in sorted(bins): n,sw,fp,fc=bins[b]; print(f"  t={b:+.2f} n={n:5d} meanParent={sw/n:.2f} fullParent={fp} fullChild={fc}")
report("KNEE_L","thigh","calf_l","foot_l")
report("KNEE_R","thigh","calf_r","foot_r")
report("ELBOW_L","upperarm","lowerarm_l","hand_l")
report("ELBOW_R","upperarm","lowerarm_r","hand_r")
# symmetric check and merged topology
import bmesh
bm=bmesh.new(); bm.from_mesh(mesh.data); n0=len(bm.verts)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
print("MERGED_VERTS",n0,"->",len(bm.verts),"nonmanifold",sum(1 for e in bm.edges if not e.is_manifold),"boundary",sum(1 for e in bm.edges if e.is_boundary))
seen=set();parts=[]
for v in bm.verts:
    if v in seen: continue
    st=[v];seen.add(v);n=0
    while st:
        x=st.pop();n+=1
        for e in x.link_edges:
            o=e.other_vert(x)
            if o not in seen: seen.add(o);st.append(o)
    parts.append(n)
parts.sort(reverse=True);print("PARTS_AFTER_MERGE",len(parts),parts[:12])
