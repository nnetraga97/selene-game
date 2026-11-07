"""Verify accepted Session 6 evidence and append its bounded-session checkpoint."""
from pathlib import Path
import json,hashlib,statistics,datetime,subprocess,ast
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-6'
def load(n):return json.loads((O/n).read_text())
before=load('before/capture.json');final=load('final/capture.json');read=load('readback-final.json');walk=load('plaza-shop-walk-final.json');apply=load('apply.json');correction=load('sightline-correction.json')
assert before['status']==final['status']=='success';assert len(before['shots'])==9 and len(final['shots'])==13
assert before['cameras']==final['cameras'][:9];assert before['cameras'][:8]==json.loads((R/'Saved/TownV2/session-5/final/capture.json').read_text())['cameras']
assert before['resolution']==final['resolution']==[1280,720] and before['fov']==final['fov']==70
assert read['status']=='verified' and walk['status']=='success' and walk['reached']==list(range(7))
assert all(not s['falling'] for s in walk['samples']);assert walk['route']==json.loads((R/'Saved/TownV2/session-5/plaza-shop-walk-final.json').read_text())['route']
protected=load('protected-before.json');bad=[n for n,h in protected.items() if not (R/n).exists() or hashlib.sha256((R/n).read_bytes()).hexdigest()!=h];assert not bad,bad
backup=load('backup-manifest.json');changed=[n for n,h in backup.items() if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h]
for p in (R/'Tools/Unreal').glob('town_v2_session6*.py'):ast.parse(p.read_text())
ast.parse((R/'Tools/Unreal/town_v2_capture.py').read_text());subprocess.run(['bash','-n',str(R/'Tools/Unreal/town_run.sh')],check=True)
proc=subprocess.run(['pgrep','-f','UnrealEditor.*Selene.uproject'],capture_output=True,text=True);assert proc.returncode==1,proc.stdout;assert not Path('/tmp/selene-unreal.lock').exists()
now=datetime.datetime.now(ZoneInfo('America/Los_Angeles'));rows=[]
for b,a in zip(before['performance'],final['performance'][:9]):
 assert b['view']==a['view'];rows.append({'view':b['view'],'before_fps':b['indicative_fps'],'final_fps':a['indicative_fps'],'change_fps':a['indicative_fps']-b['indicative_fps'],'change_percent':(a['indicative_fps']/b['indicative_fps']-1)*100,'before_ms':b['mean_ms'],'final_ms':a['mean_ms']})
b=statistics.mean(x['before_ms'] for x in rows[:8]);a=statistics.mean(x['final_ms'] for x in rows[:8]);fps={'method':'Equal-view-weighted mean world-frame time, then fps=1000/mean_ms; indicative offscreen editor game, not GPU timings','eight_fixed_before_fps':1000/b,'eight_fixed_final_fps':1000/a,'eight_fixed_change_percent':(b/a-1)*100,'views':rows};(O/'fps-comparison.json').write_text(json.dumps(fps,indent=2))
verification={'status':'verified','time':now.isoformat(),'protected_checked':len(protected),'protected_mismatches':bad,'existing_allowed_files_changed':changed,'eight_cameras_match_session5':True,'nine_matched_views':True,'supplemental_views':4,'unchanged_other_actors':True,'artdeco_instances':0,'walk_waypoints':7,'walk_grounded_samples':len(walk['samples']),'walk_seconds':walk['seconds'],'lock_released':True,'fps':fps}
artifacts=[R/'Content/Selene/Maps/TownV2.umap',*sorted((O/'final').glob('*.png')),O/'final-all-views-sheet.jpg',O/'final-supplemental-sheet.jpg',O/'before-after-comparison.jpg',O/'readback-final.json',O/'plaza-shop-walk-final.json'];verification['artifacts']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts};(O/'verification-final.json').write_text(json.dumps(verification,indent=2));(O/'process-final.json').write_text(json.dumps({'at':now.isoformat(),'pgrep_exit':proc.returncode,'processes':proc.stdout,'lock_exists':False},indent=2))
manifest={'status':'accepted saved checkpoint','placements':apply['placements'],'correction':correction,'walk_route_unchanged':True,'verification':'Saved/TownV2/session-6/verification-final.json'}
ground={x['building']:x for x in load('foundation-ground-check.json')}
for p in manifest['placements']:
 key=p['actor'].replace('V6_','');g=ground[key];p['terrace']['corners_m']=g['footprint_corners_m'];p['terrace']['corner_ground_m']=g['terrain_at_corners_m'];p['terrace']['foundation_bottom_m']=g['foundation_bottom_m']
 if key=='Lighthouse':p['yaw']=90
