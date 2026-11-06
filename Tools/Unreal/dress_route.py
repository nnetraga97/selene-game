"""Apply Design/Blockout/dressing.json to Town; safe for unattended null-RHI.

Run from the project root with UnrealEditor-Cmd Selene.uproject
-run=pythonscript -script=Tools/Unreal/dress_route.py -unattended -nop4 -nosplash -nullrhi
Folder assets are assemblies: all recursively discovered StaticMeshes share their
imported coordinates. Their combined bounds are centred and grounded as a unit.
No imports, mesh resizing, actor deletion outside our tag, or OFPA conversion.
"""
import json
import math
from pathlib import Path
import sys
import traceback

import unreal as u

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Tools/Blockout'))
from validate_dressing import (  # noqa: E402
    BUFFER, SIZES, asset_key, dimensions, overlap, path_distance, polygon, validate,
)

TAG = 'SeleneDressing'
STATE = 'SeleneDressingHidden:'
MAP = '/Game/Selene/Maps/Town'
REPORT = dict(spawned=[], skipped=[], hidden_blockout_actors=[], collision_changes=[], warnings=[])


def warn(message):
    REPORT['warnings'].append(message)
    u.log_warning(message)


def resolve(asset):
    if u.EditorAssetLibrary.does_directory_exist(asset):
        paths = sorted(u.EditorAssetLibrary.list_assets(asset, recursive=True, include_folder=False))
        return [mesh for path in paths if isinstance(mesh := u.EditorAssetLibrary.load_asset(path), u.StaticMesh)]
    mesh = u.EditorAssetLibrary.load_asset(asset) if u.EditorAssetLibrary.does_asset_exist(asset) else None
    return [mesh] if isinstance(mesh, u.StaticMesh) else []


def bounds(meshes):
    boxes = [m.get_bounding_box() for m in meshes]
    low = [min(getattr(b.min, axis) for b in boxes) for axis in ('x','y','z')]
    high = [max(getattr(b.max, axis) for b in boxes) for axis in ('x','y','z')]
    if any(b-a <= 0 for a,b in zip(low,high)):
        raise RuntimeError('Empty or degenerate mesh assembly bounds')
    return low, high


def rotate_xy(x, y, yaw):
    a = math.radians(yaw)
    return x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)


def assembly_polygon(low, high, scale, yaw, location):
    # UE centimetres -> layout metres, preserving actual pivot and yaw.
    return [[(location[1]+ry)/100, (location[0]+rx)/100]
            for x,y in [(low[0],low[1]),(high[0],low[1]),(high[0],high[1]),(low[0],high[1])]
            for rx,ry in [rotate_xy(x*scale[0], y*scale[1], yaw)]]


def simple_collision(mesh):
    library = u.EditorStaticMeshLibrary
    if library.get_simple_collision_count(mesh) == 0:
        if library.add_simple_collisions(mesh, u.ScriptingCollisionShapeType.BOX) < 0:
            raise RuntimeError('Cannot add box collision: '+mesh.get_path_name())
        # Record immediately so even a later save failure is visible.
        REPORT['collision_changes'].append(mesh.get_path_name())
        if not u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False):
            raise RuntimeError('Cannot save collision asset: '+mesh.get_path_name())


def spawn(meshes, item, location, scale, actors):
    created = []
    try:
        for i,mesh in enumerate(meshes):
            if item.get('collision','none') == 'simple':
                simple_collision(mesh)
            actor = actors.spawn_actor_from_class(u.StaticMeshActor, u.Vector(*location), u.Rotator(yaw=item['yaw_deg']))
            if not actor:
                raise RuntimeError('Actor spawn failed: '+item['id'])
            created.append(actor)
            actor.tags = [u.Name(TAG)]
            actor.set_actor_label(item['id'] if len(meshes)==1 else f"{item['id']}__{i+1:02}")
            actor.set_folder_path(u.Name('Dressing/'+item.get('group','buildings')))
            component = actor.static_mesh_component
            component.set_static_mesh(mesh)
            component.set_mobility(u.ComponentMobility.STATIC)
            component.set_collision_profile_name('BlockAll' if item.get('collision','none')=='simple' else 'NoCollision')
            component.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if item.get('collision','none')=='simple' else u.CollisionEnabled.NO_COLLISION)
            actor.set_actor_scale3d(u.Vector(*scale))
        return created
    except Exception:
        for actor in created:
            actors.destroy_actor(actor)
        raise


