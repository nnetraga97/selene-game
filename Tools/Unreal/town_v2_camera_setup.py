"""Persist capture camera for -game (runtime Python omits deferred-spawn API), and Nanite usage."""
import unreal as u,json,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);M=u.MaterialEditingLibrary;D='/Game/Selene/Materials/Ground'
m=u.load_asset(D+'/M_V2_TerrainAuto');M.set_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE);M.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m,False)
cameras=[a for a in A.get_all_level_actors() if isinstance(a,u.CameraActor)]
assert not cameras,'Capture camera already exists'
a=A.spawn_actor_from_class(u.CameraActor,u.Vector(800,-2200,810));a.set_actor_label('V2_CaptureCamera');a.tags=[u.Name('V2Capture')];a.camera_component.set_field_of_view(70);a.camera_component.set_editor_property('constrain_aspect_ratio',False)
route=A.spawn_actor_from_class(u.load_class(None,'/Script/Selene.SelenePerfRoute'),u.Vector());route.set_actor_label('V2_PlazaWalkRoute');route.set_editor_property('route_name',u.Name('V2Plaza'));s=route.get_component_by_class(u.SplineComponent);s.clear_spline_points(False)
for e,n in [(-30,6),(-20,6),(-20,15),(-30,15)]:s.add_spline_point(u.Vector(n*100,e*100,635),u.SplineCoordinateSpace.WORLD,False)
for i in range(4):s.set_spline_point_type(i,u.SplinePointType.LINEAR,False)
s.update_spline()
E.save_current_level();(R/'Saved/TownV2/session-3/camera-setup.json').write_text(json.dumps({'camera':a.get_path_name(),'route':'V2Plaza','terrain_nanite_usage':'set and saved; verify in rendered reload'},indent=2))
