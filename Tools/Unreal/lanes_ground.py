"""Build /Game/Selene/Maps/LanesGround/SM_LanesGround: one continuous ground mesh for the lanes map from
Tools/Maps/lanes_heightfield.py (plateaus, ramps, hills and plinths as smooth slopes; no seams between pieces).
Collision is the mesh itself (complex as simple). Run before lanes_build.py, which places it. Report: Saved/LanesMap/ground.json."""
import json, math, sys, traceback
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
sys.path.insert(0, str(ROOT / 'Tools/Maps'))
import lanes_heightfield as HF

ASSET_DIR, ASSET_NAME = '/Game/Selene/Maps/LanesGround', 'SM_LanesGround'
R = {'status': 'running'}
try:
    L = json.loads((ROOT / 'docs/maps/lanes-test/layout.json').read_text())
    x0, y0, nx, ny, cell, H = HF.build(L)
    R['grid'] = [nx, ny]

    def height_at(xm, ym):
        """Bilinear sample in metres (layout frame)."""
        fx = min(max((xm - x0) / cell, 0.0), nx - 1.001); fy = min(max((ym - y0) / cell, 0.0), ny - 1.001)
        i, j = int(fx), int(fy); tx, ty = fx - i, fy - j
        a = H[j][i] * (1 - tx) + H[j][i + 1] * tx
        b = H[j + 1][i] * (1 - tx) + H[j + 1][i + 1] * tx
        return a * (1 - ty) + b * ty

    dm = u.DynamicMesh()
    width_cm, depth_cm = (nx - 1) * cell * 100.0, (ny - 1) * cell * 100.0
    centre = u.Vector((x0 + (nx - 1) * cell / 2) * 100.0, -(y0 + (ny - 1) * cell / 2) * 100.0, 0.0)
    dm.append_rectangle_xy(u.GeometryScriptPrimitiveOptions(), u.Transform(centre, u.Rotator(0, 0, 0), u.Vector(1, 1, 1)),
                           width_cm, depth_cm, nx - 1, ny - 1)
    positions = dm.get_all_vertex_positions(False)
    # Geometry Script returns (mesh, out values...): take the vector list.
    if isinstance(positions, tuple): positions = next(v for v in positions if isinstance(v, u.GeometryScriptVectorList))
    # Vector lists are opaque in Python: convert through Geometry Script's list utilities (find the library by method).
    LU = next(getattr(u, n) for n in dir(u) if 'GeometryScript' in n and hasattr(getattr(u, n), 'convert_vector_list_to_array'))
    pts = LU.convert_vector_list_to_array(positions)
    if isinstance(pts, tuple): pts = next(v for v in pts if isinstance(v, (list, u.Array)))
    moved = []
    for p in pts:
        # Unreal (x, y) cm -> layout (x, -y) m
        moved.append(u.Vector(p.x, p.y, height_at(p.x / 100.0, -p.y / 100.0) * 100.0))
    CONV = next(getattr(u, n) for n in dir(u) if hasattr(getattr(u, n), 'convert_array_to_vector_list'))
    plist = CONV.convert_array_to_vector_list(moved)
    if isinstance(plist, tuple): plist = next(v for v in plist if isinstance(v, u.GeometryScriptVectorList))
    dm.set_all_mesh_vertex_positions(plist)
    R['vertices'] = len(moved)
    try:
        dm.recompute_normals(u.GeometryScriptCalculateNormalsOptions())
    except Exception as e:
        R['normals'] = str(e)[:200]
    # World-scaled UVs (4 m per tile) so the plaza material tiles like the old ground.
    for name in ('set_mesh_u_vs_from_planar_projection', 'set_mesh_uvs_from_planar_projection'):
        if hasattr(dm, name):
            try:
                getattr(dm, name)(0, u.Transform(u.Vector(0, 0, 0), u.Rotator(0, 0, 0), u.Vector(400, 400, 400)), u.GeometryScriptMeshSelection())
                R['uv'] = name; break
            except Exception as e:
                R['uv_error'] = str(e)[:200]

    path = f'{ASSET_DIR}/{ASSET_NAME}'
    if u.EditorAssetLibrary.does_asset_exist(path):
        sm = u.load_asset(path)
        opts = u.GeometryScriptCopyMeshToAssetOptions()
        u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dm, sm, opts, u.GeometryScriptMeshWriteLOD())
        R['asset'] = 'updated'
    else:
        opts = u.GeometryScriptCreateNewStaticMeshAssetOptions()
        opts.set_editor_property('enable_collision', True)
        opts.set_editor_property('collision_mode', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        res = u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, opts)
        sm = res[0] if isinstance(res, tuple) else res
        R['asset'] = 'created'
    bs = sm.get_editor_property('body_setup')
    if bs: bs.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    mat = u.load_asset('/Game/Selene/Materials/Ground/MI_Town_Plaza')
    if mat: sm.set_material(0, mat)
    u.EditorAssetLibrary.save_loaded_asset(sm, only_if_is_dirty=False)
    R['path'] = sm.get_path_name()
    R['status'] = 'saved'
except Exception:
    R.update(status='failed', error=traceback.format_exc())
(ROOT / 'Saved/LanesMap').mkdir(parents=True, exist_ok=True)
(ROOT / 'Saved/LanesMap/ground.json').write_text(json.dumps(R, indent=1))