def restore_blockout(actor):
    tags = [str(t) for t in actor.tags]
    states = [t for t in tags if t.startswith(STATE)]
    if not states:
        return
    actor.modify()
    if actor.root_component: actor.root_component.modify()
    old = json.loads(states[0][len(STATE):])
    actor.set_actor_hidden_in_game(old['hidden'])
    actor.set_is_temporarily_hidden_in_editor(old['editor_hidden'])
    actor.set_actor_enable_collision(old['collision'])
    if actor.root_component: actor.root_component.set_visibility(True, True)
    actor.tags = [u.Name(t) for t in tags if not t.startswith(STATE)]


def hide_blockout(actor):
    actor.modify()  # mark the external actor package dirty so the change is saved
    if actor.root_component: actor.root_component.modify()
    old = dict(hidden=bool(actor.get_editor_property('hidden')), editor_hidden=actor.is_temporarily_hidden_in_editor(), collision=actor.get_actor_enable_collision())
    actor.tags = list(actor.tags)+[u.Name(STATE+json.dumps(old,separators=(',',':')))]
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    actor.set_actor_enable_collision(False)
    # Hidden-in-game alone is not saved for editor views; component visibility is saved and applies everywhere.
    if actor.root_component: actor.root_component.set_visibility(False, True)
    REPORT['hidden_blockout_actors'].append(actor.get_actor_label())


