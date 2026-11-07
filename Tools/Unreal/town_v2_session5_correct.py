"""One diagnosed street-clearance correction and one visual rollback; never replay."""
import unreal as u,json,pathlib,math,array,shutil
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-5';assert not (O/'correction.json').exists();assert json.loads((O/'apply.json').read_text())['status']=='saved';E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');by={a.get_actor_label():a for a in A.get_all_level_actors()};D='/Game/Selene/Materials/Ground';rep={'status':'correcting','removed':[],'shifted':[],'reverted':[]};z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):
 x=max(0,min(1007.999,(e+590)/1500*1008));y=max(0,min(1007.999,(n+750)/1500*1008));i=int(x);j=int(y);a=x-i;b=y-j
 return z[i*1009+j]*(1-a)*(1-b)+z[(i+1)*1009+j]*a*(1-b)+z[i*1009+j+1]*(1-a)*b+z[(i+1)*1009+j+1]*a*b
def vec(e,n,z):return u.Vector(n*100,e*100,z*100)
def shift(label,prefix,old,new,foundation=None):
 delta=vec(new[0]-old[0],new[1]-old[1],h(*new)-h(*old));labels=[label]+[k for k in by if k.startswith(prefix)]
 if foundation:labels.append(foundation)
 for k in set(labels):a=by[k];a.set_actor_location(a.get_actor_location()+delta,False,False)
 rep['shifted'].append({'actor':label,'old_center_m':old,'new_center_m':new,'actors':list(set(labels))})
# This rejected extra shop intersects Ali'i Drive in the design overlay.
for k,a in by.items():
 if k.startswith('V5_LowerShop') or k in ['V5_LinkWall_0','V5_LinkCap_0']:
  rep['removed'].append(k);A.destroy_actor(a)
shift('V2_Hero_clock-hall','V5_Front_4_',[28,3],[32,9],'V4_Foundation_4')
shift('V5_CafeNeighbour','V5_CafeNeighbour_',[3,50],[5,53])
shift('V5_ShopCorner','V5_ShopCorner_',[-33,63],[-31.5,64.5])
shift('V5_ShopRow','V5_ShopRow_',[-46,76],[-43,79])
# Restore the townhouse that vanished behind the bakery in fixed view 03.
old=json.loads((R/'Saved/TownV2/session-4/apply.json').read_text())['placements'][9];saved=next(x for x in json.loads((R/'Saved/TownV2/session-4/readback-final.json').read_text())['buildings'] if x['actor']==old['actor']);a=by[old['actor']];a.set_actor_location(u.Vector(*saved['position_cm']),False,False);a.set_actor_rotation(u.Rotator(yaw=old['yaw']),False);a.set_actor_scale3d(u.Vector(old['scale'],old['scale'],old['scale']));e,n,base=old['center_m'];f=by['V4_Foundation_9'];f.set_actor_location(vec(e,n,base-.27),False,False);f.set_actor_rotation(u.Rotator(yaw=old['yaw']),False);w,d=old['building_dimensions_m'];f.set_actor_scale3d(u.Vector(w*.99,d*.99,.54));f.static_mesh_component.set_material(0,u.load_asset(D+'/MI_V4_Curbs'))
for k,a in by.items():
 if k.startswith('V5_Front_9_'):rep['removed'].append(k);A.destroy_actor(a)
rep['reverted'].append({'actor':old['actor'],'reason':'Rotated townhouse lost visible facade behind bakery in fixed view 03; restored exact Session 4 transform and foundation'})
assert E.save_current_level();rep['status']='saved';rep['rejected_buildings']=['V5_LowerShop'];rep['reason']='Recorded street/footpath geometry exposed one road obstruction and tight corners; corrected once. Separately reverted visually worse townhouse turn.';(O/'correction.json').write_text(json.dumps(rep,indent=2));u.log('V5_CORRECTED')
