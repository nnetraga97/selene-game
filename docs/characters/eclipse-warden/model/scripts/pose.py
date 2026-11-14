import bpy, sys, math, bmesh
from mathutils import Vector, Matrix
out=sys.argv[sys.argv.index("--")+1]
arm=bpy.data.objects["Armature"]
mesh=[o for o in bpy.data.objects if o.type=="MESH" and o.name!="Icosphere"][0]
ico=bpy.data.objects.get("Icosphere")
if ico: bpy.data.objects.remove(ico)
# loose parts
bm=bmesh.new(); bm.from_mesh(mesh.data)
seen=set(); parts=[]
for v in bm.verts:
    if v.index in seen: continue
    st=[v]; seen.add(v.index); n=0
    while st:
        x=st.pop(); n+=1
        for e in x.link_edges:
            o=e.other_vert(x)
            if o.index not in seen: seen.add(o.index); st.append(o)
    parts.append(n)
parts.sort(reverse=True)
print("ARM_WORLD",[list(map(lambda x:round(x,3),r)) for r in arm.matrix_world]);print("ROTMODES",[(o.name,o.rotation_mode,tuple(round(x,3) for x in o.rotation_quaternion)) for o in bpy.data.objects]);print("LOOSE_PARTS",len(parts),parts[:15])
nonman=sum(1 for e in bm.edges if not e.is_manifold); print("NONMANIFOLD_EDGES",nonman)
bm.free()
scn=bpy.context.scene
scn.render.engine='BLENDER_WORKBENCH'
sh=scn.display.shading
sh.light='STUDIO'; sh.show_cavity=True; sh.cavity_type='BOTH'; sh.show_shadows=False
scn.render.resolution_x=900; scn.render.resolution_y=900
scn.render.film_transparent=False
scn.world=bpy.data.worlds.new("w"); scn.world.color=(0.35,0.37,0.42)
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); scn.collection.objects.link(cam); scn.camera=cam
cam.data.type='ORTHO'
def shot(name,target,direction,scale,tex=True,res=(900,900)):
    sh.color_type='TEXTURE' if tex else 'SINGLE'
    sh.single_color=(0.75,0.75,0.75)
    t=Vector(target); d=Vector(direction).normalized()
    cam.location=t+d*5
    cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale
    scn.render.resolution_x,scn.render.resolution_y=res
    scn.render.filepath=f"{out}/{name}.png"
    bpy.ops.render.render(write_still=True)
pb=arm.pose.bones
def rot(name,axis,deg):
    b=pb[name]; bpy.context.view_layer.update()
    W=arm.matrix_world
    M=W@b.matrix; h=M.to_translation()
    R=Matrix.Rotation(math.radians(deg),4,Vector(axis))
    b.matrix=W.inverted()@(Matrix.Translation(h)@R@Matrix.Translation(-h)@M)
    bpy.context.view_layer.update()
def reset():
    for b in pb: b.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def wpos(name):
    bpy.context.view_layer.update(); return arm.matrix_world@pb[name].head
F=(0,-1,0); Bk=(0,1,0); L=(1,0,0); Rt=(-1,0,0)
# rest
shot("00_rest_front",(0,0,0.5),F,1.1,res=(900,1100))
shot("00_rest_back",(0,0,0.5),Bk,1.1,res=(900,1100))
shot("00_rest_side",(0,0,0.5),L,1.1,res=(900,1100))
shot("00_rest_front_clay",(0,0,0.5),F,1.1,tex=False,res=(900,1100))
shot("01_face_front",(0,0,0.93),F,0.2)
shot("01_face_side",(0,0,0.93),L,0.2)
shot("01_face_clay",(0,0,0.93),(0.4,-1,0.1),0.2,tex=False)
h=wpos("hand_l")
shot("02_hand_rest_top",tuple(h+Vector((0.04,0,0))),(0,0,1),0.16,tex=False)
shot("02_hand_rest_front",tuple(h+Vector((0.04,0,0))),F,0.16,tex=False)
# arms down (A/idle) + shoulders
for a in (75,):
    reset(); rot("upperarm_l",(0,1,0),a); rot("upperarm_r",(0,1,0),-a)
    shot("03_armsdown_front",(0,0,0.5),F,1.1,res=(900,1100)); shot("03_armsdown_back",(0,0,0.5),Bk,1.1,res=(900,1100))
    shot("03_shoulder_front_clay",(0.08,0,0.8),F,0.3,tex=False); shot("03_shoulder_back_clay",(0.08,0,0.8),Bk,0.3,tex=False)
