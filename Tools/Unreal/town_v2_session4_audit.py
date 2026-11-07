import unreal as u,json,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);M=u.MaterialEditingLibrary;out={'assets':{},'actors':[]}
for slug in ['shop-bakery-corner','shop-tool-repair','townhouse-terrace','apartment-curved','workshop-garage','clock-hall']:
 m=u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}');b=m.get_bounding_box();mats=[]
 for slot in m.static_materials:
  mat=slot.material_interface;mats.append({'path':mat.get_path_name(),'class':mat.get_class().get_name(),'vector':[str(x) for x in M.get_vector_parameter_names(mat)],'texture':[str(x) for x in M.get_texture_parameter_names(mat)],'textures':{str(x): (M.get_material_instance_texture_parameter_value(mat,x).get_path_name() if M.get_material_instance_texture_parameter_value(mat,x) else None) for x in M.get_texture_parameter_names(mat)}})
 out['assets'][slug]={'bounds':[[b.min.x,b.min.y,b.min.z],[b.max.x,b.max.y,b.max.z]],'materials':mats}
for a in A.get_all_level_actors():
 p=a.get_actor_location();o,b=a.get_actor_bounds(False);out['actors'].append({'label':a.get_actor_label(),'class':a.get_class().get_name(),'position':[p.x,p.y,p.z],'bounds_center':[o.x,o.y,o.z],'extent':[b.x,b.y,b.z],'rotation':str(a.get_actor_rotation())})
(R/'Saved/TownV2/session-4/audit.json').write_text(json.dumps(out,indent=2))
