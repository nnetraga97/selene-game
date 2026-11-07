# Nerine and the base body: hookup brief (Astra, xhigh, bounded sessions)

## Goal

Make two new playable roster entries, both cycled with C (and selectable from the new picker once it lands):

1. **"Nerine"** (`nerine`, run `20261107T095808-f8653b`, delivered as a draft) is the first modular hero: a base body with separately fitted hair, jacket and skirt. The user will compare her **in game against Ysolde**, so match Ysolde's setup wherever possible.
2. **"Base"** (`base-female-v2`, run `20261107T095609-81aed3`) is the user's new bald base body, imported so the user can see it move. It has no secondary chains.

**Reuse the Ysolde recipe exactly:** `docs/YSOLDE-HOOKUP-BRIEF.md`, `docs/YSOLDE-HOOKUP-PROGRESS.md`, `Tools/Unreal/ysolde_*`. Copy the scripts to `nerine_*` and `basebody_*`; don't rediscover anything.

Each session is killed at 30 minutes. Stop at a verified checkpoint by about 25 minutes, and append to `docs/NERINE-BASE-HOOKUP-PROGRESS.md` (create it).

## What exists (imported and verified by Claude, both upright)

| Entry | SkeletalMesh | Size | Materials |
|---|---|---|---|
| Nerine | `/Game/Assets/nerine/nerine/SkeletalMeshes/nerine` (skeleton `nerine_Skeleton`) | 0.72 × 0.41 × 1.80 m (hair included; body 1.74 m) | 4 slots: `Nerine_Body`, `Nerine_Hair`, `Nerine_Jacket`, `Nerine_Skirt`, each with its own 2048 texture |
| Base | `/Game/Assets/base-female-v2/base-female-v2/SkeletalMeshes/base-female-v2` | 0.66 × 0.28 × 1.74 m | 1 slot |

- **Skeletons:** both are on the UE5 Mannequin contract with a `root` bone at the origin above `pelvis`.
  - Nerine has 80 body bones plus 26 secondary bones; the chain list and roster snippet are in `/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/evidence/nerine-session2.md` and `work/repairs/nerine/session2/JOINTS-AND-CHAINS.md`.
  - Base has 80 bones and no chains.
- **Rig notes and known limits:** `/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/work/repairs/nerine/session2/SOL-REVIEW.md`. The shoulders, skirt clipping, waist fit and fist are still needs-work; that's expected. The user wants to judge her in engine.

## Steps, per entry

1. **Retarget, the Ysolde way.**
   - `IK_Nerine` and `IK_Base` from the mannequin template, with `root` as the retarget root.
   - The bind pose aligned to Manny.
   - Pelvis Motion → `pelvis`, Root Motion → `root`.
   - The same GASP clip set, with `force_root_lock=True` and the `REF_POSE` root lock.
   - Measure the loop speeds.
2. **Facing:** judge it from front and side captures, expecting yaw −90 like Ysolde.
3. **Materials.**
   - Project-owned toon instances from `M_Character_Toon`, which is now standard lit shading despite its name, with each slot's own texture:
     - **Nerine:** body, hair, jacket and skirt. Jacket and skirt use `M_Character_Toon_TwoSided`.
     - **Base:** one slot.
   - Apply them through the existing `SlotMaterials` roster field. **No mesh duplicates.**
4. **Roster:** one line each in `Config/DefaultGame.ini`, plus cook directories, placed **after Ysolde**.
   - **Nerine:**
     - Use her chain snippet, with colliders as generous as Ysolde's (thigh 8 / calf 6.5 cm).
     - Start from Ysolde's Kawaii values (cape, coat as skirt, sash, tassels); her ponytail chain is lighter, like hair.
   - **Base:** no chains, no colliders.
5. **Captures:** the AnimMatch harness, **Nerine next to Ysolde** (not Sparrow) from front, side and back: idle, walk, run, sprint, stop, pivot, jump.
   - Plus Ysolde's watch items for both: skirt or coat through the legs in run and sprint, the crotch at stride and jump, shoulders in the arm swing, the idle hand.
   - Rate each one for each hero at gameplay distance.
   - One short Base capture: walk, run, jump, front and side.
   - Regression captures: Ysolde and Sparrow.

## Rules

- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, wait up to 15 minutes, then stop and report. Never kill it.
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it on exit.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV'`.

  Claude may be building C++ at the same time; the lock handles it.
- **Headless only:** no editor UI and no computer use.
- **Files you may touch:**
  - `Content/Selene/Characters/Nerine/**`, `Content/Selene/Characters/Base/**`
  - `Content/Selene/Materials/Character/MI_Toon_Nerine_*` and `MI_Toon_Base*`
  - `Config/DefaultGame.ini` (these two lines and their cook directories only)
  - `Tools/Unreal/nerine_*`, `Tools/Unreal/basebody_*`
  - `docs/NERINE-BASE-HOOKUP-PROGRESS.md`
  - `Saved/NerineHookup/**`
- **Never:**
  - `Source/**` (Claude is editing it now);
  - `Config/DefaultEngine.ini`;
  - `/Game/Assets/*` source assets, other heroes or maps;
  - Blender, commits, the browser, downloads or paid services.
- **Failure rule:** one fix per distinct, diagnosed failure. Stop and report on a repeat.
- **Final reply:**
  - the roster lines;
  - the Kawaii values;
  - the contact-sheet paths;
  - Nerine vs Ysolde, rated per watch item;
  - what Base looks like in motion;
  - the exact next step.
