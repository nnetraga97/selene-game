"""Free, deterministic bevelled curb and wall kit; metres, Blender +X length."""
import bpy
from pathlib import Path
out=Path(__file__).resolve().parents[2]/'Saved/Town/session-1/kit'
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name,dims,bevel in [('SM_TownCurb',(2,.32,.18),.035),('SM_TownRetainingWall',(2,.45,1),.045)]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,dims[2]/2))
 obj=bpy.context.object;obj.name=name;obj.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=obj.modifiers.new('Soft stone arris','BEVEL');mod.width=bevel;mod.segments=3
 bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.ops.object.transform_apply(location=True,rotation=False,scale=False)
 bpy.ops.export_scene.gltf(filepath=str(out/(name+'.glb')),export_format='GLB',use_selection=True)
 obj.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'town-kit.blend'))
