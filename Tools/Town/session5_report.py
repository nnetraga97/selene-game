"""Reconcile the Session 5 evidence and append the bounded checkpoint once."""
from pathlib import Path
import json,hashlib,ast,datetime,subprocess
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-5';load=lambda p:json.loads((O/p).read_text());before=load('before/capture.json');final=load('final/capture.json');walk=load('plaza-shop-walk-final.json');readback=load('readback-final.json');scale=load('scale-reference-clear/capture.json');correction=load('correction.json');design=json.loads((R/'Design/TownV2/session-5-checkpoint.json').read_text());assert final['status']=='success' and len(final['shots'])==8;assert before['cameras']==final['cameras'] and before['fov']==final['fov'] and before['resolution']==final['resolution'];oldc=json.loads((R/'Saved/TownV2/session-4/final/capture.json').read_text());assert oldc['cameras']==final['cameras'][:6];assert walk['status']=='success' and len(walk['reached'])==7 and all(not x['falling'] for x in walk['samples']);assert readback['status']=='verified';assert scale['status']=='success';assert not Path('/tmp/selene-unreal.lock').exists();proc=subprocess.run(['pgrep','-fl','UnrealEditor.*Selene.uproject'],capture_output=True,text=True);assert proc.returncode==1,proc.stdout
protected=load('protected-before.json');bad=[n for n,d in protected.items() if not (R/n).exists() or hashlib.sha256((R/n).read_bytes()).hexdigest()!=d];assert not bad,bad
original=load('backup-manifest.json');changed=[n for n,d in original.items() if hashlib.sha256((R/n).read_bytes()).hexdigest()!=d]
for p in list((R/'Tools/Unreal').glob('town_v2_session5*.py'))+list((R/'Tools/Town').glob('session5*.py')):ast.parse(p.read_text())
subprocess.run(['bash','-n',str(R/'Tools/Unreal/town_run.sh')],check=True)
now=datetime.datetime.now(ZoneInfo('America/Los_Angeles'));artifacts=[R/'Content/Selene/Maps/TownV2.umap',*sorted((O/'final').glob('*.png')),O/'final-all-views-sheet.jpg',O/'final-eye-level-sheet.jpg',O/'before-after-comparison.jpg',O/'plaza-shop-walk-final.json',O/'readback-final.json',O/'scale-reference-clear/09_cafe_character_scale.png'];verification={'status':'verified checkpoint; visual finish partial','time':now.isoformat(),'protected_checked':len(protected),'protected_mismatches':bad,'existing_allowed_files_changed':changed,'fixed_cameras_match_session4':True,'all_eight_before_after_cameras_identical':True,'walk_waypoints':7,'grounded_samples':len(walk['samples']),'walk_seconds':walk['seconds'],'processes':proc.stdout,'lock_released':True,'artifacts':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}};(O/'verification-final.json').write_text(json.dumps(verification,indent=2));(O/'process-final.json').write_text(json.dumps({'pgrep_exit':proc.returncode,'processes':proc.stdout,'lock_exists':False,'at':now.isoformat()},indent=2));design['status']='verified saved checkpoint; visual finish partial';(R/'Design/TownV2/session-5-checkpoint.json').write_text(json.dumps(design,indent=2))
perf='\n'.join('| '+x['view']+' | '+f"{next(y['indicative_fps'] for y in before['performance'] if y['view']==x['view']):.1f}"+' | '+f"{x['indicative_fps']:.1f}"+' | '+f"{x['mean_ms']:.2f}"+' |' for x in final['performance'])
text=f'''

## Session 5 — 2026-11-06 — plaza block tightened, headless checkpoint

Started **19:45 PST**; verified **{now:%H:%M PST}**. Continued the saved Session 4
`/Game/Selene/Maps/TownV2`; no Session 4 apply/refine/sightline script was replayed.
This is a **verified partial visual checkpoint**: the cafe/shop row reads much more
like a connected street, but the whole plaza block is not yet a finished town.

### Accepted changes

- Backed up **145 existing allowed files** before editing to
  `Saved/TownV2/session-5/backup/`; hashes in `backup-manifest.json`. Captured the
  untouched saved map into `before/`. A separate `before-correction/TownV2.umap`
  preserves the intermediate candidate, not the accepted map.
- **Five existing buildings moved or rotated in place**, with their original
  uniform scales: clock hall to **(32,9) m**, cafe to **(-24.34,50) m**, tool shop
  to **(-10,50) m**, curved apartment to **(18,50) m**, and the southern townhouse
  turned toward the plaza at **(-18,-17) m**. The clock is about 19 m closer east-west
  and the cafe about 14 m closer north-south than Session 4.
- **Four accepted new Tripo instances**: two bakery-corner shells (southern plaza
  corner and cafe neighbour), a tool-shop shell at the shop bend, and a townhouse
  terrace continuing the opposite street frontage. Cream, sand, ivory and coral
  instances use the original texture-bearing parents. All 33 buildings in the map
  use existing owned Tripo assets. No new Fab buildings or downloaded assets.
- The cafe/tool/bakery/apartment row now has short gaps and varied widths. The
  cafe retains its sign, canopy, coffee counter and scooter; its six table groups
  were regrouped onto the front terrace and narrow side court, off the carriageway.
- **Four walled planted courts cover 1,977 m² of former visible paving**: cafe rear,
  upper court, clock rear and the vacated eastern apartment court. New terrain-
  conforming grass surfaces, capped low walls, gate piers/slats, 12 existing-asset
  street trees and 12 hydrangea groups form enclosed gardens. The original Session 4
  pavement remains below these surfaces; it was not destructively cut or rebuilt.
- **Ten visible frontages** received darker skirting, two shallow entrance steps,
  thresholds/doormats and paired planted doorways, including the unchanged bakery
  nearest fixed camera 03. A short capped wall closes the southern frontage gap.
- No lighting, seafront, palms, backdrop, Source, Config or source-asset edits.
  Original pack props remain. Stylized Medieval City remains absent/unused.

Exact accepted placements: [checkpoint manifest](../Design/TownV2/session-5-checkpoint.json).
[Plan overlay](../Saved/TownV2/session-5/after-plan.png).
The original `session-5-design.json` and `apply.json` describe the first candidate;
apply `correction.json` when reconciling history. Do not replay either one-time
mutation script. Use the saved map and fresh readback as the checkpoint.

### Scale check

No existing building was enlarged or stretched: **relative factor 1.000 for every
existing asset type**. Central shells were already substantial against the intended
1.8 m person; inflating them would worsen door/storey proportions. Every building
read back with equal X/Y/Z scale. Exact instance values are in
[scale-factors.json](../Saved/TownV2/session-5/scale-factors.json).

| Asset | Accepted block absolute mesh scale | Relative change to existing instance |
| --- | ---: | ---: |
| clock-hall | 0.7019 approximately, retained (15.44 m total height) | 1.000 |
| shop-tool-repair | 1.120 (10.64 m total height) | 1.000 |
| townhouse-terrace | 1.128 (11.28 m total height) | 1.000 |
| apartment-curved | 1.128 (20.30 m total height) | 1.000 |
| shop-bakery-corner | existing hero 1.120; new copies 1.050 | existing 1.000; new copies have no previous transform |
| workshop-garage | unchanged, outside this pass | 1.000 |

[Actual playable character beside cafe](../Saved/TownV2/session-5/scale-reference-clear/09_cafe_character_scale.png)
provides a separate stationary scale reference. Runtime capsule height recorded as
**{scale['scale_reference']['capsule_height_cm']:.1f} cm**; the character is the roughly
1.8 m visual reference, not a newly generated proxy. That separate capture positions
the pawn once and does not save. **The grounded route below never teleports.**
Total building height includes roofs and parapets and is not a measured floor height.
Some original shutters/entrances still have oversized proportions; no claim that
all baked asset storeys now measure 3–3.5 m.

### Matched captures and visual review

- [Before — all eight views](../Saved/TownV2/session-5/before-all-views-sheet.jpg).
- [Accepted final — all eight views](../Saved/TownV2/session-5/final-all-views-sheet.jpg).
- [Before eye-level sheet](../Saved/TownV2/session-5/before-eye-level-sheet.jpg).
- [Final eye-level sheet](../Saved/TownV2/session-5/final-eye-level-sheet.jpg).
- [Paired before/after sheet](../Saved/TownV2/session-5/before-after-comparison.jpg).
- [Final close plaza-block aerial](../Saved/TownV2/session-5/final/08_plaza_block_aerial.png).

Views **01–06 match Session 4 exactly**, including Z, target, FOV 70°, 1280 × 720
and paused 15:00. New **07_shop_from_plaza** and **08_plaza_block_aerial** use identical
cameras before/after. Both eight-image sets completed; full images and manifests
are in `before/` and `final/`. `after/` is the rejected intermediate candidate.
Eye-level review drove acceptance, not density counts or the aerial alone.

### Corrections and rollback

- Street/footpath overlay exposed an added lower shop over the main carriageway.
  Removed that entire addition and its linking wall. In the same single diagnosed
  clearance correction, shifted the clock, cafe neighbour and two shop-row pieces
  to clear existing paths/service-road corners. The route waypoints stayed unchanged.
- The first townhouse rotation hid its facade behind the bakery in view 03 and
  weakened the composition. **Reverted that actor and foundation to their exact
  Session 4 transforms** and removed its new entrance dressing. No second attempt.
- Local contact-sheet helper initially used a Python without Pillow; reused the
  existing read-only installed-wheel wrapper, without installing anything.
- The walk game completed successfully, but its launcher reported a trailing shell
  parse error because the helper file had been extended while that shell was active.
  Reconciled the completed walk JSON and normal game shutdown; did not replay it.
  Finished helper edits while idle and verified `bash -n`; subsequent guarded
  launches completed with the fixed helper. The lock trap released correctly.

### Grounded walk and indicative fps

**7/7 original waypoints reached in {walk['seconds']:.2f} seconds; {len(walk['samples'])}/{len(walk['samples'])}
samples grounded**, using normal AddMovementInput and CharacterMovement collision
from PlayerStart. No teleports and no waypoint changes. Evidence:
[plaza-shop-walk-final.json](../Saved/TownV2/session-5/plaza-shop-walk-final.json).
This checks that route, not all entrances, garden gates or advanced movement.

| View | Before fps | Final fps | Final mean ms |
| --- | ---: | ---: | ---: |
{perf}

These are indicative offscreen `-game` world-frame-delta throughput samples from
editor binaries, with a 45-second warmup, five-second stationary samples, screenshot
frames excluded, VSync/frame cap off and screen percentage 100. They are not packaged
GPU/stat-unit measurements and do not establish 60 fps gameplay.

### Preservation and remaining gaps

Fresh readback: **{readback['actor_count']} actors, 33 building actors**, three new garden
meshes with saved materials/collision, no duplicate V2/V4/V5 labels, no missing
recorded actors, no nonuniform building scales. **4,940/4,940 protected SHA256 hashes
match** the session start, including already user-modified Config/Source files.
Existing Environment/Ground assets stayed unchanged; the saved TownV2 map and
allowed tooling changed, and new content is confined to the allowed Environment
root. [Verification](../Saved/TownV2/session-5/verification-final.json).

Every Selene launch used `town_run.sh`: pre-launch pgrep, bounded 15-minute wait,
shared mkdir lock, post-lock pgrep, Perl alarm and EXIT lock cleanup. No existing
Selene was killed. Only commandlets and offscreen scripted games were used;
no editor UI or computer use. All owned game/editor processes ended and the lock
is released. No downloads, purchases, paid calls, external submissions or commits;
there is no paid receipt to reconcile. Startup/default map stays unchanged.

**Still fake:** the plaza's foreground/centre remains broad, the eastern transition
between clock and cafe still lacks a continuous built edge, and the garden rectangles
and distant pale slope expose the blockout underneath. Repeated shuttered tool-shop
shells remain obvious, some doorway proportions are large, and the cafe is an
exterior conversion. The full aerial still has sparse outskirts beyond this scope.
The new courts need more deliberate paths/planting composition, not more isolated
props spread across paving.

**Exact next step:** back up this accepted map, keep the eight cameras and the seven
walk points, and finish the **eastern plaza edge between the clock and cafe row**.
Overlay service street `way/1331478365/0` and footway `way/1331478370/0` first; fit
one low corner/annex and short frontage links in the remaining buildable pockets,
then shape the adjacent garden boundaries into smaller connected courts. Review
01/02/07 before extending elsewhere. Keep seafront, palms, backdrop and lighting
for a separately scoped pass. Do not rerun Session 4 or Session 5 one-time scripts.

Existing site/data evidence remains unchanged: **Kailua-Kona**, chosen for its curved
waterfront, commercial strip and landmark anchors; [site comparison](../Saved/TownV2/session-1/site-comparison.png),
[layout](../Saved/TownV2/session-1/layout-preview.png),
[heightmap](../Saved/TownV2/session-1/heightmap-preview.png).

ORCH_OUTCOME {{"version":1,"state":"partial","reason":"Saved and verified tighter cafe/shop frontage, gardens and entrance detailing with eight matched views and grounded walk; complete plaza enclosure remains unfinished","unmet_checks":["dense finished enclosure across the entire plaza block","consistent doorway and storey proportions in existing Tripo shells"]}}
'''
p=R/'docs/TOWN-V2-PROGRESS.md';existing=p.read_text();assert '## Session 5 —' not in existing,'Progress already appended';p.write_text(existing+text);verification['existing_allowed_files_changed']=[n for n,d in original.items() if hashlib.sha256((R/n).read_bytes()).hexdigest()!=d];verification['artifacts'][str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest();(O/'verification-final.json').write_text(json.dumps(verification,indent=2));print(json.dumps({'verification':verification['status'],'at':now.isoformat(),'protected':len(protected),'fps':[(x['view'],round(x['indicative_fps'],1)) for x in final['performance']]},indent=2))
