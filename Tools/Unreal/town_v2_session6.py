"""One-time targeted Session 6 placement. Continue saved map; never replay."""
import unreal as u,json,pathlib,math,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-6';E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.EditorAssetLibrary
assert (O/'backup-manifest.json').exists() and (O/'audit-before.json').exists()
assert json.loads((O/'before/capture.json').read_text())['status']=='success'
assert not (O/'apply-started.json').exists(),'Reconcile receipt before any retry'
assert E.load_level('/Game/Selene/Maps/TownV2');by={a.get_actor_label():a for a in A.get_all_level_actors()};assert not any(k.startswith('V6_') for k in by)
rep={'status':'started','assets':[],'placements':[],'removed':[],'new_actors':[],'scale_policy':'Source real-scale meshes at uniform 1.0; base-centred pivot retained'}
(O/'apply-started.json').write_text(json.dumps(rep,indent=2))
meshes={}
for slug in ['seaside-guesthouse','seaside-lighthouse-house','harbour-boathouse','artdeco-tower']:
 m=u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}');assert m
 ns=m.get_editor_property('nanite_settings');ns.set_editor_property('enabled',True);m.set_editor_property('nanite_settings',ns)
 m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert L.save_loaded_asset(m,False);meshes[slug]=m;rep['assets'].append({'asset':slug,'nanite':True,'collision':'complex-as-simple'})
 (O/'engine-setup.json').write_text(json.dumps(rep['assets'],indent=2))
z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):
 x=max(0,min(1007.999,(e+590)/1500*1008));y=max(0,min(1007.999,(n+750)/1500*1008));i=int(x);j=int(y);a=x-i;b=y-j
 return z[i*1009+j]*(1-a)*(1-b)+z[(i+1)*1009+j]*a*(1-b)+z[i*1009+j+1]*(1-a)*b+z[(i+1)*1009+j+1]*a*b
cube=u.load_asset('/Engine/BasicShapes/Cube');D='/Game/Selene/Materials/Ground/';paving=u.load_asset(D+'MI_V4_Paving');stone=u.load_asset(D+'MI_Town_Gutter');cream=u.load_asset(D+'M_Town_Cream');petrol=u.load_asset(D+'M_Town_Petrol')
def vec(e,n,z):return u.Vector(n*100,e*100,z*100)
def spawn(label,mesh,e,n,z,scale=(1,1,1),yaw=0,mat=None):
 a=A.spawn_actor_from_class(u.StaticMeshActor,vec(e,n,z),u.Rotator(yaw=yaw));a.set_actor_label('V6_'+label);a.set_folder_path('TownV2/Session6');a.tags=[u.Name('TownV2Session6')];c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll');a.set_actor_scale3d(u.Vector(*scale))
 if mat:c.set_material(0,mat)
 rep['new_actors'].append(a.get_actor_label());return a
def box(label,e,n,bottom,top,w,d,yaw=0,mat=None):
 assert top>bottom
 return spawn(label,cube,e,n,(bottom+top)/2,(w,d,top-bottom),yaw,mat or stone)
def point(e,n,yaw,x,y):
 a=math.radians(yaw);return e+x*math.sin(a)+y*math.cos(a),n+x*math.cos(a)-y*math.sin(a)
def terrace(key,e,n,yaw,w,d,base):
 # A solid retaining foundation extends below the lowest terrain corner. The cap
 # is exactly flush with the asset's Z=0 base, with space around doors and stairs.
 corners=[point(e,n,yaw,x,y) for x,y in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
 bottom=min(h(*p) for p in corners)-.3
 box(key+'_Foundation',e,n,bottom,base-.12,w,d,yaw,stone)
 box(key+'_Paving',e,n,base-.12,base,w+.08,d+.08,yaw,paving)
 return {'base_m':base,'foundation_bottom_m':bottom,'corners_m':corners,'corner_ground_m':[h(*p) for p in corners]}
def stairs(key,start,end,start_z,end_z,width=2.4):
 # Flight rises from existing pavement to the new apron with <=15 cm risers.
 de=end[0]-start[0];dn=end[1]-start[1];dist=math.hypot(de,dn);count=max(1,math.ceil(abs(end_z-start_z)/.15));yaw=math.degrees(math.atan2(de,dn));length=dist/count
 for i in range(count):
  t=(i+.5)/count;e=start[0]+de*t;n=start[1]+dn*t;top=start_z+(end_z-start_z)*(i+1)/count;bottom=min(h(e,n)-.12,top-.12)
  box(key+'_Step_'+str(i),e,n,bottom,top,length+.03,width,yaw,paving)
 rep.setdefault('connections',[]).append({'name':key,'start_m':[*start,start_z],'end_m':[*end,end_z],'steps':count})
# Only the repeated townhouse and its own old foundation are removed.
for label in ['V2_Lot_way_663900822','V4_Foundation_9']:
 assert label in by;A.destroy_actor(by[label]);rep['removed'].append(label)
placements=[('Guesthouse','seaside-guesthouse',-77.0,70.0,45.0,6.22),('Lighthouse','seaside-lighthouse-house',-59.5,22.0,180.0,5.55),('Boathouse','harbour-boathouse',-58.0,-8.0,180.0,3.85)]
for key,slug,e,n,yaw,base in placements:
 m=meshes[slug];b=m.get_bounding_box();w=(b.max.x-b.min.x)/100;d=(b.max.y-b.min.y)/100
 # Guesthouse's side stair has an extra 1.4 m clear apron on both sides.
 apron=terrace(key,e,n,yaw,w+2.8,d+2.8,base)
 a=spawn(key,m,e,n,base,yaw=yaw)
 rep['placements'].append({'actor':a.get_actor_label(),'asset':slug,'center_m':[e,n,base],'yaw':yaw,'uniform_scale':1,'height_m':(b.max.z-b.min.z)/100,'terrace':apron})
# All connections stay clear of the unchanged seven-point plaza/shop route.
gfront=point(-77,70,45,0,12.526/2+1.4);gstart=point(-77,70,45,0,12.526/2+3.2)
stairs('GuesthouseEntry',gstart,gfront,h(*gstart)+.19,6.22,3.0)
stairs('LighthouseLink',(-49.8,22),(-51.7,22),h(-49.8,22)+.19,5.55,3.0)
stairs('BoathouseLink',(-49.0,-8),(-51.75,-8),h(-49,-8)+.19,3.85,3.0)
# Low capped seaward walls edge the lighthouse terrace, leaving the front opening.
for i,n in enumerate([13.4,30.6]):
 box('LighthouseWall_'+str(i),-59.5,n,5.55,6.20,14.6,.30,90,cream)
 box('LighthouseCap_'+str(i),-59.5,n,6.20,6.28,14.8,.40,90,stone)
# Water-facing apron and a short landing beside the boathouse door.
box('BoathouseLanding',-65.0,-8,-.4,3.85,5.0,2.7,0,paving)
# Keep the large art-deco asset uninstantiated.
assert not any(isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh==meshes['artdeco-tower'] for a in A.get_all_level_actors())
assert E.save_current_level();rep['status']='saved';rep['actor_count']=len(A.get_all_level_actors());(O/'apply.json').write_text(json.dumps(rep,indent=2));(R/'Design/TownV2/session-6-placements.json').write_text(json.dumps(rep,indent=2));u.log('V6_SAVED '+str(rep['actor_count']))
