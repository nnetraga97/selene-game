"""Read-only retarget setup and compressed pose comparison. No numerical acceptance gates."""
import json, math, traceback
from pathlib import Path
import unreal as u
ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/AnimMatch/session-1/audit.json'
report = dict(status='running', heroes={})
HEROES = {'Sparrow': '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Sparrow',
          **{name: '/Game/Assets/'+slug+'/'+slug+'/SkeletalMeshes/'+slug for name,slug in
             [('Champion','festival-champion-p2'),('Angel','angel-warrior'),('Fixer','night-market-fixer'),('Courier','scooter-courier')]}}
def v(vec): return [vec.x,vec.y,vec.z]
def snapshot(): OUT.write_text(json.dumps(report, indent=2))
def main():
    for hero,path in HEROES.items():
        mesh=u.load_asset(path)
        base='/Game/Selene/Characters/'+hero
        r=u.IKRetargeterController.get_controller(u.load_asset(base+'/RTG_Manny_To_'+hero))
        c=u.IKRigController.get_controller(u.load_asset(base+'/IK_'+hero))
        item=dict(mesh=path,height_cm=mesh.get_bounds().box_extent.z*2,root=str(c.get_retarget_root()),
                  solver_count=c.get_num_solvers(),chains=[],ops=[],clips={})
        report['heroes'][hero]=item
        for chain in c.get_retarget_chains():
            n=chain.chain_name
            item['chains'].append(dict(name=str(n),start=str(c.get_retarget_chain_start_bone(n)),end=str(c.get_retarget_chain_end_bone(n)),source=str(r.get_source_chain(n))))
        for i in range(r.get_num_retarget_ops()):
            ctrl=r.get_op_controller(i)
            entry=dict(name=str(r.get_op_name(i)),enabled=r.get_retarget_op_enabled(i),controller_class=str(type(ctrl)))
            # API inventory is saved for a later settings audit without guessing function signatures.
            entry['getters']={n:getattr(ctrl,n).__doc__ for n in dir(ctrl) if n.startswith('get_') and any(k in n for k in ['settings','root','chain','pelvis'])}
            item['ops'].append(entry)
        item['pose_getters']={n:getattr(r,n).__doc__ for n in dir(r) if n.startswith('get_') and 'pose' in n}
        bones=['pelvis','thigh_l','calf_l','foot_l','ball_l','foot_r','ball_r','clavicle_l','clavicle_r','head'] if hero=='Sparrow' else ['mixamorig_Hips','mixamorig_LeftUpLeg','mixamorig_LeftLeg','mixamorig_LeftFoot','mixamorig_LeftToeBase','mixamorig_RightFoot','mixamorig_RightToeBase','mixamorig_LeftShoulder','mixamorig_RightShoulder','mixamorig_Head']
        for role,clip in [('idle','M_Neutral_Stand_Idle_Loop'),('walk','M_Neutral_Walk_Loop_F'),('run','M_Neutral_Run_Loop_F')]:
            asset=base+'/Anims/GASP/'+clip+'_'+hero
            if hero=='Sparrow' and role=='idle': asset='/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/Travel_mode_Idle'
            anim=u.load_asset(asset)
            opts=u.AnimPoseEvaluationOptions()
            for key,value in dict(optional_skeletal_mesh=mesh,evaluation_type=u.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=False,evaluate_curves=False).items(): opts.set_editor_property(key,value)
            samples=[]
            for frame in range(31):
                t=anim.get_play_length()*frame/30
                u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
                pose=u.AnimPoseExtensions.get_anim_pose_at_time(anim,t,opts)
                samples.append(dict(time=t,bones={b:v(u.AnimPoseExtensions.get_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation) for b in bones}))
                if frame==0 and role=='idle':
                    item['reference']={b:v(u.AnimPoseExtensions.get_ref_bone_pose(pose,b,u.AnimPoseSpaces.WORLD).translation) for b in bones}
                    q=u.AnimPoseExtensions.get_ref_bone_pose(pose,bones[0],u.AnimPoseSpaces.WORLD).rotation
                    item['reference_hips_quaternion']=[q.x,q.y,q.z,q.w]
            item['clips'][role]=dict(asset=asset,samples=samples)
        snapshot()
    report['status']='success'
try: main()
except Exception: report.update(status='failed',error=traceback.format_exc())
finally: snapshot()
if report['status']!='success': raise RuntimeError(report['error'])