def main():
    data = json.loads((ROOT/'Design/Blockout/dressing.json').read_text())
    layout = json.loads((ROOT/'Design/Blockout/layout.json').read_text())
    errors,_ = validate(data,layout)
    if errors:
        raise RuntimeError('\n'.join(errors))
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError('Cannot load '+MAP)
    level = levels.get_current_level()
    REPORT['external_actors_enabled'] = bool(level.get_editor_property('use_external_actors'))
    if not REPORT['external_actors_enabled']:
        warn('Town has not been converted to external actors. Run the documented ConvertLevelsToExternalActors commandlet separately; changing the flag alone does not convert packages.')
    all_actors = list(actors.get_all_level_actors())
    REPORT['removed_previous'] = 0
    for actor in all_actors:
        restore_blockout(actor)
        if actor.actor_has_tag(TAG):
            if not actors.destroy_actor(actor):
                raise RuntimeError('Cannot remove '+actor.get_actor_label())
            REPORT['removed_previous'] += 1
    route = next(r['points'] for r in layout['routes'] if r['id']=='R1')
    lots = {lot['id']:lot for lot in layout['lots']}
    successful = set()
    for item in data['placements'] + data['buildings']:
        meshes = resolve(item['asset'])
        if not meshes:
            reason = 'Missing StaticMesh asset(s): '+item['asset']
            warn(item['id']+': '+reason)
            REPORT['skipped'].append(dict(id=item['id'],reason=reason))
            continue
        # Do not leave flowers hanging in space if the pending planter is absent.
        support = item['id'].replace('hydrangea_','planter_')
        if item['id'].startswith('hydrangea_') and support not in successful:
            REPORT['skipped'].append(dict(id=item['id'],reason='Supporting planter unavailable'))
            warn(item['id']+': supporting planter unavailable')
            continue
        low,high = bounds(meshes)
        size = [b-a for a,b in zip(low,high)]
        shell_actors = []
        if 'lot' in item:
            lot = lots[item['lot']]
            height = lot['ground_height']+(lot['storeys']-1)*lot['floor_height']
            # Extents in lot-local E/N after converting UE rotation.
            a = math.radians(90-item['yaw_deg']-lot['footprint'].get('rotation',0))
            width = abs(math.cos(a))*size[0]+abs(math.sin(a))*size[1]
            depth = abs(math.sin(a))*size[0]+abs(math.cos(a))*size[1]
            fit_fp = min(lot['footprint']['size'][0]*100/width,lot['footprint']['size'][1]*100/depth)
            # 'native': keep the pipeline's real-world scale (height_m was normalised), shrinking only if it overflows the lot.
            s = height*100/size[2] if item['fit']=='height' else min(1.0, fit_fp) if item['fit']=='native' else fit_fp
            scale = [s]*3
            center = lot['footprint']['center']
            rx,ry = rotate_xy((low[0]+high[0])*s/2,(low[1]+high[1])*s/2,item['yaw_deg'])
            location = [center[1]*100-rx,center[0]*100-ry,lot['base_z']*100-low[2]*s]
            shell_actors = [actor for actor in actors.get_all_level_actors()
                            if actor.actor_has_tag('SeleneBlockout') and str(actor.get_folder_path())=='Blockout/'+lot['area']
                            and actor.get_actor_label().startswith(lot['id']+'_')]
            if not shell_actors:
                raise RuntimeError('No matching blockout actors for '+lot['id'])
        else:
            scale = item.get('scale',[1,1,1])
            if isinstance(scale,(int,float)): scale = [scale]*3
            e,n,z = item['position']
            location = [n*100,e*100,z*100]
            if u.EditorAssetLibrary.does_directory_exist(item['asset']):
                # Unknown folder meshes may have off-centre pivots. Ground their
                # aggregate, leaving direct mesh paths at the authored base pivot.
                rx,ry = rotate_xy((low[0]+high[0])*scale[0]/2,(low[1]+high[1])*scale[1]/2,item['yaw_deg'])
                location = [location[0]-rx,location[1]-ry,location[2]-low[2]*scale[2]]
            expected = dimensions(item)
            if any(actual*s/100 > limit+.025 for actual,s,limit in zip(size,scale,expected)):
                reason = 'Actual imported bounds exceed validated envelope; revise plan before spawning'
                warn(item['id']+': '+reason)
                REPORT['skipped'].append(dict(id=item['id'],reason=reason,bounds_m=[v*s/100 for v,s in zip(size,scale)],envelope_m=expected))
                continue
        actual_poly = assembly_polygon(low,high,scale,item['yaw_deg'],location)
        if 'lot' not in item:
            # Validate actual pivot/bounds against walls and door apertures too,
            # not merely the expected maximum dimensions.
            key = asset_key(item)
            original_size = SIZES[key]
            SIZES[key] = tuple(v/100 for v in size)
            probe = dict(item, position=[sum(v[0] for v in actual_poly)/4,
                                        sum(v[1] for v in actual_poly)/4,
                                        (location[2]+low[2]*scale[2])/100])
            try:
                actual_errors,_ = validate(dict(schema_version=1,placements=[probe],buildings=[]),layout)
            finally:
                SIZES[key] = original_size
            if actual_errors:
                reason='Actual imported bounds fail plan checks: '+'; '.join(actual_errors)
                warn(item['id']+': '+reason)
                REPORT['skipped'].append(dict(id=item['id'],reason=reason))
                continue
        distance = path_distance(actual_poly, route)
        # Height fit is not clamped: skip unsafe art rather than spill over lots.
        if distance < BUFFER-1e-6 or ('lot' in item and any(
                overlap(actual_poly,polygon(other['footprint']))
                for other in layout['lots'] if other['id']!=item['lot'])):
            reason='Actual assembly bounds violate R1 clearance or another lot'
            warn(item['id']+': '+reason)
            REPORT['skipped'].append(dict(id=item['id'],reason=reason))
            continue
        created = spawn(meshes, item if 'lot' not in item else dict(item,collision='simple'), location, scale, actors)
        successful.add(item['id'])
        for actor in created:
            REPORT['spawned'].append(dict(id=item['id'],label=actor.get_actor_label(),asset=actor.static_mesh_component.static_mesh.get_path_name(),location_ue_cm=location,scale=scale,yaw_deg=item['yaw_deg'],external=actor.is_package_external()))
        # Hide only after the replacement assembly has spawned successfully.
        for actor in shell_actors:
            hide_blockout(actor)
    if not levels.save_current_level():
        raise RuntimeError('Town save failed')
    if not u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Dirty level/external actor package save failed')
    REPORT['map'] = MAP
    REPORT['status'] = 'success'
    REPORT['review_required'] = ['Imported front/corner orientation and clock-hall 7.7m height fit', 'Planter bowl/flower support, pendant ceiling and wall attachments', 'Player capsule sweep through R1 and cafe; visual and collision review', 'Confirm external actor packaging if Town was not converted']


if __name__ == '__main__':
    report = ROOT/'Saved/Dressing/report.json'
    try:
        main()
    except Exception as error:
        REPORT.update(status='failed',error=str(error),traceback=traceback.format_exc())
        raise
    finally:
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(REPORT,indent=2)+'\n')
        u.log('Dressing report: '+str(report))
