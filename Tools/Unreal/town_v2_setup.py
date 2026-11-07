"""Create the isolated TownV2 map and accept single-use local task dispatch files."""
import json,os,pathlib,time,traceback,runpy
import unreal as u
ROOT=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT=ROOT/'Saved/TownV2/session-2';OUT.mkdir(parents=True,exist_ok=True)
MAP='/Game/Selene/Maps/TownV2'
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
if u.EditorAssetLibrary.does_asset_exist(MAP):
 if not levels.load_level(MAP):raise RuntimeError('Existing TownV2 load failed')
else:
 if not levels.new_level(MAP,False):raise RuntimeError('New level failed')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Script/Selene.SeleneGameMode'))
levels.save_current_level()
(OUT/'setup.json').write_text(json.dumps({'map':MAP,'created':True,'engine':u.SystemLibrary.get_engine_version(),'landscape':'pending UI import'},indent=2))
last=[0]
def dispatch(dt):
 if time.time()-last[0]<1:return
 last[0]=time.time();path=OUT/'dispatch.json'
 if not path.exists():return
 job=json.loads(path.read_text());path.rename(OUT/('dispatch-'+job['id']+'.json'))
 try:
  name=job['script']
  if not name.startswith('town_v2_') or '/' in name or not name.endswith('.py'):raise ValueError('Invalid task script')
  runpy.run_path(str(ROOT/'Tools/Unreal'/name),run_name='__main__')
  result={'id':job['id'],'status':'success'}
 except Exception:
  result={'id':job['id'],'status':'failed','error':traceback.format_exc()};u.log_error(result['error'])
 (OUT/('dispatch-'+job['id']+'-result.json')).write_text(json.dumps(result,indent=2))
handle=u.register_slate_post_tick_callback(dispatch)
