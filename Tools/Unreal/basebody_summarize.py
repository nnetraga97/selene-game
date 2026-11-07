"""Compact audit facts, without treating measurements as visual acceptance gates."""
import json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/NerineHookup/session-1/Base'
r=json.loads((OUT/'measure/report.json').read_text());ret=json.loads((OUT/'retarget/report.json').read_text())
summary={'root_retarget_bone':'root','mannequin_template_auto_detected':ret['target_auto_template'],'facing_yaw_correction':0,'normalization_copies':0,'edited_animation_tracks':0,'clips':[],'material':r['material']}
for c in r['clips']:
 s=c['runtime']['summary'];p=s['pelvis'];root=s['root']
 summary['clips'].append({'role':c['role'],'root_first_cm':root['first'],'root_range_cm':root['range'],'pelvis_first_cm':p['first'],'pelvis_y_range_cm':p['range'][1],'pelvis_xy_seam_cm':math.dist(p['first'][:2],p['last'][:2]),'stance_speed_cm_s':c['runtime']['stance_speed_cm_s'],'stance_samples':c['runtime']['stance_sample_count']})
(OUT/'measurements-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Saved accepted measurements summary')
