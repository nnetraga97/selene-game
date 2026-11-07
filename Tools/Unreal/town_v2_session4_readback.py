"""Fresh process readback of the saved Session 4 checkpoint; no mutations."""
import unreal as u,json,pathlib,collections
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-4';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);M=u.MaterialEditingLibrary;actors=A.get_all_level_actors();rep={'actor_count':len(actors),'classes':dict(collections.Counter(a.get_class().get_name() for a in actors)),'buildings':[],'ground':[],'village_buildings':[],'rect_lights':[],'missing_recorded_actors':[],'duplicates':[]}
labels=collections.Counter(a.get_actor_label() for a in actors);rep['duplicates']=[k for k,v in labels.items() if v>1 and k.startswith(('V2_','V4_'))];bylabel={a.get_actor_label():a for a in actors};records=json.loads((O/'apply.json').read_text())
for x in records['placements']:
 a=bylabel.get(x['actor'])
 if not a:rep['missing_recorded_actors'].append(x['actor']);continue
 c=a.static_mesh_component;m=c.get_material(0);color=M.get_material_instance_vector_parameter_value(m,'BaseColorFactor');p=a.get_actor_location();rep['buildings'].append({'actor':a.get_actor_label(),'mesh':c.static_mesh.get_path_name(),'material':m.get_path_name(),'tint':[color.r,color.g,color.b,color.a],'position_cm':[p.x,p.y,p.z],'collision':str(c.get_collision_enabled()),'scale':str(a.get_actor_scale3d()),'yaw':a.get_actor_rotation().yaw})
for a in actors:
 cls=a.get_class().get_name();label=a.get_actor_label()
 if 'BP_BLD_house' in cls:rep['village_buildings'].append(label)
 if isinstance(a,u.RectLight):rep['rect_lights'].append(label)
 if label in ['V4_Roads','V4_Paving','V4_Parking','V4_Curbs']:
  c=a.static_mesh_component;m=c.static_mesh;b=m.get_bounding_box();rep['ground'].append({'actor':label,'mesh':m.get_path_name(),'material':c.get_material(0).get_path_name(),'saved_mesh_material':m.get_material(0).get_path_name(),'scale':str(a.get_actor_scale3d()),'bounds_cm':[[b.min.x,b.min.y,b.min.z],[b.max.x,b.max.y,b.max.z]],'collision':str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))})
rep['old_road_actors']=[a.get_actor_label() for a in actors if a.get_actor_label() in ['V2_V2Roads','V2_V2Sidewalks','V2_V2Curbs','V2_Plaza']];rep['cafe_sign']=str(bylabel['V4_CafeSign'].text_render.text) if 'V4_CafeSign' in bylabel else None;rep['status']='verified' if len(rep['buildings'])==29 and len(rep['ground'])==4 and not rep['village_buildings'] and not rep['missing_recorded_actors'] and not rep['duplicates'] and not rep['old_road_actors'] else 'incomplete';(O/'readback-final.json').write_text(json.dumps(rep,indent=2));u.log('V4_READBACK '+rep['status'])
