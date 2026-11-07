"""Read back the early Session 2 checkpoint, then exit this owned editor normally."""
import unreal as u,json,pathlib,hashlib
ROOT=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=ROOT/'Saved/TownV2/session-2'
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
if world.get_name()!='TownV2':raise RuntimeError('Wrong checkpoint world')
levels.save_current_level()
if not levels.load_level('/Game/Selene/Maps/TownV2'):raise RuntimeError('Checkpoint reload failed')
a=actors.get_all_level_actors()
report={'status':'empty_map_saved_and_reloaded','map':'/Game/Selene/Maps/TownV2','actor_count':len(a),'actors':[{'label':x.get_actor_label(),'class':x.get_class().get_name()} for x in a],'landscape_count':sum(isinstance(x,u.LandscapeProxy) for x in a),'placed_from_fantastic_village':0,'placed_tripo_heroes':0,'fps':None,'captures':[],'stop_reason':'Repeated native UI mode-selection input produced no visible change; cause unresolved, brief stop rule triggered','unmet':['Landscape import','road splines and sea','plaza/building placement','PCG dressing and palette pass','eye-level captures','movement and FPS verification'],'default_map_changed':False}
(OUT/'checkpoint.json').write_text(json.dumps(report,indent=2));u.SystemLibrary.quit_editor()
