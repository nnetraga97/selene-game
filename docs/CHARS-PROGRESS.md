# Fixer / Courier integration progress

**Current status: STOPPED in session 3 at the inherited in-place loop translation-model check (exit 255). Default base regeneration and exactly 11 GASP clips per hero passed. No loop edits, materials, roster changes, build or game captures occurred. Numerical facing gates were removed. See the session 3 final checkpoint.**

## Session 1 — 2026-11-06, started 18:52 UTC

Checkpoint due before 19:17 UTC; session cutoff 19:22 UTC.

- Read Champion roster, settings fields, retarget/material scripts, GASP progress and loop correction/measurement scripts.
- Import reports: Fixer 170 cm, Courier 178 cm. Live mesh bounds and bone orientation preflight pending.
- Preserve pre-existing modifications, including DefaultEngine.ini, DefaultGame.ini, SeleneCharacter.cpp and several Unreal scripts. No Source or DefaultEngine edits are permitted.
- Added guarded alarm-wrapped launcher and scoped integration script. No character assets or roster entries created yet.
- Evidence directory: `Saved/Chars/session-1/`.

Exact next step: run `bash Tools/Unreal/chars_session_run.sh preflight`, inspect height/bone orientation, then implement scoped retarget/GASP/material stages. Do not rescale imported meshes. No visual acceptance yet.

### 18:56 UTC checkpoint

- Live bounds passed: Fixer 170.000011 cm, Courier 177.999899 cm (`preflight.json`, commandlet exit 0). Both expose 65 bones including terminal bones. Unticked-component socket positions were zeros and are not used as reference-pose evidence.
- Base rigs, retargeters and 21 base assets each created successfully (`Fixer-base.json`, `Courier-base.json`, `create.json`). All 21 Mixamo chains map; Root Motion op disabled.
- `create.json` uses AnimPose reference transforms: meshes face -X. `diagnose.json` demonstrates base walk toes travel along +Y, a 90-degree body/travel mismatch. No roster entries enabled yet.
- One diagnosed fix: opt-in `SELENE_CHAR_POSE_YAW=-90` aligns the target root retarget pose to Manny before chain auto-alignment. Default zero retains Champion/Angel behavior. No imported mesh rotation/scale edits.
- Exact next step: run `align`, inspect resulting body orientation, then 11 GASP clips, loop correction/measurement, scoped material instances, roster, build and game captures. If alignment fails, stop; no second fix.

### Final checkpoint — 18:59 UTC (before the 25-minute limit)

Stopped early under the explicit failure rule. No further Unreal launches or second fix were attempted.

#### Done and evidence

1. **Bounds confirmed, no rescaling:** `Saved/Chars/session-1/preflight.json`; `preflight-exit.txt` = 0. Fixer 170.000011 cm; Courier 177.999899 cm. Mesh minima Z are -0.047771 / -0.038763 cm. Initial bone-position readings on unticked components are zero placeholders; valid reference transforms are in `create.json`.
2. **Initial base assets saved:** `create-exit.txt` = 0, `Fixer-base.json`, `Courier-base.json`. Each has `IK_Manny`, `IK_<Hero>`, `RTG_Manny_To_<Hero>`, plus 21 base animation/blend-space assets including idle/walk/jog/jump/fall/land. All 21 chain mappings resolve. Auto-definition recognized both rigs; fallback was retained but not needed. Root Motion op disabled as for Champion.
3. **Orientation diagnosis:** `create.json` shows toe-minus-foot direction approximately -X in reference and idle; `diagnose.json` shows the base walking toes moving primarily along +Y. No visual acceptance is claimed. `diagnose-exit.txt` = 0.
4. **Single correction attempt saved partial output:** optional `SELENE_CHAR_POSE_YAW=-90` in `character_retarget.py` converts a world-Z turn into the root's local bind coordinates, sets it in the target retarget pose before auto-alignment, and reuses the existing retarget pipeline. Defaults remain zero for Champion/Angel. `Fixer-aligned-base.json` and `Courier-aligned-base.json` record the quaternions and returned package names. This attempt is **unverified**, not a confirmed orientation fix.

