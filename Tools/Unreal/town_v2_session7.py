"""One-time Session 7 city preview. Receipts prevent mutation replay."""
import unreal as u,json,pathlib,math,array
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-7';E=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.EditorAssetLibrary
assert (O/'backup-manifest.json').exists() and (O/'audit-before.json').exists()
assert json.loads((O/'before/capture.json').read_text())['status']=='success'
assert not (O/'apply-started.json').exists(),'Reconcile receipt; never replay'
assert E.load_level('/Game/Selene/Maps/TownV2');assert not any(a.get_actor_label().startswith('V7_') for a in A.get_all_level_actors())
rep={'status':'started','assets':[],'placements':[],'new_actors':[],'removed':[],'connections':[]};(O/'apply-started.json').write_text(json.dumps(rep,indent=2))
meshes={}
for slug in ['metro-walkup','metro-brownstones','metro-lane-houses','metro-diner','artdeco-tower','metro-glass-office']:
 m=u.load_asset(f'/Game/Assets/{slug}/{slug}/StaticMeshes/{slug}');assert m
 ns=m.get_editor_property('nanite_settings');ns.set_editor_property('enabled',True);m.set_editor_property('nanite_settings',ns)
 m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 assert L.save_loaded_asset(m,False);meshes[slug]=m;rep['assets'].append({'asset':slug,'nanite':True,'collision':'complex-as-simple'});(O/'engine-setup.json').write_text(json.dumps(rep['assets'],indent=2))
z=array.array('f');z.frombytes((R/'Saved/TownV2/session-3/meshes/graded-elevation-ue.f32').read_bytes())
def h(e,n):
 x=max(0,min(1007.999,(e+590)/1500*1008));y=max(0,min(1007.999,(n+750)/1500*1008));i=int(x);j=int(y);a=x-i;b=y-j
 return z[i*1009+j]*(1-a)*(1-b)+z[(i+1)*1009+j]*a*(1-b)+z[i*1009+j+1]*(1-a)*b+z[(i+1)*1009+j+1]*a*b
cube=u.load_asset('/Engine/BasicShapes/Cube');D='/Game/Selene/Materials/Ground/';paving=u.load_asset(D+'MI_V4_Paving');stone=u.load_asset(D+'MI_Town_Gutter')
def vec(e,n,z):return u.Vector(n*100,e*100,z*100)
def spawn(label,mesh,e,n,z,scale=(1,1,1),yaw=0,mat=None,pitch=0):
 a=A.spawn_actor_from_class(u.StaticMeshActor,vec(e,n,z),u.Rotator(pitch=pitch,yaw=yaw));a.set_actor_label('V7_'+label);a.set_folder_path('TownV2/Session7');a.tags=[u.Name('TownV2Session7')];c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_mobility(u.ComponentMobility.STATIC);c.set_collision_profile_name('BlockAll');a.set_actor_scale3d(u.Vector(*scale))
 if mat:c.set_material(0,mat)
 rep['new_actors'].append(a.get_actor_label());return a
def box(label,e,n,bottom,top,w,d,mat=None):
 return spawn(label,cube,e,n,(bottom+top)/2,(w,d,top-bottom),mat=mat or stone)
def ramp(label,p,q,width=3):
 de=q[0]-p[0];dn=q[1]-p[1];dz=q[2]-p[2];dist=math.hypot(de,dn);length=math.hypot(dist,dz);yaw=math.degrees(math.atan2(de,dn));pitch=math.degrees(math.atan2(dz,dist));assert abs(pitch)<25
 # Top of the 16 cm slab follows the endpoint heights. Short segments follow terrain.
 spawn(label,cube,(p[0]+q[0])/2,(p[1]+q[1])/2,(p[2]+q[2])/2-.08,(length+.05,width,.16),yaw,paving,pitch)
 rep['connections'].append({'name':label,'start_m':p,'end_m':q,'slope_degrees':pitch})
def terrain_path(label,pts,width=3):
 k=0
 for p,q in zip(pts,pts[1:]):
  count=max(1,math.ceil(math.dist(p,q)/2));last=[p[0],p[1],h(*p)+.18]
  for i in range(1,count+1):
   t=i/count;pt=[p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t];nxt=[*pt,h(*pt)+.18];ramp(label+'_'+str(k),last,nxt,width);last=nxt;k+=1
terrain_path('CityLane',[(164,5),(164,108)],5)
terrain_path('TownLink',[(125,55),(134,60),(164,60)],3)
placements=[('Walkup','metro-walkup',146,22,0),('Brownstones','metro-brownstones',146,48,0),('LaneHouses','metro-lane-houses',146,70,0),('Diner','metro-diner',146,90,0),('ArtDeco','artdeco-tower',192,32,180),('GlassOffice','metro-glass-office',192,87,180)]
for key,slug,e,n,yaw in placements:
 m=meshes[slug];b=m.get_bounding_box();w=(b.max.x-b.min.x)/100;d=(b.max.y-b.min.y)/100;aw=w+2;ad=d+3
 corners=[[e+se*ad/2,n+sn*aw/2] for se,sn in [(-1,-1),(-1,1),(1,1),(1,-1)]]
 samples=[h(e+se*ad/2,n+sn*aw/2) for se in [-1,0,1] for sn in [-1,0,1]];base=max(samples)+.03;bottom=min(samples)-.25
 box(key+'_Foundation',e,n,bottom,base-.12,aw,ad);box(key+'_Paving',e,n,base-.12,base,aw,ad,paving)
 a=spawn(key,m,e,n,base,yaw=yaw)
 sign=1 if yaw==0 else -1;front=e+sign*ad/2
 ramp(key+'_Entry',[164,n,h(164,n)+.18],[front,n,base],3)
 rep['placements'].append({'actor':a.get_actor_label(),'asset':slug,'center_m':[e,n,base],'yaw':yaw,'uniform_scale':1,'height_m':(b.max.z-b.min.z)/100,'terrace':{'corners_m':corners,'corner_ground_m':[h(*p) for p in corners],'base_m':base,'foundation_bottom_m':bottom},'front_apron_m':[front,n,base]})
assert E.save_current_level();rep['status']='saved';rep['actor_count']=len(A.get_all_level_actors());(O/'apply.json').write_text(json.dumps(rep,indent=2));(R/'Design/TownV2/session-7-placements.json').write_text(json.dumps(rep,indent=2));u.log('V7_SAVED '+str(rep['actor_count']))
