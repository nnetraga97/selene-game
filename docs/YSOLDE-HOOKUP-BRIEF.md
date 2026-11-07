# Ysolde (council-envoy) hookup: brief (Astra, xhigh, bounded sessions)

## Goal

Make `council-envoy` (roster name **"Ysolde"**) a playable hero, cycled with C, moving as close to **Sparrow** as our pipeline allows, with Kawaii motion on her cape, coat tails and sash. She's an original Selene character: the harbour council envoy.

She's the second hero on the **UE5 Mannequin skeleton**, and the first one we rigged ourselves. **Reuse the Wanderer recipe** (`docs/WANDERER-HOOKUP-PROGRESS.md`, `Tools/Unreal/wanderer_*.py`). Don't rediscover it: copy those scripts to `ysolde_*.py` and change the names and paths.

Each session is killed at 30 minutes. Stop at a verified checkpoint by about 25 minutes, and append to `docs/YSOLDE-HOOKUP-PROGRESS.md` (create it): what's done, the evidence, and the exact next step.

## What exists

- **Imported** under `/Game/Assets/council-envoy/` (check the exact SkeletalMesh path and the import report `Saved/AssetImport/council-envoy.json`; confirm it's **one** SkeletalMesh).
  - Delivery: `SourceArt/Assets/council-envoy/council-envoy.provenance.json`, run `20261107T053653-5ba909`, delivered as a **draft** (the rig review said needs-work on things only the engine can judge; see below).
- **Skeleton:** 111 joints. The 80 body bones are the exact teal-wanderer UE5 contract (`root` at the origin, `pelvis`, `spine_01`–`05`, `neck_01`/`02`, `head`, arms with twists, fingers, legs).
  - The 31 secondary bones: `cape_back_l_00`, `cape_back_c_00`, `cape_back_r_00`, `skirt_front_l_00`, `skirt_front_r_00`, `skirt_back_c_00`, `sash_front_c_00`, `tassel_front_l_00`, `tassel_front_r_00` (chain roots; check the children in the asset).
- **Materials:** two slots, from a 2048² atlas.
  - The opaque body (skin, face, eyes, hair, boots, jewellery).
  - Cloth (coat, cape, sash, trousers), which **must render two-sided**, because the coat's inner surface and the cape lining show through the open coat front.
- **Rig notes and the reviews:** `/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/work/repairs/council-envoy/PROGRESS.md` and `SOL-REVIEW.md`.
- **The proposed roster chain and collider snippet** is in that PROGRESS.md.

## Materials: no mesh duplicates this time

The Wanderer needed a duplicated `SK_Wanderer`, because the imported glTF material lacked the skeletal-mesh usage flag. **Don't duplicate the mesh.** The roster must point at the imported mesh.

1. Create `MI_Toon_Ysolde_Body` from `M_Character_Toon` with her atlas as base colour, and read it back to verify.
2. Create the cloth material:
   - Make a two-sided toon parent, `M_Character_Toon_TwoSided` (a copy of `M_Character_Toon` with Two Sided on), under `Content/Selene/Materials/Character/`.
   - Then create `MI_Toon_Ysolde_Cloth` from it.
   - Check that the backfaces are lit sensibly. The inside of the coat must not read as a black void at gameplay distance.
3. The roster today has one `OverrideMaterial` plus `KeepMaterialSlots`. **Add one small, clearly marked C++ field**: `TMap<FName, TSoftObjectPtr<UMaterialInterface>> SlotMaterials`, in `FSelenePlayableCharacter` (`SeleneCharacterSettings.h`).
   - In `ASeleneCharacter::ApplyCharacter`, next to the existing override and keep-slots lines, apply it per slot name after the override.
   - Existing heroes must behave exactly as before.
   - Build `SeleneEditor` with `-NoHotReloadFromIDE -NoHotReload`.
   - `SeleneCharacter.cpp` holds other uncommitted work. Touch only those few marked lines.

## Steps

1. **Retarget**, the Wanderer way:
   - `IK_Ysolde` from the mannequin template, with `root` as the retarget root.
   - The bind pose aligned to Manny.
   - **Pelvis Motion → `pelvis`, Root Motion → `root`**, with the operator audit that caught Wanderer issue T9.
   - The same GASP clip set the other heroes use, with `force_root_lock=True` and `REF_POSE` root lock.
   - Measure the loop speeds.
2. **Facing:** judge it from **front and side** captures. Expect the same mesh yaw −90° as the Wanderer, but confirm it.
3. **Roster:** one Ysolde line plus cook directories in `Config/DefaultGame.ini`.
   - Use the measured speeds, `SlotMaterials`, and the chains and colliders.
   - **Colliders:** pelvis, `spine_01`–`spine_05`, thighs, calves, upper and lower arms.
   - **Make the thigh and calf colliders generous enough that the coat tails and cape clear the legs in run and sprint.** That's the main open risk from the rig review.
   - **Kawaii values:** start from the fox's installed cloth values (`docs/FOX-HOOKUP-PROGRESS.md`) and the Wanderer's skirt values. The cape is heavier and slower than the coat tails; the sash and tassels are lightest.
4. **Captures:** the `selene.AnimMatch` harness, Ysolde next to Sparrow from front, side and back.
   - The moves: idle, walk, run, sprint, stop, pivot, jump. Use `selene.AdvancedMovement 0` for the comparison, then one short capture with it set to 1.
   - **Plus these, from the rig review:**
     - **cape and coat clipping** in run and sprint, from the side and back;
     - the **dark coat interior** from the front;
     - **the crotch and trouser area** at the stride extreme and the jump tuck, from the front;
     - **the shoulders** during the run arm swing;
     - the **idle hand** shape.
   - Judge these at **gameplay camera distance**, and also close up. Report each one as fine, visible-but-minor, or needs a Blender fix. Don't fix the mesh; that's a separate decision.
   - **Regression captures:** Sparrow, the Wanderer and the Fox.

## Rules

- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, the user may be playing: wait up to 15 minutes, then stop and report. **Never kill it.**
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it afterwards, including on failure.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV'`.
- **Headless only:** `-run=pythonscript` commandlets and scripted `-game` captures. No editor UI and no computer use.
- **Files you may touch:**
  - `Content/Selene/Characters/Ysolde/**`
  - `Content/Selene/Materials/Character/MI_Toon_Ysolde_*` and `M_Character_Toon_TwoSided`
  - `Config/DefaultGame.ini` (the Ysolde line and cook directories only)
  - `Source/Selene/SeleneCharacterSettings.h` (the one new field) and the marked material lines in `Source/Selene/SeleneCharacter.cpp`
  - `Tools/Unreal/ysolde_*` (new scripts)
  - `docs/YSOLDE-HOOKUP-PROGRESS.md`
  - `Saved/YsoldeHookup/**`
- **Never:**
  - `Config/DefaultEngine.ini`;
  - `/Game/Assets/*` source assets (instances are fine), any other hero's assets, or the town maps;
  - Blender edits. Mesh problems go in the report;
  - commits, the browser, downloads or paid services.
- **Failure rule:** one fix per distinct, diagnosed failure. Clear compile and script errors are normal work. Stop and report when a failure repeats or can't be diagnosed.
- **Final reply:**
  - what works;
  - contact-sheet paths;
  - the roster line;
  - the Kawaii values and collider radii;
  - the material check (two-sided cloth, no duplicate mesh);
  - each rig-review watch item rated;
  - what still differs from Sparrow;
  - the exact next step.
