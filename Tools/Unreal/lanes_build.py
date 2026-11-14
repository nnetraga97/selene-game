"""Build /Game/Selene/Maps/Lanes from docs/maps/lanes-test/layout.json (the approved top-down layout).
Layout metres (x, y) map to Unreal (x, -y) cm so the level seen from above matches the diagram."""
import json, math, pathlib, traceback
import unreal as u
ROOT = pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT = ROOT / 'Saved/LanesMap'; OUT.mkdir(parents=True, exist_ok=True)
MAP = '/Game/Selene/Maps/Lanes'
R = {'status': 'started'}
# Yaw (degrees) added per asset when its street front is not on the mesh's -Y side.
FRONT_FIX = json.loads((ROOT / 'Tools/Maps/lanes_front_fix.json').read_text()) if (ROOT / 'Tools/Maps/lanes_front_fix.json').exists() else {}
try:
    L = json.loads((ROOT / 'docs/maps/lanes-test/layout.json').read_text())
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    A = u.get_editor_subsystem(u.EditorActorSubsystem)
    if u.EditorAssetLibrary.does_asset_exist(MAP):
        if not levels.load_level(MAP): raise RuntimeError('load failed')
        for a in A.get_all_level_actors():
            if str(a.get_folder_path()).startswith('Lanes'): A.destroy_actor(a)
    elif not levels.new_level(MAP, False): raise RuntimeError('new level failed')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode', u.load_class(None, '/Script/Selene.SeleneGameMode'))
    V = lambda x, y, z=0.0: u.Vector(x * 100.0, -y * 100.0, z * 100.0)
    def spawn(cls, label, loc, yaw=0.0, folder='Lanes'):
        a = A.spawn_actor_from_class(cls, loc, u.Rotator(0, 0, yaw)); a.set_actor_label(label); a.set_folder_path(folder); return a
    CUBE = u.load_asset('/Engine/BasicShapes/Cube')
    road = u.load_asset('/Game/Selene/Materials/Ground/MI_Town_Road'); pave = u.load_asset('/Game/Selene/Materials/Ground/MI_Town_Plaza')
    curb = u.load_asset('/Game/Selene/Materials/Ground/MI_Town_Curb')
    def box(label, centre, size_m, yaw, mat, folder):
        a = spawn(u.StaticMeshActor, label, centre, yaw, folder); c = a.static_mesh_component
        c.set_static_mesh(CUBE); a.set_actor_scale3d(u.Vector(*size_m))
        if mat: c.set_material(0, mat)
        c.set_mobility(u.ComponentMobility.STATIC); return a
    bx, by = L['bounds']
    # One continuous ground mesh (Tools/Unreal/lanes_ground.py) when it exists; the flat slab otherwise.
    import sys; sys.path.insert(0, str(ROOT / 'Tools/Maps')); import lanes_heightfield as HF
    G = HF.sampler(L)   # full ground height (m): buildings and the player start sit on it
    M = HF.macro(L)     # macro elevation only: pieces with absolute heights (they already include plateaus) are raised by it
    GROUND_MESH = u.load_asset('/Game/Selene/Maps/LanesGround/SM_LanesGround') if u.EditorAssetLibrary.does_asset_exist('/Game/Selene/Maps/LanesGround/SM_LanesGround') else None
    if GROUND_MESH:
        ground = spawn(u.StaticMeshActor, 'Ground', u.Vector(0, 0, 0), 0, 'Lanes/Ground')
        ground.static_mesh_component.set_static_mesh(GROUND_MESH); ground.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
        # a deep slab under it so nothing falls through gaps at the very edge
        box('GroundUnder', V(0, 0, -2.0), (bx * 2 + 60, by * 2 + 60, 1.0), 0, pave or road, 'Lanes/Ground')
    else:
        ground = box('Ground', V(0, 0, -0.5), (bx * 2 + 60, by * 2 + 60, 1.0), 0, pave or road, 'Lanes/Ground')
    R['ground_material'] = (pave or road).get_path_name() if (pave or road) else None
    # terrain: plateaus, hills, overpasses, cover, plinths (Tools/Maps/lanes_terrain.py)
    mats = {'plaza': pave, 'road': road, 'curb': curb}
    FVP = '/Game/Fantastic_Village_Pack/meshes/props/'
    CRATES = [u.load_asset(FVP + p) for p in ('container/SM_PROP_crate_01', 'food/SM_PROP_crate_02', 'food/SM_PROP_crate_04', 'food/SM_PROP_crate_05')]
    HAY = [u.load_asset(FVP + p) for p in ('natural/SM_PROP_hay_01', 'natural/SM_PROP_hay_02')]
    CRATES = [m for m in CRATES if m]; HAY = [m for m in HAY if m]
    def cover_prop(t):
        """Cover boxes get a dressed look: crates for crate stacks, two hay bales for a low wall."""
        if t['role'] != 'cover' or t['kind'] != 'box': return None
        sx, sy, sz = t['size']
        if abs(sx - 1.6) < 0.01 and abs(sz - 1.6) < 0.01 and CRATES: return (CRATES[int(abs(t['c'][0] * 7 + t['c'][1] * 3)) % len(CRATES)], 1)
        if abs(sz - 1.2) < 0.01 and sx >= 2.4 and HAY: return (HAY[int(abs(t['c'][0] + t['c'][1])) % len(HAY)], 2)
        return None
    for i, t in enumerate(L.get('terrain', [])):
        if GROUND_MESH and HF.is_ground(t): continue   # shaped into the ground mesh instead
        folder = 'Lanes/Terrain/' + t['role']; mat = mats.get(t['mat'], pave)
        if t['kind'] == 'box':
            sx, sy, sz = t['size']
            a = box(f"T{i:03d}_{t['role']}", V(t['c'][0], t['c'][1], M(*t['c']) + t['z'] + sz / 2), (sx, sy, sz), -t['yaw_deg'], mat, folder)
            prop = cover_prop(t)
            if prop:
                # Exact box collision stays (consistent cover); a real prop scaled to the box is what you see.
                a.static_mesh_component.set_visibility(False)
                pm, pieces = prop
                for k in range(pieces):
                    seg = sx / pieces; off = -sx / 2 + seg * (k + 0.5)
                    yaw = -t['yaw_deg']; r = math.radians(-yaw)
                    cx, cy = t['c'][0] + off * math.cos(r), t['c'][1] + off * math.sin(r)
                    bb = pm.get_bounding_box(); size = bb.max - bb.min
                    # Turn the prop so its longest side runs along the cover piece (hay bales are long in Y).
                    swap = size.y > size.x * 1.15 and seg > sy * 1.15
                    mx, my = (size.y, size.x) if swap else (size.x, size.y)
                    scale = u.Vector(seg * 100 / max(mx, 1), sy * 100 / max(my, 1), sz * 100 / max(size.z, 1))
                    if swap: scale = u.Vector(scale.y, scale.x, scale.z)
                    pa = spawn(u.StaticMeshActor, f"T{i:03d}_{t['role']}_prop{k}", V(cx, cy, M(*t['c']) + t['z']), yaw + (90.0 if swap else 0.0), folder)
                    pc = pa.static_mesh_component; pc.set_static_mesh(pm); pa.set_actor_scale3d(scale)
                    pc.set_collision_enabled(u.CollisionEnabled.NO_COLLISION); pc.set_mobility(u.ComponentMobility.STATIC)
                    # mesh pivot may not sit at its base centre: shift so the scaled bounds fill the box
                    c = (bb.min + bb.max) * 0.5
                    pa.add_actor_local_offset(u.Vector(-c.x * scale.x, -c.y * scale.y, -bb.min.z * scale.z), False, False)
            continue
        (lx, ly), (hx, hy) = t['low'], t['high']
        zl, zh = t['z_low'] + M(lx, ly), t['z_high'] + M(hx, hy)
        run = math.hypot(hx - lx, hy - ly); rise = zh - zl; th = t['thick']
        pitch = math.atan2(rise, run); slab = math.hypot(run, rise)
        yaw = -math.degrees(math.atan2(hy - ly, hx - lx))
        # top surface passes through both end points: centre of the top line, then down half the thickness along the normal
        cx, cy, cz = (lx + hx) / 2, (ly + hy) / 2, (zl + zh) / 2
        dx, dy = (hx - lx) / run, (hy - ly) / run
        nx, ny, nz = -dx * math.sin(pitch), -dy * math.sin(pitch), math.cos(pitch)   # slab normal (layout frame)
        cx -= nx * th / 2; cy -= ny * th / 2; cz -= nz * th / 2
        a = spawn(u.StaticMeshActor, f"T{i:03d}_{t['role']}_ramp", V(cx, cy, cz), 0, folder)
        a.static_mesh_component.set_static_mesh(CUBE); a.set_actor_scale3d(u.Vector(slab + 0.6, t['width'], th))
        a.set_actor_rotation(u.Rotator(0.0, math.degrees(pitch), yaw), False)  # Rotator(roll, pitch, yaw)
        if mat: a.static_mesh_component.set_material(0, mat)
        a.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
    R['terrain'] = len(L.get('terrain', []))
    # buildings
    meshes = {}; placed = []
    for i, b in enumerate(L['buildings']):
        slug = b['asset']
        if slug not in meshes:
            m = u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}')
            if not m: raise RuntimeError('missing mesh ' + slug)
            bb = m.get_bounding_box(); meshes[slug] = (m, bb)
        m, bb = meshes[slug]
        size = (bb.max.x - bb.min.x, bb.max.y - bb.min.y)
        want = L['sizes'][slug]                       # frontage, depth in metres as drawn
        # the diagram treats the longer import-report axis order (x = frontage); turn 90 if the mesh disagrees
        swap = abs(size[0] / 100 - want[0]) > abs(size[1] / 100 - want[0]) + 0.05
        yaw = -b['yaw_deg'] + (90.0 if swap else 0.0) + FRONT_FIX.get(slug, 0.0)
        cx, cy = (bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2
        r = math.radians(yaw); ox = cx * math.cos(r) - cy * math.sin(r); oy = cx * math.sin(r) + cy * math.cos(r)
        # Seat on the lowest ground under the footprint (the rest sinks in, nothing floats).
        fw, fd = want[0] / 2, want[1] / 2; br = math.radians(b['yaw_deg'])
        gz = min(G(b['x'] + dx * math.cos(br) - dy * math.sin(br), b['y'] + dx * math.sin(br) + dy * math.cos(br)) for dx in (-fw, 0, fw) for dy in (-fd, 0, fd))
        t = V(b['x'], b['y']); loc = u.Vector(t.x - ox, t.y - oy, -bb.min.z + gz * 100.0)
        a = spawn(u.StaticMeshActor, f'B{i:03d}_{slug}', loc, yaw, 'Lanes/Buildings/' + b['role'])
        a.static_mesh_component.set_static_mesh(m); a.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
        placed.append({'label': a.get_actor_label(), 'yaw': yaw, 'swap': swap})
    R['buildings'] = len(placed); R['mesh_sizes_m'] = {k: [round((v[1].max.x - v[1].min.x) / 100, 2), round((v[1].max.y - v[1].min.y) / 100, 2), round((v[1].max.z - v[1].min.z) / 100, 2)] for k, v in meshes.items()}
    R['collision'] = {k: v[0].get_editor_property('body_setup').get_editor_property('collision_trace_flag').name if v[0].get_editor_property('body_setup') else None for k, v in meshes.items()}
    # gap walls
    for i, (a0, b0) in enumerate(L['walls']):
        length = math.hypot(b0[0] - a0[0], b0[1] - a0[1]) + 1.2
        yaw = -math.degrees(math.atan2(b0[1] - a0[1], b0[0] - a0[0]))
        box(f'Wall{i:03d}', V((a0[0] + b0[0]) / 2, (a0[1] + b0[1]) / 2, 2.5 + M((a0[0] + b0[0]) / 2, (a0[1] + b0[1]) / 2)), (length, 0.5, 5.0), yaw, curb, 'Lanes/Walls')
    R['walls'] = len(L['walls'])
    # outer boundary so nobody leaves the map
    for i, (cx, cy, sx, sy) in enumerate(((0, by + 28, bx * 2 + 60, 1), (0, -by - 28, bx * 2 + 60, 1), (bx + 28, 0, 1, by * 2 + 60), (-bx - 28, 0, 1, by * 2 + 60))):
        box(f'Edge{i}', V(cx, cy, 4), (sx, sy, 8.0), 0, curb, 'Lanes/Walls')
    # lighting, player start, lane director
    tod = spawn(u.load_class(None, '/Script/Selene.SeleneTimeOfDay'), 'TimeOfDay', u.Vector(0, 0, 0), 0, 'Lanes/Lighting'); tod.set_hour(15)
    hero = next(s for s in L['structures'] if s['type'] == 'hero_spawn' and s['team'] == 'dawn')
    spawn(u.PlayerStart, 'PlayerStart_Dawn', V(hero['pos'][0], hero['pos'][1], 1.2 + G(*hero['pos'])), 0, 'Lanes')
    d = spawn(u.load_class(None, '/Script/Selene.SeleneLaneDirector'), 'LaneDirector', u.Vector(0, 0, 0), 0, 'Lanes')
    lanes = []
    for name in ('north', 'mid', 'south'):
        ln = u.SeleneLane(); ln.set_editor_property('lane_name', name)
        ln.set_editor_property('points', [V(p[0], p[1]) for p in L['lanes'][name]]); lanes.append(ln)
    d.set_editor_property('lanes', lanes)
    d.set_editor_property('dawn_base', V(*L['bases']['dawn'])); d.set_editor_property('dusk_base', V(*L['bases']['dusk']))
    if not levels.save_current_level(): raise RuntimeError('save failed')
    R.update(status='saved', actors=len(A.get_all_level_actors()), lanes=len(d.get_editor_property('lanes')))
except Exception:
    R.update(status='failed', error=traceback.format_exc()); u.log_error(R['error'])
(OUT / 'build.json').write_text(json.dumps(R, indent=1))
