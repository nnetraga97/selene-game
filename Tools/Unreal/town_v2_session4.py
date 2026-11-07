"""Session 4 targeted replacement of TownV2 buildings and ground only."""
import unreal as u,json,pathlib,math,array,collections
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-4';E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);LIB=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;T=u.AssetToolsHelpers.get_asset_tools();D='/Game/Selene/Materials/Ground';ENV='/Game/Selene/Environment/TownV2/Session4';L=json.loads((R/'Design/TownV2/layout.json').read_text());oldrecords=json.loads((R/'Saved/TownV2/session-3/placements-final.json').read_text());audit=json.loads((O/'audit.json').read_text())
assert (O/'backup-manifest.json').exists() and json.loads((O/'before/capture.json').read_text())['status']=='success'
assert not (O/'apply.json').exists(),'Already recorded; read checkpoint and use targeted changes'
assert E.load_level('/Game/Selene/Maps/TownV2')
assert not any(a.get_actor_label().startswith('V4_') for a in A.get_all_level_actors()),'V4 already saved; do not replay'
rep={'status':'building','placements':[],'ground':[],'props':[],'removed':[],'palette':{}}
z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):
 x=max(0,min(1007.999,(e+590)/1500*1008));y=max(0,min(1007.999,(n+750)/1500*1008));i=int(x);j=int(y);a=x-i;b=y-j
 return z[i*1009+j]*(1-a)*(1-b)+z[(i+1)*1009+j]*a*(1-b)+z[i*1009+j+1]*(1-a)*b+z[(i+1)*1009+j+1]*a*b

def vec(p):return u.Vector(p[1]*100,p[0]*100,p[2]*100)
def create(name,cls,factory,folder=ENV):
 path=folder+'/'+name
 return u.load_asset(path) if LIB.does_asset_exist(path) else T.create_asset(name,folder,cls,factory)
def mi(name,parent,color,folder=ENV):
 m=create(name,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew(),folder);M.set_material_instance_parent(m,parent);M.set_material_instance_vector_parameter_value(m,'BaseColorFactor',u.LinearColor(*color,1));M.update_material_instance(m);LIB.save_loaded_asset(m,False);return m

def meshactor(label,mesh,p,scale=1,yaw=0,mat=None,coll=True):
 a=A.spawn_actor_from_class(u.StaticMeshActor,vec(p),u.Rotator(yaw=yaw));a.set_actor_label(label);a.set_folder_path('TownV2/Session4');a.tags=[u.Name('TownV2Session4')];c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll' if coll else 'NoCollision');a.set_actor_scale3d(u.Vector(scale,scale,scale) if isinstance(scale,(int,float)) else u.Vector(*scale))
 if mat:c.set_material(0,mat)
 return a
cube=u.load_asset('/Engine/BasicShapes/Cube')
def box(label,p,size,mat,yaw=90,coll=True):return meshactor('V4_'+label,cube,p,size,yaw,mat,coll)
def center(a,p):
 origin,ext=a.get_actor_bounds(False);loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x+p[1]*100-origin.x,loc.y+p[0]*100-origin.y,loc.z+p[2]*100-(origin.z-ext.z)),False,False)
# All ground variants descend from the same existing ground_tiles_27 family.
ground={}
for name,parent,tint in [('Paving','MI_Town_Plaza',(1.03,1.02,.98)),('Roads','MI_Town_Road',(.52,.58,.61)),('Parking','MI_Town_Road',(.69,.71,.69)),('Curbs','MI_Town_Curb',(1.05,1.03,.98))]:
 m=create('MI_V4_'+name,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew(),D);M.set_material_instance_parent(m,u.load_asset(D+'/'+parent));M.set_material_instance_vector_parameter_value(m,'Tint',u.LinearColor(*tint,1));M.set_material_instance_scalar_parameter_value(m,'NormalStrength',.10);M.update_material_instance(m);LIB.save_loaded_asset(m,False);ground[name]=m
