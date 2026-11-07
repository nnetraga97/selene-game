"""Headless, bounded Session 3 builder. Existing TownV2 only."""
import unreal as u,json,math,random,pathlib
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-3';L=json.loads((R/'Design/TownV2/layout.json').read_text());A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.get_editor_subsystem(u.LevelEditorSubsystem);LIB=u.EditorAssetLibrary;T=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary
assert E.load_level('/Game/Selene/Maps/TownV2')
assert not any(a.get_actor_label().startswith('V2_') for a in A.get_all_level_actors()),'Existing V2 content: no duplicate rebuild'
D='/Game/Selene/Materials/Ground';ENV='/Game/Selene/Environment/TownV2';F='/Game/Fantastic_Village_Pack';report={'placements':[],'tints':{},'scatter':{},'checkpoints':[]}
def write(): (O/'build.json').write_text(json.dumps(report,indent=2))
def checkpoint(s):
 E.save_current_level();report['checkpoints'].append(s);report['actors']=len(A.get_all_level_actors());write();u.log('V2_CHECKPOINT '+s)
def vec(p):return u.Vector(p[1]*100,p[0]*100,p[2]*100)
def spawn(cls,name,p,angle=0):
 a=A.spawn_actor_from_class(cls,vec(p),u.Rotator(yaw=angle));a.set_actor_label('V2_'+name);a.set_folder_path('TownV2');return a
def mesh_actor(name,mesh,p,scale=1,yaw=0,mat=None,coll=True):
 a=spawn(u.StaticMeshActor,name,p,yaw);c=a.static_mesh_component;c.set_static_mesh(mesh);a.set_actor_scale3d(u.Vector(scale,scale,scale) if isinstance(scale,(int,float)) else u.Vector(*scale));c.set_collision_profile_name('BlockAll' if coll else 'NoCollision')
 if mat:c.set_material(0,mat)
 return a
cube=u.load_asset('/Engine/BasicShapes/Cube')
def box(name,p,size,mat):return mesh_actor(name,cube,p,size,90,mat)
def expression(mat,cls,**props):
 e=M.create_material_expression(mat,cls)
 for k,v in props.items():e.set_editor_property(k,v)
 return e
def constant(mat,v):return expression(mat,u.MaterialExpressionConstant,r=v)
def save_mat(m):M.recompile_material(m);LIB.save_loaded_asset(m,False);return m
# World-space triplanar textures, normal slope blend and sea-level sand.
terrain=LIB.load_asset(D+'/M_V2_TerrainAuto') if LIB.does_asset_exist(D+'/M_V2_TerrainAuto') else T.create_asset('M_V2_TerrainAuto',D,u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(terrain)
pos=expression(terrain,u.MaterialExpressionWorldPosition);normal=expression(terrain,u.MaterialExpressionVertexNormalWS)
custom=expression(terrain,u.MaterialExpressionCustom,output_type=u.CustomMaterialOutputType.CMOT_FLOAT3)
inputs=[]
for name in ['P','N','G','S']:
 item=u.CustomInput();item.set_editor_property('input_name',name);inputs.append(item)
custom.set_editor_property('inputs',inputs)
custom.set_editor_property('code','float3 w=pow(abs(N),4);w/=max(w.x+w.y+w.z,.001);float3 g=(Texture2DSample(G,GSampler,P.yz/450).rgb*w.x+Texture2DSample(G,GSampler,P.xz/450).rgb*w.y+Texture2DSample(G,GSampler,P.xy/450).rgb*w.z);float3 s=(Texture2DSample(S,SSampler,P.yz/350).rgb*w.x+Texture2DSample(S,SSampler,P.xz/350).rgb*w.y+Texture2DSample(S,SSampler,P.xy/350).rgb*w.z);float slope=smoothstep(.12,.40,1-N.z);float3 land=lerp(g*float3(.55,.72,.43),s*float3(.65,.59,.48),slope);return lerp(s*float3(1.1,.99,.77),land,smoothstep(80,330,P.z));')
M.connect_material_expressions(pos,'',custom,'P');M.connect_material_expressions(normal,'',custom,'N')
for name,path in [('G',D+'/grass_07/T_grass_07_BaseColorTex'),('S',D+'/ground_tiles_17/T_ground_tiles_17_BaseColorTex')]:
 tex=expression(terrain,u.MaterialExpressionTextureObject,texture=u.load_asset(path));M.connect_material_expressions(tex,'',custom,name)
M.connect_material_property(custom,'',u.MaterialProperty.MP_BASE_COLOR);M.connect_material_property(constant(terrain,.92),'',u.MaterialProperty.MP_ROUGHNESS);save_mat(terrain)
materials={'V2TerrainCore':terrain,'V2TerrainRing':terrain,'V2Roads':u.load_asset(D+'/MI_Town_Road'),'V2Sidewalks':u.load_asset(D+'/MI_Town_Plaza'),'V2Curbs':u.load_asset(D+'/MI_Town_Curb')}
for name,mat in materials.items():
 dest=ENV+'/'+name
 if not LIB.does_directory_exist(dest):
  manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',False)
  assert manager.import_asset(dest,manager.create_source_data(str(O/'meshes'/(name+'.glb'))),params),name
 meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)];assert len(meshes)==1,(name,len(meshes));mesh=meshes[0]
 mesh.set_material(0,mat);body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);LIB.save_loaded_asset(mesh,False);mesh_actor(name,mesh,[0,0,0],mat=mat)
 bbox=mesh.get_bounding_box();report.setdefault('mesh_bounds_cm',{})[name]={'min':[bbox.min.x,bbox.min.y,bbox.min.z],'max':[bbox.max.x,bbox.max.y,bbox.max.z]}
