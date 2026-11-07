"""One visual correction pass: ribbon winding reimport, ordinary houses, hero facing and plaza dressing."""
import unreal as u,json,pathlib,math,random,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-3';E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);LIB=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;D='/Game/Selene/Materials/Ground';ENV='/Game/Selene/Environment/TownV2';F='/Game/Fantastic_Village_Pack';L=json.loads((R/'Design/TownV2/layout.json').read_text());B=json.loads((O/'build.json').read_text());rep={'road_reimports':[],'building_replacements':[],'hero_facing':[],'broadleaf_replacements':0,'new_props':[]}
assert not (O/'refine.json').exists(),'Already applied; inspect saved state before replay'
for name,matname in [('V2Roads','MI_Town_Road'),('V2Sidewalks','MI_Town_Plaza'),('V2Curbs','MI_Town_Curb')]:
 manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',True);dest=ENV+'/'+name
 assert manager.import_asset(dest,manager.create_source_data(str(O/'meshes'/(name+'.glb'))),params)
 meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)];assert len(meshes)==1
 mesh=meshes[0];mat=u.load_asset(D+'/'+matname);mesh.set_material(0,mat);mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);LIB.save_loaded_asset(mesh,False)
 for a in A.get_all_level_actors():
  if a.get_actor_label()=='V2_'+name:a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,mat)
 rep['road_reimports'].append(mesh.get_path_name())
def tint(a):
 for c in a.get_components_by_class(u.StaticMeshComponent):
  for i in range(c.get_num_materials()):
   m=c.get_material(i)
   if m:
    path='/Game/Selene/Environment/FabTints/MI_V2_'+m.get_name()
    if LIB.does_asset_exist(path):c.set_material(i,u.load_asset(path))
def center(a,p):
 o,e=a.get_actor_bounds(False);loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x+p[1]*100-o.x,loc.y+p[0]*100-o.y,loc.z+p[2]*100-(o.z-e.z)),False,False)
variants=[2,3,4,6,8,9,10,11,12];counts={i:0 for i in variants};candidates={int(x['asset'].split('_')[-1]):x for x in B['pack_candidates']}
bylabel={a.get_actor_label():a for a in A.get_all_level_actors()}
for record in B['placements']:
 if not record['asset'].endswith(('_13','_14')):continue
 lot=next(q for q in L['lots'] if q['id']==record['lot']);pts=lot['footprint']['outer'][:-1];p,q=max(zip(pts,pts[1:]+pts[:1]),key=lambda t:math.dist(*t));angle=math.atan2(q[1]-p[1],q[0]-p[0]);c=math.cos(angle);s=math.sin(angle);us=[x*c+y*s for x,y in pts];vs=[-x*s+y*c for x,y in pts];w=max(us)-min(us);d=max(vs)-min(vs)
 choice=min(variants,key=lambda i:abs(math.log((w/d)/(candidates[i]['size_cm'][0]/candidates[i]['size_cm'][1])))+.3*counts[i]);counts[choice]+=1;data=candidates[choice];sx,sy,sz=data['size_cm'];scale=min(w*100/sx,d*100/sy,1.3)*.94
 old=bylabel[record['actor']];rot=old.get_actor_rotation();loc=old.get_actor_location();A.destroy_actor(old);cls=LIB.load_blueprint_class(data['asset']);a=A.spawn_actor_from_class(cls,loc,rot);a.set_actor_label(record['actor']);a.set_folder_path('TownV2');a.set_actor_scale3d(u.Vector(scale,scale,scale));center(a,record['center_m']);tint(a)
 rep['building_replacements'].append({'actor':record['actor'],'old':record['asset'],'new':data['asset'],'scale':scale});record.update(asset=data['asset'],scale=scale)
