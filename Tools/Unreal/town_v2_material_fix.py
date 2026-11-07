"""One diagnosed fix: bind imported mesh slots to the saved presentation material."""
import unreal as u,json,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));D='/Game/Selene/Materials/Ground';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);fixed=[]
for a in A.get_all_level_actors():
 if a.get_actor_label() in ['V2_V2TerrainCore','V2_V2TerrainRing','V2_V2Roads','V2_V2Sidewalks','V2_V2Curbs']:
  c=a.static_mesh_component;mesh=c.static_mesh;mat=c.get_material(0);assert mat;mesh.set_material(0,mat);u.EditorAssetLibrary.save_loaded_asset(mesh,False);fixed.append({'mesh':mesh.get_path_name(),'material':mat.get_path_name()})
assert len(fixed)==5
(R/'Saved/TownV2/session-3/material-fix.json').write_text(json.dumps(fixed,indent=2))