water=T.create_asset('MI_V2_Water',ENV,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());M.set_material_instance_parent(water,u.load_asset(F+'/materials/MI_ENV_water'));LIB.save_loaded_asset(water,False)
plane=u.load_asset('/Engine/BasicShapes/Plane');mesh_actor('Sea',plane,[0,0,0],[10000,10000,1],mat=water,coll=False)
plaza=next(a for a in L['areas'] if a['kind']=='plaza');box('Plaza',[-22.5,10,plaza['base_z_m']],[29,20,.14],u.load_asset(D+'/MI_Town_Plaza'))
# Pack tint instances only, with original texture and material functions retained.
tintcache={}
def tint(c):
 for i in range(c.get_num_materials()):
  parent=c.get_material(i)
  if not parent or not parent.get_path_name().startswith(F):continue
  name=parent.get_name();lower=name.lower();col=(.86,.78,.62) if 'wall' in lower else ((.06,.20,.24) if 'wood' in lower else ((.58,.22,.14) if 'roof' in lower else None))
  if col is None:continue
  if name not in tintcache:
   mi=T.create_asset('MI_V2_'+name,'/Game/Selene/Environment/FabTints',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());M.set_material_instance_parent(mi,parent);params=[str(n) for n in M.get_vector_parameter_names(parent)];changed=[]
   for p in params:
    if any(s in p.lower() for s in ['color','colour','tint']):M.set_material_instance_vector_parameter_value(mi,p,u.LinearColor(*col,1));changed.append(p)
   M.update_material_instance(mi);LIB.save_loaded_asset(mi,False);tintcache[name]=mi;report['tints'][name]={'parameters':params,'changed':changed,'color':col}
  c.set_material(i,tintcache[name])
classes=[]
for i in range(1,15):
 path=F+f'/blueprints/buildings/BP_BLD_house_{i}';cls=LIB.load_blueprint_class(path);a=spawn(cls,'Probe'+str(i),[0,0,-1000]);o,e=a.get_actor_bounds(False);classes.append((cls,path,max(1,e.x*2),max(1,e.y*2),max(1,e.z*2)));A.destroy_actor(a)
report['pack_candidates']=[{'asset':p,'size_cm':[x,y,z]} for c,p,x,y,z in classes]
heroes={'clock-hall':'clock-hall','bakery':'shop-bakery-corner','tool-shop':'shop-tool-repair'}
for idx,lot in enumerate(L['lots']):
 if lot['area_m2']<25:continue
 pts=lot['footprint']['outer'][:-1];p,q=max(zip(pts,pts[1:]+pts[:1]),key=lambda t:math.dist(*t));angle=math.atan2(q[1]-p[1],q[0]-p[0]);c=math.cos(angle);s=math.sin(angle);us=[x*c+y*s for x,y in pts];vs=[-x*s+y*c for x,y in pts];w=max(us)-min(us);d=max(vs)-min(vs);uc=(max(us)+min(us))/2;vc=(max(vs)+min(vs))/2;cx=uc*c-vc*s;cy=uc*s+vc*c;yaw=90-math.degrees(angle);hero=lot.get('hero');name=hero or lot['id'].replace('/','_')
 if hero in heroes:
  slug=heroes[hero];path=f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}';mesh=u.load_asset(path);assert mesh,path;b=mesh.get_bounds();sx,sy=b.box_extent.x*2,b.box_extent.y*2;scale=min(w*100/sx,d*100/sy,1.6)*.92;a=mesh_actor('Hero_'+name,mesh,[cx,cy,lot['base_z_m']],scale,yaw)
 else:
  # Fit both footprint aspect and plausible size; preserve doors by limiting scale.
  cls,path,sx,sy,sz=min(classes,key=lambda t:abs(math.log((w/d)/(t[2]/t[3])))+abs(math.log(max(.1,min(w*100/t[2],d*100/t[3]))))*.5)
  scale=min(w*100/sx,d*100/sy,1.35)*.92;a=spawn(cls,('Cafe_' if hero else 'Lot_')+name,[cx,cy,lot['base_z_m']],yaw);a.set_actor_scale3d(u.Vector(scale,scale,scale))
  for comp in a.get_components_by_class(u.StaticMeshComponent):tint(comp)
 o,e=a.get_actor_bounds(False);target=vec([cx,cy,lot['base_z_m']]);loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x+target.x-o.x,loc.y+target.y-o.y,loc.z+target.z-(o.z-e.z)),False,False)
 report['placements'].append({'lot':lot['id'],'hero':hero,'asset':path,'scale':scale,'center_m':[cx,cy,lot['base_z_m']],'actor':a.get_actor_label()})
