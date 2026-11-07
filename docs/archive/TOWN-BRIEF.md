# Make the Selene town look good: brief (Astra, xhigh, bounded sessions)

## Goal

The user says the town is **sparse, the road textures conflict, and the terrain doesn't make sense.** It reads like a demo piece. Make it look like a real, lived-in soft-cinematic anime town.

Follow the recommended path in `docs/research/town-quality.md` (read it fully first): **rebuild the presentation around the existing layout.**
- No downloaded or purchased town or kit (the user is spending no more budget).
- No paid generation.
- Use the existing Tripo assets, Blender-authored kit pieces (free) and selective PCG.

Each session is killed at **30 minutes**. Stop at a verified checkpoint and append to `docs/TOWN-PROGRESS.md` (create it):
- what is done;
- before and after images;
- the exact next step.

This is multi-session work. Do the biggest visual win first.

## Read first

- `docs/research/town-quality.md`: diagnosis, phased plan and density targets.
- `VISUAL-DEMO-BRIEF.md` and `docs/ART-DIRECTION.md`: style B.
  - Cream and ivory rounded architecture, petrol-blue trim, coral accents.
  - Warm key light, cool shadow fill, restrained bloom.
  - The concepts are in `concepts/town-style-study-01/` and `concepts/environment-style-B-01/`. Look at them; they are the target.
- `Design/Blockout/` (`README.md`, `layout.json`, `dressing.json`, `ground_materials.json`) and the coordinate contract in that README.
- The current builders: `Tools/Unreal/build_blockout.py`, `build_ground_materials.py`, `apply_ground_materials.py`, `dress_route.py`, `toon_lighting_shots.py`.
- The map is `/Game/Selene/Maps/Town`.
- Assets are in `Content/Assets/*`: shops, townhouses, apartments, clock hall, workshop, plaza furniture, plants, lamps, scooters, vending machine and others.
- The current look: `Saved/Checkpoint1/simple/11_overlook_to_town.png` and `12_aerial_overview.png`.

## Session 1: ground, roads and the plaza route view (Phase 1 of the research)

1. **Before captures.** Add a small, reusable fixed-viewpoint capture: about 8 eye-level views along route R1 (plaza → café) and main street, plus the overlook and one aerial view. Use a cvar or Python camera bookmarks with daylight fixed, and contact sheets (the Swift helpers work). These are the before/after baseline for every session.
2. **One road and paving family.**
   - Replace the clashing petrol-gray-cobble-against-cream-paving seams with a coherent hierarchy: road surface, then curb, then sidewalk, then plaza paving.
   - Use consistent texture scale and tone close to the concepts, varied through material instances (roughness, colour, patches) rather than unrelated tiling materials.
   - Add **curb and gutter geometry** along the street edges: a Blender-authored modular curb piece or a spline mesh.
   - Add simple road-edge and grime **decals**, and crossings at the plaza.
3. **Terrain reads as a place.**
   - Soften the hard pad edges where they're visible from the route.
   - Add **retaining walls and steps** at the hillside terrace edges nearest the plaza view.
   - Blend grass into soil where it meets paving.
   - Hide the map edges with an embankment or backdrop silhouette if the overlook or aerial shows them.
   - Keep route grades walkable. Check that the capsule can still walk R1.
4. **Plaza and café route density.** Using existing assets only, and starting from the research's density targets for the plaza, dress the R1 views: planters, street trees, benches, lamps, bins, the vending machine, scooters, signage and awnings on the existing shops. Hand-place the hero spots. Use PCG only for small scatter (flowers, grass tufts, pebbles) inside masks, and bake it to instances.
5. **Light pass for style B** on the same views: warm key, cool fill, exposure and restrained bloom. Use the existing time-of-day setup; don't rewrite it.
6. **After captures** of the same views.
   - Run a quick perf sanity pass in the editor: `stat unit` numbers on 2–3 of the views, noted as indicative only. Packaged measurement comes later.
   - Note any frame-time jump caused by your changes.

Session 2 onward is the research's Phases 2–4:
- finish the plaza and café to the style checkpoint;
- a small Blender modular kit (curbs, retaining walls, sign frames, railings);
- spreading it district by district;
- the hillside, the overlook and the backdrop.

Propose the next session's scope in `TOWN-PROGRESS.md`.

## Rules

- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, **the user may be playing: never kill it.** Wait up to 15 minutes, then stop and report.
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it afterwards, including on failure. Other jobs (character hookups) share this lock, so hold it only while Unreal runs.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV'`.

  Headless Python writes its results to files. Known Python startup errors (AgentSkill, PythonTestRunner, `EditorToolset`/`ToolsetRegistry`) are already cleared.
- **Back up the map** (copy `Town.umap` and its external actors, or duplicate the level asset) before your first edit, so you can roll back.
- **Files you may touch:**
  - `Content/Selene/Maps/Town*` and its external actors
  - `Content/Selene/Materials/Ground/**`
  - new `Content/Selene/Environment/**`
  - `Tools/Unreal/town_*.py`, plus new helpers
  - `Tools/Blender/**`, for kit pieces
  - `Design/Blockout/**`, for data changes, with the validator kept passing
  - `docs/TOWN-PROGRESS.md`

  Blender kit pieces go through Unreal import as static meshes under `Content/Selene/Environment/Kit/`.
- **Never:**
  - touch `Config/DefaultEngine.ini`, `Config/DefaultGame.ini`, `Source/**`, `Content/Selene/Characters/**`, `Content/Selene/Maps/MovementTest*` or `/Game/Assets/*` source assets. Placing instances of them in the map is fine.
  - Tripo, Studio or paid services; downloads; the browser; commits.
- **Failure rule:** one fix per distinct, diagnosed failure. Clear script errors are normal work. Stop and report when a failure repeats, can't be diagnosed, or needs variations tried.
- **Judge by the eye-level captures,** not by invented numeric gates. If a change makes a view worse, revert it.
- **Final reply:**
  - before and after contact sheets (the paths);
  - what changed (materials, curbs, terrain, dressing, light);
  - the perf note;
  - what still reads as fake;
  - the proposed next session.
