"""Correct only six measured hero loops, or fresh-reload verify that correction.

The measured hero hips translation is source pelvis translation times a constant
scale (<0.001 cm residual). Remove only that scaled source root XY trajectory;
keep hips Z, rotation, scale, and every other track. Then disable force_root_lock.
Uses the saved 60 Hz audit as immutable expected data. Saves no supporting assets.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT/'Saved/Clips/session-4'
MODE = os.environ.get('SELENE_LOOP_MODE', 'correct')
FILE = OUT/('loop-correction.json' if MODE == 'correct' else 'loop-reload.json')
report = {'status':'running','mode':MODE,'clips':[],'saved_packages':[]}


def checkpoint():
    FILE.write_text(json.dumps(report,indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pos(x):
    return [x.x,x.y,x.z]


def main():
    if FILE.exists() or MODE not in ('correct','verify') or not (ROOT/'Selene.uproject').is_file():
        raise RuntimeError('Wrong project/mode or existing report; do not replay')
    measured = json.loads((OUT/'measurement.json').read_text())
    manifest = json.loads((ROOT/'Saved/Clips/session-3/retarget.json').read_text())
    if measured['status'] != 'success':
        raise RuntimeError('Measurement must pass')
    corrected = json.loads((OUT/'loop-correction.json').read_text()) if MODE=='verify' else None
    if corrected and corrected['status'] != 'success':
        raise RuntimeError('Correction must pass before reload')
    work=[]
    for clip in measured['clips']:
        if clip['hero']=='Manny':
            continue
        name,role=clip['hero'],clip['role']
        source=next(c for c in measured['clips'] if c['hero']=='Manny' and c['role']==role)
        m=source['modes']['raw_unlocked']['samples']; h=clip['modes']['raw_unlocked']['samples']
        scale=statistics.median(b['bones']['mixamorig_Hips']['translation'][2]/a['bones']['pelvis']['translation'][2] for a,b in zip(m,h))
        residual=max(math.dist([v*scale for v in a['bones']['pelvis']['translation']],b['bones']['mixamorig_Hips']['translation']) for a,b in zip(m,h))
        if residual>0.001 or max(abs(v) for a in m for v in a['bones']['root']['quaternion'][:3])>0.0001:
            raise RuntimeError('Unvalidated root translation/rotation model: '+name+role)
        filename=ROOT/'Content'/(clip['package'][6:]+'.uasset')
        expected_sha=(next(c for c in corrected['clips'] if c['package']==clip['package'])['sha256_after'] if corrected else clip['sha256'])
        if sha(filename)!=expected_sha:
            raise RuntimeError('Input hash mismatch: '+clip['package'])
        mesh=u.load_asset(manifest['heroes'][name]['mesh']);anim=u.load_asset(clip['package'])
        if not mesh or not isinstance(anim,u.AnimSequence):
            raise RuntimeError('Missing asset: '+clip['package'])
        work.append((clip,m,h,scale,residual,filename,mesh,anim))
    for clip,m,h,scale,residual,filename,mesh,anim in work:
        item={'hero':clip['hero'],'role':clip['role'],'package':clip['package'], 'sha256_before':sha(filename),
              'pelvis_scale':scale,'scaled_source_pelvis_max_residual_cm':residual}
        report['clips'].append(item);checkpoint()
        opts=u.AnimPoseEvaluationOptions()
        for k,v in {'optional_skeletal_mesh':mesh,'evaluation_type':u.AnimDataEvalType.RAW,
                    'incorporate_root_motion_into_pose':True,'evaluate_curves':False}.items():opts.set_editor_property(k,v)
        model=anim.get_editor_property('data_model_interface')
        before_frames=model.get_number_of_frames()
        if MODE=='correct':
            if not anim.get_editor_property('force_root_lock') or anim.get_editor_property('enable_root_motion'):
                raise RuntimeError('Unexpected original playback flags')
            backup=OUT/'original-loops'/filename.relative_to(ROOT/'Content')
            backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(filename,backup)
            item['backup']=str(backup.relative_to(ROOT))
            keys=[];rots=[];scales=[]
            # Native 30 Hz keys, not resampled output. Hips is bone zero so local=component.
            for frame in range(before_frames+1):
                pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,frame/30.,opts)
                x=u.AnimPoseExtensions.get_bone_pose(pose,'mixamorig_Hips',u.AnimPoseSpaces.LOCAL)
                root=m[frame*2]['bones']['root']['translation']
                keys.append(u.Vector(x.translation.x-root[0]*scale,x.translation.y-root[1]*scale,x.translation.z))
                rots.append(x.rotation);scales.append(x.scale3d)
            controller=anim.get_editor_property("controller")
            controller.open_bracket('Remove measured GASP loop ground travel',False)
            try:
                if not controller.set_bone_track_keys('mixamorig_Hips',keys,rots,scales,False):
                    raise RuntimeError('SetBoneTrackKeys failed')
            finally:
                controller.close_bracket(False)
            anim.set_editor_property('force_root_lock',False)
        if anim.get_editor_property('force_root_lock') or anim.get_editor_property('enable_root_motion'):
            raise RuntimeError('Incorrect corrected flags')
        opts.set_editor_property('incorporate_root_motion_into_pose',False)
        if MODE=='verify':opts.set_editor_property('evaluation_type',u.AnimDataEvalType.COMPRESSED)
        samples=[];error=0.;angle_error=0.
        for i,old in enumerate(h):
            pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,old['time'],opts)
            if not u.AnimPoseExtensions.is_valid(pose):raise RuntimeError('Invalid corrected pose')
            values={}
            for bone,b in old['bones'].items():
                x=u.AnimPoseExtensions.get_bone_pose(pose,bone,u.AnimPoseSpaces.WORLD)
                expected=[b['translation'][k]-(m[i]['bones']['root']['translation'][k]*scale if k<2 else 0) for k in range(3)]
                error=max(error,math.dist(pos(x.translation),expected))
                q=x.rotation;quat=[q.x,q.y,q.z,q.w]
                angle_error=max(angle_error,1-abs(sum(a*b for a,b in zip(quat,b['quaternion']))))
                values[bone]={'translation':pos(x.translation),'quaternion':quat}
            samples.append({'time':old['time'],'bones':values})
        item.update(max_expected_pose_error_cm=error,max_quaternion_one_minus_abs_dot=angle_error,samples=samples)
        tolerance=0.001 if MODE=='correct' else 0.06
        if error>tolerance or angle_error>0.00001 or model.get_number_of_frames()!=before_frames:
            raise RuntimeError('Corrected pose/frame validation failed: '+str(error))
        if MODE=='correct':
            if not u.EditorAssetLibrary.save_loaded_asset(anim,only_if_is_dirty=False):raise RuntimeError('Save failed')
            report['saved_packages'].append(clip['package'])
        item.update(sha256_after=sha(filename),bytes=filename.stat().st_size,force_root_lock=False,enable_root_motion=False)
        checkpoint()
    report['status']='success'


try:
    main()
except Exception as exc:
    report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
finally:
    checkpoint()
u.log('SELENE_LOOP_'+MODE.upper()+' '+report['status'])
if report['status']!='success':raise RuntimeError(report['error'])