# arms overhead
reset(); rot("clavicle_l",(0,1,0),-20); rot("clavicle_r",(0,1,0),20); rot("upperarm_l",(0,1,0),-60); rot("upperarm_r",(0,1,0),60)
shot("04_armsup_front",(0,0,0.6),F,1.3,res=(900,1100)); shot("04_armsup_clay",(0.06,0,0.85),F,0.35,tex=False)
# elbows
for a in (90,140):
    reset(); rot("lowerarm_l",(0,0,1),-a); rot("lowerarm_r",(0,0,1),a)
    e=wpos("lowerarm_l")
    shot(f"05_elbow{a}_top",tuple(e),(0,0,1),0.3); shot(f"05_elbow{a}_top_clay",tuple(e),(0,0,1),0.3,tex=False)
    shot(f"05_elbow{a}_under_clay",tuple(e),(0.3,-0.3,-1),0.3,tex=False)
# knees: standing leg curl and squat
for a in (90,140):
    reset(); rot("calf_l",(1,0,0),a)
    k=wpos("calf_l")
    shot(f"06_knee{a}_side",tuple(k),L,0.4); shot(f"06_knee{a}_side_clay",tuple(k),L,0.4,tex=False)
    shot(f"06_knee{a}_front_clay",tuple(k),F,0.4,tex=False)
    shot(f"06_knee{a}_back_clay",tuple(k),(0.5,1,0),0.4,tex=False)
reset(); 
for s in "lr":
    rot("thigh_"+s,(1,0,0),-100); rot("calf_"+s,(1,0,0),130); rot("foot_"+s,(1,0,0),-30)
shot("07_squat_side",(0,-0.1,0.45),L,1.0); shot("07_squat_front",(0,-0.1,0.45),F,1.0)
shot("07_squat_side_clay",(0,-0.15,0.5),L,0.6,tex=False); shot("07_squat_34_clay",(0,-0.15,0.5),(1,-1,0.3),0.7,tex=False)
# high step / hip
reset(); rot("thigh_l",(1,0,0),-90); rot("calf_l",(1,0,0),90)
shot("08_hip_side_clay",(0,-0.1,0.5),L,0.6,tex=False); shot("08_hip_front_clay",(0,-0.1,0.5),F,0.6,tex=False)
reset(); rot("thigh_l",(0,1,0),-45)
shot("08_hip_abduct_clay",(0.1,0,0.45),F,0.7,tex=False)
# fist
reset()
for f in ("index","middle","ring","pinky"):
    for j,a in (("01",80),("02",95),("03",70)):
        rot(f"{f}_{j}_l",(0,1,0),a)
rot("thumb_01_l",(0,0,1),-30); rot("thumb_02_l",(0,1,0),40); rot("thumb_03_l",(0,1,0),50)
h=wpos("hand_l")
shot("09_fist_front_clay",tuple(h+Vector((0.03,0,-0.01))),F,0.14,tex=False); shot("09_fist_under_clay",tuple(h+Vector((0.03,0,-0.01))),(0.3,-0.4,-1),0.14,tex=False)
shot("09_fist_tex",tuple(h+Vector((0.03,0,-0.01))),(0.5,-1,0.4),0.14)
# wrist bend + forearm twist
reset(); rot("hand_l",(0,1,0),70)
shot("10_wrist_down_clay",tuple(wpos("hand_l")),F,0.2,tex=False)
reset(); rot("hand_l",(1,0,0),90); rot("lowerarm_twist_01_l",(1,0,0),60); rot("lowerarm_twist_02_l",(1,0,0),30)
shot("10_forearm_twist_clay",tuple(wpos("lowerarm_l")+Vector((0.06,0,0))),F,0.3,tex=False)
# head turn, spine bend, twist
reset(); rot("head",(0,0,1),60); rot("neck_01",(0,0,1),15)
shot("11_headturn",(0,0,0.9),F,0.3)
reset(); rot("spine_01",(1,0,0),-25); rot("spine_03",(1,0,0),-25); rot("spine_05",(1,0,0),-20)
shot("11_bend_fwd_side",(0,-0.15,0.6),L,0.9)
reset(); rot("spine_02",(0,0,1),25); rot("spine_04",(0,0,1),25)
shot("11_twist_front_clay",(0,0,0.7),F,0.6,tex=False)
# foot
reset(); rot("foot_l",(1,0,0),-40); rot("ball_l",(1,0,0),40)
shot("12_foot_clay",tuple(wpos("foot_l")+Vector((0,-0.03,-0.02))),L,0.25,tex=False)
