# Selene checkpoint 1: data-driven graybox

`layout.json` is the source of truth. This is massing, circulation and interior-access material for human review; it makes no finished-art or performance claim. The four images in `concepts/town-style-study-01/` were inspected: the clock landmark, elevated rail, framed shopfronts, rounded building corners and stepped residential lanes inform this layout. The north overlook looks back toward the plaza and tower. R1's final window-seat view looks toward the tower through the café's east storefront.

| Area | Planning envelope, E–W × N–S | Lots | Hero façades | Interiors |
| --- | --- | ---: | ---: | --- |
| Plaza | 140 × 110 m; paved core 75 × 60 m | 6 | 4 | Café 14 × 12 m, 4.2 m clear; clock-hall concourse 34 × 22 m, 7 m clear |
| Commercial | 220 × 180 m; 199.4 m diagonal main street | 16 | 2 | None |
| Residential A | 160 × 140 m; 0–28 m hillside | 20 | 1 | One optional townhouse ground floor, 20 × 14 m |
| Residential B | 150 × 120 m; flattened at +4 m | 8 | 1 | None |
| Industrial | 170 × 120 m | 7 | 2 | Workshop 20 × 14 m, 6 m clear |
| Total | 480 × 400 m terrain | 57 | 10 | Three required, one optional |

Dimensions of interiors describe outer shells; clear width/depth are reduced by 0.25 m walls on each side. Residential A has five stepped rows of four units at +8/+13/+18/+23/+28 m. Residential B has eight approximated curved-corner blocks, alternating four/five storeys. Industrial has the workshop, five sheds and a rail depot below the viaduct. Building height is `ground_height + (storeys - 1) * floor_height`; normal floors use 4.2/3.5 m, with explicit taller workshop and double-height concourse exceptions.

## Coordinate and import contract

All JSON positions and dimensions are **metres**. Origin is the plaza centre; layout `x` is east, `y` north, `z` up. Positive rectangle rotation is counterclockwise from east in this plan. Local rectangle `+x/+y` rotate with the footprint; door wall names refer to **local** north/south/east/west.

Unreal is left-handed: X forward, Y right, Z up. We choose **UE +X north and UE +Y east**. Convert layout `(x,y,z)` to UE `(100*y,100*x,100*z)` cm. A footprint angle `a` becomes UE yaw `90-a` degrees. Route distances and segment boundaries become centimetres; route splines use linear point types so cumulative lengths match the JSON polylines.

Blender mesh vertices are baked as `(y,-x,z)` metres, with unit scale 1. Blender's Y-up glTF exporter maps this to glTF `(y,z,x)`. UE 5.8 Interchange's GLTF `ConvertVec3` swaps glTF Y/Z, yielding UE `(y,x,z)`; its metre-to-centimetre import yields the same mapping as the builder. Spawn the terrain at zero with **unit actor scale and zero rotation**, with no extra 90-degree correction. The builder refuses a terrain whose imported horizontal half-extents differ from UE X=20,000 cm / Y=24,000 cm. UV0 spans the full layout footprint once.

## Schema v2

The schema is enforced procedurally by the stdlib validator. V2 uses **rect+rotation footprints**, not arbitrary polygons. `layout_core.polygon()` converts rectangles into convex polygons for SAT checks and plotting. Unknown descriptive keys are allowed; required shape/type/range and geometric checks are in `validate_layout.py`.

