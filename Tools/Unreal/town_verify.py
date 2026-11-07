"""Read-only saved-map audit after external actor reconciliation."""
import unreal as u,json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Saved/Town/session-1'
levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
assert levels.load_level('/Game/Selene/Maps/Town')
all_actors=list(actors.get_all_level_actors());tagged=[a for a in all_actors if a.actor_has_tag('SeleneTownSession1')]
labels=Counter(a.get_actor_label() for a in tagged)
report={'tagged_count':len(tagged),'duplicates':[k for k,v in labels.items() if v>1],'mounds_remaining':[a.get_actor_label() for a in tagged if '_berm_' in a.get_actor_label()],'earth_skirt':labels['Town1_earth_skirt'],'practical_lights':sum(k.startswith('Town1_cafe_practical') for k in labels),'external_count':sum(a.is_package_external() for a in tagged)}
terrace=next(a for a in all_actors if a.get_actor_label()=='cafe_terrace')
report['terrace_material']=terrace.static_mesh_component.get_material(0).get_path_name()
report['status']='success' if len(tagged)==274 and not report['duplicates'] and not report['mounds_remaining'] and report['earth_skirt']==1 and report['practical_lights']==2 and 'MI_Town_Plaza' in report['terrace_material'] else 'failed'
(OUT/'saved-verification.json').write_text(json.dumps(report,indent=2))
assert report['status']=='success',report
