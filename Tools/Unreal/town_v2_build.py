"""UNEXECUTED DRAFT: populate only the saved TownV2 map using OSM lots and already-installed assets."""
import json,math,pathlib,traceback
import unreal as u
ROOT=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=ROOT/'Saved/TownV2/session-2'
L=json.loads((ROOT/'Design/TownV2/layout.json').read_text());A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.get_editor_subsystem(u.LevelEditorSubsystem)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
if world.get_name()!='TownV2':raise RuntimeError('Wrong world')
if any(a.get_actor_label().startswith('V2_') for a in A.get_all_level_actors()):raise RuntimeError('Refuse duplicate build')
land=[a for a in A.get_all_level_actors() if isinstance(a,u.LandscapeProxy)]
if not land:raise RuntimeError('Import and verify the Landscape before running this draft')
R={'status':'started','placements':[],'gaps':['Stylized Medieval City missing','No palms installed','No Tripo cafe mesh; cafe role uses FANTASTIC Village','PCG dressing not implemented in this bounded checkpoint']}
(OUT/'build.json').write_text(json.dumps(R,indent=2))
def vec(p):return u.Vector(p[1]*100,p[0]*100,p[2]*100)
def spawn(cls,label,p,rot=None):
 a=A.spawn_actor_from_class(cls,vec(p),rot or u.Rotator());a.set_actor_label('V2_'+label);a.set_folder_path('TownV2');return a
CUBE=u.load_asset('/Engine/BasicShapes/Cube')
def box(label,p,size,mat,angle=0):
 a=spawn(u.StaticMeshActor,label,p,u.Rotator(yaw=90-angle));a.static_mesh_component.set_static_mesh(CUBE);a.static_mesh_component.set_material(0,mat);a.set_actor_scale3d(u.Vector(*size));return a
T=u.AssetToolsHelpers.get_asset_tools();ML=u.MaterialEditingLibrary
DIR='/Game/Selene/Materials/Ground'
def solid(name,color,rough=.85):
 m=T.create_asset(name,DIR,u.Material,u.MaterialFactoryNew());c=ML.create_material_expression(m,u.MaterialExpressionConstant3Vector);c.set_editor_property('constant',u.LinearColor(*color,1));ML.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 r=ML.create_material_expression(m,u.MaterialExpressionConstant);r.set_editor_property('r',rough);ML.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS);ML.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m);return m
water=solid('M_V2_Sea',(.025,.17,.22),.23)
terrain=T.create_asset('M_V2_TerrainAuto',DIR,u.Material,u.MaterialFactoryNew());pos=ML.create_material_expression(terrain,u.MaterialExpressionWorldPosition);normal=ML.create_material_expression(terrain,u.MaterialExpressionVertexNormalWS);custom=ML.create_material_expression(terrain,u.MaterialExpressionCustom)
inputs=[]
for name in ['P','N']:
 x=u.CustomInput();x.set_editor_property('input_name',name);inputs.append(x)
custom.set_editor_property('inputs',inputs);custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3);custom.set_editor_property('code','float s=1-saturate(N.z); float v=.94+.06*sin(P.x*.006)*sin(P.y*.008); float3 c=lerp(float3(.09,.18,.065),float3(.22,.19,.14),smoothstep(.07,.30,s)); return lerp(c,float3(.50,.43,.28),1-smoothstep(100,350,P.z))*v;')
ML.connect_material_expressions(pos,'',custom,'P');ML.connect_material_expressions(normal,'',custom,'N');ML.connect_material_property(custom,'',u.MaterialProperty.MP_BASE_COLOR);ML.recompile_material(terrain);u.EditorAssetLibrary.save_loaded_asset(terrain)
land=[a for a in A.get_all_level_actors() if isinstance(a,u.LandscapeProxy)]
if not land:raise RuntimeError('Import the heightmap Landscape before building')
for a in land:a.set_editor_property('landscape_material',terrain)
road=u.load_asset(DIR+'/MI_Town_Road');pave=u.load_asset(DIR+'/MI_Town_Plaza');curb=u.load_asset(DIR+'/MI_Town_Curb')
box('Sea',[0,0,-.15],[5000,5000,.3],water)
plaza=next(a for a in L['areas'] if a['kind']=='plaza');box('Plaza',[-22.5,10,plaza['base_z_m']+.06],[29,20,.12],pave)
routecls=u.load_class(None,'/Script/Selene.SelenePerfRoute')
for i,r in enumerate(L['streets']):
 a=spawn(routecls,'RoadSpline_'+str(i),[0,0,0]);a.set_editor_property('route_name',u.Name('V2Road_'+str(i)));s=a.get_component_by_class(u.SplineComponent);s.clear_spline_points(False)
 for p in r['points']:s.add_spline_point(vec(p),u.SplineCoordinateSpace.WORLD,False)
 for j in range(len(r['points'])):s.set_spline_point_type(j,u.SplinePointType.LINEAR,False)
 s.update_spline();ped=r['kind'] in ['footway','path','steps','pedestrian'];width=r['width_m']
 for j,(p,q) in enumerate(zip(r['points'],r['points'][1:])):
  dx=q[0]-p[0];dy=q[1]-p[1];n=math.hypot(dx,dy)
  if n<.1:continue
  z=(p[2]+q[2])/2;ang=math.degrees(math.atan2(dy,dx));mid=[(p[0]+q[0])/2,(p[1]+q[1])/2,z+.05]
  actor=box(f'Road_{i}_{j}',mid,[n+.05,width,.10],pave if ped else road,ang)
  actor.set_actor_rotation(u.Rotator(pitch=math.degrees(math.atan2(q[2]-p[2],n)),yaw=90-ang),False)
  if not ped and r['kind'] not in ['service','steps']:
   for side in [-1,1]:
    off=(width/2+.7)*side;centre=[mid[0]-dy/n*off,mid[1]+dx/n*off,z+.10]
    actor=box(f'Sidewalk_{i}_{j}_{side}',centre,[n+.05,1.4,.20],pave,ang);actor.set_actor_rotation(u.Rotator(pitch=math.degrees(math.atan2(q[2]-p[2],n)),yaw=90-ang),False)
    off=(width/2+.12)*side;box(f'Curb_{i}_{j}_{side}',[mid[0]-dy/n*off,mid[1]+dx/n*off,z+.14],[n+.05,.24,.28],curb,ang)
