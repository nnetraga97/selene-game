"""Read-only source and saved-map audit before Session 7 placement."""
import unreal as u,json,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-7';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);M=u.MaterialEditingLibrary
out={'assets':{},'actors':[]}
for slug in ['metro-walkup', 'metro-brownstones', 'metro-glass-office', 'metro-lane-houses', 'metro-diner', 'artdeco-tower']:
 m=u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}');b=m.get_bounding_box();ns=m.get_editor_property('nanite_settings');mats=[]
 for slot in m.static_materials:
  mat=slot.material_interface;mats.append({'path':mat.get_path_name(),'textures':{str(x):(M.get_material_instance_texture_parameter_value(mat,x).get_path_name() if M.get_material_instance_texture_parameter_value(mat,x) else None) for x in M.get_texture_parameter_names(mat)}})
 out['assets'][slug]={'bounds':[[b.min.x,b.min.y,b.min.z],[b.max.x,b.max.y,b.max.z]],'nanite':ns.get_editor_property('enabled'),'collision':str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),'materials':mats}
for a in A.get_all_level_actors():
 p=a.get_actor_location();o,b=a.get_actor_bounds(False);r=a.get_actor_rotation();s=a.get_actor_scale3d();c=a.get_component_by_class(u.StaticMeshComponent)
 out['actors'].append({'label':a.get_actor_label(),'class':a.get_class().get_name(),'position':[p.x,p.y,p.z],'bounds_center':[o.x,o.y,o.z],'extent':[b.x,b.y,b.z],'rotation':[r.pitch,r.yaw,r.roll],'scale':[s.x,s.y,s.z],'mesh':c.static_mesh.get_path_name() if c and c.static_mesh else None})
before=json.loads((O/'audit-before.json').read_text());old={x['label']:x for x in before['actors']};now={x['label']:x for x in out['actors']}
out['changed_existing_actors']=[k for k,v in old.items() if now.get(k)!=v]
out['unexpected_missing']=[k for k in old if k not in now]
out['all_nanite']=all(x['nanite'] for x in out['assets'].values());out['all_complex_collision']=all('CTF_USE_COMPLEX_AS_SIMPLE' in x['collision'] for x in out['assets'].values())
out['ground_contacts']=[]
for key in ['Walkup','Brownstones','LaneHouses','Diner','ArtDeco','GlassOffice']:
 a=now['V7_'+key];pad=now['V7_'+key+'_Paving'];offset=1.65 if key=='Walkup' else 0;raw_base=(a['bounds_center'][2]-a['extent'][2])/100;base=raw_base+offset;top=(pad['bounds_center'][2]+pad['extent'][2])/100
 out['ground_contacts'].append({'building':key,'visible_base_m':base,'raw_bounds_base_m':raw_base,'visible_floor_offset_m':offset,'support_top_m':top,'gap_cm':round((base-top)*100,6)})
out['status']='verified' if not out['changed_existing_actors'] and not out['unexpected_missing'] and out['all_nanite'] and out['all_complex_collision'] and all(abs(x['gap_cm'])<.01 for x in out['ground_contacts']) else 'incomplete'
(O/'readback-final.json').write_text(json.dumps(out,indent=2))
