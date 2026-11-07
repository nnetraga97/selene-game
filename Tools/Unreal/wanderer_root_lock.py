"""Use normal real-root reference-pose locking where measured first-frame origins displace playback. No bone keys are edited."""
import json,os,traceback,math
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'running','changed':[]}
try:
 before=json.loads((ROOT/'Saved/WandererHookup/session-1/root-separated-measure/report.json').read_text());assert before['status']=='success'
 for c in before['clips']:
  if '/GASP/' not in c['asset']:continue
  assert c['asset'].startswith('/Game/Selene/Characters/Wanderer/RootSeparated/')
  a=u.load_asset(c['asset']);root=c['runtime']['summary']['root']
  # A true root has its own authored origin. REF_POSE preserves this imported root's nonidentity bind rotation.
  # Set uniformly for the GASP set so transitions blend with the template's existing REF_POSE behavior.
  a.set_editor_property('enable_root_motion',False);a.set_editor_property('force_root_lock',True);a.set_editor_property('root_motion_root_lock',u.RootMotionRootLock.REF_POSE)
  assert u.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=False)
  report['changed'].append({'asset':c['asset'],'role':c['role'],'before_root_first':root['first'],'before_flags':c['flags'],'after_root_lock':'REF_POSE','bone_tracks_edited':False})
 report['status']='success'
except Exception:report.update(status='failed',error=traceback.format_exc())
OUT.write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='success':raise RuntimeError(report['error'])