# Audit and fit existing complete blueprint buildings, then use source lot long axes.
classes=[]
for i in range(1,15):
 path=f'/Game/Fantastic_Village_Pack/blueprints/buildings/BP_BLD_house_{i}'
 cls=u.EditorAssetLibrary.load_blueprint_class(path)
 if not cls:continue
 a=A.spawn_actor_from_class(cls,u.Vector(0,0,-100000));o,e=a.get_actor_bounds(False);classes.append((cls,path,max(1,e.x*2),max(1,e.y*2),max(1,e.z*2)));A.destroy_actor(a)
R['pack_candidates']=[{'asset':p,'size_cm':[x,y,z]} for c,p,x,y,z in classes]
heroes={'clock-hall':'clock-hall','bakery':'shop-bakery-corner','tool-shop':'shop-tool-repair'}
for lot in L['lots']:
 if lot['area_m2']<25:continue
 points=lot['footprint']['outer'][:-1];cx=sum(p[0] for p in points)/len(points);cy=sum(p[1] for p in points)/len(points)
 p,q=max(zip(points,points[1:]+points[:1]),key=lambda t:math.dist(*t));ang=math.degrees(math.atan2(q[1]-p[1],q[0]-p[0]));c=math.cos(math.radians(ang));s=math.sin(math.radians(ang));us=[x*c+y*s for x,y in points];vs=[-x*s+y*c for x,y in points];w=max(us)-min(us);d=max(vs)-min(vs)
 label=lot['id'].replace('/','_');hero=lot.get('hero')
 if hero in heroes:
  slug=heroes[hero];path=f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}';mesh=u.load_asset(path);a=spawn(u.StaticMeshActor,'Hero_'+hero,[cx,cy,lot['base_z_m']]);a.static_mesh_component.set_static_mesh(mesh);bounds=mesh.get_bounds();sx,sy,sz=bounds.box_extent.x*2,bounds.box_extent.y*2,bounds.box_extent.z*2
  scale=min(w*100/sx,d*100/sy,1.6);a.set_actor_scale3d(u.Vector(scale,scale,scale));a.set_actor_rotation(u.Rotator(yaw=90-ang),False)
 else:
  cls,path,sx,sy,sz=min(classes,key=lambda t:abs(math.log((w/d)/(t[2]/t[3])))+abs(math.log(max(.1,min(w*100/t[2],d*100/t[3]))))*.2)
  a=spawn(cls,('Cafe_' if hero=='cafe' else 'Lot_')+label,[cx,cy,lot['base_z_m']],u.Rotator(yaw=90-ang));scale=min(w*100/sx,d*100/sy,1.6)*.90;a.set_actor_scale3d(u.Vector(scale,scale,scale))
 o,e=a.get_actor_bounds(False);target=vec([cx,cy,lot['base_z_m']]);loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x+target.x-o.x,loc.y+target.y-o.y,loc.z+target.z-(o.z-e.z)),False,False)
 R['placements'].append({'lot':lot['id'],'hero':hero,'asset':path,'scale':scale,'actor':a.get_actor_label()})
spawn(u.PlayerStart,'PlayerStart',[*L['player_spawn']['point'][:2],L['player_spawn']['point'][2]+1])
todcls=u.load_class(None,'/Script/Selene.SeleneTimeOfDay');tod=spawn(todcls,'TimeOfDay',[0,0,0]);tod.set_hour(15)
# Keep the established Selene light system; add no movement or config changes.
E.save_current_level();u.EditorAssetLibrary.save_directory(DIR,only_if_is_dirty=True,recursive=True)
R.update(status='saved',landscape_count=len(land),road_splines=len(L['streets']),actor_count=len(A.get_all_level_actors()))
(OUT/'build.json').write_text(json.dumps(R,indent=2))
