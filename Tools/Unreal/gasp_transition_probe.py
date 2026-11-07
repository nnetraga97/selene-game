"""Bounded read-only qualification of locked transition poses. No standing turns."""
import json, math, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT=ROOT/'Saved/Clips/session-7/transition-probe.json'
report={'status':'running','clips':[], 'scope':'Compressed locked playback, 9 phases per clip; no exhaustive foot-contact qualification.'}
try:
    manifest=json.loads((ROOT/'Saved/Clips/session-3/retarget.json').read_text())
    for hero,data in manifest['heroes'].items():
        mesh=u.load_asset(data['mesh'])
        for clip in data['clips']:
            if clip['role'] not in ('Idle','WalkStart','RunStart','WalkStop','RunStop','SprintStop','PivotWalk','PivotRun'): continue
            anim=u.load_asset(clip['package'])
            opts=u.AnimPoseEvaluationOptions()
            for k,v in {'optional_skeletal_mesh':mesh,'evaluation_type':u.AnimDataEvalType.COMPRESSED,'evaluate_curves':False,'extract_root_motion':False,'incorporate_root_motion_into_pose':False}.items(): opts.set_editor_property(k,v)
            row={'hero':hero,'role':clip['role'],'package':clip['package'],'force_root_lock':anim.get_editor_property('force_root_lock'),'enable_root_motion':anim.get_editor_property('enable_root_motion'),'samples':[]}
            for i in range(9):
                t=anim.get_play_length()*i/8
                pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
                bones={}
                for b in ['mixamorig_Hips','mixamorig_Head','mixamorig_LeftFoot','mixamorig_RightFoot']:
                    x=u.AnimPoseExtensions.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD)
                    bones[b]=[x.translation.x,x.translation.y,x.translation.z]
                    if not all(math.isfinite(v) for v in bones[b]): raise RuntimeError('Nonfinite pose')
                row['samples'].append({'time':t,'bones':bones})
            hips=[s['bones']['mixamorig_Hips'] for s in row['samples']]
            row['hips_travel_cm']=max(math.dist(p,hips[0]) for p in hips)
            row['max_foot_radius_cm']=max(math.hypot(s['bones'][b][0],s['bones'][b][1]) for s in row['samples'] for b in ('mixamorig_LeftFoot','mixamorig_RightFoot'))
            row['foot_z_cm']=[min(s['bones'][b][2] for s in row['samples'] for b in ('mixamorig_LeftFoot','mixamorig_RightFoot')),max(s['bones'][b][2] for s in row['samples'] for b in ('mixamorig_LeftFoot','mixamorig_RightFoot'))]
            report['clips'].append(row)
            if row['hips_travel_cm']>1 or row['max_foot_radius_cm']>150 or row['enable_root_motion']: raise RuntimeError('Unsafe root/pose extent: '+hero+clip['role'])
    report['status']='success'
except Exception as e:
    report.update(status='failed',error=str(e),traceback=traceback.format_exc())
OUT.write_text(json.dumps(report,indent=2))
if report['status']!='success': raise RuntimeError(report['error'])
