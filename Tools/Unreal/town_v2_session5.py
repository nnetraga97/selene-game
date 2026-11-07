"""Targeted Session 5 in-place frontage edits. Receipt and actor guards prohibit replay."""
import unreal as u,json,pathlib,math,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-5';E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);LIB=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;T=u.AssetToolsHelpers.get_asset_tools();D='/Game/Selene/Materials/Ground';ENV='/Game/Selene/Environment/TownV2/Session5';design=json.loads((R/'Design/TownV2/session-5-design.json').read_text());old=json.loads((R/'Saved/TownV2/session-4/apply.json').read_text())['placements']
assert (O/'backup-manifest.json').exists();assert json.loads((O/'before/capture.json').read_text())['status']=='success';assert not (O/'apply.json').exists(),'Do not replay'
assert E.load_level('/Game/Selene/Maps/TownV2');actors=A.get_all_level_actors();by={a.get_actor_label():a for a in actors};assert not any(k.startswith('V5_') for k in by),'Already mutated; reconcile before doing anything'
rep={'status':'applying','moved':[],'added':[],'detail':[],'gardens':design['gardens'],'props':[]};z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):
 x=max(0,min(1007.999,(e+590)/1500*1008));y=max(0,min(1007.999,(n+750)/1500*1008));i=int(x);j=int(y);a=x-i;b=y-j
 return z[i*1009+j]*(1-a)*(1-b)+z[(i+1)*1009+j]*a*(1-b)+z[i*1009+j+1]*(1-a)*b+z[(i+1)*1009+j+1]*a*b
def vec(e,n,z):return u.Vector(n*100,e*100,z*100)
def spawn(label,mesh,e,n,z,scale,yaw=0,mat=None,coll=True):
 a=A.spawn_actor_from_class(u.StaticMeshActor,vec(e,n,z),u.Rotator(yaw=yaw));a.set_actor_label('V5_'+label);a.set_folder_path('TownV2/Session5');a.tags=[u.Name('TownV2Session5')];c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll' if coll else 'NoCollision');a.set_actor_scale3d(u.Vector(*scale) if isinstance(scale,(list,tuple)) else u.Vector(scale,scale,scale))
 if mat:c.set_material(0,mat)
 return a
cube=u.load_asset('/Engine/BasicShapes/Cube');cream=u.load_asset(D+'/M_Town_Cream');petrol=u.load_asset(D+'/M_Town_Petrol');curb=u.load_asset(D+'/MI_Town_Gutter');paving=u.load_asset(D+'/MI_V4_Paving');coral=u.load_asset(D+'/M_Town_Coral');grass=u.load_asset(D+'/MI_Town_Grass');soil=u.load_asset(D+'/M_Town_Soil')
def box(label,e,n,z,size,mat,yaw=90,coll=True):return spawn(label,cube,e,n,z,size,yaw,mat,coll)
def center(a,e,n,base):
 origin,ext=a.get_actor_bounds(False);p=a.get_actor_location();a.set_actor_location(u.Vector(p.x+n*100-origin.x,p.y+e*100-origin.y,p.z+base*100-(origin.z-ext.z)),False,False)
def dimensions(a):
 b=a.static_mesh_component.static_mesh.get_bounding_box();s=a.get_actor_scale3d().x;return ((b.max.x-b.min.x)*s/100,(b.max.y-b.min.y)*s/100,(b.max.z-b.min.z)*s/100)
def point(e,n,yaw,x,y):
 a=math.radians(yaw);return e+x*math.sin(a)+y*math.cos(a),n+x*math.cos(a)-y*math.sin(a)
cache={}
def prop(label,slug,e,n,height,yaw=0,zz=None):
 if slug not in cache:cache[slug]=[u.load_asset(p) for p in LIB.list_assets('/Game/Assets/'+slug,True) if isinstance(u.load_asset(p),u.StaticMesh)]
 parts=cache[slug];assert parts,slug;bounds=[m.get_bounding_box() for m in parts];lo=min(b.min.z for b in bounds);hi=max(b.max.z for b in bounds);cx=(min(b.min.x for b in bounds)+max(b.max.x for b in bounds))/2;cy=(min(b.min.y for b in bounds)+max(b.max.y for b in bounds))/2;s=height*100/(hi-lo);a=math.radians(yaw);rx=(cx*math.cos(a)-cy*math.sin(a))*s;ry=(cx*math.sin(a)+cy*math.cos(a))*s;zz=h(e,n)+.28 if zz is None else zz
 for i,m in enumerate(parts):
  actor=spawn(label+'_'+str(i),m,e-ry/100,n-rx/100,zz-lo*s/100,s,yaw,coll=False)
  if 'LeafCards' in m.get_name():actor.static_mesh_component.set_editor_property('disallow_nanite',True)
 rep['props'].append({'label':label,'asset':slug,'center_m':[e,n,zz],'height_m':height})
