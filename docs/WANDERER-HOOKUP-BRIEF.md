# Wanderer (teal-wanderer) hookup: brief (Astra, xhigh, bounded sessions)

## Goal

Make `teal-wanderer` (roster name **"Wanderer"**) a playable hero, cycled with C, moving as close to **Sparrow** as our pipeline allows, with Kawaii skirt and hair motion.

She is the **first hero on Tripo's UE5 Mannequin skeleton** instead of Mixamo. Part of the job is to show whether that removes the Mixamo workarounds:
- the hips-as-root offsets;
- the in-place loop hacks;
- the facing fixes.

Report clearly what was or wasn't needed.

Each session is killed at 30 minutes. Stop at a verified checkpoint and append to `docs/WANDERER-HOOKUP-PROGRESS.md` (create it):
- what is done;
- the evidence;
- the exact next step.

## What exists

- **Imported:**
  - `/Game/Assets/teal-wanderer/teal-wanderer/SkeletalMeshes/teal-wanderer`, skeleton `teal-wanderer_Skeleton`, plus its PhysicsAsset;
  - 1.68 m tall, 0 errors (report: `docs/engine-checks/teal-wanderer.json`);
  - delivery provenance: `SourceArt/Assets/teal-wanderer/teal-wanderer.provenance.json`, run `20261107T001402-33b409`.
- **Skeleton:** 108 joints. UE5 Mannequin names: `root` (at the origin), `pelvis`, `spine_01`–`spine_05`, `neck_01`/`neck_02`, `head`, `clavicle`/`upperarm`/`lowerarm` with `*_twist_01/02`, `hand`, metacarpals and fingers, and `thigh`/`calf`/`foot`/`ball`.
  - **Secondary chains:**
    - `skirt_front_c_00`, `skirt_side_l_00`, `skirt_side_r_00`, `skirt_back_c_00` (rooted on `pelvis`);
    - `hair_back_c_00`, `hair_side_l_00`, `hair_side_r_00` (rooted on `head`).
  - **The ruffle chains were removed.** Don't reference them.
- **Material slots:**
  - slot 0 is the body (Tripo base colour);
  - slot 1 is `FoxEye_amber`, the eye cards over her eyes.
- **Rig notes:**
  - `/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/work/repairs/teal-wanderer/PROGRESS.md`
  - `rig-prep/SOL-REVIEW.md`
  - `report.json` files with the proposed collider and chain snippet.
- **Patterns to reuse:**
  - `docs/FOX-HOOKUP-BRIEF.md` and `docs/FOX-HOOKUP-PROGRESS.md`, the most recent hookup. Follow the same steps and captures.
  - `docs/ANIM-MATCH-PROGRESS.md`, `Tools/Unreal/character_retarget.py`, `gasp_clip_retarget.py`, `chars_toon_instances.py`.
  - Sparrow's roster line in `Config/DefaultGame.ini` already uses UE5-style collider names (`pelvis`, `spine_01`, `thigh_l` and so on).

## Known issue: you must handle it

`ASeleneCharacter::ApplyCharacter` (`Source/Selene/SeleneCharacter.cpp` around lines 353–357) applies the roster `OverrideMaterial` to **every** material slot. For Wanderer, that would paint the body toon material over her eye cards and break her eyes.

**Make one small, clearly marked C++ change:** a new optional roster field in `FSelenePlayableCharacter` (`SeleneCharacterSettings.h`), for example `TArray<FName> KeepMaterialSlots`, naming the slots to leave untouched. Leave existing heroes' behaviour unchanged.
- Build `SeleneEditor`.
- Verify her eyes keep `FoxEye_amber` in game, with close and gameplay-distance captures.
- `SeleneCharacter.cpp` also holds uncommitted AnimMatch and movement work. Edit only those few lines, and don't touch anything else in the file.

## Steps

1. **Retarget.**
   - Create `IK_Wanderer`.
     - With UE5 names, Unreal's mannequin template auto-mapping should work, but define the chains explicitly if the extra skirt and hair bones confuse it.
     - Set `root` as the retarget root.
   - Create `RTG_Manny_To_Wanderer`, or use whichever GASP source skeleton the other heroes' retargets use (see `gasp_clip_retarget.py` and `docs/GASP-INTEGRATION.md`).
   - Retarget the same GASP clip set the other heroes use.
   - **Measure first, then decide.**
     - Do the transition clips still carry hips offsets?
     - Do the loops need in-place correction, given a real root bone?

     Apply the AnimMatch session-3 normalization only where the measurements show it's needed, and record the numbers.
2. **Facing.** Judge it from **side and front captures**, with the mesh forward compared to the travel direction. Her bind pose should match Manny's. Set MeshRotation and MeshOffset to match the other heroes only where the captures show it's right.
3. **Material.** Create `MI_Toon_Wanderer` from `M_Character_Toon` with her base-colour texture, verified by reading it back. Use it for slot 0 only, through the new keep-slots field.
4. **Roster.** Add one Wanderer line plus cook directories to `Config/DefaultGame.ini`.
   - Measured speeds.
   - Colliders in UE5 names: pelvis, `spine_01`–`spine_05`, thighs, calves, upper and lower arms. **The long back hair needs spine and arm colliders; the skirt panels need thigh and calf colliders.**
   - Per-group Kawaii values (skirt like cloth, hair lighter). Start from the fox's installed values in `docs/FOX-HOOKUP-PROGRESS.md`.
5. **Captures:** the `selene.AnimMatch` harness, Wanderer next to Sparrow from front, side and back.
   - The moves: idle, walk, run, sprint, stop, pivot, jump.
   - Plus an **arms-up or forward clip, if one exists in the set**, checking the shoulder trim.
   - Plus a **stride and crouch close-up**, checking skirt-to-thigh clipping.
   - Plus **eye close-ups**.
   - Run with `selene.AdvancedMovement 0` for the comparison, then one short capture with it set to 1.
   - Regression captures: Sparrow, Champion and Fox.

## Rules

- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, the user may be playing: wait up to 15 minutes, then stop and report. **Never kill it.**
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it afterwards, including on failure. The town jobs share this lock.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV'`.

  Known startup errors are already cleared.
- **Files you may touch:**
  - `Content/Selene/Characters/Wanderer/**`
  - `Content/Selene/Materials/Character/MI_Toon_Wanderer`
  - `Config/DefaultGame.ini` (the Wanderer line and cook directories only)
  - `Source/Selene/SeleneCharacterSettings.h` and the marked material-slot lines in `Source/Selene/SeleneCharacter.cpp`
  - `Tools/Unreal/**` (new wanderer scripts)
  - `docs/WANDERER-HOOKUP-PROGRESS.md`
- **Never:**
  - `Config/DefaultEngine.ini`;
  - `/Game/Assets/*` source assets, any other hero's assets, or the Town map;
  - Blender edits. Rig problems go in the report;
  - commits, the browser, downloads or paid services.
- **Failure rule:** one fix per distinct, diagnosed failure. Clear compile and script errors are normal work.
- **Final reply:**
  - what works;
  - **UE5 vs Mixamo:** which workarounds were not needed;
  - contact-sheet paths;
  - the roster line;
  - the Kawaii values;
  - the eye check;
  - skirt clipping;
  - what still differs from Sparrow;
  - the exact next step.
