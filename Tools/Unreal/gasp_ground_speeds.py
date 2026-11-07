"""Offline stance-speed estimates from freshly reloaded corrected hero loops."""
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Saved/Clips/session-4'
D=json.loads((OUT/'loop-reload.json').read_text())
if D['status']!='success':raise SystemExit('Reload must pass')
result={'status':'success','method':'60 Hz compressed evaluation; toe in lowest 35% of heights; abs vertical speed <25 cm/s; backward speed >30 cm/s; bilateral median.',
        'limits':['Bone-space estimate, not a runtime no-sliding test.','One scalar cannot remove within-stance retarget velocity variation.','Requested minimum rate 0.7 prevents exact 350 cm/s run matching for these clips.'], 'clips':[]}
for c in D['clips']:
    samples=c['samples'];feet={};all_speeds=[]
    for toe in ('mixamorig_LeftToeBase','mixamorig_RightToeBase'):
        xyz=[s['bones'][toe]['translation'] for s in samples]
        h=sorted(v[2] for v in xyz)[int((len(xyz)-1)*.35)];candidates=[]
        for i in range(1,len(samples)-1):
            dt=samples[i+1]['time']-samples[i-1]['time']
            v=[(xyz[i+1][k]-xyz[i-1][k])/dt for k in range(3)]
            if xyz[i][2]<=h and abs(v[2])<25 and -v[1]>30:
                candidates.append({'time':samples[i]['time'],'backward_speed_cm_s':-v[1],'height_cm':xyz[i][2]})
        speeds=sorted(x['backward_speed_cm_s'] for x in candidates)
        if len(speeds)<3:raise SystemExit('Insufficient stance samples: '+c['hero']+c['role']+toe)
        feet[toe]={'samples':candidates,'median_cm_s':statistics.median(speeds),'range_cm_s':[min(speeds),max(speeds)]}
        all_speeds+=speeds
    speed=statistics.median(all_speeds);ordered=sorted(all_speeds)
    nominal={'WalkLoop':150.,'RunLoop':350.,'SprintLoop':600.}[c['role']]
    rate=max(.7,min(1.3,nominal/speed))
    hips=[s['bones']['mixamorig_Hips']['translation'] for s in samples]
    result['clips'].append({'hero':c['hero'],'role':c['role'],'package':c['package'],'sha256':c['sha256_after'],
        'ground_speed_cm_s':speed,'stance_samples':len(ordered),'stance_p10_p90_cm_s':[ordered[int((len(ordered)-1)*.1)],ordered[int((len(ordered)-1)*.9)]],
        'feet':feet,'hips_xyz_range_cm':[[min(p[k] for p in hips),max(p[k] for p in hips)] for k in range(3)],
        'hips_loop_seam_translation_cm':math.dist(hips[0],hips[-1]),
        'nominal_movement_speed_cm_s':nominal,'unclamped_rate':nominal/speed,'clamped_rate':rate,
        'median_foot_speed_at_clamped_rate_cm_s':speed*rate,'median_speed_mismatch_cm_s':speed*rate-nominal})
(OUT/'ground-speeds.json').write_text(json.dumps(result,indent=2)+'\n')
for c in result['clips']:
    print(c['hero'],c['role'],round(c['ground_speed_cm_s'],3),'cm/s',c['stance_samples'],'samples',
          'p10-p90',*[round(x,3) for x in c['stance_p10_p90_cm_s']], 'seam cm',round(c['hips_loop_seam_translation_cm'],4),
          'clamp mismatch cm/s',round(c['median_speed_mismatch_cm_s'],3))
