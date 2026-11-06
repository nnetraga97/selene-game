# Sparrow integration progress

## Session 1 — 2026-11-06

- Started **17:06 UTC**. Stop before approximately **17:31 UTC**.
- Read `SPARROW-BRIEF.md` and its specified C++, configuration, retarget,
  secondary-motion, material-usage, and GASP progress sources.
- Initial game: **PID 99336**, `UnrealEditor ... Selene.uproject
  /Game/Selene/Maps/Town -game`, log `Saved/playtest3.log`. Never interrupt it.
- Initial Git branch `setup/project-scaffold`, origin
  `https://github.com/nnetraga97/selene-game.git`. Existing edits include
  `Config/DefaultEngine.ini` and several Unreal scripts; preserve them.
- Checkpoint currently **offline preflight only; step 1 remains incomplete**.
  No roster/configuration, source, material, or animation changes yet.

### Offline findings (not an Unreal or visual verification)

- All 19 named Paragon candidate `.uasset` files exist, including all three
  idle candidates, jog/sprint loop/start/stop/pivot, four jump clips, and turns.
- Raw strings in the default mesh include `ponytail_01..04`,
  `hair_curls_A/B_l/r_01`, `hair_top`, front straps, skirt/back/chest cloth,
  `quiver`, and the bow shaft/string bones. The shared skeleton also names
  skin-specific hair/cloth chains absent from the default mesh's strings.
  **Do not configure Kawaii from skeleton names alone.** Verify the default
  mesh hierarchy first.
- Default mesh strings include material slot `M04_BowAndArrow` and bow bones:
  evidence suggests an integrated bow, but actual sections/geometry remain
  unverified. Do not add an extra bow component from this preliminary evidence.
- The default mesh references 14 distinct material package paths, including
  `Skins/Rogue/Materials/M_M04_TeethAndTongue` and `M_TearLine_Inst2`. These are
  references already on the default mesh, not a request to select the Rogue
  skin. A precise cook plan must account for the actual dependency closure.
- Existing native fields cover the requested clips, speed values, camera/mesh
  placement, and Kawaii chains. `AnimClass` must stay unset for Sparrow.
  No new C++ roster field is currently justified.
- Existing `character_retarget.py` is tailored to Mixamo and retargets ABP
  dependencies; **do not run it unchanged for Sparrow**. Make a new walk-only
  script after the audit, with `include_referenced_assets=False` and four inputs.
- Original Paragon animation files are outside the permitted edit allowlist.
  If root flags need changing, report it or create scoped copies of her own
  clips under `/Game/Selene/Characters/Sparrow/Anims/Paragon`; never edit the
  source pack's sequences. Preserve authored locomotion rather than borrowing
  GASP jog/sprint/jump.

### Prepared tools

- `Tools/Unreal/sparrow_audit.py`: read-only default-mesh/material inventory,
  reference bone positions, candidate flags/notifies, and compressed pose
  sampling at 60 Hz with playback/unlocked root evaluation. Reports stance
  estimates for all four horizontal facing axes using the GASP stance filters.
  Never saves assets; NullRHI explicitly leaves shader/visual approval pending.
- `Tools/Unreal/sparrow_session_run.sh`: checks the user's game every 30 seconds
  for up to 15 minutes; then either stops or runs the audit behind the exact
  Unreal lock and `perl` alarm required by the brief. Checks again immediately
  before launch. Evidence goes under `Saved/Sparrow/<session>/`.
- These tools are preparation, **not yet an executed Unreal audit**. Final
  session evidence and the exact next step will be appended below.

### Offline verification and evidence

- `Saved/Sparrow/session-1/offline-preflight.json`: all 19 candidate files,
  sizes and SHA-256 hashes; raw default-mesh/shared-skeleton name hints;
  14 material package references; mesh/skeleton hashes; protected engine-config
  hash. Raw strings are explicitly **not** a verified bone hierarchy or slot count.
- The same report verifies the four existing Manny source packages and records
  their hashes and exact destinations under
  `/Game/Selene/Characters/Sparrow/Anims/GASP/`, with suffix `_Sparrow`:
  `M_Neutral_Walk_Loop_F`, `M_Neutral_Walk_Start_F_Lfoot`,
  `M_Neutral_Walk_Stop_F_Lfoot`, `M_Neutral_Walk_Pivot_F_B_Lfoot`.
- `Saved/Sparrow/session-1/static-verification.json`: audit passes `ast.parse`,
  launcher passes `bash -n` (exit 0), no asset-save/delete/rename/duplicate or
  material-recompile API calls in the read-only audit. This is static validation,
  **not validation of its Unreal Python API calls**.
