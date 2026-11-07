"""Add only Fox's roster line and two cook directories; preserve every entry byte."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/FoxHookup/session-1'
clips=json.loads((OUT/'clips/report.json').read_text());reload=json.loads((OUT/'reload/report.json').read_text())
assert clips['status']==reload['status']=='success'
path=ROOT/'Config/DefaultGame.ini';text=path.read_text();assert 'Name="Fox"' not in text
base='/Game/Selene/Characters/Fox/Anims/'
def obj(p):return p+'.'+p.rsplit('/',1)[-1]
fields={'Name':'Fox','Mesh':obj('/Game/Assets/fox-spirit-sovereign/fox-spirit-sovereign/SkeletalMeshes/fox-spirit-sovereign'),'Locomotion':obj(base+'BS_Idle_Walk_Run_Fox')}
for k,n in {'FallLoop':'MM_Fall_Loop','Jump':'MM_Jump','Land':'MM_Land'}.items():fields[k]=obj(base+n+'_Fox')
for c in clips['clips']:
 if c['role'] in ('Idle','WalkLoop','RunLoop','SprintLoop'):fields['IdleLoop' if c['role']=='Idle' else c['role']]=c['asset']
for c in clips['transitions']:
 if not c['role'].startswith('Turn'):fields[{'PivotWalk':'WalkPivot','PivotRun':'RunPivot'}.get(c['role'],c['role'])]=c['asset']
parts=[k+'="'+v+'"' for k,v in fields.items()]
speeds={c['role']:c['stance_speed_cm_s'] for c in reload['clips'] if c['role'] in ('WalkLoop','RunLoop','SprintLoop')}
assert all(v and v>0 for v in speeds.values())
parts += [k+'Speed='+f'{v:.3f}' for k,v in speeds.items()]
parts += ['OverrideMaterial="'+obj('/Game/Selene/Materials/Character/MI_Toon_Fox')+'"','EyeHeight=163.0','BoomLength=350.0','MeshOffset=(X=0,Y=0,Z=-87.5)','MeshRotation=(Pitch=0,Yaw=-90,Roll=0)']
# Damping, stiffness, world-location/rotation damping, radius cm, angle deg, gravity cm/s².
groups={'tail':(.16,.06,.55,.65,3.,55,-650),'sleeve':(.22,.09,.62,.70,.7,50,-490),'tabard':(.22,.09,.62,.70,.8,45,-490),'hair':(.24,.12,.65,.70,.6,30,-245),'tassel':(.14,.05,.55,.60,.4,65,-490),'sash':(.20,.10,.60,.68,.5,35,-490)}
keys=['Damping','Stiffness','WorldDampingLocation','WorldDampingRotation','Radius','LimitAngle','GravityZ']
chains=[]
for name in reload['chains']:
 group=name.split('_')[0];v=groups[group];chains.append('(RootBone="'+name+'",'+','.join(f'{k}={val}' for k,val in zip(keys,v))+')')
assert len(chains)==24
parts.append('SecondaryChains=('+','.join(chains)+')')
colliders=[('Hips',None,11),('Spine','Spine2',8.5),('Spine2','Neck',9)]
for side in ('Left','Right'):
 colliders += [(side+'UpLeg',side+'Leg',6.5),(side+'Leg',side+'Foot',4.5),(side+'Arm',side+'ForeArm',4),(side+'ForeArm',side+'Hand',3.5)]
parts.append('SecondaryColliders=('+','.join('(Bone="mixamorig_'+b+'",'+('ChildBone="mixamorig_'+c+'",' if c else '')+f'Radius={r})' for b,c,r in colliders)+')')
line='+Roster=('+','.join(parts)+')'
cook=['+DirectoriesToAlwaysCook=(Path="/Game/Assets/fox-spirit-sovereign/fox-spirit-sovereign/SkeletalMeshes")','+DirectoriesToAlwaysCook=(Path="/Game/Selene/Characters/Fox")']
new=text.replace('[/Script/Selene.SeleneCharacterSettings]','\n'.join(cook)+'\n[/Script/Selene.SeleneCharacterSettings]',1)
new += ('' if new.endswith('\n') else '\n')+line+'\n'
assert ''.join(l for l in new.splitlines(keepends=True) if l.strip()!=line and l.strip() not in cook)==text
path.write_text(new);(OUT/'Fox-roster-line.txt').write_text(line+'\n')
(OUT/'kawaii-values.json').write_text(json.dumps({'parameter_order':keys,'groups':groups,'chains':reload['chains'],'colliders':colliders,'speeds':speeds},indent=2)+'\n')
print(speeds);print('Fox roster: 24 chains, 1 sphere + 10 capsules')