#### Failure / stop reason

`align-exit.txt` = **1**. `align-editor.log:1729`:

> LogAssetTools: Error: /Game/Selene/Characters/Fixer/Anims/BS_Idle_Walk_Run_Fixer1 - An object named '/Game/Selene/Characters/Fixer/Anims/BS_Idle_Walk_Run_Fixer.BS_Idle_Walk_Run_Fixer' already exists.
> Couldn't rename 'BlendSpace /Game/Selene/Characters/Fixer/Anims/BS_Idle_Walk_Run_Fixer1.BS_Idle_Walk_Run_Fixer1'.

Unreal's final summary is **Failure - 1 error(s), 83 warning(s)**. The shared retarget script checks saves/nonempty output but does not detect engine-internal overwrite/rename errors; therefore its per-hero reports and `align.json` falsely report success for overall stage acceptance. The wrapper's nonzero exit and `verification.json` are authoritative. No crash or SIGALRM occurred.

- Both canonical `BS_Idle_Walk_Run_Fixer.uasset` and extra `BS_Idle_Walk_Run_Fixer1.uasset` now exist. Fixer's returned blend space is the `...Fixer1` package. Other returned Fixer outputs use canonical names; Courier returned canonical names. Do not treat canonical files as uniformly regenerated without a fresh reload.
- `align.json` sampled canonical idle assets in the same process and returned positions identical to the first pass; it does **not** prove the updated saved animations face correctly. It may be stale loaded data, or the pose alignment may need diagnosis. No conclusion beyond this evidence.
- Original first-pass animation assets were not backed up before the permitted overwrite retry. Reports/logs of both passes remain. Do not replay either command blindly or delete the duplicate before inspecting references.

#### Not done

- No GASP clips created for Fixer/Courier; **Walk/Run/Sprint speeds unmeasured**.
- No toon MIs, imported material relinks/usage changes, roster lines or cook-directory additions.
- No EyeHeight/MeshOffset/MeshRotation accepted, no SecondaryChains added.
- No SeleneEditor build, game run, or Champion regression load after this work.
- **No screenshots** for idle, walk, sprint, stop, jog-back, pivot or jump. Grounding, facing, T-pose absence and rendered toon shading remain unverified.
- A prepared but unexecuted GASP script was removed after the failure; it created no assets. The launcher's future `clips/materials/verify` cases are placeholders and currently fail deliberately in `chars_integrate.py` until implemented.
- No Config or Source edits, browser, downloads, paid calls, or commits. Existing user edits preserved. Final process check: no matching Selene editor; session lock released.

#### Exact next step for a new session

Start with a **new evidence directory**, retaining `Saved/Chars/session-1/`. Before any launch, apply the same process wait/lock/alarm guard. Run a **read-only fresh-process audit** of:

1. Both Fixer blend spaces (`BS_Idle_Walk_Run_Fixer` and `BS_Idle_Walk_Run_Fixer1`), their sample references, canonical Fixer/Courier idle/walk sequences, and both retargeters' current target pose/root rotation offsets. Sample compressed poses twice after initialization and record facing from shoulders/feet and travel from walk stance motion. Compare against `create.json`/`diagnose.json`.
2. Diagnose why overwrite retained Fixer's original blend-space object and emitted `Fixer1`. The canonical idle was explicitly loaded for reference quaternion extraction before retargeting; retained UObject references are a possible cause, not proven. The unchanged same-process samples also need a fresh reload before deciding whether alignment itself failed.
3. Once diagnosed, correct only the new heroes' base assets and require exact canonical output names plus commandlet exit 0. Preserve Champion/Angel assets and default script behavior. Do not merely trust the existing `status: success` JSON.

