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
    ground = box('Ground', V(0, 0, -0.5), (bx * 2 + 60, by * 2 + 60, 1.0), 0, pave or road, 'Lanes/Ground')
    R['ground_material'] = (pave or road).get_path_name() if (pave or road) else None
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
        t = V(b['x'], b['y']); loc = u.Vector(t.x - ox, t.y - oy, -bb.min.z)
        a = spawn(u.StaticMeshActor, f'B{i:03d}_{slug}', loc, yaw, 'Lanes/Buildings/' + b['role'])
        a.static_mesh_component.set_static_mesh(m); a.static_mesh_component.set_mobility(u.ComponentMobility.STATIC)
        placed.append({'label': a.get_actor_label(), 'yaw': yaw, 'swap': swap})
    R['buildings'] = len(placed); R['mesh_sizes_m'] = {k: [round((v[1].max.x - v[1].min.x) / 100, 2), round((v[1].max.y - v[1].min.y) / 100, 2), round((v[1].max.z - v[1].min.z) / 100, 2)] for k, v in meshes.items()}
    R['collision'] = {k: v[0].get_editor_property('body_setup').get_editor_property('collision_trace_flag').name if v[0].get_editor_property('body_setup') else None for k, v in meshes.items()}
    # gap walls
    for i, (a0, b0) in enumerate(L['walls']):
        length = math.hypot(b0[0] - a0[0], b0[1] - a0[1]) + 1.2
        yaw = -math.degrees(math.atan2(b0[1] - a0[1], b0[0] - a0[0]))
        box(f'Wall{i:03d}', V((a0[0] + b0[0]) / 2, (a0[1] + b0[1]) / 2, 2.5), (length, 0.5, 5.0), yaw, curb, 'Lanes/Walls')
    R['walls'] = len(L['walls'])
    # outer boundary so nobody leaves the map
    for i, (cx, cy, sx, sy) in enumerate(((0, by + 28, bx * 2 + 60, 1), (0, -by - 28, bx * 2 + 60, 1), (bx + 28, 0, 1, by * 2 + 60), (-bx - 28, 0, 1, by * 2 + 60))):
        box(f'Edge{i}', V(cx, cy, 4), (sx, sy, 8.0), 0, curb, 'Lanes/Walls')
    # lighting, player start, lane director
    tod = spawn(u.load_class(None, '/Script/Selene.SeleneTimeOfDay'), 'TimeOfDay', u.Vector(0, 0, 0), 0, 'Lanes/Lighting'); tod.set_hour(15)
    hero = next(s for s in L['structures'] if s['type'] == 'hero_spawn' and s['team'] == 'dawn')
    spawn(u.PlayerStart, 'PlayerStart_Dawn', V(hero['pos'][0], hero['pos'][1], 1.2), 0, 'Lanes')
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
