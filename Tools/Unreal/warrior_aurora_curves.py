"""Warrior: load the Aurora-retargeted clips in the editor so their curve names are added to the skeleton, then save both.
Without this, -game crashes in UAnimSequenceBase::PostLoad (AccumulateCurveMetaData opens an editor transaction)."""
import json,os,traceback
from pathlib import Path
import unreal as u
OUT=Path(os.environ['SELENE_STAGE_REPORT']);report={'status':'running'};LIB=u.EditorAssetLibrary
def main():
 skel=u.load_asset('/Game/Assets/eclipse-warrior/eclipse-warrior/SkeletalMeshes/eclipse-warrior_Skeleton');assert skel
 paths=LIB.list_assets('/Game/Selene/Characters/Warrior/Anims/Aurora',recursive=True);report['clips']=[]
 for p in paths:
  a=u.load_asset(p)
  if isinstance(a,u.AnimSequence):
   names=[str(n) for n in u.AnimationLibrary.get_animation_curve_names(a,u.RawCurveTrackTypes.RCT_FLOAT)]
   report['clips'].append({'asset':p,'curves':names});assert LIB.save_loaded_asset(a,only_if_is_dirty=False)
 assert LIB.save_loaded_asset(skel,only_if_is_dirty=False)
 report['status']='success'
try:main()
except Exception:report.update(status='failed',error=traceback.format_exc())
OUT.write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='success':raise RuntimeError(report['error'])
