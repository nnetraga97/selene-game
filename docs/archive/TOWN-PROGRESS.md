# Town presentation progress

## Session 1 — 2026-11-06, verified checkpoint

Session began at 15:39 PST. This checkpoint contains a saved and reloaded Town map, ten matched before/after views, and a successful live R1 capsule walk. It is a **partial Phase 1 checkpoint**, not the finished style-B town. The stat-unit performance requirement remains incomplete.

### Done

- Unified the streets, plaza, café terrace, sidewalks, curbs and gutters around the existing `ground_tiles_27` texture and world-space ground parent. New material instances control tone, roughness, normal strength and scale; the blue cobble/cream material clash is removed. Original source assets were not edited.
- Imported a free Blender curb and retaining-wall kit into `/Game/Selene/Environment/Kit/`. Added 20 main-street curb sections, 20 gutter strips, matching sidewalks, six plaza curb sections, a flush plaza crossing, and ten restrained road-wear decals. Curbs are 18 cm tall and 32 cm wide; R1 crossing gaps remain open.
- Added a soil fade around the plaza/café paving, planted beds, and 24 retaining-wall sections at the first hillside terrace. Existing stair geometry and route grades remain; the stair materials now match. A continuous, non-colliding Blender terrain skirt softens the outer map boundary. The inner hillside pads still need shaping.
- Added eight trees, six bench/bin pairs, five planter/flower compositions, street pots, small flower rows, a scooter and five posts using existing wall-lantern assets. These are authored placements; no runtime PCG or paid generation was used. A later pass should consolidate repeated small foliage into instances.
- Replaced the café's diagnostic grid appearance with cream surfaces, petrol window trim, a coral canopy and original café sign. Turned the existing vending-machine assembly toward its customers. Added two warm interior practical lights.
- Kept the existing time-of-day system and curves. Added a 5700 K sun temperature treatment, softer sun angle, cool shadow fill/grade and bloom 0.18. No day/night rewrite. Dusk and night acceptance are deferred.

The final map contains **274 session actors**, all saved as external actors. A fresh reload found **no duplicate labels**, no rejected sphere mounds, one continuous terrain skirt, two practical lights, and the correct café terrace paving. See `Saved/Town/session-1/saved-verification.json`.

### Before and after sheets

- **Before:** [before-contact.jpg](../Saved/Town/session-1/before-contact.jpg)
- **Accepted after:** [after-verified-contact.jpg](../Saved/Town/session-1/after-verified-contact.jpg)
- Full-resolution originals: `Saved/Town/session-1/before/` and `Saved/Town/session-1/after-verified/`.

Each set has eight eye-level views, the overlook and one aerial. The camera manifests are identical: noon, 75° FOV, 1920 × 1080, identical positions and targets. Both capture reports record 10/10 images. The individual images and final contact sheet were visually reviewed. The earlier `after/` and `after-final/` folders are **rejected candidates**, marked with `REJECTED.txt`; do not use them as the checkpoint.

### Verification and performance limits

- Existing layout validator: PASS, 57 lots / 10 hero lots, R1 92.27 m. Existing dressing validator: PASS, 48 original placements / 53 building replacements. The new presentation layer is separate from that original dressing data.
- **Actual runtime R1 walk: PASS.** The 34 cm-radius / 87.5 cm-half-height character capsule reached all nine authored waypoints in **60.54 seconds**, including the café doorway and interior endpoint. After one initial positioning, the helper used normal `AddMovementInput` and `CharacterMovement` collision; it did not teleport along the route. All 553 recorded movement samples were grounded. Evidence: `Saved/Town/session-1/walk-python/report.json`.
- The existing `-PerfRoute` harness exits on `/Temp/Untitled_0` before Town starts, with `World destroyed before capture completed`. Older local perf runs contain the same failure. `Source/**` is outside this session's permission scope, so it was not changed. A single Python movement driver bypassed that startup-harness defect for the walk check.
- **No valid stat-unit performance comparison.** `stat unit` was enabled, but AutomationLibrary returned unavailable counters. Enabling the Engine stat group did not resolve it; retries stopped. The recorded Slate callback intervals were 22.75 / 17.70 / 18.57 ms before and 8.62 / 8.44 / 8.46 ms after for plaza / café / main street. These are **not GPU or reliable rendered-frame timings** and do not prove an improvement. The frame-time jump is **unknown**. No 60 fps or packaged-performance claim is made.
- 424 pre-existing protected files under Config, Source, source Assets and Characters matched their starting SHA256 hashes at the final check. Content modification-time inspection before the concurrent import found no changes outside allowed Content roots. No commits, downloads, purchases or paid generation.

### Backup and diagnosed corrections

- Before the first map edit, copied Town, its external actors/objects and the original Ground assets to `Saved/Town/session-1/backup/`; `manifest.json` records 1,048 hashes.
- Rejected and removed the separate sphere berms after the aerial showed an artificial row of balls. Replaced them with one continuous Blender skirt. Corrected the café terrace accidentally matching a wall-material prefix.
- UE commandlet actor deletion did not remove superseded OFPA files: 291 old packages reappeared on reload. Identified them exactly from the first apply log and starting manifest, moved only those packages into `Saved/Town/session-1/rejected-first-pass-actors/`, and verified the corrected map in a fresh process. `reconciliation-receipt.json` records every moved path and hash. Original actor packages were not removed.
- `active-content-manifest.json` records the accepted changed/new content. `town_session1.py` now refuses to reapply over existing session actors. **Do not rerun the builder or reconciliation against this accepted map.** Use targeted in-place edits in future sessions.
- Every session launch used the process guard, shared lock and alarm. Another job's Selene import was observed between captures and walking; it was allowed to finish. The session's editor/game instances exited, and the shared lock was released.

### What still reads as fake

The plaza is still too broad and empty in its middle, buildings repeat with large grassy gaps, the café upper storey is a plain box, and the hillside/overlook retain hard engineered pads. The imported foliage is simple, the road pattern repeats conspicuously, and noon shadows and interiors need more careful lighting work. The outer skirt hides the rectangular cut but is still a bare landform rather than a finished backdrop. This is a presentation foundation, not a match to the approved concepts yet.

### Exact next step / proposed session 2

Back up the **current accepted** map and its external actors first. Keep the shared launch guard. Capture the same baseline into a fresh folder:

```sh
SELENE_TOWN_OUT="$PWD/Saved/Town/session-2" bash Tools/Unreal/town_run.sh capture before
```

Then finish the **café/plaza vignette in views 02–05 and 08**: add convincing café upper-storey/window depth, refine the canopy and frontage, compose larger planting/seating groups to break up empty paving, add curb junctions/ramps and planting transitions, and repair the nearest exposed terrace edge. Edit existing actors in place; do not rebuild the entire map. Consolidate repeated small foliage into instances. Review noon, dusk and night before spreading the treatment to more districts. Obtain valid editor frame timings with a supported capture path; the existing PerfRoute startup bug needs a separately authorized Source fix before packaged profiling can be trusted.
