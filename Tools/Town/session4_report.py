"""Write bounded-session verification/progress after the final captures exist."""
from pathlib import Path
import json,hashlib,ast,datetime,subprocess
from zoneinfo import ZoneInfo
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-4';load=lambda p:json.loads((O/p).read_text());B=load('apply.json');C=load('final/capture.json');Before=load('before/capture.json');W=load('plaza-shop-walk-final.json');A=load('readback-final.json')
assert C['status']=='success' and len(C['shots'])==6
assert C['cameras']==Before['cameras'] and C['fov']==Before['fov'] and C['resolution']==Before['resolution']
assert W['status']=='success' and all(not x['falling'] for x in W['samples'])
assert A['status']=='verified'
protected=load('protected-before.json');mismatch=[n for n,d in protected.items() if not (R/n).exists() or hashlib.sha256((R/n).read_bytes()).hexdigest()!=d];assert not mismatch,mismatch
scripts=list((R/'Tools/Unreal').glob('town_v2_session4*.py'))+list((R/'Tools/Town').glob('session4_*.py'))
for p in scripts:ast.parse(p.read_text())
subprocess.run(['bash','-n',str(R/'Tools/Unreal/town_run.sh')],check=True)
# Assets in the original Ground/Environment backup remain identical; only TownV2 changed.
existing=load('backup-manifest.json');existing_changed=[n for n,d in existing.items() if not (R/n).exists() or hashlib.sha256((R/n).read_bytes()).hexdigest()!=d]
artifacts={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'Content/Selene/Maps/TownV2.umap',R/'Design/TownV2/session-4-build.json',*sorted((O/'final').glob('*.png')),O/'final-eye-level-sheet.jpg',O/'final-all-views-sheet.jpg',O/'before-after-comparison.jpg',O/'readback-final.json',O/'plaza-shop-walk-final.json']}
now=datetime.datetime.now(ZoneInfo('America/Los_Angeles'));verification={'status':'verified','time':now.isoformat(),'protected_files_checked':len(protected),'protected_mismatches':mismatch,'preexisting_allowed_files_changed':existing_changed,'identical_cameras':True,'captures':6,'grounded_samples':len(W['samples']),'walk_seconds':W['seconds'],'syntax_scripts':len(scripts),'artifact_sha256':artifacts};(O/'verification-final.json').write_text(json.dumps(verification,indent=2))
perf='\n'.join('| '+x['view']+' | '+f"{next(y['indicative_fps'] for y in Before['performance'] if y['view']==x['view']):.1f}"+' | '+f"{x['indicative_fps']:.1f}"+' | '+f"{x['mean_ms']:.2f}"+' |' for x in C['performance'])
lots='\n'.join('| '+x['lot']+' | '+x['building']+(' — '+str(x['hero']) if x['hero'] else '')+' | '+x['palette']+' | '+f"{x['yaw']:.1f}"+' |' for x in B['placements'])
text=f'''

## Session 4 — 2026-11-06 — buildings and ground, headless checkpoint

Started **18:24 PST**; verified **{now:%H:%M PST}**. Saved `/Game/Selene/Maps/TownV2`,
rendered the identical Session 3 viewpoints, and rechecked a grounded plaza/shop
walk. **All 29 occupied lots now use our Tripo buildings; zero Village cottages
remain.** This is a verified buildings-and-ground checkpoint with an explicitly
partial visual finish: the district still has broad, sparsely articulated courts.

### Building placement and palette

- **15 townhouse-terrace**, **4 apartment-curved**, **5 shop-bakery-corner**,
  **2 shop-tool-repair**, **2 workshop-garage**, **1 clock-hall**.
- Shops populate the waterfront/commercial strip; most townhouses/apartments fill
  the residential lots behind. Workshops occupy the eastern edge at approximately
  **(111,-75) m** and **(107,-29) m**. The clock stays at **(51,13) m** facing the plaza.
- Café hero `way/1296717081`, approximately **(-24,64) m**, now uses
  **shop-tool-repair** as its shell, with coral canopy/fascia, **CAFÉ SELENE** sign,
  a coffee counter and espresso machine, six tables/twelve chairs, planted terrace
  edges and a scooter. It is an exterior café adaptation, not a new dedicated
  café mesh or a tested accessible interior.
- Footprint fitting evaluates four rotations and preserves uniform mesh scale.
  Each placed building gets a separate saved material instance using the original
  texture-bearing parent and `BaseColorFactor`: ivory, cream, sand, petrol or coral.
  These are overall texture tints, not separately remasked wall/trim materials.
  No mirroring was needed. Original `/Game/Assets/*` assets were not changed.
- Existing Village props/filler remain, including lamps, benches, flower pots and
  backdrop conifers. **All 203 cottage rect-light children are gone.**
  The two previously unoccupied clipped lots below 25 m² remain empty.
- [Placement plan](../Saved/TownV2/session-4/building-placement-plan.png) and
  [exact placement/ground manifest](../Design/TownV2/session-4-build.json).

| OSM lot | Installed Tripo building / role | Tint | Yaw ° |
| --- | --- | --- | ---: |
{lots}

### Ground

- Replaced the three overlapping Session 3 road/sidewalk/curb actors and old plaza
  slab with **four saved meshes**: roads, connected paving, parking and curbs.
  A shared constrained triangulation joins intersections without overlapping
  road ribbons; terrain triangle constraints make the surface follow the existing
  graded mesh without grass breakthroughs. The source heightmap and terrain
  meshes remain unchanged.
- Main road **7.5 m**, side streets **5.5 m**, service lanes **4.5 m**; footways at
  least **2.5 m**. Sidewalk envelopes extend **2.5 m per side** of carriageways,
  with additional approximately 2.5 m lot aprons. Existing OSM roads have no width
  tags: these are explicit plausible game-design widths, **not surveyed widths**.
- Paved the built district, lots and in-between areas, the complete plaza and mapped
  parking courts. Added eight parking bay separators, shallow building plinths,
  short low court walls, six planted courtyard/seating groups, four plaza
  planter/tree/bench groups, and framed pocket parks. Existing source grass islands,
  three designed small park islands, seaward park and hillside retain grass.
- All new ground material instances use the existing **ground_tiles_27** family:
  pale paving/curbs and darker road/parking variants. Curbs have a five-point rounded
  profile and a roughly 13 cm road-to-paving rise. Planting and low walls soften
  selected court edges. Large district boundary corners and distant plinths remain
  visibly schematic; this is not final landscaping.

### Matched before/after evidence

- [Before eye-level sheet](../Saved/TownV2/session-4/before-eye-level-sheet.jpg).
- [Final eye-level sheet](../Saved/TownV2/session-4/final-eye-level-sheet.jpg).
- [Before all views including aerial](../Saved/TownV2/session-4/before-all-views-sheet.jpg).
- [Final all views including aerial](../Saved/TownV2/session-4/final-all-views-sheet.jpg).
- [Side-by-side comparison](../Saved/TownV2/session-4/before-after-comparison.jpg).
- [Final aerial](../Saved/TownV2/session-4/final/06_aerial.png).
- Full-resolution captures and timing manifests are in `before/` and `final/` under
  `Saved/TownV2/session-4/`. **6/6 final captures**: plaza/clock, café, shop street,
  seafront control, hills and aerial. Camera position **including Z**, target,
  70° FOV, 1280 × 720 resolution and paused 15:00 are identical to the baseline.
  The final images were visually inspected. `after/` and `after-verified/` are
  intermediate candidates, **not the final checkpoint**.

### Runtime and indicative frame rate

The actual plaza-to-shop-street walk starts at the saved PlayerStart, then follows
seven waypoints through the plaza and commercial frontage using normal
`AddMovementInput` and CharacterMovement collision. **7/7 waypoints reached in
{W['seconds']:.2f} s; {len(W['samples'])}/{len(W['samples'])} samples grounded; no teleports.**
The first walk also passed before refinement. The final walk follows the corrected
paving and court geometry. The subsequent tree-only sightline correction changes
only two non-colliding tree components; captures and fresh readback verify that
last saved map. Full advanced movement and interiors were not regression-tested.
Evidence: [final walk](../Saved/TownV2/session-4/plaza-shop-walk-final.json).

| View | Before fps | Final fps | Final mean ms |
| --- | ---: | ---: | ---: |
{perf}

These are **indicative offscreen -game world-frame-delta throughput samples** from
editor binaries, after a 45-second warmup and during five-second stationary samples,
with screenshot frames excluded, VSync/frame cap off and screen percentage 100.
They are not packaged GPU/stat-unit timings and do not prove 60 fps gameplay.
Added geometry and plant groups have a measurable cost; no performance improvement
is claimed despite removal of cottage lights.

### Verification, diagnosed fixes and preservation

- [Fresh final readback](../Saved/TownV2/session-4/readback-final.json):
  **{A['actor_count']} actors**, 29 recorded Tripo building actors, four new ground meshes
  with complex-as-simple collision and saved material bindings, zero Village house
  classes, zero rect lights, zero duplicate V2/V4 labels and zero superseded road
  actors. All per-instance tints read back from saved materials.
- [Final verification](../Saved/TownV2/session-4/verification-final.json):
  **{len(protected):,}/{len(protected):,} protected SHA256 hashes match**. Config, Source, old Town,
  Blockout, source Tripo assets, characters and Fab packs are unchanged. Among the
  59 backed-up existing allowed files, **only TownV2.umap changed**; existing Ground
  and Environment assets remain identical. New assets are confined to allowed
  Environment/Ground roots. Python AST and shell syntax checks pass.
- One read-only audit API correction: `GetUsedTextures` accepts a Material, not a
  MaterialInstanceConstant; reading instance texture parameters instead succeeded.
- One capture-diagnosed pavement correction: explicit terrain diagonal constraints
  removed visible triangular grass breakthroughs. One separate composition
  correction relocated/reduced the new shop-pocket tree after it obscured the
  bakery in the fixed camera. No repeated mutating retry was used.
- Every Selene launch went through the process guard, `/tmp/selene-unreal.lock`,
  post-lock recheck and Perl alarm. No existing Selene was killed. Only headless
  commandlets and offscreen scripted game runs were used; no editor UI/computer use.
  Blender ran headlessly with local geometry only. No downloads, installs,
  purchases, paid services, external publication or commits occurred. No paid
  submission or receipt exists to reconcile. Startup/default map was not changed.
- Backups: `Saved/TownV2/session-4/backup/` and `before-refinement/`.
  One-time apply/refine/sightline scripts have receipt guards. **Do not replay them
  over the saved checkpoint.** Continue with targeted in-place changes.

### Gaps and next session

The cottage/Tripo style clash is resolved and urban lawn has been replaced by a
coherent paved district. The fixed views still expose **too much open paved space**,
repeated townhouse end walls and simple plinth/edge treatment. Courtyard groups
improve local scale but do not yet produce the dense, finished coastal district
from the concepts. The café reads as an exterior café conversion; its interior and
shop-shell shutter geometry need a later architectural pass. No palms were added;
sea, sky, hills and the existing backdrop conifers were outside this session.
Stylized Medieval City remains unused. No full movement or packaged GPU validation.

Next session: keep these cameras and the saved map; finish the plaza–café–shop
frontages with tighter, deliberately enclosed courts, aligned door thresholds,
more varied wall lengths and façade orientation. Review those eye-level views before
expanding. A separately scoped later session can address tropical planting,
seafront/backdrop and lighting. Profile repeated prop assemblies before adding more.

Existing site/data evidence remains unchanged: **Kailua-Kona**, selected for its
curved waterfront, commercial strip and palace/church anchors; [site comparison](../Saved/TownV2/session-1/site-comparison.png),
[layout preview](../Saved/TownV2/session-1/layout-preview.png), and
[heightmap preview](../Saved/TownV2/session-1/heightmap-preview.png).

ORCH_OUTCOME {{"version":1,"state":"partial","reason":"All 29 Tripo building replacements and paved ground checkpoint saved with matched captures and grounded shop walk; dense courtyard visual finish remains incomplete","unmet_checks":["dense finished courtyard and frontage composition","final plinth and district-edge detailing"]}}
'''
p=R/'docs/TOWN-V2-PROGRESS.md';assert '## Session 4 —' not in p.read_text(),'Progress already appended'
with p.open('a') as f:f.write(text)
print('Progress appended and preservation verified at',now.isoformat())
