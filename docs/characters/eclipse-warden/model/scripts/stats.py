import bpy, sys, json, math
from mathutils import Vector
path=sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)
out={}
out["objects"]=[(o.name,o.type,[round(x,4) for x in o.scale],[round(math.degrees(x),1) for x in o.rotation_euler], o.parent.name if o.parent else None) for o in bpy.data.objects]
meshes=[o for o in bpy.data.objects if o.type=="MESH"]
arm=[o for o in bpy.data.objects if o.type=="ARMATURE"]
ms=[]
dg=bpy.context.evaluated_depsgraph_get()
for o in meshes:
    m=o.data
    tris=sum(len(p.vertices)-2 for p in m.polygons)
    quads=sum(1 for p in m.polygons if len(p.vertices)==4)
    ws=[v.co for v in m.vertices]
    wco=[o.matrix_world@c for c in ws]
    mn=[min(c[i] for c in wco) for i in range(3)]; mx=[max(c[i] for c in wco) for i in range(3)]
    infl=[len([g for g in v.groups if g.weight>0.001]) for v in m.vertices]
    unw=sum(1 for i in infl if i==0)
    ms.append(dict(name=o.name,verts=len(m.vertices),polys=len(m.polygons),tris=tris,quads=quads,
       bbox_min=[round(x,3) for x in mn],bbox_max=[round(x,3) for x in mx],
       mats=[s.material.name if s.material else None for s in o.material_slots],
       shapekeys=len(m.shape_keys.key_blocks) if m.shape_keys else 0,
       vgroups=len(o.vertex_groups),max_infl=max(infl) if infl else 0,unweighted=unw,
       infl_hist={k:infl.count(k) for k in sorted(set(infl))},
       uv_layers=len(m.uv_layers), has_normals_custom=m.has_custom_normals))
out["meshes"]=ms
out["images"]=[(i.name,list(i.size)) for i in bpy.data.images]
mats=[]
for m in bpy.data.materials:
    if not m.use_nodes: continue
    b=next((n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
    d={"name":m.name}
    if b:
        for k in ["Base Color","Metallic","Roughness","Normal","Emission Color"]:
            if k in b.inputs: d[k]="linked" if b.inputs[k].is_linked else "value"
    mats.append(d)
out["materials"]=mats
for a in arm:
    bones=a.data.bones
    out["armature"]=dict(name=a.name,scale=list(a.scale),nbones=len(bones),
      bones=[(b.name,b.parent.name if b.parent else None,[round(x,3) for x in (a.matrix_world@b.head_local)],round(b.length,3)) for b in bones])
out["actions"]=[(a.name,list(a.frame_range)) for a in bpy.data.actions]
print("JSON_START");print(json.dumps(out,indent=1));print("JSON_END")
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index("--")+2])