def detail(a,e,n,base,slug,key,yaw):
 w,d,height=dimensions(a);box(key+'_Skirt',e,n,base-.17,[w*.99,d*.99,.40],curb,yaw)
 # Bakery's primary rounded entrance is on local +X; other frontages use +Y.
 frontyaw=yaw-90 if slug=='shop-bakery-corner' else yaw;fw,depth=(d,w) if slug=='shop-bakery-corner' else (w,d)
 fe,fn=point(e,n,frontyaw,0,depth/2);ground=h(fe,fn)+.19;rise=max(.18,base-ground+.12);steps=max(1,min(6,math.ceil(rise/.16)))
 for i in range(steps):
  pe,pn=point(e,n,frontyaw,0,depth/2+(steps-i)*.30);top=ground+rise*(i+1)/steps;box(key+'_Step_'+str(i),pe,pn,ground+(top-ground)/2,[min(3.2,fw*.38),.75,top-ground],paving,frontyaw)
 pe,pn=point(e,n,frontyaw,0,depth/2+.06);box(key+'_Threshold',pe,pn,base+.10,[2.1,.42,.08],petrol,frontyaw)
 pe,pn=point(e,n,frontyaw,0,depth/2+.65);box(key+'_Mat',pe,pn,ground+.025,[1.7,.65,.03],petrol,frontyaw,False)
 for j,side in enumerate([-1,1]):
  pe,pn=point(e,n,frontyaw,side*min(fw*.35,4),depth/2+.4);prop(key+'_DoorPot_'+str(j),'concrete-planter',pe,pn,.58,frontyaw);prop(key+'_DoorFlowers_'+str(j),'hydrangea-clump-r2',pe,pn,.75,frontyaw,zz=h(pe,pn)+.86)
 rep['detail'].append({'actor':a.get_actor_label(),'building':slug,'height_m':height,'uniform_scale':a.get_actor_scale3d().x,'front_yaw':frontyaw,'steps':steps,'rise_m':rise})
for x in design['moves']:
 a=by[x['actor']];e,n=x['new_center_m'];yaw=x['new_yaw'];base=h(e,n)+.26;a.set_actor_rotation(u.Rotator(yaw=yaw),False);a.set_actor_scale3d(u.Vector(x['new_scale'],x['new_scale'],x['new_scale']));center(a,e,n,base);foundation=by['V4_Foundation_'+str(x['index'])];w,d,hh=dimensions(a);foundation.set_actor_location(vec(e,n,base-.20),False,False);foundation.set_actor_rotation(u.Rotator(yaw=yaw),False);foundation.set_actor_scale3d(u.Vector(w*.99,d*.99,.42));foundation.static_mesh_component.set_material(0,curb)
 x.update(after_base_m=base,after_height_m=hh,relative_scale_factor=x['new_scale']/x['scale']);rep['moved'].append(x);detail(a,e,n,base,x['building'],'Front_'+str(x['index']),yaw)
# Cafe sign/canopy/counter move with the saved shell; terrace seats are regrouped off the carriageway.
c=next(x for x in rep['moved'] if x['index']==23);ce,cn=c['new_center_m'];oldce,oldcn,oldbase=c['center_m'];dz=c['after_base_m']-oldbase;delta=vec(ce-oldce,cn-oldcn,dz)
for label,a in by.items():
 if label.startswith('V4_Cafe'):
  a.set_actor_location(a.get_actor_location()+delta,False,False)
  if label.startswith(('V4_CafeTerraceBed','V4_CafeTerraceFlower')):A.destroy_actor(a)
def move_group(prefix,oldcenter,newcenter):
 delta=vec(newcenter[0]-oldcenter[0],newcenter[1]-oldcenter[1],h(*newcenter)-h(*oldcenter))
 for label,a in by.items():
  if label.startswith(prefix):a.set_actor_location(a.get_actor_location()+delta,False,False)
front=cn-c['building_dimensions_m'][1]/2
for i,(de,dn) in enumerate([(-4,-5),(0,-5),(4,-5),(-4,-9),(0,-9),(4,-9)]):
 oldp=(ce+de,front+dn);newp=(ce+de,front-2.2) if i<3 else (ce+7.25,front+1.0+(i-3)*3.0)
 move_group('V4_CafeTable_'+str(i)+'_',oldp,newp);move_group('V4_CafeChair_'+str(i)+'_',oldp,newp)
