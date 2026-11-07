"""Session-one presentation pass. Only Town, Ground and new Environment packages.
One-shot builder: restore the map checkpoint before reapplying. Existing source meshes are read-only.
"""
import json,math,sys,traceback
from pathlib import Path
import unreal as u
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Tools/Unreal'))
from dress_route import resolve,bounds,rotate_xy
sys.path.insert(0,str(ROOT/'Tools/Blockout'))
from layout_core import height
from validate_dressing import path_distance,polygon
OUT=ROOT/'Saved/Town/session-1'
TAG='SeleneTownSession1'; GROUND='/Game/Selene/Materials/Ground'; ENV='/Game/Selene/Environment'
MEL=u.MaterialEditingLibrary; LIB=u.EditorAssetLibrary; TOOLS=u.AssetToolsHelpers.get_asset_tools()
ACT=u.get_editor_subsystem(u.EditorActorSubsystem); LEVEL=u.get_editor_subsystem(u.LevelEditorSubsystem)
REPORT={'status':'started','actors':[],'materials':{},'warnings':[]}
LAYOUT=json.loads((ROOT/'Design/Blockout/layout.json').read_text())
R1=next(r['points'] for r in LAYOUT['routes'] if r['id']=='R1')

def vec(p): return u.Vector(p[1]*100,p[0]*100,p[2]*100)
def asset(name,cls,factory,base=GROUND):
 p=base+'/'+name
 return u.load_asset(p) if LIB.does_asset_exist(p) else TOOLS.create_asset(name,base,cls,factory)
def mi(name,source,tint,tile=3,normal=.16):
 p=GROUND+'/'+name
 m=u.load_asset(p) if LIB.does_asset_exist(p) else LIB.duplicate_asset(source,p)
 m.modify()
 for k,v in dict(TileSizeMetres=tile,Saturation=.3,NormalStrength=normal,RoughnessScale=1.1,MacroStrength=.045,MacroSizeMetres=15).items(): MEL.set_material_instance_scalar_parameter_value(m,k,v)
 MEL.set_material_instance_vector_parameter_value(m,'Tint',u.LinearColor(*tint,1))
 MEL.update_material_instance(m);LIB.save_loaded_asset(m,False)
 REPORT['materials'][name]={'source':source,'tint':tint,'tile_m':tile,'normal':normal}
 return m

def solid(name,color,rough=.8,decal=False):
 m=asset(name,u.Material,u.MaterialFactoryNew())
 MEL.delete_all_material_expressions(m)
 if decal:
  m.set_editor_property('material_domain',u.MaterialDomain.MD_DEFERRED_DECAL)
  m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
 c=MEL.create_material_expression(m,u.MaterialExpressionConstant3Vector);c.set_editor_property('constant',u.LinearColor(*color,1));MEL.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
 r=MEL.create_material_expression(m,u.MaterialExpressionConstant);r.set_editor_property('r',rough);MEL.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
 if decal:
  uv=MEL.create_material_expression(m,u.MaterialExpressionTextureCoordinate)
  custom=MEL.create_material_expression(m,u.MaterialExpressionCustom);custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT1)
  inp=u.CustomInput();inp.set_editor_property('input_name','UV');custom.set_editor_property('inputs',[inp])
  custom.set_editor_property('code','float2 d=abs(UV-0.5)*2; return (1-smoothstep(0.55,1,max(d.x,d.y)))*0.23;')
  MEL.connect_material_expressions(uv,'',custom,'UV');MEL.connect_material_property(custom,'',u.MaterialProperty.MP_OPACITY)
 MEL.recompile_material(m);LIB.save_loaded_asset(m,False);return m

def spawn(name,mesh,p,scale=(1,1,1),yaw=0,material=None,collision=False,group='details'):
 a=ACT.spawn_actor_from_class(u.StaticMeshActor,vec(p),u.Rotator(yaw=yaw))
 a.set_actor_label('Town1_'+name);a.tags=[u.Name(TAG)];a.set_folder_path('TownQuality/'+group)
 c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(u.ComponentMobility.STATIC)
 if 'LeafCards' in mesh.get_name() or 'DisplayGlass' in mesh.get_name():c.set_editor_property('disallow_nanite',True)
 c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
 c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if collision else u.CollisionEnabled.NO_COLLISION)
 a.set_actor_scale3d(u.Vector(*scale))
 if material:
  for i in range(c.get_num_materials()):c.set_material(i,material)
 REPORT['actors'].append({'label':a.get_actor_label(),'group':group,'position':p,'collision':collision})
 return a