# Clock face originally faces local +Y (verified old Town uses yaw 90 for a south-facing front).
clock=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='V2_Hero_clock-hall');p=next(r['center_m'] for r in B['placements'] if r['hero']=='clock-hall');yaw=math.degrees(math.atan2(-22.5-p[0],10-p[1]))-90;clock.set_actor_rotation(u.Rotator(yaw=yaw),False);center(clock,p);rep['hero_facing'].append({'actor':clock.get_actor_label(),'yaw':yaw,'toward':'plaza'})
z=array.array('H');z.frombytes((R/'Design/TownV2/terrain/heightmap-ue.r16').read_bytes())
def h(e,n):return (z[round((e+590)/1500*1008)*1009+round((n+750)/1500*1008)]-32768)/128
# Replace core conifers with our existing leafy street-tree assembly; distant pack vegetation stays.
paths=['/Game/Assets/street-tree/street-tree/StaticMeshes/SM_street-tree_Trunk','/Game/Assets/street-tree/street-tree/StaticMeshes/SM_street-tree_LeafCards'];meshes=[u.load_asset(p) for p in paths];bounds=[m.get_bounding_box() for m in meshes];low=min(b.min.z for b in bounds);high=max(b.max.z for b in bounds)
for a in list(A.get_all_level_actors()):
 if not a.get_actor_label().startswith('V2_Tree_'):continue
 pos=a.get_actor_location();e=pos.y/100;n=pos.x/100
 if not(-100<e<130 and -100<n<125):continue
 name=a.get_actor_label();o,ex=a.get_actor_bounds(False);height=ex.z*2;scale=height/(high-low);A.destroy_actor(a)
 for i,m in enumerate(meshes):
  b=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(n*100,e*100,h(e,n)*100-low*scale));b.set_actor_label(name+('_Trunk' if i==0 else '_Leaves'));b.set_folder_path('TownV2');b.static_mesh_component.set_static_mesh(m);b.static_mesh_component.set_collision_profile_name('NoCollision');b.set_actor_scale3d(u.Vector(scale,scale,scale))
  if i==1:b.static_mesh_component.set_editor_property('disallow_nanite',True)
 rep['broadleaf_replacements']+=1
# Existing Selene props add a stronger contemporary plaza identity.
def prop(label,path,e,n,height,ground=None,yaw=0):
 m=u.load_asset(path);bounds=m.get_bounding_box();scale=height*100/(bounds.max.z-bounds.min.z);zz=h(e,n)+.22 if ground is None else ground;a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(n*100,e*100,zz*100),u.Rotator(yaw=yaw));a.set_actor_label('V2_'+label);a.set_folder_path('TownV2');a.static_mesh_component.set_static_mesh(m);a.set_actor_scale3d(u.Vector(scale,scale,scale));center(a,[e,n,zz]);a.static_mesh_component.set_collision_profile_name('NoCollision');rep['new_props'].append({'label':label,'asset':path})
for i,(e,n) in enumerate([(-34,6),(-34,14),(-11,6),(-11,14)]):prop('SeleneBin_'+str(i),'/Game/Assets/trash-bin-r2/trash-bin-r2/StaticMeshes/trash-bin-r2',e,n,1.05,6.34)
for i,(e,n,yaw0) in enumerate([(-31,3,0),(-26,3,0),(-31,17,180),(-26,17,180)]):prop('SeleneBench_'+str(i),'/Game/Assets/plaza-bench/plaza-bench/StaticMeshes/plaza-bench',e,n,1.05,6.34,yaw0)
# Use existing village table/barrel set for cafe/shop threshold clutter.
for i,(e,n) in enumerate([(-42,48),(-38,49),(-19,47),(-15,48)]):
 prop('ShopPot_'+str(i),F+'/meshes/props/natural/SM_PROP_PLANT_pot_v2_01',e,n,1.2)
# Readable daylight with softened warm key and cooler shadow grade; preserve TOD system.
tod=next(a for a in A.get_all_level_actors() if a.get_class().get_name()=='SeleneTimeOfDay');sun=tod.get_editor_property('sun');sun.set_editor_property('light_source_angle',4.)
# Cream/petrol accents are intentionally brighter than the heavily darkened first tint pass.
for path in LIB.list_assets('/Game/Selene/Environment/FabTints',True):
 m=u.load_asset(path);name=m.get_name();col=(.32,.52,.56) if 'wood' in name else ((1.0,.84,.65) if 'wall' in name else ((1.0,.55,.38) if 'roof' in name else None))
 if col:M.set_material_instance_vector_parameter_value(m,'Base Color Tint',u.LinearColor(*col,1));M.update_material_instance(m);LIB.save_loaded_asset(m,False)
E.save_current_level();rep['actor_count']=len(A.get_all_level_actors());rep['status']='saved';(O/'refine.json').write_text(json.dumps(rep,indent=2));(O/'placements-final.json').write_text(json.dumps(B['placements'],indent=2))
