"""One correction for house occluding lighthouse silhouette from plaza."""
import unreal as u,json,pathlib,shutil
R=pathlib.Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));O=R/'Saved/TownV2/session-6';assert (O/'readback-final.json').exists();assert not (O/'sightline-correction.json').exists();B=O/'before-sightline';B.mkdir(exist_ok=False);shutil.copy2(R/'Content/Selene/Maps/TownV2.umap',B/'TownV2.umap')
E=u.get_editor_subsystem(u.LevelEditorSubsystem);assert E.load_level('/Game/Selene/Maps/TownV2');A=u.get_editor_subsystem(u.EditorActorSubsystem);by={a.get_actor_label():a for a in A.get_all_level_actors()}
for k in ['V6_Lighthouse','V6_Lighthouse_Foundation','V6_Lighthouse_Paving']:by[k].set_actor_rotation(u.Rotator(yaw=90),False)
for i,n in enumerate([14.4,29.6]):
 for kind,zz,size in [('Wall',5.875,(17.1,.30,.65)),('Cap',6.24,(17.3,.40,.08))]:
  a=by['V6_Lighthouse'+kind+'_'+str(i)];a.set_actor_location(u.Vector(n*100,-5950,zz*100),False,False);a.set_actor_scale3d(u.Vector(*size))
assert E.save_current_level();rep={'status':'saved','diagnosis':'Attached house hid lighthouse tower from plaza eye-level view 10','correction':'Rotate new lighthouse and its support terrace from yaw 180 to 90; refit low walls; keep building centre/base and every preexisting actor unchanged','yaw_before':180,'yaw_after':90,'center_m':[-59.5,22,5.55]};(O/'sightline-correction.json').write_text(json.dumps(rep,indent=2))