def box(name,p,size,material,yaw=90,collision=False,group='ground'):
 return spawn(name,CUBE,p,size,yaw,material,collision,group)

def strip(name,a,b,width,top,mat,thick=.12,collision=True,mesh=None):
 dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);yaw=90-math.degrees(math.atan2(dy,dx))
 if mesh:
  actor=spawn(name,mesh,[(a[0]+b[0])/2,(a[1]+b[1])/2,top-.18],(length/2,1,1),yaw,mat,collision,'curbs')
 else: actor=box(name,[(a[0]+b[0])/2,(a[1]+b[1])/2,top-thick/2],[length,width,thick],mat,yaw,collision)
 return actor

CACHE={}
def prop(name,key,p,yaw=90,scale=1,group='dressing'):
 if key not in CACHE:CACHE[key]=resolve('/Game/Assets/'+key)
 meshes=CACHE[key]
 if not meshes:raise RuntimeError('Missing existing asset '+key)
 lo,hi=bounds(meshes);cx,cy=(lo[0]+hi[0])*scale/2,(lo[1]+hi[1])*scale/2
 rx,ry=rotate_xy(cx,cy,yaw)
 pos=[p[0]-ry/100,p[1]-rx/100,p[2]-lo[2]*scale/100]
 for i,m in enumerate(meshes):spawn(name+'_'+str(i),m,pos,(scale,)*3,yaw,group=group)

def import_kit(name):
 dest=ENV+'/Kit/'+name
 if not LIB.does_directory_exist(dest):
  manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters()
  params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',False)
  if not manager.import_asset(dest,manager.create_source_data(str(OUT/'kit'/(name+'.glb'))),params):raise RuntimeError('Kit import failed '+name)
 meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)]
 if len(meshes)!=1:raise RuntimeError('Kit mesh count '+name)
 m=meshes[0]
 bbox=m.get_bounding_box();REPORT.setdefault('kit_bounds_cm',{})[name]={'min':[bbox.min.x,bbox.min.y,bbox.min.z],'max':[bbox.max.x,bbox.max.y,bbox.max.z]}
 body=m.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 LIB.save_loaded_asset(m,False)
 return m