Then continue requested steps 3–7: exactly 11 GASP clips, validated in-place loop correction and fresh compressed stance-speed measurement as in `gasp_loop_in_place.py` / `gasp_ground_speeds.py`, scoped toon/material usage setup, measured roster placement and narrow cook dirs, SeleneEditor build, one 75-second AutoWalk/AutoShots run per hero and a short Champion load. Move and inspect the phase screenshots before claiming runtime completion.

## Session 2 — 2026-11-06, started approximately 19:00 UTC

- Controller authorized deletion only within Fixer/Courier generated character folders after checking external references, then separate fresh regeneration with target pose yaw -90 and a third fresh facing audit.
- Evidence: `Saved/Chars/session-2/`. Checkpoint due before approximately 19:25 UTC.
- Baseline hashes and script/config snapshots saved. No matching Selene editor observed at entry.
- Exact next step: cleanup audit and scoped EditorAssetLibrary deletion, then canonical regeneration and compressed idle/walk facing gate.

### 19:05 UTC — single permitted correction

- Cleanup passed (exit 0): 49 generated assets, no external package references, both directories deleted through EditorAssetLibrary.
- First regeneration stopped after Fixer: exact 21 returned names and 24 disk packages were correct, but the immediate post-batch AssetRegistry directory inventory check failed (exit 255). No engine retarget/name-collision error occurred.
- Fresh read-only inventory passed (exit 0): library and disk inventories both contain exactly the canonical 24 Fixer packages; Courier is empty. Evidence: `create-inventory-diagnosis.json`, `inventory.json`. This localizes the failed gate to same-process registry visibility; the precise transient list was not captured.
- One correction: use exact returned package names plus exact on-disk inventory during generation; a separate fresh process still validates the saved results. Cleanup/recreation retries use new report/log names, retaining failed-attempt evidence. No further correction is permitted if this or facing fails.

### Session 2 final checkpoint — 19:07 UTC (before 25 minutes)

**Stopped. No additional Unreal launches, repairs, or integration steps after the failed facing check.**

#### Completed and evidence

- `Saved/Chars/session-2/cleanup.json`, `cleanup-exit.txt` = **0**: 49 generated assets audited with `EditorAssetLibrary.find_package_referencers_for_asset(..., load_assets_to_confirm=True)`; no references outside the two new hero directories. Both directories, including stray `BS_Idle_Walk_Run_Fixer1`, deleted with `EditorAssetLibrary.delete_directory` in a separate process.
- Saved bind-root quaternions and live mesh bounds in the cleanup report. Heights remain **Fixer 170.000011 cm**, **Courier 177.999899 cm**; no rescaling or mesh edits.
- Shared `character_retarget.py` now accepts an optional audited `SELENE_CHAR_BIND_QUAT` JSON quaternion. Together with `SELENE_CHAR_POSE_YAW=-90`, it allows a clean generation without loading canonical outputs. Default yaw remains 0. Optional exact returned-package validation added.
- First generation (`create-exit.txt` = **255**) saved canonical Fixer outputs, then the immediate AssetRegistry inventory assertion failed before Courier. Disk inventory and a fresh read-only process (`inventory-exit.txt` = **0**) both showed exactly 24 canonical Fixer packages. The precise transient same-process list was not captured, so registry visibility is the localized explanation, not a proven internal engine cause.
- **Single permitted correction used:** generation checks exact returned names plus on-disk package inventory, with fresh-process validation afterward. A second scoped cleanup (`cleanup-retry-exit.txt` = **0**) and separate regeneration (`create-retry-exit.txt` = **0**) completed. Log summary: **Success - 0 errors, 82 warnings**. Both `Fixer-base-retry.json` and `Courier-base-retry.json` contain the yaw/quaternion evidence and exactly 21 canonical animation/blend-space names. Each hero has **24 assets total**, including the three rig/retargeter assets. No numbered duplicates remain.

#### Failure and limits

