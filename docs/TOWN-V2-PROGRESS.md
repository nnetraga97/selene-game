# TownV2 progress

## Session 1 — 2026-11-06 — blocked checkpoint

Started approximately 17:18 PST; stopped source work at 17:23 PST after repeated
Overpass timeouts. Checkpoint verification completed at approximately 17:25 PST,
well inside the 30-minute bound. **The requested site/layout/terrain result is not
delivered.** The brief's failure rule triggered before any usable map data arrived.

### Done

- Read the full TownV2 brief, town-quality research, previous Town Session 1
  progress, town concept prompts and style-B environment prompts. Visually
  inspected both existing style-B environment concepts.
- Recorded the dirty starting Git state and hashed 1,339 protected files across
  `Design/Blockout/`, Config, Source, maps and Town external actors/objects.
- Prepared four provisional 300 × 300 m query centres: Kona palace/church
  seafront (19.63965, -155.99555), Hilo bayfront/Kalakaua Park
  (19.72525, -155.08600), Haleiwa bridge/harbour edge
  (21.59295, -158.10350), Sanur/Sindhu beach centre
  (-8.68385, 115.26520). These centres have **not** been verified against returned
  data and are not a comparative site decision.
- Added draft acquisition, local geometry, conversion and offline Python helpers
  under `Tools/Town/`. Added `Design/TownV2/sites.json`, a saved attempted query,
  README and the required OSM attribution text.
- Confirmed pre-existing NumPy 2.5.4, Pillow 13.0.0 and Matplotlib 3.11.2 work with
  Python 3.14. No packages were downloaded. The first dependency probe selected a
  Python 3.12 NumPy wheel; filtering for a compatible cached wheel fixed it once.

### Failure evidence and stop decision

1. `https://overpass-api.de/api/interpreter`: HTTP **502 Bad Gateway**.
2. `https://overpass.kumi.systems/api/interpreter`: **70-second read timeout**.
3. A read-only documentation check showed that the former kumi service is now
   listed at `https://overpass.private.coffee/api/interpreter`. Corrected that
   stale endpoint once; the **70-second read timeout repeated**.

