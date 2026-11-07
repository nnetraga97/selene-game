"""Import the single road-grading correction, then save and audit exact imported bounds."""
import unreal as u,json,pathlib,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-3';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);LIB=u.EditorAssetLibrary;D='/Game/Selene/Materials/Ground';ENV='/Game/Selene/Environment/TownV2';rep=[]
assert not (O/'grade-import.json').exists(),'Grade correction already recorded'
for name,matname in [('V2TerrainCore','M_V2_TerrainAuto'),('V2TerrainRing','M_V2_TerrainAuto'),('V2Roads','MI_Town_Road'),('V2Sidewalks','MI_Town_Plaza'),('V2Curbs','MI_Town_Curb')]:
 manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',True);dest=ENV+'/'+name;assert manager.import_asset(dest,manager.create_source_data(str(O/'meshes'/(name+'.glb'))),params)
 meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)];assert len(meshes)==1;mesh=meshes[0];mat=u.load_asset(D+'/'+matname);mesh.set_material(0,mat);mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);LIB.save_loaded_asset(mesh,False)
 for a in A.get_all_level_actors():
  if a.get_actor_label()=='V2_'+name:a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,mat)
 rep.append(mesh.get_path_name())
E.save_current_level();(O/'grade-import.json').write_text(json.dumps({'status':'saved','meshes':rep},indent=2))