- `Saved/Sparrow/session-1/before.json`: size/mtime baseline for 3,232 files
  under Content/Config/Source/Tools (including the two new scripts).
  At 17:19 UTC, excluding the new scripts, zero changed/missing existing files;
  `DefaultEngine.ini` hash unchanged. `git-before.txt` preserves dirty state.
- `Saved/Sparrow/session-1/wait.log`: 30-second process checks beginning at
  **17:09:52 UTC**. Do not treat the live user's existing `Saved/playtest3.log`
  as evidence of Sparrow loading or of this session's success/failure.

### Remaining work after the offline checkpoint

1. Execute the prepared read-only audit once the user's game is closed, with
   a fresh evidence directory. Inspect `audit.json` and `audit-editor.log`;
   confirm actual default-mesh parents, bounds, material slots/base usage flags,
   loop stance estimates, and original root-motion flags. The audit does not
   verify Metal rendering, exact mesh sole placement, or bow geometry.
2. Finish step 1 with visual inspection of the default mesh/bow/materials and
   idle candidates. Do not mistake the NullRHI audit for shader approval.
3. Create a **new** Sparrow-specific IK/walk retarget script using the existing
   retarget implementation as a reference, not by running its Mixamo/ABP batch.
   Create `IK_Sparrow` and `RTG_Manny_To_Sparrow`, retarget only the four walks,
   and measure the resulting walk speed. Use Sparrow's own other locomotion.
4. Add the roster/cook references with measured values; preserve default
   materials; fix only required usage flags. Add verified mesh chains/colliders
   via `secondary_roster.py`. Build and run the brief's full screenshot/log
   acceptance plus Champion/Angel load checks.

**No measured Sparrow speed, height/placement value, shader verdict, retargeted
asset, in-game screenshot, or gameplay acceptance is established yet.**

### Final checkpoint — stopped 17:26 UTC (about 20 minutes)

**Blocked: waiting for the user's game to close. Sparrow is not playable yet.**

- Completed **31 process checks**, every approximately 30 seconds, from
  **17:09:52 through 17:24:54 UTC** (902 seconds). Every check found the same
  user's **PID 99336**. The launcher exited **2**, as intended for this blocker.
  A final independent process check at 17:25 UTC still found that game.
- No Unreal process was launched; no Unreal lock was acquired or removed;
  the user's game was never signalled or killed. No retry was attempted.
- Step 1 is **partially complete: verified offline inventory and prepared audit**.
  Steps 2–6 (retarget, roster, secondary setup, builds, game acceptance) are
  **not started**. No Unreal audit failure or shader result exists to diagnose.
- `Saved/Sparrow/session-1/verification.json` records final validation:
  **3,230 existing files checked, zero metadata changes/deletions**;
  `DefaultEngine.ini` hash unchanged; Python/shell syntax pass; no trailing
  whitespace in the three new source/doc files. `git-after.txt` records scope.
- Changed only the two new scripts and this progress document, plus ignored
  evidence under `Saved/Sparrow/session-1/`. No commits, browser, downloads,
  paid services, builds, or packaging. Existing user changes remain intact.

### Exact next step for session 2

Read this progress file and the brief. Once the game can close naturally,
run the prepared **read-only audit** from the project root with fresh evidence:

```sh
SELENE_SPARROW_SESSION=session-2 bash Tools/Unreal/sparrow_session_run.sh
```

The launcher performs the required `pgrep`/30-second waiting guard, acquires the
brief's lock only after no matching process remains, rechecks, then uses the
900-second alarm wrapper. **Do not run its default `session-1` again**; its
existing wait evidence intentionally prevents replay. Inspect
`Saved/Sparrow/session-2/audit.json`, `audit-editor.log`, and `audit-console.log`
before proceeding. The script's Unreal API calls are not yet runtime-tested;
follow the brief's stop/one-obvious-fix rule if it fails. Then finish step 1's
visual/material/facing/height/bow checks and proceed through the remaining work
above in order. Do not claim measured speeds or a playable roster until verified.


## Session 2 — 2026-11-06

- Started **17:46 UTC**; checkpoint saved **18:10 UTC**, within the approximately
  25-minute session budget. The prepared audit was the only Unreal launch.
  Wall-clock time advanced substantially during startup; the Zen utility also
  logged a timeout. Do not attribute all elapsed time to that warning alone.
- Ran exactly `SELENE_SPARROW_SESSION=session-2 bash Tools/Unreal/sparrow_session_run.sh`.
  Its fresh process guard found no user's game, acquired the required lock,
  rechecked, and launched the read-only commandlet with `perl`'s 900-second alarm.
- **Verified checkpoint: data audit succeeded; step 1 visual qualification remains
  incomplete. Sparrow is not playable yet.** No retry or corrective asset edit.
