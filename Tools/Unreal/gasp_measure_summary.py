"""Summarize session-4 dense pose audit without Unreal or asset changes."""
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'Saved/Clips/session-4'
data = json.loads((OUT/'measurement.json').read_text())
if data['status'] != 'success':
    raise SystemExit('Measurement did not pass: '+data.get('error', data['status']))
summary = {'status': 'success', 'clips': []}
for clip in data['clips']:
    hip = 'pelvis' if clip['hero'] == 'Manny' else 'mixamorig_Hips'
    toes = ['ball_l','ball_r'] if clip['hero'] == 'Manny' else ['mixamorig_LeftToeBase','mixamorig_RightToeBase']
    modes = clip['modes']
    result = {'hero': clip['hero'], 'role': clip['role'], 'bone_zero': clip['bone_zero'], 'modes': {}}
    for name, mode in modes.items():
        bones = mode['summary']
        speeds = [c['speed'] for toe in toes for c in bones[toe]['stance_candidates']]
        result['modes'][name] = {
            'hips_xyz_range_cm': bones[hip]['xyz_range_cm'],
            'hips_net_cm': bones[hip]['endpoint_delta_cm'],
            'toe_stance_speed_cm_s': statistics.median(speeds) if speeds else None,
            'toe_stance_count': len(speeds),
            'toe_z_range_cm': {toe: bones[toe]['xyz_range_cm'][2] for toe in toes},
            'toe_stance_speed_individual_cm_s': {toe: bones[toe]['stance_speed_cm_s'] for toe in toes}}
    for lock in ('locked','unlocked'):
        raw = modes['raw_'+lock]['samples']; compressed = modes['compressed_'+lock]['samples']
        result['raw_compressed_max_position_error_cm_'+lock] = max(
            math.dist(a['bones'][bone]['translation'], b['bones'][bone]['translation'])
            for a,b in zip(raw,compressed) for bone in a['bones'])
    if clip['hero'] == 'Manny':
        delta = modes['raw_unlocked']['summary']['root']['endpoint_delta_cm']
        result['root_net_speed_cm_s'] = math.hypot(delta[0], delta[1])/clip['seconds']
    summary['clips'].append(result)
(OUT/'measurement-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for clip in summary['clips']:
    print(clip['hero'],clip['role'],'bone zero:',clip['bone_zero'])
    for mode in ['compressed_locked','compressed_unlocked']:
        m=clip['modes'][mode]
        print(' ',mode,'hip range',m['hips_xyz_range_cm'],'net',m['hips_net_cm'], 'stance',m['toe_stance_speed_cm_s'], 'n',m['toe_stance_count'], 'toe Z',m['toe_z_range_cm'])
    print(' max raw/compressed error',clip['raw_compressed_max_position_error_cm_locked'],clip['raw_compressed_max_position_error_cm_unlocked'])
