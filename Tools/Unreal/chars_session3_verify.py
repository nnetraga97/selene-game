"""Fresh read-only verification of roster references, saved clips and material flags."""
import json
from pathlib import Path
import re
import traceback
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT=ROOT/'Saved/Chars/session-3'
report=dict(status='running',heroes={})
try:
    if (OUT/'verify.json').exists(): raise RuntimeError('Existing report; do not replay')
    lines=(ROOT/'Config/DefaultGame.ini').read_text().splitlines()
    registry=u.AssetRegistryHelpers.get_asset_registry(); registry.search_all_assets(True)
    for name,slug in {'Fixer':'night-market-fixer','Courier':'scooter-courier'}.items():
        line=next(x for x in lines if x.startswith('+Roster=(Name="'+name+'"'))
        if 'SecondaryChains=' in line: raise RuntimeError('New heroes must not have secondary chains')
        paths=re.findall(r'="(/Game/[^\"]+)"',line)
        loaded=[u.load_asset(p) for p in paths]
        if not all(loaded): raise RuntimeError('Cannot load all configured assets: '+name)
        mesh=loaded[0]
        base='/Game/Selene/Characters/'+name
        actual=sorted(str(x.package_name) for x in registry.get_assets_by_path(base,recursive=True))
        expected=json.loads((OUT/'create.json').read_text())['heroes'][name]['packages']
        expected+= [x['package'] for x in json.loads((OUT/'clips.json').read_text())['heroes'][name]['clips']]
        if actual!=sorted(expected) or len(actual)!=35: raise RuntimeError('Canonical fresh inventory mismatch: '+name)
        for a in loaded:
            if isinstance(a,u.AnimSequence) and a.get_editor_property('skeleton')!=mesh.get_editor_property('skeleton'):
                raise RuntimeError('Wrong skeleton: '+a.get_path_name())
        mi=u.load_asset('/Game/Selene/Materials/Character/MI_Toon_'+name)
        if not mi.get_base_material().get_editor_property('used_with_skeletal_mesh'):
            raise RuntimeError('Missing toon skeletal usage')
        imported=[]
        for slot in mesh.get_editor_property('materials'):
            mat=slot.material_interface
            base_mat=mat.get_base_material()
            if not base_mat.get_path_name().startswith('/Game/Selene/') or not base_mat.get_editor_property('used_with_skeletal_mesh'):
                raise RuntimeError('Imported material usage/relink incomplete')
            imported.append(dict(material=mat.get_path_name(),base=base_mat.get_path_name(),skeletal=True))
        report['heroes'][name]=dict(roster=line,loaded_paths=paths,canonical_packages=actual,
            height_cm=2*mesh.get_bounds().box_extent.z,imported_materials=imported,toon_skeletal=True)
    report['status']='success'
except Exception:
    report.update(status='failed',error=traceback.format_exc())
finally:
    (OUT/'verify.json').write_text(json.dumps(report,indent=2)+'\n')
if report['status']!='success': raise RuntimeError(report['error'])
