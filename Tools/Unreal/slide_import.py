"""A2.3: import the exported FBX clips onto Selene's existing Manny skeleton.

Run once in a locked Selene commandlet, with Interchange.FeatureFlags.Import.FBX=0
to use the explicit FbxFactory/animation-only options. Reject existing outputs.
"""
import hashlib
import json
import math
from pathlib import Path
import traceback

import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()
OUT = ROOT / "Saved/SlidePass/session-1"
DEST = "/Game/Selene/Animation/GASP"
SKELETON = "/Game/Characters/Mannequins/Meshes/SK_Mannequin"
MESH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
report = {"status": "failed", "clips": []}


def main():
    if not (ROOT / "Selene.uproject").is_file():
        raise RuntimeError("Run only in Selene")
    exported = json.loads((OUT / "export.json").read_text())
    if exported["status"] != "success" or len(exported["clips"]) != 4:
        raise RuntimeError("Missing complete, successful export")
    registry = u.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    skeleton, mesh = u.load_asset(SKELETON), u.load_asset(MESH)
    if not skeleton or not mesh:
        raise RuntimeError("Missing Selene Manny skeleton or mesh")
    tasks = []
    for clip in exported["clips"]:
        filename = ROOT / clip["fbx"]
        name = filename.stem
        if u.EditorAssetLibrary.does_asset_exist(DEST + "/" + name):
            raise RuntimeError("Destination exists; inspect before replay: " + name)
        if hashlib.sha256(filename.read_bytes()).hexdigest() != clip["sha256"]:
            raise RuntimeError("FBX hash changed: " + name)
        options = u.FbxImportUI()
        for key, value in {
            "automated_import_should_detect_type": False,
            "mesh_type_to_import": u.FBXImportType.FBXIT_ANIMATION,
            "original_import_type": u.FBXImportType.FBXIT_ANIMATION,
            "import_mesh": False, "import_animations": True,
            "import_materials": False, "import_textures": False,
            "create_physics_asset": False, "skeleton": skeleton,
        }.items():
            options.set_editor_property(key, value)
        data = options.get_editor_property("anim_sequence_import_data")
        for key, value in {
            "use_default_sample_rate": True, "custom_sample_rate": 30,
            "animation_length": u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME,
            "import_bone_tracks": True, "import_custom_attribute": True,
            "remove_redundant_keys": False, "do_not_import_curve_with_zero": False,
            "add_curve_metadata_to_skeleton": False,
            "convert_scene": True, "force_front_x_axis": False,
        }.items():
            data.set_editor_property(key, value)
        task = u.AssetImportTask()
        for key, value in {
            "filename": str(filename), "destination_path": DEST,
            "destination_name": name, "automated": True, "replace_existing": False,
            "save": False, "factory": u.FbxFactory(), "options": options,
        }.items():
            task.set_editor_property(key, value)
        tasks.append(task)
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for clip, task in zip(exported["clips"], tasks):
        name = Path(clip["fbx"]).stem
        path = DEST + "/" + name
        objects = task.get_objects()
        if len(objects) != 1 or not isinstance(objects[0], u.AnimSequence):
            raise RuntimeError("Expected one animation only: " + name)
        anim = objects[0]
        if anim.get_path_name().split(".")[0] != path or anim.get_editor_property("skeleton") != skeleton:
            raise RuntimeError("Unexpected animation destination/skeleton: " + name)
        model = anim.get_editor_property("data_model_interface")
        rate = model.get_frame_rate()
        if rate.numerator != 30 * rate.denominator or model.get_number_of_frames() != clip["frames"]:
            raise RuntimeError("Frame count/rate changed: " + name)
        if abs(anim.get_play_length() - clip["seconds"]) > 0.001 or not model.is_valid_bone_track_name("root"):
            raise RuntimeError("Duration/root track changed: " + name)
        if u.AnimationLibrary.get_animation_notify_events(anim):
            raise RuntimeError("Unexpected imported notifies: " + name)
        options = u.AnimPoseEvaluationOptions()
        options.set_editor_property("optional_skeletal_mesh", mesh)
        points = []
        for seconds in (0.0, anim.get_play_length()):
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, seconds, options)
            v = u.AnimPoseExtensions.get_bone_pose(pose, "root", u.AnimPoseSpaces.LOCAL).translation
            points.append([v.x, v.y, v.z])
        root_error = max(math.dist(a, b) for a, b in zip(points, (clip["root_first_cm"], clip["root_last_cm"])))
        if root_error > 0.1:
            raise RuntimeError("FBX round trip changed root translation: %s, %.3f cm" % (name, root_error))
        # CharacterMovement drives translation. Preserve the track for measurements/retargeting,
        # but evaluate in place (the source GASP clips also have force_root_lock enabled).
        anim.set_editor_property("enable_root_motion", False)
        anim.set_editor_property("force_root_lock", True)
        anim.set_editor_property("root_motion_root_lock", u.RootMotionRootLock.REF_POSE)
        # Strip source ground travel before retargeting, as in gasp_loop_in_place.py.
        # Keeping pelvis Z lets the new clips lower the body without a fake mesh drop.
        opts = u.AnimPoseEvaluationOptions()
        opts.set_editor_property("evaluation_type", u.AnimDataEvalType.RAW)
        opts.set_editor_property("incorporate_root_motion_into_pose", True)
        keys = []
        for frame in range(model.get_number_of_frames() + 1):
            u.AnimPoseExtensions.get_anim_pose_at_time(anim, frame / 30., opts)
            pose = u.AnimPoseExtensions.get_anim_pose_at_time(anim, frame / 30., opts)
            keys.append(u.AnimPoseExtensions.get_bone_pose(pose, "root", u.AnimPoseSpaces.LOCAL))
        controller = anim.get_editor_property("controller")
        controller.open_bracket("Slide in place source root", False)
        try:
            if not controller.set_bone_track_keys("root", [u.Vector(0, 0, k.translation.z) for k in keys], [k.rotation for k in keys], [k.scale3d for k in keys], False):
                raise RuntimeError("Root track write failed")
        finally:
            controller.close_bracket(False)
        if not u.EditorAssetLibrary.save_loaded_asset(anim, only_if_is_dirty=False):
            raise RuntimeError("Save failed: " + path)
        report["clips"].append({"role": clip["role"], "package": path,
            "seconds": anim.get_play_length(), "fps": rate.numerator / rate.denominator,
            "frames": model.get_number_of_frames(), "bone_tracks": model.get_num_bone_tracks(),
            "float_curves": model.get_number_of_float_curves(), "notifies": 0,
            "root_roundtrip_max_error_cm": root_error,
            "root_net_speed_xy_cm_s": clip["root_net_speed_xy_cm_s"]})
    registry.scan_paths_synchronous([DEST], True)
    dependencies = u.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True, include_searchable_names=False,
        include_soft_management_references=False, include_hard_management_references=False)
    pending = [c["package"] for c in report["clips"]]
    graph = {}
    while pending:
        path = pending.pop()
        if path in graph:
            continue
        deps = sorted(str(p) for p in (registry.get_dependencies(path, dependencies) or []))
        graph[path] = deps
        for dep in deps:
            if "UEFN_Mannequin" in dep or "UE5_Mannequins" in dep or "__SeleneClips" in dep:
                raise RuntimeError("GASP dependency survived: " + dep)
            if dep.startswith("/Game/"):
                if not (ROOT / "Content" / (dep[6:] + ".uasset")).is_file():
                    raise RuntimeError("Missing Selene-local dependency: " + dep)
                pending.append(dep)
            elif not dep.startswith(("/Engine/", "/Script/")):
                raise RuntimeError("Unexpected external dependency: " + dep)
    report["dependency_graph"] = graph
    report["total_asset_bytes"] = sum((ROOT / "Content" / (c["package"][6:] + ".uasset")).stat().st_size for c in report["clips"])
    if report["total_asset_bytes"] >= 100_000_000:
        raise RuntimeError("Unexpectedly large imported animation set")
    report["status"] = "success"


try:
    main()
except Exception as exc:
    report["error"] = str(exc)
    report["traceback"] = traceback.format_exc()
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "import.json").write_text(json.dumps(report, indent=2) + "\n")
u.log("SELENE_CLIP_IMPORT " + report["status"])
if report["status"] != "success":
    raise RuntimeError(report["error"])

# New slide assets only. Existing hero retargeters, rigs and locomotion stay immutable.
report = {"status": "running", "heroes": {}, "saved_packages": []}
def checkpoint():
    (OUT / 'retarget.json').write_text(json.dumps(report, indent=2) + '\n')
def retarget():
    import re
    manifest = json.loads((OUT / 'import.json').read_text())
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
