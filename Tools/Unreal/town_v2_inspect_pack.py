import unreal as u,json,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));E=u.get_editor_subsystem(u.LevelEditorSubsystem);E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);out={}
for i in range(1,15):
 cls=u.EditorAssetLibrary.load_blueprint_class(f'/Game/Fantastic_Village_Pack/blueprints/buildings/BP_BLD_house_{i}');a=A.spawn_actor_from_class(cls,u.Vector(0,0,-100000));out[str(i)]=list(sorted(set(c.static_mesh.get_name() for c in a.get_components_by_class(u.StaticMeshComponent) if c.static_mesh)));A.destroy_actor(a)
(R/'Saved/TownV2/session-3/pack-components.json').write_text(json.dumps(out,indent=2))
