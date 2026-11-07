"""Fresh-process Session 5 saved-map readback. No mutations."""
import unreal as u,json,pathlib,collections,math
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-5';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=A.get_all_level_actors();by={a.get_actor_label():a for a in actors};labels=collections.Counter(a.get_actor_label() for a in actors);apply=json.loads((O/'apply.json').read_text());rep={'actor_count':len(actors),'duplicates':[k for k,v in labels.items() if v>1 and k.startswith(('V2_','V4_','V5_'))],'buildings':[],'missing':[],'nonuniform_buildings':[],'ground':[]}
old=json.loads((R/'Saved/TownV2/session-4/apply.json').read_text())['placements']
correction=json.loads((O/'correction.json').read_text())
for x in old+[x for x in apply['added'] if x['actor'] not in correction['rejected_buildings']]:
 a=by.get(x['actor'])
 if not a:rep['missing'].append(x['actor']);continue
 s=a.get_actor_scale3d();p=a.get_actor_location();b=a.static_mesh_component.static_mesh.get_bounding_box();origin,ext=a.get_actor_bounds(False)
 rep['buildings'].append({'actor':a.get_actor_label(),'mesh':a.static_mesh_component.static_mesh.get_path_name(),'center_m':[origin.y/100,origin.x/100,(origin.z-ext.z)/100],'scale':[s.x,s.y,s.z],'yaw':a.get_actor_rotation().yaw,'height_m':(b.max.z-b.min.z)*s.z/100})
 if max(s.x,s.y,s.z)-min(s.x,s.y,s.z)>.0001:rep['nonuniform_buildings'].append(a.get_actor_label())
for label in ['V5_V5Gardens','V5_V5GardenWalls','V5_V5GardenCaps']:
 a=by.get(label)
 if not a:rep['missing'].append(label);continue
 m=a.static_mesh_component.static_mesh;rep['ground'].append({'actor':label,'mesh':m.get_path_name(),'material':m.get_material(0).get_path_name(),'collision':str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))})
rep['v5_actors']=sum(a.get_actor_label().startswith('V5_') for a in actors);rep['status']='verified' if not rep['duplicates'] and not rep['missing'] and not rep['nonuniform_buildings'] and len(rep['buildings'])==33 else 'incomplete';(O/'readback-final.json').write_text(json.dumps(rep,indent=2));u.log('V5_READBACK '+rep['status'])
