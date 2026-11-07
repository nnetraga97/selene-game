"""One capture-diagnosed correction: conform pavement to terrain diagonals;
articulate oversized courts with low planted edges and finish cafe counter."""
import unreal as u,pathlib,json,math,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-4';E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);LIB=u.EditorAssetLibrary;D='/Game/Selene/Materials/Ground';ENV='/Game/Selene/Environment/TownV2/Session4';L=json.loads((R/'Design/TownV2/layout.json').read_text());B=json.loads((O/'apply.json').read_text());rep={'geometry':[],'groups':[],'props':[]}
assert not (O/'refine.json').exists(),'Correction already recorded; do not replay'
assert E.load_level('/Game/Selene/Maps/TownV2');bylabel={a.get_actor_label():a for a in A.get_all_level_actors()};assert 'V4_CafeCounter' not in bylabel
for name in ['Roads','Paving','Parking','Curbs']:
 dest=ENV+'/V4'+name;manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',True);assert manager.import_asset(dest,manager.create_source_data(str(O/'meshes-refined'/('V4'+name+'.glb'))),params)
 meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)];assert len(meshes)==1;m=meshes[0];mat=u.load_asset(D+'/MI_V4_'+name);m.set_material(0,mat);m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);LIB.save_loaded_asset(m,False);a=bylabel['V4_'+name];a.static_mesh_component.set_static_mesh(m);a.static_mesh_component.set_material(0,mat);rep['geometry'].append(m.get_path_name())
z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):return z[round((e+590)/1500*1008)*1009+round((n+750)/1500*1008)]
def vec(p):return u.Vector(p[1]*100,p[0]*100,p[2]*100)
def spawn(label,mesh,e,n,z,scale,yaw=0,mat=None,coll=False):
 a=A.spawn_actor_from_class(u.StaticMeshActor,vec([e,n,z]),u.Rotator(yaw=yaw));a.set_actor_label('V4_'+label);a.set_folder_path('TownV2/Session4');a.tags=[u.Name('TownV2Session4')];c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll' if coll else 'NoCollision');a.set_actor_scale3d(u.Vector(*scale))
 if mat:c.set_material(0,mat)
 if 'LeafCards' in mesh.get_name():c.set_editor_property('disallow_nanite',True)
 return a
cube=u.load_asset('/Engine/BasicShapes/Cube');curb=u.load_asset(D+'/MI_V4_Curbs');coral=u.load_asset(D+'/M_Town_Coral');petrol=u.load_asset(D+'/M_Town_Petrol');cream=u.load_asset(D+'/M_Town_Cream')
def box(label,e,n,z,size,mat,yaw=90):return spawn(label,cube,e,n,z,size,yaw,mat,True)
cache={}
def prop(label,slug,e,n,height,yaw=0,zz=None):
 if slug not in cache:cache[slug]=[u.load_asset(p) for p in LIB.list_assets('/Game/Assets/'+slug,True) if isinstance(u.load_asset(p),u.StaticMesh)]
 parts=cache[slug];assert parts;bounds=[m.get_bounding_box() for m in parts];low=min(b.min.z for b in bounds);high=max(b.max.z for b in bounds);sx=(min(b.min.x for b in bounds)+max(b.max.x for b in bounds))/2;sy=(min(b.min.y for b in bounds)+max(b.max.y for b in bounds))/2;scale=height*100/(high-low);angle=math.radians(yaw);rx=(sx*math.cos(angle)-sy*math.sin(angle))*scale;ry=(sx*math.sin(angle)+sy*math.cos(angle))*scale;zz=h(e,n)+.22 if zz is None else zz
 for i,m in enumerate(parts):spawn(label+'_'+str(i),m,e-ry/100,n-rx/100,zz-low*scale/100,[scale]*3,yaw)
 rep['props'].append({'label':label,'slug':slug,'point_m':[e,n,zz]})