(R/'Design/TownV2/session-6-checkpoint.json').write_text(json.dumps(manifest,indent=2))
table='\n'.join(f"| {x['view']} | {x['before_fps']:.1f} | {x['final_fps']:.1f} | {x['change_fps']:+.1f} | {x['change_percent']:+.1f}% |" for x in rows)
text=f'''

## Session 6 — 2026-11-07 UTC — seaside buildings placed and verified

Started **23:37 PST on November 6**; verified **{now:%H:%M PST}**. Continued the saved
Session 5 map. No previous one-time apply/refine/correction script was replayed.

### Saved result and asset setup

- Backed up **{len(backup)} existing allowed files**, including TownV2 and the four
  imported static meshes, into `Saved/TownV2/session-6/backup/` before mutation.
  The separate `before-sightline/TownV2.umap` preserves the first placement candidate.
- **Guesthouse:** `V6_Guesthouse`, **(-77,70,6.22) m**, yaw **45°**, uniform scale **1**.
  Replaces `V2_Lot_way_663900822`, the repeated townhouse beside the bakery, and its
  own `V4_Foundation_9`. The 15 m guesthouse keeps its original textures and side
  stair; a paved apron and four shallow approach steps join the existing shop
  frontage. It is visible beside the bakery in 03/07 and clearly in 09/12.
- **Lighthouse house:** `V6_Lighthouse`, **(-59.5,22,5.55) m**, accepted yaw **90°**,
  uniform scale **1**. The 14 m landmark overlooks the shore below the plaza.
  A supported stone terrace, low capped walls and a short east-side connection
  meet the existing paving. Supplemental views 10 and 11 check the plaza and
  shop-street sightlines toward the sea.
- **Boathouse:** `V6_Boathouse`, **(-58,-8,3.85) m**, yaw **180°**, uniform scale **1**.
  Its large door faces the water. A supported quay, water-facing landing and seven
  shallow approach steps connect it to the shore-side path. View 04 and supplemental
  13 show it at the waterfront.
- All four imports already had **Nanite enabled** on live inspection, despite the
  brief's older import information. Kept it enabled and saved **complex-as-simple
  collision** on all four static meshes. Imported materials/textures are unchanged.
  **Art-deco tower has zero instances in TownV2.**
- Only existing owned meshes and ground materials were used. No new Fab buildings,
  material source edits, new lighting, palms, backdrop or character changes.
  Final map contains **{len(read['actors'])} actors and 35 building instances**.
  Every preexisting actor except the removed townhouse and its foundation is
  identical in fresh-process readback, including all other buildings.

Coordinates are local east/north/up metres; Unreal X=north and Y=east.
[Accepted checkpoint](../Design/TownV2/session-6-checkpoint.json),
[placement plan](../Saved/TownV2/session-6/placement-plan.png), and
[fresh readback](../Saved/TownV2/session-6/readback-final.json).

### Captures and eye-level review

- [Before — nine matched views](../Saved/TownV2/session-6/before-all-views-sheet.jpg).
- [Final — nine matched views](../Saved/TownV2/session-6/final-all-views-sheet.jpg).
- [Before/after comparison](../Saved/TownV2/session-6/before-after-comparison.jpg).
- [Final eye-level sheet](../Saved/TownV2/session-6/final-eye-level-sheet.jpg).
- [Supplemental plaza, shop, guesthouse and boathouse views](../Saved/TownV2/session-6/final-supplemental-sheet.jpg).
- [Lighthouse from the seafront](../Saved/TownV2/session-6/final/09_lighthouse_from_seafront.png).
- [Lighthouse from the plaza](../Saved/TownV2/session-6/final/10_lighthouse_from_plaza.png).

Views **01–08 exactly match Session 5**. New 09 uses the same camera before and after.
All retain 1280×720, FOV 70°, paused 15:00. Four supplemental eye-level captures
were added because the original plaza/clock cameras face inland. The final capture
run produced all **13 images**. `after/` and `details/` preserve the first candidate;
`final/` is the accepted saved map.

The cream/petrol/coral textures render correctly in the unchanged town light.
Buildings meet supported paving rather than hovering over the slope. The coastal
retaining walls are substantial and still plainly geometric; their masonry is
supported into the terrain/shore, not a floating thin plinth. This is a placement
checkpoint, not a finished harbour landscaping pass.

### Diagnosed corrections and verification

- One read-only API correction: StaticMeshEditorSubsystem is unavailable in this
  commandlet; removed its unnecessary collision-count call and read the mesh/body
  properties directly. The corrected audit succeeded. No mutating replay.
- One **lighthouse sightline correction**: the first yaw hid the tower behind the
  attached house from the plaza. Rotated only the new lighthouse and its terrace
  from 180° to 90°, and refit its low walls. Re-captured the same nine views plus
  the supplemental sightlines. No second placement iteration.
- One **supplemental guesthouse camera correction**: the initial camera was inside
  the unchanged bakery. Moved that diagnostic camera to the open frontage; the
  nine matched before/after cameras were not changed.
- Fresh readback verifies Nanite and complex-as-simple on all four assets, zero
  art-deco instances, no unexpected removed/changed existing actors, and **0 cm
  base-to-support gaps** for all three new buildings. The stone support volumes
  extend below sampled terrain at their corners, verified against the final rotated
  bounds in [foundation check](../Saved/TownV2/session-6/foundation-ground-check.json). Doorways/side stairs were reviewed
  in captures; the seven-point walk is not a full entrance/interior navigation test.
- **{len(protected):,}/{len(protected):,} protected file SHA256 hashes match**, including
  the already modified Source/Config, old Town, Blockout, characters, Fab packs,
  source art and all imported textures/materials. Existing Environment/Ground
  assets are unchanged. New geometry uses map actors and existing kit meshes.
  Python syntax and `bash -n` checks pass.
- Headless commandlets and offscreen scripted games only. Every launch used the
  pgrep guard, bounded 15-minute wait, shared mkdir lock, post-lock check, Perl
  alarm and EXIT cleanup. No running Selene was killed. Final process check is
  clear and the lock is released. No editor UI/computer use, downloads, purchases,
  paid services, external publication or commits. No paid receipt to reconcile.

### Grounded walk and indicative fps change

The accepted saved map reached **7/7 unchanged waypoints in {walk['seconds']:.2f} s**;
**{len(walk['samples'])}/{len(walk['samples'])} samples grounded**. Normal AddMovementInput
and CharacterMovement collision from PlayerStart; no teleports. The first candidate
walk also passed and is preserved separately.
[Final walk](../Saved/TownV2/session-6/plaza-shop-walk-final.json).

| View | Before fps | Final fps | Change | Change % |
| --- | ---: | ---: | ---: | ---: |
{table}

Across the original eight views, equal-view-weighted mean frame time changes from
**{b:.2f} to {a:.2f} ms**, equivalent to **{1000/b:.1f} → {1000/a:.1f} fps
({(b/a-1)*100:+.1f}%)**. These are indicative offscreen editor `-game` world-frame-delta
throughput samples: 45 s warmup, five-second stationary samples, screenshot frames
excluded, VSync/frame cap off, screen percentage 100. They are not packaged GPU or
stat-unit timings. Background activity/thermal state are uncontrolled; the observed
change should not be attributed entirely to mesh triangle count. No 60 fps claim.
[Fps data](../Saved/TownV2/session-6/fps-comparison.json),
[verification](../Saved/TownV2/session-6/verification-final.json).

### Exact next step

Keep this saved map, the nine fixed cameras and seven walk points. Before adding
more assets, profile the three new buildings' Nanite fallback, shadow and material
costs in a separately scoped run, then soften the lighthouse/boathouse retaining
walls with stepped shore paths and existing planting. Do not replay the Session 6
apply or sightline script: use fresh readback and targeted edits after another backup.
Earlier plaza enclosure, sparse outskirts, palms and missing Stylized Medieval City
remain outside this session's scope.

Existing site choice remains **Kailua-Kona**, for its curved waterfront, commercial
strip and landmark anchors: [site comparison](../Saved/TownV2/session-1/site-comparison.png),
[layout](../Saved/TownV2/session-1/layout-preview.png),
[heightmap](../Saved/TownV2/session-1/heightmap-preview.png).

ORCH_OUTCOME {{"version":1,"state":"delivered","reason":"Three seaside buildings saved in TownV2 with four-asset Nanite/collision setup, matched captures, lighthouse sightlines, grounded walk and fps comparison"}}
'''
p=R/'docs/TOWN-V2-PROGRESS.md';existing=p.read_text();assert '## Session 6 —' not in existing;p.write_text(existing+text)
verification['existing_allowed_files_changed']=[n for n,h in backup.items() if hashlib.sha256((R/n).read_bytes()).hexdigest()!=h];verification['artifacts'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();(O/'verification-final.json').write_text(json.dumps(verification,indent=2));print(json.dumps({'status':'delivered','time':now.isoformat(),'fps_before':1000/b,'fps_final':1000/a,'change_percent':(b/a-1)*100,'grounded_samples':len(walk['samples']),'walk_seconds':walk['seconds']},indent=2))