| Key | Contract |
| --- | --- |
| `schema_version`, `name`, `units`, `axes` | Version 2, descriptive title, `metres`, `east,north,up` |
| `terrain.bounds` | `[min_x,min_y,max_x,max_y]`; all lots and route/corridor points must lie inside |
| `terrain.grid` | Mesh grid spacing, 2–4 m; current 2.5 m |
| `terrain.height_model` | `north_ramp`: 0 below `start_y`, linear to `rise` at `end_y`, then constant |
| `terrain.pads[]` | Rectangles with `center:[x,y]`, `size:[w,d]`, optional `rotation`, fixed `z`, `blend` distance and optional `margin` |
| `areas[]` | Unique `id`, `label`, rect `center/size`, `color:#RRGGBB`; planning envelopes may overlap and are not parcels |
| `lots[]` | Unique `id`, valid `area`, `footprint:{center,size,rotation}`, integer `storeys`, boolean `hero`, `base_z`, `ground_height`, `floor_height`; optional `corner_radius`, `landmark`, `interior` |
| `interior` | `clear_height`, `wall_thickness`, boolean `optional`, `openings[]`, `props[]`; roof sits above clear height; unused upper storeys are solid massing |
| `openings[]` | Local `wall`, along-wall `offset` from centre, `width`, `height`, `sill` above floor, `kind:door/window`. Doors have sill 0; windows get translucent non-colliding placeholders. Walls are split around openings, never a solid cube with a fake door pasted on |
| `props[]` | Simple counter/gate/seat blocks: `id`, local XY `center`, `size:[w,d,h]`; bottom on floor |
| `slabs[]` | `id`, `area`, rect `center/size`, top elevation `z`, `kind`; plaza, terrace, side square, yard, garden, overlook |
| `streets[]` | `id`, `area`, `points:[[x,y,z],...]`, `width`, `kind`; heights interpolate linearly. Service lane is a 3 m strip inside the 14 m pedestrian street |
| `stairs[]` | `id`, `area`, 3D `points`, `width`, `max_riser`; step count is ceil(rise/max_riser), current maximum 0.17 m |
| `viaduct` | Two 3D `points`, `width`, `deck_thickness`, `pier_spacing`, `pier_size`, `exclude_piers:[[min_x,max_x],...]` for crossings/depot. Deck surface is +12 m on the flat north-plaza corridor |
| `boundaries[]` | South/west edge polylines and `embankment_depth`; terrain-following retaining blocks, posts and two rails |
| `backdrop` | `center:[x,y,z]`, 2D `size`, `collision:false`, optional rectangular `west_extension`; distant bay proxy only |
| `routes[]` | Unique R1/R2/R3 `id`, `points`, `length_range:[min,max]` metres, `segments`, optional `look_at:[x,y,z]`. A 2D point follows final terrain height; a 3D point is an **absolute feet/floor elevation**. The builder samples the feet path at most every 25 cm (5 cm near stairs), follows terrain and constructed paving/treads, and accounts for lower-hemisphere contact near riser edges. Authored indices remain segment boundaries after resampling. Capsule half-height and camera offsets belong to the character |
| `segments[]` | `tag` unique per route (case-insensitive), `category:exterior/doorway/interior`, `start_index`, `end_index`; contiguous spans covering every route edge. Converted to cumulative 3D centimetre distances on `SelenePerfRoute` |
| `player_start` | Absolute capsule-centre `position:[x,y,z]`, `look_at:[x,y,z]` |
| `east_west_walk` | Separate full-width traversal `points`, `speed:1.5`, `expected_minutes:[5,6]`; horizontal open corridor south of plaza |

Terrain evaluation order is deterministic and shared by Blender, map rendering and routes: north ramp; explicit pads in order with smoothstep shoulders; derived flat lot pads (`base_z`, 0.8 m margin, 2 m blend); street ramps; then stair ramps. Corridors have 2 m blending shoulders outside their half-width. The final height supports step boxes, while their upper faces form the walkable treads. Lot pads and streets must stay clear of solid buildings; the validator checks complete corridor widths against solid footprints.

The validator checks malformed fields, duplicate IDs, finite coordinates, footprint bounds, lot/lot SAT overlap, street/stair intrusion into solid lots, count targets, opening bounds/overlaps, unique segment tags and valid categories, sampled capsule footprint/height and eye clearance through shell doors, route length ranges and the 5–6 minute crossing. These are plan-level checks; they do not substitute for a player capsule sweep or human review.

## Run from the project root

```sh
python3 Tools/Blockout/validate_layout.py
uv run --with matplotlib python Tools/Blockout/render_map.py
```

The map defaults to `Design/Blockout/map.png`; `--layout` and `--out` override inputs/output. It shows area envelopes, lot storeys, hero stars, required/optional interior markers, doors, contours, stairs, rail, route arrows, north arrow and a 50 m scale. Regenerate it locally; the PNG is intentionally excluded from the handoff.

On this Mac, `/opt/homebrew/bin/blender` points at a binary that could not find its bundled Python. The app binary works:

```sh
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
"$BLENDER" -b --factory-startup --python Tools/Blender/terrain_from_layout.py -- \
  --layout Design/Blockout/layout.json --out "$PWD/Saved/Blockout/Terrain"
```

Outputs: `terrain.blend`, `terrain.glb`, `terrain-report.json`. `--factory-startup` avoids loading user scene/add-on state. The requested plain `blender -b --python ... -- ...` form also works when the `blender` executable has an intact resource path.

Compile and build:

```sh
ENGINE='/Users/Shared/Epic Games/UE_5.8'
"$ENGINE/Engine/Build/BatchFiles/Mac/Build.sh" SeleneEditor Mac Development \
  -Project="$PWD/Selene.uproject" -WaitMutex

export SELENE_LAYOUT="$PWD/Design/Blockout/layout.json"
export SELENE_TERRAIN_GLB="$PWD/Saved/Blockout/Terrain/terrain.glb"
"$ENGINE/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
  -run=pythonscript -script="$PWD/Tools/Unreal/build_blockout.py" \
  -unattended -nop4 -nosplash -nullrhi \
  -abslog="$PWD/Saved/Blockout/build.log"
```