The [OpenStreetMap public-instance table](https://wiki.openstreetmap.org/wiki/Overpass_API)
supports the endpoint correction. Status diagnostics returned HTTP 406 from the
main endpoint and a 15-second timeout from kumi. These observations do not establish
that Overpass is globally down, or that the query itself is invalid. The remaining
transport/server cause is unresolved. No further extract requests were made after
the repeated timeout, following the brief's instruction: **“Stop and report when a
failure repeats or can't be diagnosed.”**

[Acquisition failure record](../Saved/TownV2/session-1/acquisition-failures.json)
contains endpoints, outcomes, timeout limits and the documentation finding.
No paid or publishing action occurred; there is no paid submission to reconcile.
No raw OSM JSON/XML response, DEM tile or other asset was successfully downloaded.
Documentation was consulted only to diagnose the endpoint; no imagery, software,
Fab asset or replacement dataset was downloaded.

### Site, comparison and previews

**Kailua-Kona remains the provisional default from the brief**, because the brief
identifies a compact shopfront seafront with palace/church landmarks and uphill
backdrop potential. This is not a newly verified finding or final site selection.
Hilo, Haleiwa and Sanur could not be compared without the requested OSM extracts.

- Comparison image: **not created**.
- `Design/TownV2/layout.json`: **not created**.
- Layout preview / comparison with a raw OSM render: **not created**.
- Copernicus tile, cropped terrain, 16-bit heightmap and heightmap preview:
  **not created**. No AWS tile request was made while site selection was blocked.
- Before/after sheets: no new after state exists. The previous Town checkpoint's
  [accepted sheet](../Saved/Town/session-1/after-verified-contact.jpg) and
  [old layout](../Design/Blockout/map.png) remain the unchanged baseline; neither
  is presented as a TownV2 result.

### Verified scope and limitations

[Verification record](../Saved/TownV2/session-1/verification.json): all **1,339
protected SHA256 hashes matched**, including Blockout and the old Town map and
external actors. All three new Python files compile, the shell helper passes
syntax validation, and cached plotting dependencies import. These checks prove
preparation and preservation only; the converter has not been exercised on real
OSM and no layout/terrain quality check has passed.

Draft converter limitations are explicit: missing road widths are estimates;
multipolygon assembly and semantic area validation are incomplete; no central
plaza has been chosen or adapted; terrain elevations and shoreline handling have
not been implemented or checked. Do not import its output into Unreal yet.

No Unreal/Selene launch, process termination, Blender step, Fab access, paid
service, commit, Config/Source edit or old-Town/Blockout edit occurred.
Only `Tools/Town/`, `Design/TownV2/`, `Saved/TownV2/` and this report were written.

### Open questions

- Can an approved Overpass endpoint return the extracts from this environment?
  A fresh session should diagnose transport/endpoint health before resuming data
  acquisition, without an automatic retry loop.
- Does the Kona extract contain a usable plaza, or should a clearly labelled
  design adaptation create one beside the real street/landmark geometry?
- Which road widths/heights are tagged, and which need explicit estimates or
  later review? Is the 30 m Copernicus surface model adequate near the seafront
  after light smoothing, real sea-level handling and blended pads?

### Exact next step and proposed session 2

**Resume unfinished Session 1 first:** diagnose the Overpass response failure,
fetch and preserve all four raw extracts with receipts, render/inspect the
comparison and select the site. Then fetch exactly one anonymous Copernicus
GLO-30 tile, crop the 1.5 km backdrop, implement the shoreline/pad treatment and
16-bit heightmap with documented vertical encoding, complete/validate polygon
conversion, and inspect the layout and heightmap previews. Record a new verified
checkpoint before Unreal work.

**Session 2, after those artifacts exist:** check which already-owned packs are
present in Content; back up relevant existing content; use the required process
guard, lock and alarm before any launch. Create only `/Game/Selene/Maps/TownV2`,
import the heightmap and real street/lot geometry, and build the plaza district
first with installed assets and the existing Tripo hero buildings. Keep Town as
the fallback. Capture fixed eye-level plaza, shop-street, sea and hill views plus
an aerial, review the style-B light pass, and record indicative fps with a valid
measurement path. No Fab download or purchase is authorized.

ORCH_OUTCOME {"version":1,"state":"blocked","reason":"Repeated Overpass response timeouts triggered the brief's stop rule; preparation checkpoint saved","unmet_checks":["four OSM extracts and site comparison","verified site selection","layout.json and visual validation","one Copernicus tile and 16-bit heightmap","layout and heightmap previews"]}

## Session 1 retry — 2026-11-06, verified data checkpoint at 17:40 PST

Started 17:28:46 PST; overall stop target 17:58 PST. Read the complete brief,
including the retry diagnosis, quality research, prior Town progress and both
style-B images. Preserved a fresh 4,980-file baseline under
`Saved/TownV2/session-1/retry/protected-before.json`.

**Session 1 artifacts now exist and pass readback checks.** Five raw JSON/XML pairs
were acquired: Kona, Hilo, Haleiwa, Sanur, and a refined Kona core. All have matching
entity IDs, query files and receipt hashes. The first XML request returned 502 when
the draft sent an XML Accept header. Correcting that deviation to the brief's exact
JSON Accept header succeeded; all subsequent requests succeeded. This sequence
supports the working configuration, but does not prove the cause of that 502.
Only `overpass-api.de` was used, with the specified User-Agent and 10-second spacing.

**Chosen site: Kailua-Kona**, with its origin refined to 19.63950,-155.99420. The
initial origin put too much of the core over the bay. Kona's curved waterfront,
shop strip and palace/church anchors fit this composition best. Hilo's denser
frontage is separated from the bay by a broad road corridor; Haleiwa is looser;
the sampled Sanur frontage is linear. These are local-window comparisons, not
exhaustive judgements of the towns. See `Design/TownV2/site-selection.md`.

- [Four-site comparison](../Saved/TownV2/session-1/site-comparison.png)
- [OSM versus converted layout](../Saved/TownV2/session-1/layout-preview.png)
- [Source/prepared heightmap and pad preview](../Saved/TownV2/session-1/heightmap-preview.png)
- [Layout JSON](../Design/TownV2/layout.json)
- [Readback verification](../Saved/TownV2/session-1/retry/verification.json)

The layout contains **31 lots, 26 streets/paths, eight areas, one mapped tree and
zero mapped seawalls**. The converter assembles the mapped courtyard multipolygon
with its inner ring. A concave-bay classification bug in the draft renderer was
corrected using directed horizontal ray crossings. A **29 × 20 m plaza** is an
explicit design adaptation on open ground north of the palace. Four lots are
assigned to clock-hall, café, bakery and tool shop. No dedicated Tripo café mesh was
found in Content; that role needs a pack building or the prior authored shell.
All 26 road widths lack width tags and are **class estimates**, not measured widths.

Exactly one 30 MB Copernicus GLO-30 tile, N19/W156, was acquired and decoded. Its
GeoTIFF declares PixelIsPoint, which the sampler respects. The initial centred
1.5 km crop crossed the tile onto land; shifting the crop 160 m east resolved this
without a second tile or fabricated missing land. Final bounds are east -590..910 m,
north -750..750 m. The terrain has mild 9 m smoothing, blended pads, sea at 0 m,
synthetic submerged seabed and elevations -8..82.169 m. No vertical exaggeration.
This 30 m DSM includes structures and vegetation; it is not surveyed bare earth.

Both PNG and little-endian R16 are **1009 × 1009**. UE import mapping, component
counts, location and scale are in `Design/TownV2/terrain/metadata.json`. PNG/R16
values agree exactly, orientation roundtrips, and maximum encoding error is
0.00390625 m. No land is missing from the single tile. Visual review confirmed the
shoreline, source lot arrangement, labelled adaptation and uphill backdrop.
These checks establish data readiness with the stated width/DSM limitations;
they do not establish Unreal appearance or movement.

**Next:** begin Session 2 within the remaining bound: create only TownV2, import
this Landscape, then place the existing pack and Tripo buildings and capture it.
The old Town remains the baseline/fallback. No paid or publishing action occurred.

## Session 2 start — 2026-11-06, stopped at an empty-map checkpoint

Session 1 was verified before the first launch. Created and saved the separate
`/Game/Selene/Maps/TownV2`; then reloaded it successfully in the editor. The final
[engine checkpoint](../Saved/TownV2/session-2/checkpoint.json) confirms **zero actors
and zero Landscape actors**. **No landscape, roads, sea, plaza buildings or dressing
were placed.** This is an early Session 2 checkpoint, not a built-town result.

### Concrete blocker and bounded stop

The initial executable launch was successful, but computer use selected an older
empty Unreal project-browser window. Closed that empty browser normally, quit the
owned TownV2 editor using `SystemLibrary.quit_editor()`, and relaunched with the
app-bundle executable so computer use could select the correct Selene window.
The second window visibly showed TownV2 and zero actors. However, Landscape-mode
keyboard and mouse input repeatedly produced no UI transition, including after
raising/refocusing the window. The cause remains unresolved. No further import
or placement attempts were made after this repeated input failure, following the
brief's stop rule. **No existing running Selene was killed.**

Both launches used the Selene process guard, `/tmp/selene-unreal.lock`, a second
post-lock guard and a 780-second Perl alarm. The owned editor exited normally
before its alarm and the shared lock was released. A shell EOF appeared after the
first run because its helper file was edited while that shell was still active;
the final helper passes `bash -n`, and the second guarded launch/exits completed.
Future edits to the launch helper should happen only after its previous shell exits.

### Before/after, packs and performance

- **Before:** the prior accepted Town sheet remains the visual baseline:
  [after-verified-contact.jpg](../Saved/Town/session-1/after-verified-contact.jpg).
  This is the old Town and not a matched TownV2 camera comparison.
- **After:** unavailable. The new map is empty; no town/eye-level acceptance image
  was produced. Do not treat the Session 1 maps as Unreal renders.
- **FANTASTIC Village Pack:** installed, with 14 complete house blueprint candidates.
  **Placed this session: zero.** Its buildings and materials were not modified.
- **Existing Tripo:** clock-hall, shop-bakery-corner and shop-tool-repair meshes are
  installed and assigned in the layout. **Placed this session: zero.** A dedicated
  Tripo café mesh was not found; the draft uses a pack house for the café role.
- **Gaps:** no installed palms; Stylized Medieval City absent; PCG, palette,
  vegetation, landscape material, routes and movement verification remain pending.
- **FPS:** not measured. No frame-rate or visual-performance claim.
- The new map is **not** the default/startup map. DefaultGame, DefaultEngine,
  Source, the old Town and Blockout were not intentionally edited.

### Tools prepared, with execution status

- `town_run.sh`: adds the guarded `v2-editor` launch; existing stages retained.
- `town_v2_setup.py`: executed; creates/reloads only TownV2 and exposes a single-use
  local dispatch-file queue under Saved/TownV2/session-2.
- `town_v2_checkpoint.py`: executed; saved/reloaded TownV2, recorded its empty state,
  and quit the owned editor normally. `town_v2_quit.py` was used for the first exit.
- `town_v2_build.py`: **unexecuted draft**, syntax checked only. It requires a
  Landscape before mutation and refuses duplicate V2 actor placement. Its material,
  road/sidewalk and footprint-fitting API calls have not been runtime validated.
  It does not implement PCG or the full requested palette pass. Do not call this a
  verified builder or run it without inspecting its assumptions.

### Exact next step

Resolve native editor input / Landscape import in a fresh bounded session. Use a
normal guarded app-bundle launch; investigate the input mode before retrying the
same unresponsive controls. Load the existing empty TownV2 rather than recreating
it. Import `Design/TownV2/terrain/heightmap-ue.png` with **1009 × 1009 vertices,
63 quads/section, one section/component, 16 × 16 components**, location
**(-75000,-59000,0) cm**, scale **(148.80952381,148.80952381,100)**. Check three or
more world-space heights and the coastline against the source grid before placing
anything. Then validate the draft builder incrementally, place the plaza district,
add PCG and the style-B pass, capture plaza/shop/seafront/hills/aerial views, and
verify movement and actual frame timing. Keep old Town as the fallback until then.

### Final preservation and stop time

Stopped at approximately **17:48 PST**, within the 30-minute bound, because the
Session 2 failure rule triggered. [Final preservation verification](../Saved/TownV2/session-1/retry/preservation-final.json)
confirms **all 4,980 pre-existing protected files match**, with none missing.
This includes Config, Source, Design/Blockout, old Town and its external actors,
Fab pack assets and existing Tripo/character assets. The only new Content file is
`Content/Selene/Maps/TownV2.umap` (8,796 bytes). The editor has exited; no Selene
process or shared lock remains. Python syntax and helper shell syntax pass.
No commit, Fab download, purchase, paid generation, publication, Source edit or
startup/default-map change occurred. Acquisition was limited to the approved
OSM extracts and one Copernicus tile; primary documentation was read for the DEM
format and attribution. There is no paid submission/receipt to reconcile.

ORCH_OUTCOME {"version":1,"state":"partial","reason":"Session 1 site/layout/heightmap artifacts verified; Session 2 stopped at saved empty TownV2 after repeated native UI input failure","unmet_checks":["Landscape import","road splines, sea and plaza placement","pack and hero building placement","PCG and palette pass","eye-level captures","movement and FPS verification"]}

## Session 3 — 2026-11-06 — headless mesh-terrain checkpoint

Started **17:49:36 PST**; verified checkpoint **18:09 PST**, about 20 minutes.
**TownV2 is built, saved, reloaded and captured. This is a partial visual-quality
checkpoint, not a finished style-B plaza district.** The existing empty map was
loaded and populated; it was not recreated. No Landscape actor, editor UI,
computer use, download, purchase, paid service or commit was used.

### Built and placed

- **Terrain:** headless Blender meshes derived from the existing prepared
  Copernicus heightmap. A 300 × 300 m core uses a **2.5 m grid** (28,800 triangles);
  the 1.5 km backdrop ring uses a **10 m grid** (43,200 triangles), with the core
  hole removed. glTF import uses unit actor scale and the established north/east/up
  mapping. Imported bounds match the metre-to-centimetre contract. No vertical
  exaggeration; outer elevation remains approximately -8..82.17 m.
- **Ground:** `M_V2_TerrainAuto`, under `/Game/Selene/Materials/Ground/`, uses
  world-space triplanar sampling of existing `grass_07` and `ground_tiles_17`
  textures, a vertex-normal slope blend, and a sea-level sand blend. Its Nanite
  usage is saved and verified. Terrain and road meshes have complex-as-simple
  collision. There are **zero Landscape actors**.
- **Roads:** mesh ribbons for all **26 source road/path records**, retaining their
  source centre lines and estimated widths, with raised sidewalks and curbs.
  A mesh-only grading derivative smooths longitudinal road heights and blends
  shoulders over 5 m. Maximum local terrain adjustment is **2.160 m**; the source
  heightmap and canonical layout remain unchanged. Two explicit design paths link
  the plaza to the clock hall and café. Their coordinates and widths are recorded
  in `Design/TownV2/session-3-build.json`.
- **Sea/plaza:** water plane at **Z=0**, with a child of FANTASTIC Village's
  `MI_ENV_water`; the existing 29 × 20 m adapted plaza is paved.
- **Buildings:** **29 occupied lots**: **26 FANTASTIC Village houses** across 11
  variants (`BP_BLD_house_2` through `_12`) plus our Tripo **clock-hall,
  shop-bakery-corner and shop-tool-repair** on their assigned hero lots. The café
  hero lot uses `BP_BLD_house_5`, because no dedicated installed Tripo café mesh
  was found. Two clipped lots smaller than 25 m² remain unoccupied. Building
  replacements are fictional and do not reproduce Kona architecture.
- **Palette:** 11 material instances under `Environment/FabTints/` adjust the pack's
  exposed `Base Color Tint` parameters toward cream walls, petrol wood/trim and
  coral roof accents. Source pack materials and Tripo assets were not edited.
  The pack textures still strongly influence the visible result.
- **Scripted scatter:** 121 Village conifers, 26 Selene leafy street-tree
  assemblies, 72 grass patches, 24 lamps, eight potted plants, two Village benches,
  four Selene plaza benches and four Selene bins. These are deterministic authored
  actors, not a PCG graph or instanced foliage system. Storefront clutter remains
  minimal. The pack supplies 203 child rect-light actors, which need profiling.
- **Lighting/spawn:** retained the Selene time-of-day system at paused 15:00 with a
  5700 K sun treatment, softer sun angle, cool shadow grade and restrained bloom.
  PlayerStart is in the plaza. Saved a `V2Plaza` route and a tagged capture camera;
  runtime scripts move the camera without saving the map. Full movement features
  and MovementTest were not changed or exhaustively retested.

`Content/Stylized_Medieval_Town/` is now present, contrary to the previous session's
inventory. It was **not used or compatibility-validated**. FANTASTIC Village has
642 installed assets and no palms; no palms were placed. No additional content
was acquired.

### Before / after evidence and visual verdict

- [Starting fallback: old Town eye-level sheet](../Saved/TownV2/session-3/before-eye-level-sheet.jpg).
  TownV2 itself began empty, so this is a **different-map baseline**, not a matched
  TownV2 before capture.
- [First rendered TownV2 pass / before correction](../Saved/TownV2/session-3/after-camera-eye-level-sheet.jpg).
- [Final TownV2 eye-level sheet](../Saved/TownV2/session-3/after-graded-eye-level-sheet.jpg).
- [Final aerial](../Saved/TownV2/session-3/after-graded/06_aerial.png).
- Full-resolution final images and camera/performance manifest:
  `Saved/TownV2/session-3/after-graded/`. **6/6 captures succeeded**: plaza/clock,
  café, shop street, seafront, hillward street, aerial; 1280 × 720, 70° FOV, 15:00.
  Horizontal viewpoints and targets are fixed across TownV2 passes; final eye
  heights follow the graded ground, so camera Z is not identical across passes.

The final five eye-level images and aerial were visually inspected. Roads are
visible, the clock face faces the plaza, the repeated windmills are removed, and
source coastline/sea and graded terrain are visible. **The desired dense,
soft-cinematic coastal district is not yet achieved.** Broad empty lawns remain;
road/sidewalk junctions have overlapping edges and abrupt terminations; the café
still reads as a medieval house; dark pack roofs/windows compete with the Selene
heroes. The sea/sky are subdued and the low, bare backdrop is weak in the hillward
view. Tropical planting, closer street-front composition, fuller café dressing,
thresholds and a stronger lighting/sky pass remain work for the next session.
These are visible limitations, not hidden by the aerial or numeric checks.

Kailua-Kona remains the selected site for its curved seafront, shop strip and
palace/church anchors. Existing verified data previews remain:
[four-site comparison](../Saved/TownV2/session-1/site-comparison.png),
[layout versus OSM](../Saved/TownV2/session-1/layout-preview.png), and
[heightmap preview](../Saved/TownV2/session-1/heightmap-preview.png).
OSM/Copernicus attribution remains in `Design/TownV2/ATTRIBUTION.md`.

### Runtime, FPS and preservation verification

- **Actual plaza-to-clock walk: PASS.** From the saved PlayerStart, the pawn
  traversed approximately 59 m using normal AddMovementInput and character
  collision, reaching all three waypoints in **39.152 s**. All **187/187 samples
  were grounded**. No teleports. See
  [clock-walk.json](../Saved/TownV2/session-3/clock-walk.json).
  The capture harness also completed its short 4.44 m plaza walk.
- **Indicative offscreen -game throughput**, after a 45-second warmup, using world
  frame deltas during five-second stationary samples; screenshot frames excluded.
  Requested 1280 × 720, screen percentage 100, uncapped/VSync off:

  | View | Indicative fps | Mean frame delta |
  | --- | ---: | ---: |
  | Plaza / clock | 52.1 | 19.21 ms |
  | Café | 50.3 | 19.89 ms |
  | Shop street | 49.1 | 20.39 ms |
  | Seafront | 87.6 | 11.42 ms |
  | Hillward street | 47.8 | 20.92 ms |
  | Aerial | 59.3 | 16.85 ms |

  These are **game-delta throughput samples from editor binaries**, not GPU
  stat-unit measurements or a packaged benchmark. They do not establish 60 fps
  gameplay. See `after-graded/capture.json` for raw sample summaries.
- [Fresh readback](../Saved/TownV2/session-3/readback.json): **530 actors** including
  pack child actors, five imported meshes at unit scale, correct saved materials
  and collision, one PlayerStart, one camera, one route, four hero-role actors,
  zero Landscapes and zero underworld probe actors. No duplicate `V2_` labels.
  Pack child rect lights reuse display labels; this is reported separately and
  is not claimed to be a duplicate-free scene.
- [Final verification](../Saved/TownV2/session-3/verification-final.json): all
  **4,940 pre-existing protected SHA256 hashes match**, none missing. This covers
  Config, Source, Blockout, old Town/external actors, pack assets and original
  Tripo/character assets. Python syntax and shell syntax pass.
- Every Unreal launch used the pre-launch process guard, shared
  `/tmp/selene-unreal.lock`, a second post-lock check and a Perl alarm. No existing
  Selene was killed. All owned runs exited; the lock is released. Blender ran
  headlessly, one process at a time. No startup/default-map change was made.

### Diagnosed corrections and replay guidance

- Initial script fixes were limited to distinct diagnosed API issues: Transform
  expects a Rotator; runtime Python omits deferred camera spawning, so a saved
  camera is used; a material-usage reporting call was replaced with the supported
  readback API. The camera/map save had completed before that report-only error,
  so the mutation was **not replayed**.
- Imported mesh slots initially referenced unsaved generated materials. Bound
  them to saved Ground assets and saved each mesh once. Enabled/saved the new
  terrain material's Nanite usage. Final render loads show no corresponding
  missing-dependency, usage or material-compile warning.
- The first captures diagnosed reversed road top-face winding and inappropriate
  windmill-heavy fitting. Corrected winding once, replaced 15 mill variants once,
  and recaptured. A separate visible grading problem received one smoothing and
  shoulder-blending correction. Remaining junction/edge quality is deferred.
- Engine Toolset plugins log editor-only Python-class errors during `-game`
  initialization. They did not prevent the captures/walk. Those engine plugins
  were not edited.

Do **not** replay `town_v2_session3.py`, `town_v2_refine.py`, camera setup or grade
import over this checkpoint. They are recorded one-time stages and have duplicate
or receipt guards. The old `town_v2_build.py` is still the earlier unexecuted
Landscape draft and is not the Session 3 entry point. Continue with targeted
in-place changes. Current assets/placement provenance is in
`Design/TownV2/session-3-build.json`; stage reports/backups are in
`Saved/TownV2/session-3/`.

### Exact next session

Keep headless execution and the same capture manifest. Back up the current map and
Environment/Ground assets, then work only on the **plaza–café–clock triangle**:
merge overlapping road/sidewalk junction surfaces and provide deliberate curb
crossings; bring shop terraces, seating, planter beds and façade elements up to
street edges; make the café legible; reduce the medieval roof/wood dominance
through instance/child overrides. Profile the 203 pack rect-light children and
consolidate scatter. Improve sea/sky, broadleaf planting and the hillward sightline
using installed assets. Re-capture the same eye-level views, rerun the clock walk,
and add a café approach walk. Leave old Town as the fallback until visual quality
and wider movement/performance are accepted.

No paid or externally visible step occurred; there is no paid submission or
receipt to reconcile.

ORCH_OUTCOME {"version":1,"state":"partial","reason":"Headless TownV2 plaza foundation saved and verified with six captures and a grounded plaza-to-clock walk; visual finish remains incomplete","unmet_checks":["dense coastal style-B plaza quality","polished road junctions and storefront thresholds","tropical planting and finished sea/sky/backdrop","full advanced-movement regression and packaged GPU performance"]}


## Session 4 — 2026-11-06 — buildings and ground, headless checkpoint

Started **18:24 PST**; verified **18:41 PST**. Saved `/Game/Selene/Maps/TownV2`,
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
| way/198653703 | townhouse-terrace | ivory | -29.0 |
| way/260244425 | townhouse-terrace | cream | 180.0 |
| way/289193785 | townhouse-terrace | sand | 400.0 |
| way/289193790 | townhouse-terrace | petrol | 328.2 |
| way/455896316 | clock-hall — clock-hall | coral | 177.9 |
| way/494460070 | apartment-curved | ivory | 55.8 |
| way/552608374 | townhouse-terrace | cream | 146.7 |
| way/552608375 | shop-bakery-corner | sand | 360.0 |
| way/663900821 | shop-bakery-corner — bakery | petrol | 138.5 |
| way/663900822 | townhouse-terrace | coral | 44.5 |
| way/663900823 | shop-bakery-corner | ivory | 44.4 |
| way/831071357 | townhouse-terrace | cream | 75.4 |
| way/831071358 | townhouse-terrace | sand | 255.4 |
| way/831071359 | workshop-garage | petrol | 254.8 |
| way/831077550 | townhouse-terrace | coral | 434.9 |
| way/831077551 | apartment-curved | ivory | 432.5 |
| way/831077552 | townhouse-terrace | cream | 0.0 |
| way/831077554 | townhouse-terrace | sand | 73.7 |
| way/831077555 | apartment-curved | petrol | 431.4 |
| way/831077556 | townhouse-terrace | coral | 73.7 |
| way/831077557 | apartment-curved | ivory | 148.4 |
| way/831077558 | townhouse-terrace | cream | 146.9 |
| way/831077559 | townhouse-terrace | sand | 418.0 |
| way/1296717081 | shop-tool-repair — cafe | petrol | 90.0 |
| way/1296717082 | shop-tool-repair — tool-shop | coral | 58.7 |
| way/1331478424 | townhouse-terrace | ivory | 428.2 |
| way/1452659412 | shop-bakery-corner | cream | 244.2 |
| way/1452659413 | shop-bakery-corner | sand | 242.4 |
| relation/11356594 | workshop-garage | petrol | 417.2 |

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
50.26 s; 244/244 samples grounded; no teleports.**
The first walk also passed before refinement. The final walk follows the corrected
paving and court geometry. The subsequent tree-only sightline correction changes
only two non-colliding tree components; captures and fresh readback verify that
last saved map. Full advanced movement and interiors were not regression-tested.
Evidence: [final walk](../Saved/TownV2/session-4/plaza-shop-walk-final.json).

| View | Before fps | Final fps | Final mean ms |
| --- | ---: | ---: | ---: |
| 01_plaza_clock | 52.1 | 52.0 | 19.22 |
| 02_plaza_cafe | 49.6 | 50.1 | 19.98 |
| 03_shop_street | 48.5 | 46.2 | 21.64 |
| 04_seafront | 87.4 | 86.9 | 11.51 |
| 05_hills | 47.8 | 43.6 | 22.91 |
| 06_aerial | 59.1 | 56.3 | 17.76 |

These are **indicative offscreen -game world-frame-delta throughput samples** from
editor binaries, after a 45-second warmup and during five-second stationary samples,
with screenshot frames excluded, VSync/frame cap off and screen percentage 100.
They are not packaged GPU/stat-unit timings and do not prove 60 fps gameplay.
Added geometry and plant groups have a measurable cost; no performance improvement
is claimed despite removal of cottage lights.

### Verification, diagnosed fixes and preservation

- [Fresh final readback](../Saved/TownV2/session-4/readback-final.json):
  **554 actors**, 29 recorded Tripo building actors, four new ground meshes
  with complex-as-simple collision and saved material bindings, zero Village house
  classes, zero rect lights, zero duplicate V2/V4 labels and zero superseded road
  actors. All per-instance tints read back from saved materials.
- [Final verification](../Saved/TownV2/session-4/verification-final.json):
  **4,940/4,940 protected SHA256 hashes match**. Config, Source, old Town,
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
  All owned runs exited normally; final process inspection found no Selene process
  and the shared lock was released (`session-4/process-final.json`).
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

ORCH_OUTCOME {"version":1,"state":"partial","reason":"All 29 Tripo building replacements and paved ground checkpoint saved with matched captures and grounded shop walk; dense courtyard visual finish remains incomplete","unmet_checks":["dense finished courtyard and frontage composition","final plinth and district-edge detailing"]}


## Session 5 — 2026-11-06 — plaza block tightened, headless checkpoint

Started **19:45 PST**; verified **20:04 PST**. Continued the saved Session 4
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
**175.0 cm**; the character is the roughly
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
- The separate scale-reference camera initially aligned behind a lamp post. Moved
  only that runtime camera once; the clear capture supersedes `scale-reference/`.
  The saved map and grounded walk did not change.
- Local contact-sheet helper initially used a Python without Pillow; reused the
  existing read-only installed-wheel wrapper, without installing anything.
- The walk game completed successfully, but its launcher reported a trailing shell
  parse error because the helper file had been extended while that shell was active.
  Reconciled the completed walk JSON and normal game shutdown; did not replay it.
  Finished helper edits while idle and verified `bash -n`; subsequent guarded
  launches completed with the fixed helper. The lock trap released correctly.

### Grounded walk and indicative fps

**7/7 original waypoints reached in 50.31 seconds; 244/244
samples grounded**, using normal AddMovementInput and CharacterMovement collision
from PlayerStart. No teleports and no waypoint changes. Evidence:
[plaza-shop-walk-final.json](../Saved/TownV2/session-5/plaza-shop-walk-final.json).
This checks that route, not all entrances, garden gates or advanced movement.

| View | Before fps | Final fps | Final mean ms |
| --- | ---: | ---: | ---: |
| 01_plaza_clock | 54.3 | 54.1 | 18.50 |
| 02_plaza_cafe | 51.7 | 69.8 | 14.33 |
| 03_shop_street | 48.2 | 51.5 | 19.41 |
| 04_seafront | 97.2 | 96.7 | 10.34 |
| 05_hills | 45.5 | 42.6 | 23.46 |
| 06_aerial | 58.6 | 61.7 | 16.21 |
| 07_shop_from_plaza | 58.9 | 59.1 | 16.93 |
| 08_plaza_block_aerial | 47.9 | 45.3 | 22.08 |

These are indicative offscreen `-game` world-frame-delta throughput samples from
editor binaries, with a 45-second warmup, five-second stationary samples, screenshot
frames excluded, VSync/frame cap off and screen percentage 100. They are not packaged
GPU/stat-unit measurements and do not establish 60 fps gameplay.

### Preservation and remaining gaps

Fresh readback: **749 actors, 33 building actors**, three new garden
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

ORCH_OUTCOME {"version":1,"state":"partial","reason":"Saved and verified tighter cafe/shop frontage, gardens and entrance detailing with eight matched views and grounded walk; complete plaza enclosure remains unfinished","unmet_checks":["dense finished enclosure across the entire plaza block","consistent doorway and storey proportions in existing Tripo shells"]}


## Session 6 — 2026-11-07 UTC — seaside buildings placed and verified

Started **23:37 PST on November 6**; verified **23:56 PST**. Continued the saved
Session 5 map. No previous one-time apply/refine/correction script was replayed.

### Saved result and asset setup

- Backed up **111 existing allowed files**, including TownV2 and the four
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
  Final map contains **773 actors and 35 building instances**.
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
- **5,129/5,129 protected file SHA256 hashes match**, including
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

The accepted saved map reached **7/7 unchanged waypoints in 50.34 s**;
**237/237 samples grounded**. Normal AddMovementInput
and CharacterMovement collision from PlayerStart; no teleports. The first candidate
walk also passed and is preserved separately.
[Final walk](../Saved/TownV2/session-6/plaza-shop-walk-final.json).

| View | Before fps | Final fps | Change | Change % |
| --- | ---: | ---: | ---: | ---: |
| 01_plaza_clock | 32.6 | 30.7 | -1.9 | -5.8% |
| 02_plaza_cafe | 42.2 | 38.4 | -3.8 | -9.0% |
| 03_shop_street | 34.5 | 32.0 | -2.5 | -7.2% |
| 04_seafront | 62.9 | 49.5 | -13.5 | -21.4% |
| 05_hills | 31.5 | 27.9 | -3.7 | -11.6% |
| 06_aerial | 41.0 | 34.4 | -6.6 | -16.0% |
| 07_shop_from_plaza | 40.9 | 36.6 | -4.3 | -10.6% |
| 08_plaza_block_aerial | 28.8 | 26.5 | -2.4 | -8.3% |
| 09_lighthouse_from_seafront | 46.3 | 42.5 | -3.8 | -8.2% |

Across the original eight views, equal-view-weighted mean frame time changes from
**26.81 to 30.01 ms**, equivalent to **37.3 → 33.3 fps
(-10.7%)**. These are indicative offscreen editor `-game` world-frame-delta
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

ORCH_OUTCOME {"version":1,"state":"delivered","reason":"Three seaside buildings saved in TownV2 with four-asset Nanite/collision setup, matched captures, lighthouse sightlines, grounded walk and fps comparison"}


## Session 7 — 2026-11-07 UTC — six city buildings saved; skyline framing incomplete

Started **07:58 UTC**; completed **08:20 UTC**. Continued the saved Session 6
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
| metro-walkup | (280.0, 22.0, 16.615) | 0 | 18.265 |
| metro-brownstones | (280.0, 48.0, 17.429) | 0 | 17.429 |
| metro-lane-houses | (280.0, 70.0, 17.669) | 0 | 17.669 |
| metro-diner | (280.0, 90.0, 19.981) | 0 | 19.981 |
| artdeco-tower | (326.0, 32.0, 19.061) | 180 | 19.061 |
| metro-glass-office | (326.0, 87.0, 24.368) | 180 | 24.368 |

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
50.28 s**, with **238/238 samples grounded**.
Normal AddMovementInput and CharacterMovement collision from PlayerStart;
no teleports and no waypoint changes. [Walk evidence](../Saved/TownV2/session-7/plaza-shop-walk-final.json).

Separate runtime trials walked the full town-to-city connection and each of the
six frontage ramps: **7/7 trials succeeded**, **791/791 sampled frames grounded**.
The pawn was positioned at each trial's start, then walked normally with collision;
this is independent of the original walk. Targets reach the exterior aprons;
interior navigation and every baked doorway/stair tread were not tested.
[Approach evidence](../Saved/TownV2/session-7/front-approaches.json).
The steepest new ramp is **23.21 degrees**, on the hillside approach network.

### Indicative fps change

| View | Session 6 final fps | Fresh before fps | Session 7 final fps | Vs Session 6 | Vs fresh before |
| --- | ---: | ---: | ---: | ---: | ---: |
| 01_plaza_clock | 30.7 | 41.5 | 37.2 | +21.1% | -10.3% |
| 02_plaza_cafe | 38.4 | 53.3 | 48.0 | +24.7% | -10.1% |
| 03_shop_street | 32.0 | 41.7 | 38.2 | +19.3% | -8.4% |
| 04_seafront | 49.5 | 68.5 | 61.3 | +24.0% | -10.5% |
| 05_hills | 27.9 | 34.3 | 31.6 | +13.6% | -7.8% |
| 06_aerial | 34.4 | 47.1 | 43.0 | +24.9% | -8.7% |
| 07_shop_from_plaza | 36.6 | 46.5 | 44.1 | +20.5% | -5.3% |
| 08_plaza_block_aerial | 26.5 | 34.2 | 30.6 | +15.6% | -10.6% |
| 09_lighthouse_from_seafront | 42.5 | 54.0 | 50.6 | +18.9% | -6.3% |

Across the original eight views, equal-view-weighted mean frame time corresponds
to **33.3 → 39.9 fps vs Session 6
(+19.8%)**. The fresh same-session baseline was
**43.8 fps**, so the before/after change within this session is
**-8.9%**. The large baseline difference between
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

ORCH_OUTCOME {"version":1,"state":"partial","reason":"Six-building preview saved and verified; clear plaza skyline framing remains incomplete after one camera correction","unmet_checks":["Clear plaza skyline framing"]}