- `audit.json` reports success for **all 19 clips**, with both playback and
  unlocked compressed poses sampled at 60 Hz. Commandlet/launcher exit **0**;
  log: **Success - 0 error(s), 2 warning(s)**. No asset save operations.

### Confirmed data findings

- Default mesh has **144 bones and 14 material slots**. All 14 resolved base
  materials report `used_with_skeletal_mesh=true`; no usage-flag change was needed
  by this audit. Full material/parent paths are in `audit.json`. The default mesh
  really references the Rogue teeth/tongue material and tear-line instance.
  NullRHI does **not** establish Metal/Substrate shader or visual correctness.
- Actual default-mesh secondary hierarchy confirms `ponytail_01 -> 02 -> 03 -> 04`
  parented to `head`; two-bone `front_strap`, `skirt_back_cloth`,
  `skirt_cloth_l`, `skirt_front_cloth`, `back_tail_cloth`, and left/right
  `chest_cloth` chains. Hair curls, `hair_top`, and `front_strap_small` are
  individual bones. `quiver` is parented to `thigh_twist_01_r`: do not blindly
  treat it as a dangling multi-bone chain. Complete parents/positions are recorded.
- Mesh bounds height is **255.880 cm**, origin `(0,-5.445,54.214)`, extent
  `(40.158,18.867,127.940)`. These are asset bounds, **not body height**: the lower
  bound is negative and weapon/bounds extensions may contribute. Do not use
  this number for EyeHeight or mesh sole placement. Reference head-bone Z is
  **164.559 cm**, pelvis Z **110.188 cm**, toes Z approximately **2.521 cm**,
  ankles Z approximately **9.573 cm**; none is a sole-surface measurement.
- Bow/string bones and bow/arrow/string material slots are present on the default
  mesh. Integrated visible geometry remains to be confirmed in rendered shots.
- All 19 clips report root-motion extraction **false**, force-root-lock **false**,
  rate scale **1**, and nonadditive animation. Every sampled root translation
  is `(0,0,0)` in playback and unlocked modes. No original animation edit or
  in-place copy is currently indicated by root translation. Pelvis motion,
  turning orientation, notifies, transitions, and jump behavior still need visual/runtime review.
- Provisional **+Y-forward** bilateral stance medians (same stance filters as GASP):
  - `Jog_Fwd`: **375.728 cm/s**, 51 samples, p10–p90 **353.143–410.670**.
  - `Sprint_Fwd`: **833.369 cm/s**, 31 samples, p10–p90 **792.148–857.653**.
  These are measured contact-speed estimates, conditional on visual facing
  confirmation; they are not proof of no sliding. There is no Sparrow walk yet,
  so **WalkLoopSpeed remains unmeasured**. Per-clip stance results, flags, durations,
  notify counts, and full sampled trajectories are preserved in the reports.

### Warnings / failures / verification

- **No audit failure or crash.** Two distinct commandlet warnings:
  1. Zen utility process ran 25.1 seconds without completing and was aborted
     by Unreal's own startup code. No process was manually killed by this session.
  2. Legacy `/Game/ParagonSparrow/Characters/Heroes/Sparrow/Meshes/Orion_Proto_Retarget`
     cannot load because class `Rig` does not exist. Mesh/skeleton and all 19
     sequences still loaded and sampled successfully. The planned new IK rig
     does not yet exist; do not claim the legacy warning has been fixed.
- At **18:09:11 UTC**, verification checked **3,288 existing files** under
  Content/Config/Source/Tools: **zero modified, deleted, or added files**.
  `Config/DefaultEngine.ini` SHA-256 unchanged. No Selene Unreal process remains;
  `/tmp/selene-unreal.lock` was released. No source/config/content edits.
- Changed only this progress document, plus ignored audit/verification evidence
  under `Saved/Sparrow/session-2/`. Existing user changes were preserved.
  No commits, browser, paid services, downloads, builds, or packaging.
- Evidence (relative to project root):
  - `Saved/Sparrow/session-2/audit.json`: complete successful audit, SHA-256
    `9286296a4fc8b02c4cbf89e37c5aa1b16efc7306e5f1e6e2d8bd78e7b1c9ce9a`.
  - `Saved/Sparrow/session-2/audit-summary.json`: compact material, hierarchy,
    landmark, root, and per-clip speed summary.
  - `Saved/Sparrow/session-2/audit-editor.log`, `audit-console.log`,
    `log-summary.json`, `wait.log`: execution, warnings, and guard evidence.
  - `Saved/Sparrow/session-2/before.json`, `engine-before.sha256`,
    `verification.json`, `git-before.txt`, `git-after.txt`: scope verification.

### Exact next step for session 3