for name in ['Roads','Paving','Parking','Curbs']:
 assetname='V4'+name;dest=ENV+'/'+assetname
 if not LIB.does_directory_exist(dest):
  manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',False);assert manager.import_asset(dest,manager.create_source_data(str(O/'meshes'/(assetname+'.glb'))),params)
 meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)];assert len(meshes)==1
 mesh=meshes[0];mesh.set_material(0,ground[name]);mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);LIB.save_loaded_asset(mesh,False);meshactor('V4_'+name,mesh,[0,0,0],mat=ground[name]);rep['ground'].append(mesh.get_path_name())
for a in list(A.get_all_level_actors()):
 if a.get_actor_label() in ['V2_V2Roads','V2_V2Sidewalks','V2_V2Curbs','V2_Plaza']:
  rep['removed'].append(a.get_actor_label());A.destroy_actor(a)
# Footprint/use selection with 90-degree orientation alternatives; front faces road.
palettes=[('ivory',(1,1,1)),('cream',(1,.96,.86)),('sand',(.91,.86,.73)),('petrol',(.76,.94,.97)),('coral',(1,.85,.78))]
meshes={slug:u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}') for slug in audit['assets']};bylabel={a.get_actor_label():a for a in A.get_all_level_actors()};lots={l['id']:l for l in L['lots']}
def nearest_road(e,n):
 candidates=[]
 for r in L['streets']:
  if r['kind'] in ['footway','path','steps']:continue
  for p,q in zip(r['points'],r['points'][1:]):
   dx=q[0]-p[0];dy=q[1]-p[1];t=max(0,min(1,((e-p[0])*dx+(n-p[1])*dy)/max(.001,dx*dx+dy*dy)));x=p[0]+t*dx;y=p[1]+t*dy;candidates.append((math.hypot(e-x,n-y),x,y))
 return min(candidates)[1:]
