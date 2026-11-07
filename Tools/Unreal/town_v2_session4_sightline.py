"""Single diagnosed composition fix: clear bakery sightline from fixed camera."""
import unreal as u,json,pathlib,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-4';assert not (O/'sightline.json').exists(),'Already corrected'
E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):return z[round((e+590)/1500*1008)*1009+round((n+750)/1500*1008)]
old=u.Vector(4500,-5000,h(-50,45)*100);new=u.Vector(4910,-4700,h(-47,49.1)*100);ratio=3.4/4.8;changed=[]
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('V4_ShopPocketTree_'):
  p=a.get_actor_location();a.set_actor_location(new+(p-old)*ratio,False,False);a.set_actor_scale3d(a.get_actor_scale3d()*ratio);changed.append(a.get_actor_label())
assert len(changed)==2;assert E.save_current_level();(O/'sightline.json').write_text(json.dumps({'status':'saved','actors':changed,'before_center_m':[-50,45],'after_center_m':[-47,49.1],'height_m':3.4,'reason':'Original 4.8 m tree obscured bakery in fixed 03_shop_street capture; moved within same pocket park'},indent=2))
