"""Read-only engine capability inventory; run via Unreal's pythonscript commandlet."""

import json
from pathlib import Path
import unreal as u

report = {"engine": u.SystemLibrary.get_engine_version()}
for name in (
    "Level",
    "LevelEditorSubsystem",
    "InterchangeManager",
    "ImportAssetParameters",
    "MaterialEditingLibrary",
    "StaticMeshEditorSubsystem",
):
    cls = getattr(u, name, None)
    report[name] = [
        x
        for x in dir(cls)
        if any(
            k in x
            for k in (
                "external",
                "packag",
                "import_asset",
                "new_level",
                "collision",
                "parameter_names",
                "complex",
            )
        )
    ]
p = u.load_asset("/Game/LevelPrototyping/Materials/M_PrototypeGrid")
if p:
    report["grid_vectors"] = [
        str(v) for v in u.MaterialEditingLibrary.get_vector_parameter_names(p)
    ]
report["new_level_doc"] = u.LevelEditorSubsystem.new_level.__doc__
report["import_asset_doc"] = u.InterchangeManager.import_asset.__doc__
path = Path(u.Paths.project_saved_dir()) / "Blockout/capabilities.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2))
u.log(str(report))
