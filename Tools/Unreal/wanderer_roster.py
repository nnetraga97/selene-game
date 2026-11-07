"""Add only Wanderer's roster line and two cook directories; preserve every entry byte."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/WandererHookup/session-1'
clips=json.loads((OUT/'root-separated/report.json').read_text());reload=json.loads((OUT/'accepted-measure/report.json').read_text())
assert clips['status']==reload['status']=='success'
path=ROOT/'Config/DefaultGame.ini';text=path.read_text()
base='/Game/Selene/Characters/Wanderer/RootSeparated/Anims/'
def obj(p):return p+'.'+p.rsplit('/',1)[-1]
fields={'Name':'Wanderer','Mesh':obj('/Game/Selene/Characters/Wanderer/SK_Wanderer'),'Locomotion':obj(base+'BS_Idle_Walk_Run_Wanderer')}
for k,n in {'FallLoop':'MM_Fall_Loop','Jump':'MM_Jump','Land':'MM_Land'}.items():fields[k]=obj(base+n+'_Wanderer')
for c in clips['clips']:
 if c['role'] in ('Idle','WalkLoop','RunLoop','SprintLoop'):fields['IdleLoop' if c['role']=='Idle' else c['role']]=c['asset']
for c in clips['clips']:
 if c['role'] in ('Idle','WalkLoop','RunLoop','SprintLoop'):continue
 if not c['role'].startswith('Turn'):fields[{'PivotWalk':'WalkPivot','PivotRun':'RunPivot'}.get(c['role'],c['role'])]=c['asset']
parts=[k+'="'+v+'"' for k,v in fields.items()]
speeds={c['role']:c['runtime']['stance_speed_cm_s'] for c in reload['clips'] if c['role'] in ('WalkLoop','RunLoop','SprintLoop')}
assert all(v and v>0 for v in speeds.values())
parts += [k+'Speed='+f'{v:.3f}' for k,v in speeds.items()]
parts += ['OverrideMaterial="'+obj('/Game/Selene/Materials/Character/MI_Toon_Wanderer')+'"','KeepMaterialSlots=("FoxEye_amber")','EyeHeight=156.0','BoomLength=350.0','MeshOffset=(X=0,Y=0,Z=-87.5)','MeshRotation=(Pitch=0,Yaw=-90,Roll=0)']
# Damping, stiffness, world-location/rotation damping, radius cm, angle deg, gravity cm/s².
groups={'skirt':(.22,.09,.62,.70,.8,45,-490),'hair':(.24,.12,.65,.70,.6,30,-245)}
keys=['Damping','Stiffness','WorldDampingLocation','WorldDampingRotation','Radius','LimitAngle','GravityZ']
chains=[]
for name in reload['chains']:
 group=name.split('_')[0];v=groups[group];chains.append('(RootBone="'+name+'",'+','.join(f'{k}={val}' for k,val in zip(keys,v))+')')
assert len(chains)==7
parts.append('SecondaryChains=('+','.join(chains)+')')
colliders=[('pelvis',None,10.5),('spine_01','spine_02',8.0),('spine_02','spine_03',8.0),('spine_03','spine_04',8.5),('spine_04','spine_05',8.5),('spine_05','neck_01',9)]
for side in ('l','r'):
 colliders += [('thigh_'+side,'calf_'+side,6.5),('calf_'+side,'foot_'+side,4.5),('upperarm_'+side,'lowerarm_'+side,4),('lowerarm_'+side,'hand_'+side,3.5)]
parts.append('SecondaryColliders=('+','.join('(Bone="'+b+'",'+('ChildBone="'+c+'",' if c else '')+f'Radius={r})' for b,c,r in colliders)+')')
line='+Roster=('+','.join(parts)+')'
cook=['+DirectoriesToAlwaysCook=(Path="/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes")','+DirectoriesToAlwaysCook=(Path="/Game/Selene/Characters/Wanderer")']
previous=[l for l in text.splitlines() if l.startswith('+Roster=(Name="Wanderer",')]
assert len(previous)<=1
if previous:
 assert previous[0]==(OUT/'Wanderer-roster-line.txt').read_text().strip()
 if not (OUT/'Wanderer-roster-line-initial.txt').exists():(OUT/'Wanderer-roster-line-initial.txt').write_text(previous[0]+'\n')
 new=text.replace(previous[0],line)
 assert new.replace(line,previous[0])==text
else:
 new=text.replace('[/Script/Selene.SeleneCharacterSettings]','\n'.join(cook)+'\n[/Script/Selene.SeleneCharacterSettings]',1)
 new += ('' if new.endswith('\n') else '\n')+line+'\n'
 assert ''.join(l for l in new.splitlines(keepends=True) if l.strip()!=line and l.strip() not in cook)==text
path.write_text(new);(OUT/'Wanderer-roster-line.txt').write_text(line+'\n')
(OUT/'kawaii-values.json').write_text(json.dumps({'parameter_order':keys,'groups':groups,'chains':reload['chains'],'colliders':colliders,'speeds':speeds},indent=2)+'\n')
print(speeds);print('Wanderer roster: 7 chains, 1 sphere + 13 capsules')
