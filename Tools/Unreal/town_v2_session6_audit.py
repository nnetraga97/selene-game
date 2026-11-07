"""Read-only source and saved-map audit before Session 6 placement."""
import unreal as u,json,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-6';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);S=u.get_editor_subsystem(u.StaticMeshEditorSubsystem);M=u.MaterialEditingLibrary
out={'assets':{},'actors':[]}
for slug in ['seaside-guesthouse','seaside-lighthouse-house','harbour-boathouse','artdeco-tower']:
 m=u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}');b=m.get_bounding_box();ns=m.get_editor_property('nanite_settings');mats=[]
 for slot in m.static_materials:
  mat=slot.material_interface;mats.append({'path':mat.get_path_name(),'textures':{str(x):(M.get_material_instance_texture_parameter_value(mat,x).get_path_name() if M.get_material_instance_texture_parameter_value(mat,x) else None) for x in M.get_texture_parameter_names(mat)}})
 out['assets'][slug]={'bounds':[[b.min.x,b.min.y,b.min.z],[b.max.x,b.max.y,b.max.z]],'nanite':ns.get_editor_property('enabled'),'collision':str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),'materials':mats}
for a in A.get_all_level_actors():
 p=a.get_actor_location();o,b=a.get_actor_bounds(False);r=a.get_actor_rotation();s=a.get_actor_scale3d();c=a.get_component_by_class(u.StaticMeshComponent)
 out['actors'].append({'label':a.get_actor_label(),'class':a.get_class().get_name(),'position':[p.x,p.y,p.z],'bounds_center':[o.x,o.y,o.z],'extent':[b.x,b.y,b.z],'rotation':[r.pitch,r.yaw,r.roll],'scale':[s.x,s.y,s.z],'mesh':c.static_mesh.get_path_name() if c and c.static_mesh else None})
(O/'audit-before.json').write_text(json.dumps(out,indent=2))