**Do not rerun session-2's successful audit.** Read its summary and warnings,
then finish brief step 1 with a new Sparrow-specific **rendered, transient-actor
inspection script** under `Tools/Unreal/` (use `character_motion_shots.py` as the
API/capture pattern, not unchanged). Use the default mesh and its own materials,
compare `idle`, `idle_relaxed`, and `Travel_mode_Idle`, and capture front/back/side
views plus feet/bow detail. Record actual component/sole placement and head/eye
height; visually confirm +Y facing and whether the bow is integrated. Do not
save the map or mesh. Put fresh evidence under `Saved/Sparrow/session-3/`.
Before that launch, perform the required pgrep guard, acquire the Unreal lock,
recheck, and use the 900-second alarm wrapper; release the lock on exit/failure.
Inspect every PNG and shader/material/load warnings before proceeding.

Then, in order: create `IK_Sparrow` and `RTG_Manny_To_Sparrow` with a new scoped
walk-only script; retarget exactly the four previously inventoried Manny walk
clips with suffix `_Sparrow` and `include_referenced_assets=False`; measure the
resulting walk. Add the roster with her own Paragon clips/materials and measured
placement/speeds, narrow cook references, and verified Kawaii chains via
`secondary_roster.py`. Build SeleneEditor, then execute full in-game screenshot
acceptance and Champion/Angel load checks. **None of these later steps was
started or verified in session 2.** Continue to obey stop-on-failure and the
25-minute checkpoint limit.

## Session 3 — 2026-11-06

- Started **18:20:51 UTC**; stopped/checkpointed **18:31 UTC**, early under the
  stop-on-failure rule. No remaining Selene Unreal process or lock.
- **Sparrow is configured and loads in game, but full playable acceptance FAILED.**
  The camera correction did not produce usable foot-contact views, and the
  retargeted walk stop/pivot have nonzero locked-root offsets requiring repair.
- Completed the brief's rendered inspection, asset creation, roster/secondary
  configuration, and SeleneEditor build. Game verification is partial;
  Champion/Angel smoke runs and Shipping build were not run after the failure.

### Rendered inspection and selected placement

- One transient-actor editor run, six PNGs, all inspected:
  `Saved/Sparrow/session-3/inspection/{idle,idle_relaxed,Travel_mode_Idle,relaxed_back,relaxed_side,relaxed_feet}.png`.
  No map or mesh was saved. Run exit **0**.
- Selected **Travel_mode_Idle** for town standing: the `idle` and `idle_relaxed`
  snapshots both hold a drawn bow, while travel idle lowers it. This is a visual
  choice among the three audited original Paragon clips, not a new animation.
- Confirmed **+Y-forward**, integrated bow/string/arrow geometry, and own skin,
  leather, metal, eye and hair materials rendering without default-material fallback.
  No additional bow component or material override.
- At component origin `(-1000,0,0)`, yaw 0, soles look planted on the plaza.
  Roster uses `MeshOffset=(0,0,-87.5)` for the existing 87.5 cm capsule half-height,
  yaw **-90**, boom **350 cm**. No precise skin-vertex sole measurement claimed.
  Travel-idle eye-bone heights: **160.245 / 160.057 cm**; configured EyeHeight **160.15**.
- Evidence: `inspection/inspection.json`, `inspection-review.json`,
  `inspection-editor.log`, `inspection-console.log` under the session directory.

### Created assets, roster and secondary motion