def distance_road(e,n):
 distances=[]
 for r in L['streets']:
  if r['kind'] in ['footway','path','steps']:continue
  for a,b in zip(r['points'],r['points'][1:]):
   dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((e-a[0])*dx+(n-a[1])*dy)/max(.001,dx*dx+dy*dy)));distances.append(math.hypot(e-a[0]-t*dx,n-a[1]-t*dy)-max(r['width_m'],4.5)/2)
 return min(distances)
for i,(e,n,yaw) in enumerate([(5,35,0),(33,72,90),(72,65,90),(4,78,0),(60,-60,90),(18,-4,0),(-10,85,0),(82,-46,0)]):
 if distance_road(e,n)<6:continue
 # A short seat-height wall and offset planter pairs define courtyard rooms.
 box('CourtEdge_'+str(i),e,n,h(e,n)+.48,[7,.40,.56],curb,yaw)
 for j,off in enumerate([-2.6,2.6]):
  angle=math.radians(yaw);pe=e+off*math.sin(angle)+1.1*math.cos(angle);pn=n+off*math.cos(angle)-1.1*math.sin(angle)
  prop('CourtBed_'+str(i)+'_'+str(j),'concrete-planter',pe,pn,.75,yaw)
  prop('CourtFlowers_'+str(i)+'_'+str(j),'hydrangea-clump-r2',pe,pn,1.15,yaw,zz=h(pe,pn)+.95)
  if j==0:prop('CourtTree_'+str(i),'street-tree',pe,pn,5.5,zz=h(pe,pn)+.8)
 prop('CourtBench_'+str(i),'plaza-bench',e-1.5,n-2,.95,yaw)
 rep['groups'].append({'center_m':[e,n],'road_clearance_m':distance_road(e,n)})
for i,(e,n,rx,ry) in enumerate([(4,-17,9,5),(57,86,10,7),(91,107,7,5)]):
 prop('ParkTree_'+str(i),'street-tree',e,n,6.2,zz=h(e,n));prop('ParkBench_'+str(i),'plaza-bench',e,n-ry-1.2,.95,90)
 for j,de in enumerate([-rx*.65,rx*.65]):prop('ParkShrub_'+str(i)+'_'+str(j),'hydrangea-clump-r2',e+de,n,1.1,zz=h(e+de,n))
# Existing source grass island is explicitly a planted pocket park at the shop bend.
prop('ShopPocketTree','street-tree',-50,45,4.8,zz=h(-50,45));prop('ShopPocketSeat','plaza-bench',-47,51,.9,130)
# Make the cafe serve the terrace: compact coffee counter and espresso machine.
c=next(x for x in B['placements'] if x['hero']=='cafe');e,n,base=c['center_m'];front=n-c['building_dimensions_m'][1]/2
box('CafeCounter',e,front-.30,base+.56,[4,.75,1.12],cream);box('CafeCounterTop',e,front-.30,base+1.16,[4.15,.90,.10],petrol)
prop('CafeEspresso','espresso-machine',e-1,front-.30,.60,180,zz=base+1.23)
prop('CafeDelivery','delivery-scooter',e+7,front-8,1.15,90)
# Additional planters on the terrace edge preserve a generous central approach.
for i,(de,dn) in enumerate([(-7,-10),(7,-10),(-7,-6),(7,-6)]):
 prop('CafeTerraceBed_'+str(i),'concrete-planter',e+de,front+dn,.72,90);prop('CafeTerraceFlower_'+str(i),'hydrangea-clump-r2',e+de,front+dn,.95,zz=h(e+de,front+dn)+.85)
rep['status']='saved';assert E.save_current_level();(O/'refine.json').write_text(json.dumps(rep,indent=2));p=R/'Design/TownV2/session-4-build.json';data=json.loads(p.read_text());data['ground']=json.loads((O/'meshes-refined/ground.json').read_text());data['courtyard_groups']=rep['groups'];data['visual_correction']='Constrain paving against original terrain triangle edges; grouped court/park planting and cafe counter';p.write_text(json.dumps(data,indent=2));u.log('V4_REFINED')