for idx,record in enumerate(oldrecords):
 lot=lots[record['lot']];pts=lot['footprint']['outer'][:-1];p,q=max(zip(pts,pts[1:]+pts[:1]),key=lambda t:math.dist(*t));angle=math.atan2(q[1]-p[1],q[0]-p[0]);c=math.cos(angle);s=math.sin(angle);us=[x*c+y*s for x,y in pts];vs=[-x*s+y*c for x,y in pts];w=max(us)-min(us);d=max(vs)-min(vs);e,n,_=record['center_m'];hero=record.get('hero');old=bylabel[record['actor']]
 if hero=='clock-hall':pool=['clock-hall']
 elif hero=='bakery':pool=['shop-bakery-corner']
 elif hero=='tool-shop' or hero=='cafe':pool=['shop-tool-repair']
 elif e<0 or (n<-35 and e<55):pool=['shop-bakery-corner','shop-tool-repair','townhouse-terrace']
 elif e>90 and n<-20 and lot['area_m2']>350:pool=['workshop-garage']
 elif lot['area_m2']>370:pool=['apartment-curved','townhouse-terrace']
 else:pool=['townhouse-terrace','apartment-curved']
 options=[];target=nearest_road(e,n);front=math.degrees(math.atan2(target[0]-e,target[1]-n))-90
 for slug in pool:
  b=audit['assets'][slug]['bounds'];sx=(b[1][0]-b[0][0])/100;sy=(b[1][1]-b[0][1])/100
  for turn in [0,90,180,270]:
   ww,dd=(sx,sy) if turn%180==0 else (sy,sx);scale=min(w/ww,d/dd,1.2)*.94;yaw=90-math.degrees(angle)+turn;rotation_error=abs((yaw-front+180)%360-180)/180;score=abs(math.log((w/d)/(ww/dd)))+.3*abs(math.log(max(.1,scale)))+.2*rotation_error
   options.append((score,slug,scale,yaw,sx,sy))
 _,slug,scale,yaw,sx,sy=min(options)
 if hero=='clock-hall':scale=record['scale'];yaw=old.get_actor_rotation().yaw
 if hero=='cafe':scale=1.12;yaw=90
 # Keep original hero front direction while lowering exaggerated shop scaling.
 if hero in ['bakery','tool-shop']:yaw=old.get_actor_rotation().yaw;scale=min(scale,1.12)
 base=lot['base_z_m']+.22
 rep['removed'].append(old.get_actor_label());A.destroy_actor(old);a=meshactor(record['actor'],meshes[slug],[e,n,base],scale,yaw);center(a,[e,n,base]);pname,color=palettes[idx%len(palettes)]
 for slot in range(a.static_mesh_component.get_num_materials()):
  parent=meshes[slug].get_material(slot);mat=mi('MI_V4_Lot_'+str(idx)+'_'+str(slot)+'_'+pname,parent,color);a.static_mesh_component.set_material(slot,mat)
 item={'lot':record['lot'],'hero':hero,'actor':record['actor'],'asset':meshes[slug].get_path_name(),'building':slug,'center_m':[e,n,base],'scale':scale,'yaw':yaw,'palette':pname,'tint':color,'lot_dimensions_m':[w,d],'building_dimensions_m':[sx*scale,sy*scale]};rep['placements'].append(item)
 # Shallow continuous plinth and edge seating wall visually close any terrain gap.
 foundation=box('Foundation_'+str(idx),[e,n,base-.27],[sx*scale*.99,sy*scale*.99,.54],ground['Curbs'],yaw)
 # Two short edge walls frame courts without blocking entrances or streets.
 if idx%2==0 and not hero:
  rad=math.radians(yaw);cx=e+math.cos(rad)*(sy*scale/2+2);cy=n-math.sin(rad)*(sy*scale/2+2)
  if math.hypot(cx-target[0],cy-target[1])>5:
   box('CourtWall_'+str(idx),[cx,cy,h(cx,cy)+.42],[min(5,sx*scale),.32,.50],ground['Curbs'],yaw)
# Remove core grass patches from paved town, and seat existing props on new paving.
for a in list(A.get_all_level_actors()):
 label=a.get_actor_label();pos=a.get_actor_location();e=pos.y/100;n=pos.x/100
 if label.startswith('V2_Grass_') and -125<e<130 and -125<n<130:
  rep['removed'].append(label);A.destroy_actor(a)
 elif label.startswith(('V2_SeleneBench','V2_SeleneBin','V2_Planter','V2_Lamp','V2_Bench','V2_ShopPot')):center(a,[e,n,h(e,n)+.2])
# Existing Tripo prop assemblies retain source materials and shared part pivots.
def prop(label,slug,e,n,height,yaw=0,zz=None):
 paths=LIB.list_assets('/Game/Assets/'+slug,True);parts=[u.load_asset(p) for p in paths if isinstance(u.load_asset(p),u.StaticMesh)];assert parts,slug;bounds=[m.get_bounding_box() for m in parts];low=min(b.min.z for b in bounds);high=max(b.max.z for b in bounds);sx=(min(b.min.x for b in bounds)+max(b.max.x for b in bounds))/2;sy=(min(b.min.y for b in bounds)+max(b.max.y for b in bounds))/2;scale=height*100/(high-low);angle=math.radians(yaw);rx=(sx*math.cos(angle)-sy*math.sin(angle))*scale;ry=(sx*math.sin(angle)+sy*math.cos(angle))*scale;zz=h(e,n)+.21 if zz is None else zz
 for i,m in enumerate(parts):
  a=meshactor('V4_'+label+'_'+str(i),m,[e-ry/100,n-rx/100,zz-low*scale/100],scale,yaw,coll=False)
  if 'LeafCards' in m.get_name():a.static_mesh_component.set_editor_property('disallow_nanite',True)
 rep['props'].append({'label':label,'asset':slug,'point_m':[e,n,zz]})
