"""Resume after source assets saved: verify them afresh, then create absent hero clips."""
import json, math, hashlib, traceback
from pathlib import Path
import unreal as u
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT=ROOT/'Saved/SlidePass/session-1'
MESH='/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'
registry=u.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
old=json.loads((OUT/'import.json').read_text())
if len(old['clips'])!=4: raise RuntimeError('Incomplete source save; manual reconciliation needed')
mesh=u.load_asset(MESH)
for clip in old['clips']:
    anim=u.load_asset(clip['package'])
    if not anim or anim.get_editor_property('skeleton')!=mesh.get_editor_property('skeleton'): raise RuntimeError('Source reload mismatch')
    if not anim.get_editor_property('force_root_lock') or anim.get_editor_property('enable_root_motion') or anim.get_editor_property('root_motion_root_lock')!=u.RootMotionRootLock.REF_POSE: raise RuntimeError('Source flags')
    if abs(anim.get_play_length()-clip['seconds'])>.001: raise RuntimeError('Source duration')
    clip['sha256']=hashlib.sha256((ROOT/'Content'/(clip['package'][6:]+'.uasset')).read_bytes()).hexdigest()
old.update(status='success',reconciliation='Four source assets saved before dependency-iteration error; freshly reloaded without import replay')
(OUT/'source-reload.json').write_text(json.dumps(old,indent=2))
# New slide assets only. Existing hero retargeters, rigs and locomotion stay immutable.
report = {"status": "running", "heroes": {}, "saved_packages": []}
def checkpoint():
    (OUT / 'retarget.json').write_text(json.dumps(report, indent=2) + '\n')
def retarget():
    import re
    manifest = json.loads((OUT / 'source-reload.json').read_text())
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous(['/Game/Selene/Animation/GASP'], True)
    source = u.load_asset(MESH)
    assets = [registry.get_asset_by_object_path(u.load_asset(c['package']).get_path_name()) for c in manifest['clips']]
    roster=[]
    for line in (ROOT/'Config/DefaultGame.ini').read_text().splitlines():
        if line.startswith('+Roster='):
            fields=dict(re.findall(r'(\w+)="([^"]*)"',line))
            if fields.get('Name') in ['Champion','Angel','Sparrow','Fixer','Courier','Fox','Wanderer','Ysolde','Nerine','Base']:
                roster.append(fields)
    if len(roster)!=10: raise RuntimeError('Expected ten requested heroes')
    for entry in roster:
        name=entry['Name']; mesh=u.load_asset(entry['Mesh']); base='/Game/Selene/Characters/'+name
        dest=entry['WalkLoop'].split('.')[0].rsplit('/',1)[0]
        rtgpath=base+'/RTG_Manny_To_'+name
        if name in ('Fixer','Courier'): rtgpath=base+'/AnimMatchS1/RTG_Manny_To_'+name+'_Facing'
        rtg=u.load_asset(rtgpath)
        if not mesh or not rtg: raise RuntimeError('Missing existing mesh/retargeter '+name)
        for clip in manifest['clips']:
            if u.EditorAssetLibrary.does_asset_exist(dest+'/'+clip['package'].rsplit('/',1)[-1]+'_'+name):
                raise RuntimeError('Existing output: reconcile before rerun '+name)
        inp=u.IKRetargetBatchOperationInputs()
        for k,v in dict(assets_to_retarget=assets,source_mesh=source,target_mesh=mesh,ik_retarget_asset=rtg,target_path=dest,suffix='_'+name,include_referenced_assets=False,overwrite_existing_files=False,use_source_path=False).items():inp.set_editor_property(k,v)
        made=u.IKRetargetBatchOperation.run_batch_retarget(inp)
        if len(made)!=4: raise RuntimeError('Retarget count '+name)
        row={'mesh':entry['Mesh'],'retargeter':rtgpath,'clips':[]};report['heroes'][name]=row
        for data in made:
            anim=data.get_asset();package=anim.get_path_name().split('.')[0]
            if anim.get_editor_property('skeleton')!=mesh.get_editor_property('skeleton'):raise RuntimeError('Skeleton mismatch '+package)
            anim.set_editor_property('enable_root_motion',False)
            anim.set_editor_property('force_root_lock',True)
            anim.set_editor_property('root_motion_root_lock',u.RootMotionRootLock.REF_POSE)
            if not u.EditorAssetLibrary.save_loaded_asset(anim,only_if_is_dirty=False):raise RuntimeError('Save '+package)
            role=next(c['role'] for c in manifest['clips'] if package.rsplit('/',1)[-1]==c['package'].rsplit('/',1)[-1]+'_'+name)
            filename=ROOT/'Content'/(package[6:]+'.uasset')
            row['clips'].append(dict(role=role,package=package,seconds=anim.get_play_length(),sha256=hashlib.sha256(filename.read_bytes()).hexdigest()))
            report['saved_packages'].append(package);checkpoint()
    report['status']='success'
try: retarget()
except Exception as exc: report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
finally: checkpoint()
if report['status']!='success': raise RuntimeError(report['error'])