# Scripted deterministic furniture rhythm, kept clear of plaza centre.
def prop(name,path,p,size,yaw=0):
 mesh=u.load_asset(path);b=mesh.get_bounds();scale=size*100/max(b.box_extent.z*2,1);a=mesh_actor(name,mesh,p,scale,yaw,coll=False);o,e=a.get_actor_bounds(False);loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x,loc.y,loc.z+p[2]*100-(o.z-e.z)),False,False);report['scatter'][name.split('_')[0]]=report['scatter'].get(name.split('_')[0],0)+1
for i,(e,n) in enumerate([(-34,3),(-34,17),(-11,3),(-11,17)]):
 prop('Lamp_'+str(i),F+'/meshes/props/light/SM_PROP_streetlamp_v01_01',[e,n,6.34],3.6)
 prop('Planter_'+str(i),F+'/meshes/props/natural/SM_PROP_PLANT_pot_v2_01',[e+1.1,n,6.34],1.25)
for i,n in enumerate([5,14]):prop('Bench_'+str(i),F+'/meshes/props/furniture/SM_PROP_bench_01',[-35,n,6.34],.95,90)
# Height samples from prepared heightmap via raw R16, no third-party Python dependency.
import array
z=array.array('H');z.frombytes((R/'Design/TownV2/terrain/heightmap-ue.r16').read_bytes())
def h(e,n):return (z[round((e+590)/1500*1008)*1009+round((n+750)/1500*1008)]-32768)/128
# Roadside lamps and pots at 22 m spacing, avoiding plaza and building lots.
for ri,road in enumerate(L['streets']):
 if road['kind'] not in ['residential','tertiary','secondary','unclassified']:continue
 distance=0;next_d=12
 for p,q in zip(road['points'],road['points'][1:]):
  dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
  if length<.1:continue
  while next_d<=distance+length:
   t=(next_d-distance)/length;off=road['width_m']/2+1.;e=p[0]+dx*t-dy/length*off;n=p[1]+dy*t+dx/length*off
   if h(e,n)>1:prop(f'Roadlamp_{ri}_{int(next_d)}',F+'/meshes/props/light/SM_PROP_streetlamp_v01_01',[e,n,h(e,n)+.2],3.5)
   next_d+=22
  distance+=length
rng=random.Random(3106)
def inside(x,y,pts):
 yes=False
 for a,b in zip(pts,pts[1:]):
  if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes
for i in range(220):
 e=rng.uniform(-145,260);n=rng.uniform(-160,220);hh=h(e,n)
 if hh<2 or (-42<e<0 and -8<n<26) or any(inside(e,n,l['footprint']['outer']) for l in L['lots']):continue
 def distseg(p,q):
  dx=q[0]-p[0];dy=q[1]-p[1];t=max(0,min(1,((e-p[0])*dx+(n-p[1])*dy)/max(.001,dx*dx+dy*dy)));return math.hypot(e-p[0]-t*dx,n-p[1]-t*dy)
 if any(distseg(p,q)<road['width_m']/2+3 for road in L['streets'] for p,q in zip(road['points'],road['points'][1:])):continue
 prop('Tree_'+str(i),F+'/meshes/environment/SM_ENV_TREE_village_LOD0',[e,n,hh],rng.uniform(5,10),rng.uniform(0,360))
 if i%2==0:prop('Grass_'+str(i),F+'/meshes/environment/SM_ENV_PLANT_grass_village',[e+2,n,hh],.6)
spawn(u.PlayerStart,'PlayerStart',[-20,10,7.4])
tod=spawn(u.load_class(None,'/Script/Selene.SeleneTimeOfDay'),'TimeOfDay',[0,0,0]);tod.set_hour(15);tod.set_editor_property('paused',True)
sun=tod.get_editor_property('sun');sun.set_editor_property('use_temperature',True);sun.set_editor_property('temperature',5700.);sun.set_editor_property('light_source_angle',2.)
pp=tod.get_editor_property('post_process');settings=pp.get_editor_property('settings')
for k,v in {'override_bloom_intensity':True,'bloom_intensity':.18,'override_color_gain_shadows':True,'color_gain_shadows':u.Vector4(1.02,1.07,1.15,1),'override_color_gain_highlights':True,'color_gain_highlights':u.Vector4(1.04,1.01,.96,1)}.items():settings.set_editor_property(k,v)
pp.set_editor_property('settings',settings)
checkpoint('terrain_roads_sea_buildings_scatter_light_spawn_saved')
assert E.load_level('/Game/Selene/Maps/TownV2')
report['reload_actor_count']=len(A.get_all_level_actors());report['landscapes']=sum(isinstance(a,u.LandscapeProxy) for a in A.get_all_level_actors());report['status']='saved_and_reloaded';write()