- Fresh process `facing-exit.txt` = **255**. `facing.json` contains **455 compressed idle pose samples for Fixer**, evaluating twice per time to avoid first-evaluation initialization artifacts. Playback-style evaluation uses `incorporate_root_motion_into_pose=False`.
- Mean normalized XY toe-minus-foot vector: **[-0.858442, -0.512910]**, approximately **-149.142 degrees from +X**; expected facing was **+Y**. The assertion is at `Tools/Unreal/chars_session2.py:156`; see `facing-editor.log` and `verification.json`.
- The gate stops on this first failed idle check. **Fixer walk travel and Courier idle/walk were not sampled.** Therefore no claim is made that a measured walk travel vector disagrees with facing; the verified failure is the unexpected Fixer idle toe orientation.
- No second repair was attempted. Do not interpret saved yaw offsets or canonical generation as accepted alignment.

#### Not done

- No GASP clips, in-place corrections, or fresh stance-speed measurements. **WalkLoopSpeed / RunLoopSpeed / SprintLoopSpeed remain unmeasured for both heroes.**
- No toon MIs, imported material relinks/usage changes, roster/cook additions, or accepted EyeHeight/MeshOffset/MeshRotation.
- No editor build or game launches, including Champion. **No phase screenshots:** idle, walk, sprint, stop, jog-back, pivot and jump are all unverified visually. No T-pose/feet/toon acceptance claimed.
- Config/DefaultGame.ini, DefaultEngine.ini and all Source files match session-entry hashes. Existing user edits preserved. No commits, browser, downloads or paid services. Only permitted tools/docs/generated Content and session evidence were changed.
- Final process check found no matching Selene editor and `/tmp/selene-unreal.lock` absent. `verification.json` records process, lock, hashes, exact asset inventories, stage exits and the failure.

#### Exact next step

In a newly authorized session/evidence directory, perform a **read-only fresh-process diagnostic** without regenerating anything: sample both heroes' idle and walk fully before assertions, compare RAW/COMPRESSED and root-lock-respecting/unlocked modes, record toe and shoulder facing, walk stance travel, root transforms, and the retargeter's saved target-pose offsets. Determine whether the yaw is changed by auto-alignment, root-lock playback, or another retarget operation; none of these mechanisms is yet proven. Keep the existing canonical packages intact until that diagnosis establishes a scoped correction. Only after a successful facing/travel gate proceed to the 11 GASP clips, correction/measurement, materials, roster, build and captures.

## Session 3 — 2026-11-06, started 19:08 UTC

- Evidence: `Saved/Chars/session-3/`; checkpoint due before 19:33 UTC.
- Controller authorizes scoped cleanup in its own fresh process, separate default regeneration (pose yaw unset, bind override unset), exactly 11 GASP clips each, corrected loops and measured speeds, toon setup, Champion-based roster transforms, build, 75-second game captures and short Champion load.
- Numerical facing assertions removed from this session workflow. Only one visual facing correction/re-run per hero is permitted; stop on any other failure.
- Entry process guard: no Selene editor/game, lock absent. Baseline hashes cover Source, Config, Tools and scoped Content. Existing user modifications preserved.
- Exact next step: guarded cleanup, followed by separate guarded default generation.

### Session 3 final checkpoint — 19:13 UTC (before 25 minutes)

**Stopped on the first non-facing failure, as instructed. No corrective retry or further Unreal launch occurred.**

#### Completed