`-nullrhi` is useful for a construction audit; omit it for later rendering tests. No GUI, browser, MCP server, asset pipeline or ledger is required. If the project's prototype materials are absent, the builder creates its own world-space grid parent; otherwise it uses `/Game/LevelPrototyping/Materials/M_PrototypeGrid`. Per-area persistent MIs are saved under `/Game/Selene/Blockout/Materials`. Never assign transient MIDs to saved actors. Generated geometry uses `/Engine/BasicShapes/Cube`, except the imported terrain.

The first build uses `LevelEditorSubsystem.new_level(..., False)`, an empty **non-World-Partition** map. Rebuilds remove only actors bearing `SeleneBlockout`; unrelated actors are retained. This map is generated content: do not hand-edit tagged actors expecting the changes to survive. Materials and the imported terrain are reused/reimported at stable package paths. A rebuild may produce new actor GUIDs/external filenames; idempotence means the same scene, labels, counts and paths, not binary-identical packages. Import/schema errors fail the commandlet and write `Saved/Blockout/report.json`. Asset mutation is not transactional; rerun a failed build before reviewing it.

The report records engine/version, input SHA256 hashes, actors and lots per area, terrain bounds, route lengths and cm segment spans, class/material warnings and save status. Conditional integration uses `/Script/Selene.SelenePerfRoute`, its `Route` spline, `route_name` and a struct-array conversion from `{tag,category,start_distance,end_distance}` dictionaries. `/Script/Selene.SeleneTimeOfDay` is likewise loaded dynamically. Absent classes are warnings, not build failures; fallback sun/sky/atmosphere are spawned. R1 and R3 also get start/end review cameras aimed at `look_at`. These cameras use the native character eye height. The same targets are serialized as endpoint `view_keys` on each performance route; the runner interpolates them by distance independently of movement yaw. Town also explicitly selects `SeleneGameMode` in World Settings.

## External actors in UE 5.8.4

The local Python capability probe confirmed `Level` exposes neither `set_use_external_actors` nor `convert_all_actors_to_packaging`. `Engine/Classes/Engine/Level.h` declares their C++ counterparts without `UFUNCTION`. The editable flag alone would not convert existing actor packages, so the builder reports this limitation instead of claiming OFPA is complete.

The stock, **tested** alternative is:

```sh
"$ENGINE/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
  -run=ConvertLevelsToExternalActors /Game/Selene/Maps/Town \
  -nosourcecontrol -unattended -nop4 -nosplash -nullrhi \
  -abslog="$PWD/Saved/Blockout/ofpa.log"
```

This converts the existing non-partitioned map to OFPA. `-nosourcecontrol` is required for this commandlet, independently of `-nop4`. A later builder run detects the flag and counts actual external packages. If the engine exposes full conversion methods in future, the builder can use them directly.

Read-only engine and saved-map diagnostics:

```sh
"$ENGINE/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
  -run=pythonscript -script="$PWD/Tools/Blockout/probe_unreal.py" \
  -unattended -nop4 -nosplash -nullrhi
"$ENGINE/Engine/Binaries/Mac/UnrealEditor-Cmd" "$PWD/Selene.uproject" \
  -run=pythonscript -script="$PWD/Tools/Blockout/verify_unreal.py" \
  -unattended -nop4 -nosplash -nullrhi
```

## Verification and review limits

Final verification results are recorded below after the headless run. Generated Content, maps, material instances, terrain binaries and the map PNG are not part of the source handoff. Blender outputs and Unreal reports/logs live in ignored `Saved/Blockout/` for local inspection.

A human checkpoint still needs an editor/player walk through the café, concourse, workshop, hillside stairs and overlook. Null-RHI construction does not validate lighting, visual resemblance, runtime performance, camera motion or capsule clearance. The parallel performance-route/time-of-day C++ classes were absent from this worktree, so their successful integration remains to be verified after merge.

Verified in this worktree on UE **5.8.4** and Blender **5.2.0 LTS**:

- `SeleneEditor Mac Development` compiled successfully.
- The validator passed the final layout and rejected seven mutated invalid inputs: malformed schema, overlapping lots, out-of-bounds lot, route length, oversized door, invalid walk speed and a corridor through solid lots. Python compilation and Ruff's undefined/unused-name checks passed.
- The map PNG was regenerated and visually inspected for labels, routes, scale and north orientation.
- Blender produced a 2.5 m terrain grid: **31,073 vertices / 30,720 quads**, elevation **0–28 m**, UV0, `.blend` and GLB. The sidecar records a digest of all terrain-affecting inputs; the builder rejects stale terrain when that digest is present. Route/material-only edits do not invalidate the terrain digest.
- Interchange imported the GLB at the expected UE half-extents **X 20,000 / Y 24,000 / Z 1,400 cm**. The map saved and reloaded successfully.
- Builds with the supplied prototype grid and with that content removed both succeeded. The latter constructed the procedural grid fallback and persistent area MIs; shader appearance was not rendered.
- The stock external-actors conversion succeeded. Subsequent rebuilds preserved OFPA. Final reload found **893 unique generated actor labels and 893 external generated actors**, with no World Partition. Five floor locations and five doorway/exit segments passed geometric checks against the saved cube transforms. All R1/R2/R3 camera-centre segments cleared the colliding cube geometry; the café seat sightline exited through its storefront. Terrain collision serialized as complex-as-simple.
- Final lengths: **R1 92.26 m; R2 1,406.42 m; R3 25 m**. Full-width E–W plan traversal: **480 m / 1.5 m/s = 320 seconds = 5 minutes 20 seconds**. This is a distance/speed calculation, not a timed gameplay recording.

`Saved/Blockout/report.json`, `verification.json`, `Terrain/terrain-report.json`, the build/conversion logs and `map-reviewed.png` preserve local evidence. Generated `Content/`, including copied prototypes, and `Design/Blockout/map.png` were removed from the handoff. Unreal's automatic Android File Server config addition was restored. No commit or push was made.

## Integration contract update

Schema v2 migrates authored route Z values from camera elevations to feet elevations and removes `eye_height`. The native character currently has a 34 cm capsule radius, 87.5 cm half-height and a first-person eye 64 cm above its centre (151.5 cm above feet). `verify_unreal.py` reads these dimensions from the class default object and checks saved route coordinates, categories, view targets, sampled capsule volume and eye segments against colliding cubes. The geometric check permits 3 cm contact tolerance. It is not a runtime capsule sweep or a third-person spring-arm/visibility test. Historical results above describe the prior eye-path implementation.


## Second integration fix round

`layout_core.TerrainSurface` now defines the exported grid and explicit SW–NE
triangles. Blender exports those triangles directly, and the terrain digest
includes the triangulation version to invalidate old quad exports. Route feet
use exact lower-hemisphere support over nearby triangle faces and edges, plus
the existing paving/stair contact. This includes capsule radius on slopes.

The saved-map audit checks terrain identity, collision and actor transform,
then samples capsule support against the shared triangle surface at intervals
of at most 5 cm along each serialized linear route segment. It reports the
maximum vertical terrain penetration per route, a conservative bound on radial
capsule penetration, and rejects values over the existing 3 cm tolerance.
It also exercises the compiled native camera function every 5 cm: unkeyed
pitch must stay within ±25° and change by less than 3° per sample; authored
look-at keys must still aim at their exact targets. These are headless geometry
and camera-function checks, not a gameplay physics or rendered camera test.

Verified on UE 5.8.4 / Blender 5.2.0 LTS in this fix round:

- Editor Development and Shipping both returned `Result: Succeeded` (final
  incremental builds: 9.45 s / 14.05 s; full builds: 32.42 s / 38.30 s).
- `python3 Tools/Perf/test_summarize.py`: 14 tests, OK. Missing verification,
  integer `1`, and string `"true"` all produce INVALID; fixtures use boolean true.
- `python3 Tools/Blockout/validate_layout.py`: VALID, 57 lots / 10 heroes;
  R1 92.27 m, R2 1411.46 m, R3 25.00 m; E–W traversal 320.00 s.
- Export: 31,073 vertices / 61,440 triangles. Independent GLB decoding matched
  every shared triangle; maximum vertex error was 0.000000949 m.
- Headless build, capability probe and saved-map verification succeeded with
  894 generated actors. Capsule samples: R1 2,223; R2 40,399; R3 600.
  Maximum sampled vertical terrain penetration: R1 0 cm; R2 0.099499 cm;
  R3 0 cm (3 cm tolerance). Cube, doorway and eye checks also passed.
- At [38, 133.7], feet are now 22.284745 m; the old 22.1667 m feet fail the new
  capsule/terrain audit with an 11.8045 cm vertical support deficit.
- R2 native view pitch peaks at 23.0634°, with maximum change 0.6589° per
  5 cm of spline travel. At [38, 158.15], the raw 81.7537° tangent becomes
  a 10.4813° view pitch. Both keyed routes retained their exact look-at targets.

Commandlets reported the expected missing mannequin animation warning in this
source-only checkout; no gameplay or rendered camera validation was performed.
Generated test content (including copied prototypes), build artifacts and logs
were removed afterward, and Unreal's automatic config addition was restored.
