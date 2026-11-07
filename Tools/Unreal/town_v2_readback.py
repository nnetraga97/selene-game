"""Read-only saved TownV2 audit after captures; no map/asset saves."""
import unreal as u,json,pathlib,collections
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=A.get_all_level_actors();labels=collections.Counter(a.get_actor_label() for a in actors);out={'actor_count':len(actors),'classes':dict(collections.Counter(a.get_class().get_name() for a in actors)),'duplicate_labels':{k:v for k,v in labels.items() if v>1},'landscapes':sum(isinstance(a,u.LandscapeProxy) for a in actors),'terrains':[],'player_starts':[],'cameras':[]}
for a in actors:
 if a.get_actor_label().startswith('V2_V2'):
  c=a.static_mesh_component;m=c.static_mesh;b=m.get_bounding_box();out['terrains'].append({'actor':a.get_actor_label(),'mesh':m.get_path_name(),'material':c.get_material(0).get_path_name(),'mesh_material':m.get_material(0).get_path_name(),'collision':str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag')),'scale':str(a.get_actor_scale3d())})
 if isinstance(a,u.PlayerStart):out['player_starts'].append({'label':a.get_actor_label(),'position':str(a.get_actor_location())})
 if isinstance(a,u.CameraActor):out['cameras'].append({'label':a.get_actor_label(),'tags':[str(t) for t in a.tags]})
m=u.load_asset('/Game/Selene/Materials/Ground/M_V2_TerrainAuto');out['terrain_nanite_usage']=u.MaterialEditingLibrary.has_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE)
out['hero_actors']=[a.get_actor_label() for a in actors if a.get_actor_label().startswith(('V2_Hero_','V2_Cafe_'))]
out['route_actors']=[a.get_actor_label() for a in actors if a.get_class().get_name()=='SelenePerfRoute']
out['underworld_actors']=[a.get_actor_label() for a in actors if a.get_actor_location().z < -50000]
(R/'Saved/TownV2/session-3/readback.json').write_text(json.dumps(out,indent=2));u.log('V2_READBACK '+json.dumps(out))
