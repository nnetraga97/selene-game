"""Read-only exported retarget settings for the five comparison heroes."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))/'Saved/AnimMatch/session-1/settings.json'
def dump(x): return x.export_text() if hasattr(x,'export_text') else str(x)
result={}
for name in ('Sparrow','Champion','Angel','Fixer','Courier'):
    r=u.IKRetargeterController.get_controller(u.load_asset('/Game/Selene/Characters/'+name+'/RTG_Manny_To_'+name))
    h=dict(poses={},ops={})
    for role,side in [('source',u.RetargetSourceOrTarget.SOURCE),('target',u.RetargetSourceOrTarget.TARGET)]:
        h['poses'][role]=dict(name=str(r.get_current_retarget_pose_name(side)),value=dump(r.get_current_retarget_pose(side)))
    for i in range(r.get_num_retarget_ops()):
        c=r.get_op_controller(i)
        h['ops'][str(r.get_op_name(i))]=dump(c.get_settings())
    result[name]=h
out.write_text(json.dumps(result,indent=2))
