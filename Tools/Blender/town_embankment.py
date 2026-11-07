"""Continuous terrain skirt, shared layout axes; replaces rejected discrete mounds."""
import bpy,sys,math,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Tools/Blockout'))
from layout_core import height
layout=json.loads((ROOT/'Design/Blockout/layout.json').read_text())
out=ROOT/'Saved/Town/session-1/kit'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# One closed strip, joined corners; original gameplay ground remains unchanged.
edge=[]
for i in range(48):edge.append((-240+480*i/48,-200))
for i in range(40):edge.append((240,-200+400*i/40))
for i in range(48):edge.append((240-480*i/48,200))
for i in range(40):edge.append((-240,200-400*i/40))
verts=[];faces=[]
for d in [0,8,20,40,70,100,130]:
 t=d/130
 for x,y in edge:
  px=x*(1+d/240);py=y*(1+d/200)
  north=max(0,min(1,(y-80)/120));east=max(0,min(1,(x-120)/120))
  ridge=3+north*(26+5*math.sin(x*.025))+east*(8+4*math.sin(y*.039))
  z=height(layout,x,y)*(1-t)+ridge*math.sin(math.pi*t)-18*t
  verts.append((py,-px,z))
n=len(edge)
for ring in range(6):
 for i in range(n):
  a=ring*n+i;b=ring*n+(i+1)%n;c=(ring+1)*n+(i+1)%n;e=(ring+1)*n+i
  faces.extend([(a,c,b),(a,e,c)])
mesh=bpy.data.meshes.new('ContinuousEarthSkirt');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('SM_TownEarthSkirt',mesh);bpy.context.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
# Consistent upward winding from actual geometry; force upward top-facing normals.
for poly in mesh.polygons:
 if poly.normal.z<0: poly.flip()
 poly.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(out/'town-embankment.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'SM_TownEarthSkirt.glb'),export_format='GLB',use_selection=True,export_yup=True)
print('terrain skirt',len(verts),'vertices',len(faces),'triangles')