- New guarded immutable-log launcher: `Tools/Unreal/chars_session3_run.sh`. It uses the pgrep guard, `/tmp/selene-unreal.lock`, 600-second commandlet/build alarms and the requested 75-second game alarm (40 seconds for Champion). The launcher was not edited while running.
- Scoped cleanup in its own fresh process: `cleanup-exit.txt` = **0**, `cleanup.json` audited 48 generated packages with no external references and deleted only `/Game/Selene/Characters/Fixer/` and `/Courier/`.
- Separate default regeneration: `create-exit.txt` = **0**; both yaw and bind-quaternion environment overrides explicitly removed. `Fixer-base.json` and `Courier-base.json` contain exactly 21 canonical animation/blend-space names each and no pose-yaw override. With the three rigs/retargeters, each base inventory is 24 assets. There is no session-3 numerical facing assertion or expected-facing gate.
- Exactly **11 GASP clips per hero** retargeted with the existing batch pattern: idle, walk/run/sprint loops, walk/run starts, walk/run/sprint stops, walk/run pivots. `clips-exit.txt` = **0**; editor summary **Success - 0 errors, 22 warnings**. Warnings are animation-compression ConditionalPostLoad dependency messages. Frames, rate, duration, skeleton, hips track, notifies, canonical output paths and saves passed. `clips.json` records hashes.
- Dense **60 Hz read-only loop audit** of Manny and both new heroes completed: `measurement.json` = success, nine clips, RAW/COMPRESSED and root-lock-respecting/unlocked modes; each time is evaluated twice to avoid initialization artifacts.

#### Failure and evidence

- `correct-exit.txt` = **255**, `correct-editor.log:1661`: `Unvalidated root translation/rotation model: FixerWalkLoop`.
- The copied `gasp_loop_in_place.py` algorithm assumes target hips equal source pelvis times a single scale derived from pelvis Z, with maximum 0.001 cm residual before it subtracts scaled source root XY. That assumption does not hold for these default-retargeted heroes. This is a **loop-correction model check**, not a facing check or proof that the animation looks wrong.
- Fixer walk maximum residual **5.260487 cm**, scale **1.068392676**. Source root quaternion XYZ remains zero; translation residual is the failed part.
- Read-only diagnosis from the saved audit (`loop-model-diagnosis.json`):

| Hero | Walk residual cm | Run residual cm | Sprint residual cm |
| --- | ---: | ---: | ---: |
| Fixer | 5.260487 | 8.657182 | 7.844441 |
| Courier | 1.843052 | 3.300057 | 3.150457 |

- Failure occurs in preflight before any correction/save: `loop-correction.json` has empty `clips` and `saved_packages`. Final hashes prove all **22 GASP packages are unchanged from successful retargeting**. No backup restoration or asset retry was needed.

#### Unfinished / visual limits

- **Corrected WalkLoopSpeed / RunLoopSpeed / SprintLoopSpeed: not measured.** The audit contains pre-correction poses, which are not accepted corrected-loop speeds.
- **Screenshot names: none** for idle, walk, sprint, stop, jog-back, pivot or jump. No game run, no visible facing judgment, no visual correction, no feet/grounding/T-pose/toon acceptance, and no Champion load.
- Toon MIs, imported material relinks/usage changes, Fixer/Courier roster entries, narrow cook directories and SeleneEditor build remain undone.
- Session-specific material, verification, speed and contact-sheet scripts are prepared but **unexecuted**. They are not runtime evidence. The prepared verify stage also expects roster lines, which have not been added.
- `verification.json`: exactly **35 canonical assets per hero** on disk, no numbered duplicates; all Source, Config (including DefaultGame.ini and DefaultEngine.ini), imported hero assets, other heroes, existing materials and existing scripts match entry hashes. No commits, browser, downloads or paid services. Final pgrep is empty and the lock is absent.

#### Exact next step

In a newly authorized continuation with new immutable evidence/report names, keep the default rigs and all 22 GASP outputs intact. Use `Saved/Chars/session-3/measurement.json` to diagnose the actual horizontal root-travel transfer separately from the pelvis-Z scale. Adapt and validate the in-place subtraction for these heroes; do not merely relax the 0.001 cm model threshold or resurrect a facing assertion. Preserve hips Z/rotation/scale and all other tracks, then fresh-reload the corrected loops and measure stance speeds. Only after that continue toon/material setup, Champion-based roster transforms (no SecondaryChains), narrow cook dirs, editor build, the requested 75-second captures with at most one visual-facing correction per hero, and a short Champion load.