for i,de in enumerate([-6.5,6.5]):move_group('V4_CafePlanter_'+str(i)+'_',(ce+de,front-4),(ce+de,front-1.2));move_group('V4_CafeFlowers_'+str(i)+'_',(ce+de,front-4),(ce+de,front-1.2))
# New copies use their own material instances, never editing source assets.
colors={'ivory':(1,1,1),'cream':(1,.96,.87),'sand':(.92,.87,.76),'coral':(1,.86,.79)}
for x in design['additions']:
 slug=x['building'];mesh=u.load_asset('/Game/Assets/'+slug+'/'+slug+'/StaticMeshes/'+slug);assert mesh; e,n=x['center_m'];base=h(e,n)+.26;a=spawn(x['label'],mesh,e,n,base,x['scale'],x['yaw']);center(a,e,n,base)
 for slot in range(a.static_mesh_component.get_num_materials()):
  name='MI_V5_'+x['label']+'_'+str(slot);mat=T.create_asset(name,ENV,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew());M.set_material_instance_parent(mat,mesh.get_material(slot));M.set_material_instance_vector_parameter_value(mat,'BaseColorFactor',u.LinearColor(*colors[x['palette']],1));M.update_material_instance(mat);LIB.save_loaded_asset(mat,False);a.static_mesh_component.set_material(slot,mat)
 x.update(actor=a.get_actor_label(),base_m=base,height_m=dimensions(a)[2]);rep['added'].append(x);detail(a,e,n,base,slug,x['label'],x['yaw'])
# Finish the unchanged bakery closest to camera 03 as well.
b=old[8];detail(by[b['actor']],*b['center_m'],b['building'],'Bakery',b['yaw'])
# Four planted courts replace visible empty paving with terrain-conforming green surfaces and capped boundaries.
for name,mat in [('V5Gardens',grass),('V5GardenWalls',cream),('V5GardenCaps',curb)]:
 dest=ENV+'/'+name;manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters();params.set_editor_property('is_automated',True);params.set_editor_property('replace_existing',False);assert manager.import_asset(dest,manager.create_source_data(str(O/'meshes'/(name+'.glb'))),params);meshes=[u.load_asset(p) for p in LIB.list_assets(dest,True) if isinstance(u.load_asset(p),u.StaticMesh)];assert len(meshes)==1;m=meshes[0];m.set_material(0,mat);m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);LIB.save_loaded_asset(m,False);spawn(name,m,0,0,0,1,mat=mat)
for i,g in enumerate(design['gardens']):
 x0,y0,x1,y1=g['rect']
 for j,(e,n) in enumerate([(x0+4,y0+5),(x1-4,y1-4),(x0+5,y1-4)]):
  prop('GardenTree_'+str(i)+'_'+str(j),'street-tree',e,n,5.5 if j!=1 else 6.5,zz=h(e,n)+.28)
  prop('GardenShrub_'+str(i)+'_'+str(j),'hydrangea-clump-r2',e+1.4,n-.7,1.1,zz=h(e+1.4,n-.7)+.29)
 # Paved entry with dark slatted garden gate and cream piers.
 if g['gate']=='south':ge=(x0+x1)/2;gn=y0;yaw=90
 else:ge=x0;gn=(y0+y1)/2;yaw=180
 for j,s in enumerate([-1,1]):
  pe,pn=point(ge,gn,yaw,s*1.3,0);box('GatePier_'+str(i)+'_'+str(j),pe,pn,h(pe,pn)+.78,[.45,.45,1.12],cream,yaw)
 for j in range(9):
  pe,pn=point(ge,gn,yaw,-1.04+j*.26,0);box('GateSlat_'+str(i)+'_'+str(j),pe,pn,h(pe,pn)+.75,[.08,.10,.95],petrol,yaw)
 for zz in [.45,1.02]:box('GateRail_'+str(i)+'_'+str(zz),ge,gn,h(ge,gn)+zz,[2.2,.12,.08],petrol,yaw)
# Short low links close the remaining west shop and south plaza gaps.
for i,(e,n,w,yaw) in enumerate([(-61,48.3,3.5,135),(-5.5,-17,3.5,270)]):
 box('LinkWall_'+str(i),e,n,h(e,n)+.67,[w,.34,.92],cream,yaw);box('LinkCap_'+str(i),e,n,h(e,n)+1.16,[w+.08,.43,.08],curb,yaw)
rep['status']='saved';assert E.save_current_level();rep['actor_count']=len(A.get_all_level_actors());(O/'apply.json').write_text(json.dumps(rep,indent=2));u.log('V5_SAVED '+str(rep['actor_count']))