- `Tools/Unreal/sparrow_retarget.py` created/saved eight total Sparrow packages
  together with the cook-label stage (all under `/Game/Selene/Characters/Sparrow`):
  - `IK_Manny` (independent copy of Champion's existing Manny source rig),
    `IK_Sparrow`, `RTG_Manny_To_Sparrow`.
  - Exactly four sequences in `Anims/GASP/`, suffix `_Sparrow`:
    `M_Neutral_Walk_Loop_F`, `M_Neutral_Walk_Start_F_Lfoot`,
    `M_Neutral_Walk_Stop_F_Lfoot`, `M_Neutral_Walk_Pivot_F_B_Lfoot`.
  - `PAL_Sparrow`, created by `sparrow_cook_label.py`.
- Sparrow rig has **21 explicit body/finger chains**, all exactly mapped, with
  an aligned target pose. This is FK retargeting: `Run IK Rig` is disabled because
  the explicit target rig has no solver/goals. Pelvis/FK/root-motion ops are enabled;
  source and target root-motion bones are both `root`. No ABP or referenced-asset
  batch retargeting. Source rig, source sequences and Paragon pack were not saved.
- Retarget commandlet exited **0**, `Success - 0 error(s), 5 warning(s)`.
  `retarget.json` reports script success, **not final animation acceptance**.
  Its playback samples later exposed the transition-root issue below.
- Loop speeds configured in `Config/DefaultGame.ini`:
  - Walk **221.822 cm/s**, 109 stance samples, p10–p90 **210.680–224.079**;
    pelvis horizontal loop seam **0.0173 cm**.
  - Jog **375.728 cm/s**, sprint **833.369 cm/s**, from session 2's successful
    +Y stance estimates, now with facing visually confirmed.
  - Method remains 60 Hz compressed toe sampling, lowest 35% heights,
    vertical speed <25 cm/s, backward speed >30 cm/s, bilateral median.
    These are clip estimates, not proof of zero gameplay sliding.
- Sparrow roster uses original `Travel_mode_Idle`, `Jog_Fwd`, `Sprint_Fwd`,
  `Jog_Fwd_Start/Stop/Pivot180`, `Sprint_Fwd_Stop`, `Jump_Start`, `Jump_Apex`,
  and `Jump_Land`; four new walks; no AnimClass or OverrideMaterial.
- Narrow cooking: only `/Game/Selene/Characters/Sparrow` added to always-cook
  directories. `PAL_Sparrow` explicitly roots the mesh and 14 selected animations,
  letting mesh/material dependencies include the actual shared/Rogue assets.
  No whole-pack/whole-animation-folder cook directive. Cook-label commandlet exit
  **0**; `cook-label.json` lists all roots. Actual cooking/packaging remains untested.
- `secondary_roster.py --character Sparrow` added **8 chains**: ponytail,
  front strap, three skirt panels, back tail and two chest cloth chains; **1 sphere
  + 8 capsules** using verified Sparrow body names. Quiver, weapon, facial and
  singleton hair bones are untouched. Tuning starts from Champion values.
  Existing Champion/Angel/Manny roster lines are byte-identical to their initial state.
- No material usage fixes were needed: both game logs contain no missing usage
  flag messages. No Paragon material asset was changed. No C++ field/change needed.

### Build and game evidence / failure

- `SeleneEditor Mac Development` build **exit 0**, **4.07 s**, `Result: Succeeded`:
  `Saved/Sparrow/session-3/build-editor.log`.
- `sparrow_stage_run.sh` performed the pgrep guard, `/tmp/selene-unreal.lock`,
  post-lock recheck, and 900-second Perl alarm for **all five launches**:
  inspection, retarget, cook label, initial game, camera-correction game.
- Both `-game` runs used `selene.Character Sparrow,selene.AutoWalk 1,selene.AutoShots 1,selene.SecondaryDebug 1`
  plus a bounded `-benchmark -seconds=24 -fps=30` exit. Both exited **0** normally.
  Because asset loading consumed frames, each produced **21 Sparrow PNGs** through
  character time 20.4 seconds. Every one of the **42 game PNGs was inspected**.
- `game-Sparrow-editor.log` and `game-Sparrow-camera-editor.log` confirm
  **Active playable character: Sparrow** and **8 Kawaii chains, 1 sphere + 8 capsules**.
  Debug logs show speeds 0 / 150 / 350 / 600 cm/s and secondary displacement.
  Animated poses, bow and own materials are visible; no T-pose observed.
- **Visual acceptance failure:** every game screenshot looks upward from below
  Sparrow; ground/feet cannot be assessed. Initial captures are preserved in
  `Saved/Sparrow/session-3/game/`, second captures in `game-camera/`.
  Only this session's initial working `Saved/AutoShots/Sparrow_*.png` copies were
  removed after byte-verifying the archive, to avoid overwriting evidence.
- **One corrective attempt:** added a runtime console set of controller pitch to
  -15, with `getall` before/after. Log proves pitch **2.788785 -> -15.0**, but
  screenshots remain unusable. Thus initial controller pitch alone was not the
  cause; actual camera transform, subsequent input and collision remain unmeasured.
  No second variation, new harness or source/map camera change was attempted.
- **Separate confirmed data defect discovered while reviewing saved samples:**
  all new walks use `force_root_lock=true`, `enable_root_motion=false`,
  `ANIM_FIRST_FRAME`. The walk stop root remains at **Y=-318.493 cm** and pivot
  at **Y=-651.148 cm**; their evaluated pelvis shares the large offset. The loop
  root is zero; start is Y=-0.524 cm. These nonzero transition origins are not
  acceptable capsule alignment. No repair was attempted after stopping.
  `transition-root-review.json` records first/last poses and pelvis ranges.
- Existing engine/plugin noise remains: `AgentSkill` and `PythonTestRunner`
  initialization AttributeErrors (also present in pre-session `Saved/playtest3.log`),
  editor widget registration warnings, town translucent/Nanite glass/leaves warnings,
  and the legacy missing `Orion_Proto_Retarget` Rig class. No new Sparrow shader
  compile or configured-asset load failure was observed. See `log-summary.json`.
- **Unverified:** gameplay foot contact/sliding/sole height, complete stop/pivot
  alignment, landing quality, C-key cycle, Champion/Angel live load checks,
  Shipping build, cooked dependencies. Do not describe Sparrow as fully accepted.

### Scope verification

- `verification.json`: of **3,288 existing Content/Config/Source/Tools files**,
  only `Config/DefaultGame.ini` and `Tools/Unreal/secondary_roster.py` changed;
  no existing asset/source file changed or disappeared. Eight new scoped assets
  and four new scripts; each asset size/hash recorded.
- `Config/DefaultEngine.ini` hash unchanged; existing other roster lines unchanged.
  Python syntax, shell syntax, and scoped `git diff --check` passed.
  Final pgrep found no Unreal process; lock released. No commits, browser,
  downloads, paid services, map saves or pack edits. This progress file is appended.

### Exact next step for session 4

**Do not rerun the audit, retarget batch, or cook-label creation. The assets exist.**
First write a small scoped repair script for the existing four `_Sparrow` sequences:
change their root lock from `ANIM_FIRST_FRAME` to **ZERO** (or otherwise normalize
only their root origins), keep root extraction disabled and force lock enabled,
then re-evaluate root/pelvis playback to verify the stop/pivot no longer sit
318/651 cm away. Save only those Sparrow output assets. Use fresh session-4
logs/reports and the required process/lock/alarm guards.

Then diagnose the **live** camera after Sparrow finishes loading: read pawn,
capsule, camera and controller transforms; temporarily ignore look input and set
an ordinary third-person view for the capture. Use a short transient runtime
script or console inspection under Tools/Unreal, not an elaborate harness or a
map save. The startup-only pitch set did not solve it. Run one fresh bounded
AutoWalk/AutoShots cycle and inspect all PNGs, explicitly including the repaired
walk stop/pivot (the existing AutoWalk reverses while jogging, so it does not
exercise those walk transitions by itself). Only after that passes, complete
Champion/Angel load checks and optional Shipping build. Keep the configured
original Paragon clips/materials and re-use the existing measured loop speeds.


## Session 4 — 2026-11-06

- Started **18:36:42 UTC**; stopped/checkpointed **18:47 UTC**, within 25 minutes.
- **Steps 1 and 2 complete. All three requested game captures ran and were
  reviewed, but full Sparrow visual acceptance remains incomplete.** Body/root
  behavior improved; the retargeted jog has a suspicious bow/string silhouette.
  A separate Angel launcher bookkeeping failure triggered the stop-and-report rule.
- Controller's already-built `TickDebugDrivers` pitch fix was used unchanged.
  No camera console hacks, C++ edits, rebuild, benchmark flag, or game rerun.
- All evidence is under `Saved/Sparrow/session-4/`. Four Unreal launches total:
  one clip commandlet, then Sparrow (75 s), Champion (45 s), Angel (45 s).
  Every launch used the process guard, `/tmp/selene-unreal.lock`, a post-lock
  process recheck and a Perl alarm. No user's game was running or interrupted.

### 1. Existing walk root repair — complete

`Tools/Unreal/sparrow_session4_clips.py` first backed up the four existing walks
into `original-walks/`, changed only their output root settings to
`enable_root_motion=False`, `force_root_lock=True`, `RootMotionRootLock.ZERO`,
and sampled compressed playback at 60 Hz. The whole walk phase passed before
any run was retargeted. No source track, source sequence, pack or rig was saved.

| Existing walk output | Previous nonzero root Y (cm) | Corrected root XYZ, all samples | Corrected pelvis Y range (cm) |
| --- | ---: | --- | --- |
| Loop | 0 | (0,0,0) | -3.7878 to 2.4172 |
| Start | -0.5243 | (0,0,0) | -7.4047 to 2.4092 |
| Stop | -318.4932 | (0,0,0) | -4.5598 to 7.9774 |
| Pivot | -651.1483 | (0,0,0) | -4.1084 to 9.3617 |

Stop pelvis ends at Y **-2.9746 cm**, pivot at **-0.2424 cm**. Thus the
318/651 cm offsets are gone in evaluated playback. Evidence: `clips.json`
contains before/after samples; `root-speed-summary.json` is the compact report.
These numerical checks are same-process compressed evaluation; a separate
fresh-process numerical reload was prepared but **not executed** after stopping.

### 2. Run retarget, speed, and roster — complete

- Reused existing `RTG_Manny_To_Sparrow`, Manny/Sparrow meshes and existing rigs.
  Exactly four input sequences from `/Game/Selene/Animation/GASP/`:
  `M_Neutral_Run_Loop_F`, `M_Neutral_Run_Start_F_Lfoot`,
  `M_Neutral_Run_Stop_F_Lfoot`, `M_Neutral_Run_Pivot_F_B_Lfoot`.
- Created exactly four outputs in
  `/Game/Selene/Characters/Sparrow/Anims/GASP/`, suffix `_Sparrow`,
  `include_referenced_assets=False`, no overwrite and no referenced-asset batch.
  All use the same ZERO root fix. Root XYZ is **(0,0,0) at every sampled frame**.
  Run stop/pivot previously evaluated at root Y **-498.8018 / -487.2523 cm**;
  corrected pelvis Y ranges are **-19.2421 to 17.5478 / -28.5236 to 5.8587 cm**.
- Run loop ground speed **555.060921 cm/s**; configured `RunLoopSpeed=555.061`.
  **15 stance samples**, p10–p90 **534.819–558.308 cm/s**. Method: compressed
  poses at 60 Hz, +Y forward, bilateral toes, lowest 35% sampled heights,
  absolute vertical speed <25 cm/s and backward speed >30 cm/s.
- Current C++ clamp is **0.5–1.5**, verified in source. At 350 cm/s the new
  run's rate is **0.630561**, inside that clamp. This is a calculated match,
  not proof of zero foot sliding from one-Hz screenshots.
- Changed only Sparrow's `RunLoop`, `RunStart`, `RunStop`, `RunPivot`,
  `RunLoopSpeed` fields in `Config/DefaultGame.ini`. Own sprint/sprint-stop,
  idle, jumps, materials, placement, walks and secondary configuration remain.
  All other config lines are byte-identical to the baseline. `roster-change.json`.
- Commandlet exit **0**, `Success - 0 error(s), 5 warning(s)`:
  `clips-editor.log`, `clips-console.log`, `clips-exit.txt`.
  Warnings: existing legacy missing `Orion_Proto_Retarget` Rig class and four
  `EnsureDependenciesAreLoaded` animation-import-data messages during compression.
- Existing `PAL_Sparrow` was not rebuilt or changed. It still explicitly roots
  the old selected Paragon clips; the existing always-cook Sparrow directory
  covers the new run outputs. Actual cooked dependency behavior remains untested.

### 3. Normal game capture and image review

Exact game commands were `-game -ExecCmds="selene.Character <Name>,selene.AutoWalk 1,selene.AutoShots 1"`,
with `-unattended -nop4 -nosplash -windowed -ResX=1280 -ResY=900`.
No `-benchmark`, fixed-fps/seconds flags, pitch console commands or extra debug
settings were added. The Perl alarms bounded wall-clock launch time.

- **Sparrow:** expected alarm exit **142**, **56 PNGs**, time 000.4–056.1.
  Log confirms active Sparrow and **8 chains, 1 sphere + 8 capsules**.
- **Champion:** expected alarm exit **142**, **27 PNGs**, time 000.0–026.4.
  Log confirms active Champion and **13 chains, 1 sphere + 8 capsules**.
- **Angel:** reached its alarm with **28 PNGs**, time 000.1–027.5; log confirms
  active Angel and **12 chains, 1 sphere + 8 capsules**. Its surrounding Bash
  launcher then exited **2** as detailed below; do not call its wrapper successful.
- Moved only this session's PNGs from `Saved/AutoShots/` into `game-Sparrow/`,
  `game-Champion/`, `game-Angel/`; SHA-256 verified after each move. The initial
  AutoShots PNG baseline was empty. Manifests: `<Name>-shots.json`.
- Inspected **all 111 PNGs** via labeled contact sheets (7 Sparrow, 3 Champion,
  4 Angel); selected Sparrow originals were also opened full-size. Contact
  sheets are review aids, not modified source evidence. `visual-review.json`.

Specific evidence (relative to `Saved/Sparrow/session-4/`):

| Phase/check | Screenshot(s) | Observation |
| --- | --- | --- |
| Walk | `game-Sparrow/Sparrow_013.6.png` | Upright walk, stance near pavement, usable camera |
| Sprint | `game-Sparrow/Sparrow_004.4.png` | Own sprint pose, curved bow carried low |
| Stop/idle | `game-Sparrow/Sparrow_018.6.png` | Planted stance and normal own materials |
| Jog-back/start phase | `game-Sparrow/Sparrow_007.5.png`, `Sparrow_019.7.png` | Running arms no longer aim a drawn bow; prop concern below |
| Pivot/reversal phase | `game-Sparrow/Sparrow_009.5.png`, `Sparrow_021.7.png` | Facing reversed, no gross mesh displacement in sampled frames |
| Jump | `game-Sparrow/Sparrow_034.8.png` | Original airborne jump, ground/shadow visibly separated |
| Landing/recovery | `game-Sparrow/Sparrow_035.9.png` | Returned to ground stance |
| Champion smoke check | `game-Champion/Champion_004.1.png`, `Champion_013.2.png` | Animated sprint/walk, own materials and normal scale |
| Angel smoke check | `game-Angel/Angel_004.2.png`, `Angel_013.3.png` | Animated body/wings/dress, own materials and normal scale |

No T-pose, persistent body floating/sinking, or recurrence of the metre-scale
mesh displacement was seen. The initial doorway briefly occludes/compresses the
camera; later views are ordinary above-ground third person. Each character's
first screenshot is gray during startup, then colors resolve. No new missing
skeletal usage flag, configured animation/mesh load failure or shader compilation
failure was found. Existing AgentSkill/PythonTestRunner initialization exceptions,
widget warnings, translucent/Nanite scene warnings, and the default audio notice
remain. `log-summary.json` preserves all warnings/errors rather than claiming a
clean game log.

**Unresolved visual concern:** `Sparrow_019.7.png`, `_020.7.png`, `_031.8.png`,
`_032.8.png`, `_043.9.png` show an unusually long diagonal bow/string/arrow
silhouette during retargeted jogging. The drawn-bow combat stance is gone, but
proper weapon grip/placement is **not accepted**. The old audit confirms
`bow_base` is parented to `hand_l` yet has a reference component position near
the origin; `arrow_nock` is parented to `hand_r`. Unmapped reference weapon
transforms are a hypothesis, not a confirmed diagnosis. No weapon edits made.

One-Hz frames cannot prove no sliding or precisely identify montage onset.
Standard AutoWalk stops from sprint and reverses while jogging; dedicated
walk-stop/walk-pivot gameplay triggers were not added. Their root repair has
numerical evidence, not a separate walk-transition gameplay test.

### Failures, stop, and scope

1. Contact-sheet helper failed at `import PIL`: system Python has no Pillow.
   This occurred before any screenshot move. One diagnosed helper correction
   used installed macOS AppKit via `sparrow_session4_contacts.swift`; no install,
   network, image generation or Unreal retry. `review-helper-fix.json`.
2. **Launcher bookkeeping failure:** while Angel was executing, the session
   added the prepared `verify` case to the same shell script. On return from
   the expected SIGALRM, Bash resumed reading at a changed file offset and
   reported unexpected EOF/matching quote. Shell exit **2**, not 142; no
   `game-Angel-exit.txt` was written. The captured shell output did report
   `Alarm clock: 14`; the game had loaded and written its 28 screenshots.
   **Do not edit a launcher while it is running.** The current script passes
   `bash -n`, but that is not a successful retry. `launcher-failure.json`.
3. Stopped further launches and edits to animation assets. No game/retarget
   retries. `sparrow_session4_verify.py` is a **prepared, unexecuted** read-only
   fresh-root/bow-distance diagnostic, not evidence of a result.

`verification.json` checks **3,300 existing files**: only four Sparrow walk
packages plus `DefaultGame.ini` changed; four run packages and four session
tools were added. No existing file disappeared. No other Content, Paragon,
source, rig, material or secondary-roster file changed. `DefaultEngine.ini`
and the controller's `SeleneCharacter.cpp` hashes are unchanged. Other roster
lines and all non-run Sparrow fields are unchanged. Python syntax, shell syntax
and scoped config `git diff --check` passed. Final pgrep is empty, lock released.
No commits, browser, downloads, paid services, packaging or map changes.

### Exact next step

Do **not** replay root repair, retarget or any completed game stage. In the next
authorized continuation, run the unused read-only stage once:

```sh
bash Tools/Unreal/sparrow_session4_run.sh verify
```

It has fresh, unused `verify-*` log/report paths under this session's evidence
directory, enforces the same guard/lock/900-second alarm, and saves no assets.
Leave the script unchanged until the process finishes. Inspect
`reload-weapon-check.json` for fresh zero roots and `bow_grip_to_left_hand_cm`,
`bow_tip_span_cm`, `arrow_to_right_hand_cm` on all eight retargeted outputs versus
original `Sprint_Fwd` and `Travel_mode_Idle`. Its API calls are syntax-checked but
not runtime-tested. If the prop offset is confirmed, propose the smallest
weapon-only carry-transform correction on Sparrow output sequences, preserving
body motion and original Paragon assets; then a fresh guarded visual check is
needed. Keep acceptance partial until the weapon concern is resolved. No
Champion/Angel rerun is needed just to prove the already-observed loads.
