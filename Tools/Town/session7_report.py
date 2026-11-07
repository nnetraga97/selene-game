"""Write the verified Session 7 handoff, preserving all earlier session entries."""
from pathlib import Path
import json,datetime
R=Path(__file__).resolve().parents[2];O=R/'Saved/TownV2/session-7'
def load(n):return json.loads((O/n).read_text())
v=load('verification-final.json');p=load('placement-final.json');walk=load('plaza-shop-walk-final.json');front=load('front-approaches.json');fps=load('fps-comparison.json')
assert v['status']=='verified' and front['status']=='success'
placements='\n'.join(f"| {x['asset']} | ({x['center_m'][0]:.1f}, {x['center_m'][1]:.1f}, {x['center_m'][2]:.3f}) | {x['yaw']:.0f} | {x['visible_floor_m']:.3f} |" for x in p['placements'])
table='\n'.join(f"| {x['view']} | {x['session6_fps']:.1f} | {x['fresh_before_fps']:.1f} | {x['final_fps']:.1f} | {x['change_vs_session6_percent']:+.1f}% | {x['change_vs_fresh_before_percent']:+.1f}% |" for x in fps['views'])
a=fps['aggregates']['8'];f=a['fps'];n=sum(len(x['samples']) for x in front['trials']);g=sum(not s['falling'] for x in front['trials'] for s in x['samples']);now=datetime.datetime.now(datetime.timezone.utc)
text=f'''## Session 7 — 2026-11-07 UTC — six city buildings saved; skyline framing incomplete

Started **07:58 UTC**; completed **{now:%H:%M UTC}**. Continued the saved Session 6
map. Every launch was headless and used `town_run.sh`: pgrep guard, bounded
15-minute wait, shared mkdir lock, post-lock check, Perl alarm, EXIT lock cleanup.
No running Selene was killed; no editor UI/computer use. Final process check is
clear and the lock is released. No downloads, purchases, paid services, external
submissions or commits; no paid receipt to reconcile. Default/startup maps unchanged.

### Saved result and backup

Backed up **10 files** before mutation: TownV2, all six imported meshes, the launcher,
original capture helper and progress. See `Saved/TownV2/session-7/backup/` and
[backup manifest](../Saved/TownV2/session-7/backup-manifest.json).
`before-correction/TownV2.umap` separately preserves the rejected first candidate.
All six meshes already had Nanite enabled; kept it enabled and saved
complex-as-simple collision on all six. The art-deco tower already had that
collision mode from Session 6. Original material/texture assets are unchanged.

The final city preview sits **beyond the inland pine belt**, away from the plaza,
cafe, shop street and coast. Four low buildings face a shared walking lane; the
80 m art-deco tower and 38 m office stand behind them, farther east. A **176.5 m
paved path** connects the existing inland footway to the cluster, routed around
existing trees. It is deliberately an accessible hillside preview, not a finished
city district. All six keep uniform scale 1.0.

Coordinates are local east/north/up metres; Unreal X=north, Y=east. The Z column
is the actor pivot, while visible floor is the supported paving height.

| Asset | Actor pivot (E,N,Z m) | Yaw degrees | Visible floor m |
| --- | --- | ---: | ---: |
{placements}

[Final placement receipt](../Saved/TownV2/session-7/placement-final.json),
[plan](../Saved/TownV2/session-7/placement-plan.png),
[saved checkpoint](../Design/TownV2/session-7-checkpoint.json).
Only the new V7 actors were created or corrected. Fresh readback verifies
**939 total actors; all 773 preexisting actors identical**, including every
Session 6 building, terrace, wall and step. There are now 41 building instances.
No Fab source assets or other imported assets were modified.

### Eye-level review and diagnosed corrections

The first eye-level run exposed existing pines intersecting footprints/fronts.
The first clearance filter had checked imported asset actors but omitted the Fab
pine mesh actors. **One correction** moved the entire new cluster 134 m east onto
clear ground and routed its approach around all existing tree canopies. No old
actor was moved or removed. Final clearance includes Fab trees and imported assets.

The walk-up had a separate visible grounding fault: a thin dangling fragment
reaches local Z=0, while the perimeter of its actual floor begins at **1.626 m**.
Source GLB inspection found only **40 of 33,153 vertices below 1.5 m**. **One
correction** lowers this actor 1.65 m so its visible slab seats into the paving;
no source mesh geometry changed. Its raw bounds extend below the paving and are
not a valid floor contact measurement. The final close capture confirms the
floating gap is gone. Other buildings use their original base pivots.

[Correction diagnosis](../Saved/TownV2/session-7/correction-plan.json),
[final clearance](../Saved/TownV2/session-7/placement-clearance-final.json),
[fresh readback](../Saved/TownV2/session-7/readback-final.json).
The nine standard cameras were unchanged. A separate single camera-only framing
correction improved the north-end overview, but its plaza view hit a foreground
tree. The original plaza view shows the office and a partly occluded art-deco tower
behind the clock hall. Kept that original view and **stopped camera iteration under
the one-fix rule**. The requested clear skyline presentation remains incomplete;
`city-framing/11` is accepted, `city-framing/12` is rejected. No saved actors changed.
[Visual review](../Saved/TownV2/session-7/visual-review.json).

### Captures

- [City preview sheet](../Saved/TownV2/session-7/city-preview-sheet.jpg).
- [Eye-level cluster](../Saved/TownV2/session-7/city-framing/11_city_cluster_eye.png).
- [Skyline from the plaza](../Saved/TownV2/session-7/final/12_city_skyline_from_plaza.png).
- [City aerial](../Saved/TownV2/session-7/final/13_city_cluster_aerial.png).
- [Preserved lighthouse view from plaza](../Saved/TownV2/session-7/final/10_lighthouse_from_plaza.png).
- [Before nine standard views](../Saved/TownV2/session-7/before-all-views-sheet.jpg).
- [Final nine standard views](../Saved/TownV2/session-7/final-all-views-sheet.jpg).
- [Before/after comparison](../Saved/TownV2/session-7/before-after-comparison.jpg).
- [Six fronts and supplemental views](../Saved/TownV2/session-7/final-supplemental-sheet.jpg).

All **19 final images plus two framing-attempt images** completed. Views 01–09 exactly match Session 6 and the
fresh before run, at 1280×720, FOV 70°, paused 15:00. The original town light and
imported cream/petrol/coral/brick textures are retained. The lighthouse remains
unobstructed in its plaza view; the inland skyline is in the opposite direction.
`after/` is the rejected first placement; `final/` is the saved corrected placement.
The north overview in `city-framing/11` supplements it; `city-framing/12` is rejected.

### Grounded walk and frontage access

The unchanged seven-point plaza–shop walk reached **7/7 waypoints in
{walk['seconds']:.2f} s**, with **{len(walk['samples'])}/{len(walk['samples'])} samples grounded**.
Normal AddMovementInput and CharacterMovement collision from PlayerStart;
no teleports and no waypoint changes. [Walk evidence](../Saved/TownV2/session-7/plaza-shop-walk-final.json).

Separate runtime trials walked the full town-to-city connection and each of the
six frontage ramps: **7/7 trials succeeded**, **{g}/{n} sampled frames grounded**.
The pawn was positioned at each trial's start, then walked normally with collision;
this is independent of the original walk. Targets reach the exterior aprons;
interior navigation and every baked doorway/stair tread were not tested.
[Approach evidence](../Saved/TownV2/session-7/front-approaches.json).
The steepest new ramp is **23.21 degrees**, on the hillside approach network.

### Indicative fps change

| View | Session 6 final fps | Fresh before fps | Session 7 final fps | Vs Session 6 | Vs fresh before |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

Across the original eight views, equal-view-weighted mean frame time corresponds
to **{f['session6']:.1f} → {f['final']:.1f} fps vs Session 6
({a['change_vs_session6_percent']:+.1f}%)**. The fresh same-session baseline was
**{f['fresh_before']:.1f} fps**, so the before/after change within this session is
**{a['change_vs_fresh_before_percent']:+.1f}%**. The large baseline difference between
sessions demonstrates uncontrolled background/thermal variability; do not read
the historical comparison as an optimization gain or attribute the full change
to these meshes. These are offscreen editor `-game` world-frame-delta samples,
45 s warmup, five seconds per stationary view, screenshots excluded, VSync/frame
cap off and screen percentage 100. They are not packaged GPU/stat-unit timings
and do not establish 60 fps gameplay. [Raw comparison](../Saved/TownV2/session-7/fps-comparison.json).

### Preservation, limitations and exact next step

**5,604/5,604 protected SHA256 hashes match**, including Source/Config, old Town,
Blockout, characters, source art, Fab assets, existing Environment/Ground assets,
and imported textures/materials. Python syntax and launcher `bash -n` pass.
[Verification](../Saved/TownV2/session-7/verification-final.json).

The six-building preview exists and is walkable from town; clear plaza skyline
framing remains an unmet presentation check. It remains an isolated
hillside block connected by a long footpath, with plain supported stone terraces;
the office retaining base is substantial on the slope. The original generated
meshes have soft geometry and baked details. No landscaping, final road design,
interior setup or new asset generation was attempted. Earlier plaza enclosure,
palms and missing Stylized Medieval City remain outside this scope.

**Exact next step:** keep this saved map and review the six fronts in game via
the inland footway at **(125,55) m**, following the new path to **(298,60) m**.
In a separately scoped continuation, choose a plaza viewpoint from saved actor
bounds that clears both clock hall and planters before one capture. No further
camera retries belong to this session. If a permanent district is approved, scope a separate terrain/road
and retaining-wall integration pass before any further placement. Profile the
six buildings separately before drawing performance conclusions.
**Do not replay Session 7 apply or correction scripts, or any previous one-time
script.** Start any future edit from fresh readback and a new map backup.

The existing site remains **Kailua-Kona**, chosen for its curved waterfront,
commercial strip and landmark anchors: [comparison](../Saved/TownV2/session-1/site-comparison.png),
[layout](../Saved/TownV2/session-1/layout-preview.png),
[heightmap](../Saved/TownV2/session-1/heightmap-preview.png).

ORCH_OUTCOME {{"version":1,"state":"partial","reason":"Six-building preview saved and verified; clear plaza skyline framing remains incomplete after one camera correction","unmet_checks":["Clear plaza skyline framing"]}}
'''
p=R/'docs/TOWN-V2-PROGRESS.md';s=p.read_text();i=s.index('## Session 7 —');p.write_text(s[:i]+text);print('Wrote verified Session 7 handoff at',now.isoformat())