def main():
 global CUBE
 assert (OUT/'backup/manifest.json').is_file(),'Map backup required'
 assert (OUT/'before/10_aerial.png').is_file(),'Complete before capture required'
 if not LEVEL.load_level('/Game/Selene/Maps/Town'):raise RuntimeError('Town load failed')
 if any(a.actor_has_tag(TAG) for a in ACT.get_all_level_actors()):
  raise RuntimeError('Town session actors already exist. Use an in-place edit; commandlet OFPA deletion is not persistent.')
 CUBE=u.load_asset('/Engine/BasicShapes/Cube');sphere=u.load_asset('/Engine/BasicShapes/Sphere')
 curb=import_kit('SM_TownCurb');wall=import_kit('SM_TownRetainingWall')
 source=GROUND+'/MI_Ground_ground_tiles_27'
 plaza=mi('MI_Town_Plaza',source,[1.0,.98,.91],3,.13)
 road=mi('MI_Town_Road',source,[.67,.71,.72],2.4,.12)
 sidewalk=mi('MI_Town_Sidewalk',source,[.88,.87,.80],3,.13)
 edging=mi('MI_Town_Curb',source,[1.06,1.03,.94],3,.08)
 gutter=mi('MI_Town_Gutter',source,[.40,.43,.43],2.4,.08)
 soil=solid('M_Town_Soil',[.12,.10,.065]);coral=solid('M_Town_Coral',[.50,.18,.12]);petrol=solid('M_Town_Petrol',[.035,.12,.15]);cream=solid('M_Town_Cream',[.70,.65,.50]);grime=solid('M_Town_Grime',[.09,.07,.045],decal=True)
 grass=mi('MI_Town_Grass',GROUND+'/MI_Ground_grass_07',[.83,.93,.72],3,.1)
 # Soil shoulder fades around the plaza and cafe pad in world-space metres.
 import build_ground_materials as ground_builder
 ground_builder.SHADER=ground_builder.SHADER.replace('return saturate(color);',r"""
float2 q=P.yx/100.0;
float2 d=abs(q)-float2(37.5,30);
float plazaDistance=length(max(d,0))+min(max(d.x,d.y),0);
float2 c=abs(q-float2(-45,-20))-float2(8,3.5);
float cafeDistance=length(max(c,0))+min(max(c.x,c.y),0);
float edge=min(abs(plazaDistance),abs(cafeDistance));
float shoulder=1-smoothstep(0.0,2.2,edge);
color=lerp(color,float3(0.14,0.12,0.075)*(0.93+variation*0.08),shoulder*0.8);
return saturate(color);
""")
 tex={str(v.parameter_info.name):v.parameter_value for v in grass.get_editor_property('texture_parameter_values')}
 parent=ground_builder.build_parent(GROUND+'/TownTerrain',tex)
 MEL.set_material_instance_parent(grass,parent);MEL.update_material_instance(grass);LIB.save_loaded_asset(grass,False)
 # Reuse one paving texture family across every street and slab.
 labels={a.get_actor_label():a for a in ACT.get_all_level_actors()}
 for s in LAYOUT['streets']:
  for i in range(len(s['points'])-1):
   a=labels[s['id']+'_'+str(i)];a.modify();a.static_mesh_component.modify();a.static_mesh_component.set_material(0,road)
 for s in LAYOUT['slabs']:
  a=labels[s['id']];a.modify();a.static_mesh_component.modify();a.static_mesh_component.set_material(0,grass if s['kind']=='garden' else plaza)
 terrain=labels['SeleneTerrain'];terrain.modify();terrain.static_mesh_component.modify();terrain.static_mesh_component.set_material(0,grass)
 # Main-street sidewalks, bevelled curbs, drainage strips; keep bends open.
 main=next(s for s in LAYOUT['streets'] if s['id']=='main_street')
 for i,(a,b) in enumerate(zip(main['points'],main['points'][1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length;ux,uy=dx/length,dy/length
  for side in (-1,1):
   def off(p,d,t):return [p[0]+nx*d+ux*t,p[1]+ny*d+uy*t]
   # 60cm joints are intentional flush pedestrian access at the bends.
   aa,bb=off(a,side*7.15,.3),off(b,side*7.15,-.3)
   strip(f'curb_{i}_{side}',aa,bb,.32,.18,edging,mesh=curb)
   strip(f'gutter_{i}_{side}',off(a,side*6.8,.3),off(b,side*6.8,-.3),.35,.033,gutter,.02,False)
   strip(f'walk_{i}_{side}',off(a,side*8.25,.3),off(b,side*8.25,-.3),1.9,.15,sidewalk,.15)
   if i<4:
    for t in (.3,.7):
     p=[a[0]+t*dx+nx*side*9.3,a[1]+t*dy+ny*side*9.3,0]
     prop(f'street_pot_{i}_{side}_{t}','potted-plant-r2',p,90,1.1)
  # A restrained, soft-edged road wear decal near the gutter.
  p=[(a[0]+b[0])/2+nx*5.8,(a[1]+b[1])/2+ny*5.8,.08]
  dec=ACT.spawn_actor_from_class(u.DecalActor,vec(p),u.Rotator(pitch=-90,yaw=90-math.degrees(math.atan2(dy,dx))))
  dec.tags=[u.Name(TAG)];dec.set_actor_label('Town1_road_wear_'+str(i));dec.set_folder_path('TownQuality/decals')
  dec.decal.set_decal_material(grime);dec.decal.set_editor_property('decal_size',u.Vector(25,55,420))
 # Plaza curb sections avoid the R1 crossings and cafe entrance.
 edges=[((-16,-30),(37.5,-30)),((37.5,-30),(37.5,21)),((-37.5,3),(-37.5,27)),((-37.5,-22),(-37.5,-10)),((-34,30),(-5,30)),((5,30),(31,30))]
 for i,(a,b) in enumerate(edges):strip('plaza_curb_'+str(i),a,b,.32,.18,edging,mesh=curb)
 # Flush cream stepping bands / shared street crossing at the plaza connector.
 for i in range(7):box('crossing_'+str(i),[-30,-34+i*.72,.042],[4.6,.34,.015],edging,90,False)
 # Planting beds soften pad corners, occupying only unused plaza edges.
 beds=[(-30,23,10,3),(15,24,14,3),(32,5,3,18),(-9,-27,11,2),(24,-27,12,2)]
 for i,(x,y,w,d) in enumerate(beds):
  box('soil_bed_'+str(i),[x,y,.045],[w,d,.06],soil)
  for j in range(max(3,int(w if w>d else d))):
   t=(j+.5)/max(3,int(w if w>d else d))-.5
   p=[x+t*(w-1) if w>d else x,y if w>d else y+t*(d-1),.08]
   prop(f'flower_{i}_{j}','hydrangea-clump-r2',p,j*47,.8)
 # Hand-placed tree and seating compositions, framed around route sightlines.
 trees=[(-31,23),(-8,23),(14,23),(32,16),(32,-6),(23,-26),(6,-26),(-32,8)]
 for i,(x,y) in enumerate(trees):
  box('tree_soil_'+str(i),[x,y,.035],[2.3,2.3,.04],soil)
  prop('tree_'+str(i),'street-tree',[x,y,0],i*51,1.15)
 for i,(x,y,yaw) in enumerate([(-26,19,180),(10,19,180),(29,9,270),(29,-12,270),(15,-23,0),(-11,18,180)]):
  prop('bench_'+str(i),'plaza-bench',[x,y,.03],yaw,1)
  prop('bin_'+str(i),'trash-bin-r2',[x+1.8,y,.03],yaw,1)
 for i,p in enumerate([[-36,-15,0],[-36,-8,0],[-41,-13,0],[-51,-15,0],[-39,-15,0]]):
  prop('planter_'+str(i),'concrete-planter',p,90,1)
  prop('planter_flower_'+str(i),'hydrangea-clump-r2',[p[0],p[1],.51],i*37,1.1)
 prop('scooter','delivery-scooter',[-34,-35,0],-25,1)
 # Reuse wall lanterns on narrow petrol posts instead of inventing unavailable lamp assets.
 for i,(x,y) in enumerate([(-27,21),(20,21),(30,-15),(-34,-14),(-49,-15)]):
  box('lamp_post_'+str(i),[x,y,1.65],[.09,.09,3.3],petrol,group='furniture')
  prop('lamp_head_'+str(i),'wall-lantern-r2',[x,y,2.9],90,1.6)
 # Remove diagnostic grid from the existing cafe shell, retaining window transparency.
 for label,a in labels.items():
  if label.startswith('cafe_') and a.actor_has_tag('SeleneBlockout') and 'glass' not in label and label != 'cafe_terrace':
   a.modify();a.static_mesh_component.modify();a.static_mesh_component.set_material(0,plaza if label=='cafe_floor' else coral if 'counter' in label or 'canopy' in label else cream)
 for label in ('cafe_vending','cafe_vending_glass'):
  if label in labels:
   a=labels[label];a.modify();rot=a.get_actor_rotation();rot.yaw=270;a.set_actor_rotation(rot,False)
 for wi,cx in enumerate((-49.8,-40.2)):
  for z in (.7,3.5):box(f'window_horizontal_{wi}_{z}',[cx,-23.84,z],[3.3,.10,.09],petrol,group='facade')
  for x in (cx-1.6,cx,cx+1.6):box(f'window_vertical_{wi}_{x}',[x,-23.84,2.1],[.075,.10,2.8],petrol,group='facade')
 for z in (.7,3.5):box('east_window_'+str(z),[-37.84,-30,z],[.10,8,.09],petrol,group='facade')
 # Cafe frontage: coral sunshade, ivory fascia and readable original sign, door stays clear.
 box('cafe_awning',[-45,-23.1,3.25],[13.4,1.7,.13],coral,group='facade')
 box('cafe_fascia',[-45,-22.26,3.10],[13.4,.10,.30],coral,group='facade')
 box('cafe_sign_back',[-45,-23.83,4.05],[4.8,.10,.55],petrol,group='facade')
 sign=ACT.spawn_actor_from_class(u.TextRenderActor,vec([-45,-23.72,4.0]),u.Rotator())
 sign.tags=[u.Name(TAG)];sign.set_actor_label('Town1_CafeSign');sign.set_folder_path('TownQuality/facade')
 sign.text_render.set_text('CAFÉ  SELENE');sign.text_render.set_world_size(35);sign.text_render.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
 # Articulate first hillside retaining edge and keep the existing stair treads/grades.
 for i in range(24):spawn('retaining_'+str(i),wall,[44+i*4.5,66.25,4.8],(2.25,1,3.2),90,sidewalk,True,'terrain')
 for a in labels.values():
  if a.get_actor_label().startswith('hill_stair_'):
   a.modify();a.static_mesh_component.modify();a.static_mesh_component.set_material(0,sidewalk)
 # Continuous Blender terrain skirt, replacing rejected separate sphere mounds.
 earth=import_kit('SM_TownEarthSkirt')
 spawn('earth_skirt',earth,[0,0,0],(1,1,1),0,grass,False,'backdrop')
 for i,p in enumerate([(-48,-31,3.5),(-41,-29,3.5)]):
  light=ACT.spawn_actor_from_class(u.PointLight,vec(p),u.Rotator())
  light.tags=[u.Name(TAG)];light.set_actor_label('Town1_cafe_practical_'+str(i));light.set_folder_path('TownQuality/lighting')
  c=light.point_light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_editor_property('intensity_units',u.LightUnits.CANDELAS);c.set_intensity(900);c.set_light_color(u.LinearColor(1,.76,.48,1));c.set_attenuation_radius(650)
 # Use the existing day/night controller, keeping its animation and curves intact.
 tod=next(a for a in ACT.get_all_level_actors() if a.get_class().get_name()=='SeleneTimeOfDay')
 tod.modify();tod.set_hour(12)
 sun=tod.get_editor_property('sun');sun.modify();sun.set_editor_property('use_temperature',True);sun.set_editor_property('temperature',5700.);sun.set_editor_property('light_source_angle',2.)
 sky=tod.get_editor_property('sky_light');sky.modify();sky.set_editor_property('lower_hemisphere_color',u.LinearColor(.09,.13,.20,1));sky.set_light_color(u.LinearColor(.88,.94,1,1))
 pp=tod.get_editor_property('post_process');pp.modify();settings=pp.get_editor_property('settings')
 for k,v in {'override_bloom_intensity':True,'bloom_intensity':.18,'override_color_gain_shadows':True,'color_gain_shadows':u.Vector4(1.06,1.10,1.18,1),'override_color_gain_highlights':True,'color_gain_highlights':u.Vector4(1.06,1.02,.96,1),'override_auto_exposure_speed_up':True,'auto_exposure_speed_up':3.,'override_auto_exposure_speed_down':True,'auto_exposure_speed_down':3.}.items():settings.set_editor_property(k,v)
 pp.set_editor_property('settings',settings)
 REPORT['lighting']='Existing noon warm key; cooler lifted shadow grade; bloom 0.18; existing day/night curves retained'
 if not LEVEL.save_current_level():raise RuntimeError('Map save failed')
 LIB.save_directory(ENV,True,True);LIB.save_directory(GROUND,True,True)
 if not u.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('External actor save failed')
 expected=len([a for a in ACT.get_all_level_actors() if a.actor_has_tag(TAG)])
 if not LEVEL.load_level('/Game/Selene/Maps/Town'):raise RuntimeError('Reload failed')
 actual=len([a for a in ACT.get_all_level_actors() if a.actor_has_tag(TAG)])
 REPORT.update(expected_actor_count=expected,reloaded_actor_count=actual)
 if expected!=actual:raise RuntimeError('Saved actor count mismatch')
 REPORT.update(status='success',saved_reload_actor_count=actual)

try:main()
except Exception as e:
 REPORT.update(status='failed',error=str(e),traceback=traceback.format_exc());raise
finally:(OUT/'build.json').write_text(json.dumps(REPORT,indent=2)+'\n')
