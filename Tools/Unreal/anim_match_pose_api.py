"""Read-only exported retarget settings for the five comparison heroes."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))/'Saved/AnimMatch/session-1/settings.json'
def dump(x): return x.export_text() if hasattr(x,'export_text') else str(x)
r=u.IKRetargeterController.get_controller(u.load_asset('/Game/Selene/Characters/Fixer/RTG_Manny_To_Fixer'))
result={n:getattr(r,n).__doc__ for n in dir(r) if any(k in n for k in ['align','pose','reset'])}
result['enum']={n:str(getattr(u,n).__doc__) for n in dir(u) if 'Align' in n and 'Retarget' in n}
out=out.with_name('pose-api.json')
out.write_text(json.dumps(result,indent=2))