# Four compact plaza seating/planting groups; central walking corridor remains open.
for i,(e,n) in enumerate([(-33,3),(-13,3),(-33,18),(-13,18)]):
 prop('PlazaPlanter_'+str(i),'concrete-planter',e,n,.72)
 prop('PlazaFlowers_'+str(i),'hydrangea-clump-r2',e,n,1.0,zz=h(e,n)+.85)
 prop('PlazaTree_'+str(i),'street-tree',e,n,5.5,zz=h(e,n)+.75)
 prop('PlazaSeat_'+str(i),'plaza-bench',e+2.2,n,.95,yaw=90 if n<10 else -90)
# Cafe hero: shop body, coral canopy, large readable sign, six bistro tables.
cafe=next(x for x in rep['placements'] if x['hero']=='cafe');ce,cn,base=cafe['center_m'];front_n=cn-cafe['building_dimensions_m'][1]/2
coral=u.load_asset(D+'/M_Town_Coral');petrol=u.load_asset(D+'/M_Town_Petrol');cream=u.load_asset(D+'/M_Town_Cream')
box('CafeCanopy',[ce,front_n-1.0,base+3.6],[10.3,2.4,.18],coral,coll=False);box('CafeFascia',[ce,front_n-2.20,base+3.38],[10.3,.12,.45],coral,coll=False)
box('CafeSignBack',[ce,front_n-2.29,base+4.10],[7.6,.12,.8],petrol,coll=False)
sign=A.spawn_actor_from_class(u.TextRenderActor,vec([ce,front_n-2.37,base+3.83]),u.Rotator(yaw=180));sign.set_actor_label('V4_CafeSign');sign.set_folder_path('TownV2/Session4');sign.text_render.set_text('CAFÉ  SELENE');sign.text_render.set_world_size(57);sign.text_render.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
for i,(de,dn) in enumerate([(-4,-5),(0,-5),(4,-5),(-4,-9),(0,-9),(4,-9)]):
 e=ce+de;n=front_n+dn;prop('CafeTable_'+str(i),'bistro-table',e,n,.78)
 for j,off in enumerate([-1,1]):prop('CafeChair_'+str(i)+'_'+str(j),'bistro-chair-r2',e+off,n,.95,yaw=90*off)
for i,de in enumerate([-6.5,6.5]):
 prop('CafePlanter_'+str(i),'concrete-planter',ce+de,front_n-4,.8);prop('CafeFlowers_'+str(i),'hydrangea-clump-r2',ce+de,front_n-4,1.1,zz=h(ce+de,front_n-4)+.9)
# Paved parking court uses restrained bay lines from the same pale material family.
for i in range(8):
 e=-46+i*2.6;n=108
 box('ParkingBay_'+str(i),[e,n,h(e,n)+.12],[.10,4.8,.025],cream,coll=False)
# Keep trees in beds instead of bare paving; no seafront or hillside vegetation edits.
for a in list(A.get_all_level_actors()):
 label=a.get_actor_label();pos=a.get_actor_location();e=pos.y/100;n=pos.x/100
 if label.startswith('V2_Tree_') and label.endswith('_Trunk') and -35<e<120 and -100<n<120:
  prop('ExistingTreeBed_'+label[8:],'concrete-planter',e,n,.60)
rep['counts']=dict(collections.Counter(x['building'] for x in rep['placements']));rep['actor_count']=len(A.get_all_level_actors());rep['status']='saved';assert E.save_current_level();(O/'apply.json').write_text(json.dumps(rep,indent=2));(R/'Design/TownV2/session-4-build.json').write_text(json.dumps({'placements':rep['placements'],'counts':rep['counts'],'ground':json.loads((O/'meshes/ground.json').read_text()),'source':'session-3 checkpoint targeted building and ground replacement'},indent=2));u.log('V4_SAVED '+json.dumps(rep['counts']))
