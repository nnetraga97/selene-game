# Selene AI asset workflow: retrospective (Nov 5–6, 2026)

**Sources:** the Claude Code session `10b0d199…` (Nov 6, 03:23–23:26 UTC); the Codex chat "Review Selene MCP Failures" (`rollout-…01a1af4f…`); the Selene `docs/*-PROGRESS.md` files and `INTERVENTION-LOG.md`; the asset-workflow `work/repairs/*`, `ledger.json` and the uncommitted diffs; `~/.orchestrator/jobs/*.json` and `runs/*`; and the project memory files. All times are UTC. "(inference)" marks a conclusion the files don't prove.

---

## 1. Executive summary

**The most costly failures:**

1. **The Fixer and Courier shipped sideways, and it was committed.** CHARS session 1 measured the mismatch correctly at 18:56 (bind facing −X, walk +Y). Session 2 repeated it with numbers (toe vector −149° against an expected +Y). The controller then removed both facing gates as "overly strict". Claude judged facing from back views and declared "walks forward correctly" at 19:19, and committed `cd8ab98`. The user caught it four minutes later. The fix took AnimMatch session 1, another 23 minutes.
2. **Lessons stayed in memory and briefs, not in tooling, so they recurred.** The root-scale double import hit Champion at 05:19, then the Fixer and Courier again at 18:50. The importer Icosphere took about 17 hours and five characters before the one-line fix in `blender_worker.py`. A wrong facing rule (+X) also survived in a later brief.
3. **GASP transition clips carry 2.8–6.5 m hips offsets.** They have been live since commit `490cde9` (11:43). Sparrow's session found the offset at about 18:35. Nobody checked the other heroes for it then. **Champion's and Angel's stop and pivot clips are still the uncentred originals** in `DefaultGame.ini`.
4. **The fox hand-rig.** It took three Astra sessions (63 worker-minutes), two Sol reviews and two Sonnet reviews. The result has worse knees, wrists and fists than a 20-credit Tripo Auto Rig, though better secondary chains. The mesh was 5,833 quads because the generation settings were never re-checked at the click. It also had nine tails, not six, and nobody counted them until after rig session 1.
5. **180 CLI credits were wasted**, because the B2 brief omitted the face limit. This is the largest direct cash loss.
6. **Mixamo was chosen by habit and never evaluated.** Its hips-as-root design caused the floating walk, the root-motion workarounds, the in-place loop surgery and the transition offsets. The UE5 Mannequin preset was only considered at 23:09 on the second day, after the user asked. Teal-wanderer, the first UE5 Mannequin hero (section 4), then went from the user's file to playable in about 95 minutes. She needed no hips-key centring, no loop correction and no facing yaw.
7. **The orchestrator and transport were unreliable.** Six jobs were killed at the 30-minute limit, three of them mislabelled `[Errno 1]`. Eight worker jobs died on provider disconnects. Browser work stopped seven times (4 Champion P2 stops and 3 Chrome drops); two more stops came from pipeline bugs. Sol reviews were retried after they had already completed. MCP reloads killed in-flight work.
8. **Stop rules were tuned badly in both directions.** Sessions stopped on self-imposed thresholds: CHARS sessions 1–3, CLIPS session 7's 1 cm hips assertion, the Angel 0.01 mm rest tolerance, and Movement session 1 reading "one fix" as one per session. Meanwhile, a correct gate was discarded (item 1).

**Teal-wanderer update (Nov 6 23:03 – Nov 7 00:38).** The UE5 preset removed most of the animation workarounds. It still exposed four new gaps, all caught before the user saw them:
- a self-inflicted weight regression on the shoulder ruffles;
- a pipeline with no way to declare a deliberate bone removal;
- a multi-mesh import that Unreal split into several skeletal meshes;
- an imported material without the skeletal-mesh usage flag. That repeats R13, and the workaround left duplicate assets that a re-import won't update.

The eye defect came from the generator. It took three approaches and four Sol reviews, and still shows a rim close up.

**The biggest lesson:** a lesson isn't learned until it's an automated check that fails at intake. Character acceptance must come from in-engine front, side and back captures of the actual moves. Memory notes, brief prose and back-view screenshots each let a known defect through at least once.

---

## 2. Rigging mishaps

| # | Incident | Found by / when | Cost | Root cause | Encoded now? |
|---|---|---|---|---|---|
| R1 | Champion imported at 3.02 m (run `5df382`) | Unreal import, 05:19 | 1 rebake (`e5ac15`); recurred | UE Interchange applies a non-unit glTF root scale twice | **Partial.** Memory and briefs; `normalize_character.py` reports `non_unit_scales`. `pipeline.py`/`blender_worker.py` do **not** reject it, and the Fixer/Courier review pass reintroduced it (fixed by Claude in run `019bb6`) |
| R2 | Facing: Champion v1, the P2 brief, then the Fixer and Courier | See below | About 1 hour, 4 worker sessions, a bad commit, user trust | Retargeter assumes the bind facing matches Manny's; facing asserted, not measured | **Partial.** Brief text and the AnimMatch harness; no intake gate |
| R3 | Importer bone-display Icosphere pollutes bounds and QA | Champion about 05:00; recurred on Angel, Fixer (failed review 18:38) and Fox (21:15) | About 17 h, 5 characters, per-asset adapter scripts | `blender_worker.py:19` imported glTF without `disable_bone_shape=True` | **Yes** (22:03, uncommitted), plus `--reevaluate REASON` because the pipeline refused to re-check an evaluated candidate |
| R4 | Tail tool v1: webbing, wrong chain, tip needles | Sol review `96186864`, 20:31 | 1 fix round | Per-vertex nearest-guide ownership; checks ran in memory before export | **Yes** in the tool (whole-island ownership, post-export checks). The fix round was never re-reviewed by Sol |
| R5 | Fox: nine tails, not six; tails "fused" | Astra rig session 1, about 21:15; flagged 21:18 | Session 1 planned on false premises | Nobody counted parts on the real mesh | **No** |
| R6 | Fox mesh 5,833 quads, not Triangle 50k; privacy showed "Sharing Only" | Claude after the click, 20:36 | Low-poly limits on fingers and knees, now permanent | Settings set at 20:29; the user clicked about 20:34, and nobody re-read the panel in that 5-minute gap | **No** (advice only) |
| R7 | Hand-built body rig worse than Tripo Auto Rig | Sol plus 2 Sonnet reviews, 21:17–21:57 | 63 worker-min plus 4 reviews, 0 credits | Unvalidated premise; low-poly mesh | **No** policy yet |
| R8 | Mixamo by habit, not UE5 Mannequin | User question, 23:09 | Drove the animation workarounds below | Champion's first preset became the default | **Partly resolved by teal-wanderer.** Unreal's own mannequin template recognized her UE5 rig, secondary chains included, so no chain map was needed. `character_retarget.py` still has no UE5 path; the Wanderer setup lives in session tools (section 4) |
| R9 | Teal-wanderer skirt weighted to hands (Tripo UE5 rig) | User report | 1 session | Auto-weights in the A-pose, hands next to the skirt | **Fixed** by region (T3 in section 4) |
| R10 | Teal-wanderer eye: three approaches | User report | About 4 sessions | Generator-level overlapping eye patches | Eye cards in engine; rim still visible close up (T2 in section 4) |
| R11 | Angel secondary chains: 2 failed attempts | Astra, 09:23 / 09:34 | 2 sessions; Claude fixed it (`f4fa54`) | 0.01 mm rest gate against 17 µm float noise; vertex-group removal while iterating (7 influences, sums 1.68) | **Yes.** Codex's `rig_checks` in `blender_worker.py` checks influences, normalization and rest bones |
| R12 | Extra chain bones defeat Unreal's auto skeleton recognition | Champion re-import, 09:34 | 1 re-run | Template matcher | **Yes.** Mixamo by-name fallback in `character_retarget.py` |
| R13 | Kawaii "too stiff", plus near-black materials in game | User play test, 09:57 | 2 play tests | Stiffness 5–10× default, world damping 0.8; missing SkeletalMesh/Nanite usage flags | **Yes.** `secondary_roster.py`, debug cvars, `fix_material_usage.py` |

### R2: facing, the most expensive repeated defect

- **Champion v1 (06:33):** the legs swung sideways. Claude measured the hips, then wrote an interim "+X in Blender" rule into `normalize_character.py`. It was corrected to −Y once the files had been normalized. The P2 brief to Astra still carried +X (Claude flagged it at 07:44), so run `d8e6df` had to re-normalize locally.
- **Fixer and Courier:** the review pass's lineage (run `20261106T184552-ea2e7d`) records "retain … −Y forward **without rotation**". Unreal then measured both bind poses facing −X. The two facts are on file; why the declared facing didn't match is open. The likely reason (inference) is that the facing was assumed rather than derived from the skeleton, as `normalize_character.py` does.
- **How the correct gate was discarded:** CHARS session 1 diagnosed a "90° body/travel mismatch" at 18:56. Session 2's assertion failed with the toe vector at −149°. At 19:07 the controller told the user the check "assumes a facing direction that hasn't been confirmed" and removed it. AnimMatch session 1 later measured −164° and fixed it with a `FacingManny` target pose: a −90° hips turn, with the hips excluded from auto-alignment.
- **Net effect:** the correct diagnosis existed at 19:00 and was thrown away. The user, not the tooling, caught the shipped defect.

### R5/R6: the fox source model

- The Studio task URL, recorded in the ledger at 20:35:41, reads "kitsune-inspired-fantasy-character-**with-nine-tails**".
- At 20:36 Claude reported "All six are there and distinct … joined to the body at the lower-back plate". Both the count and the topology were wrong.
- RIG-BRIEF.md then told Astra to expect six fused tails. That made the tail tool's untested fused case the central risk, when the tails were actually nine separate components.
- The user chose "Rig all nine". That overrides the originality exclusion in the design brief, which explicitly banned nine tails.
- On the polygon count: the After the Wind research (19:49) reported that a 5k-quad mesh failed and a 25k-triangle mesh worked. Forty-five minutes later the fox came out at 5,833 quads. The fingers are one or two flat quads each and can't curl under any rig.

### R7: hand rig against Tripo Auto Rig

**The sessions:**
- `4fea30e5` (30 min): body-v2, judged "needs work".
- `8cf26b18`: cancelled at 3 minutes for an MCP reload.
- `30b7ff20` (30 min): rig-v10, 160 bones, 24 chains.

**Results:**
- **Wrist:** both repair rounds were used. `v6` was a partial; `v6b` was rejected for a detached forearm.
- **Fist:** `v7` was rejected for no improvement.
- **Knees:** they spike at 130°, and play reached 145.5° of flexion (`FOX-HOOKUP-PROGRESS.md`). The knee shows when the tabards lift.

**Verdicts:** Sol, both Sonnet reviews and Claude (22:51) agree. The auto-rigged Fixer has better knees, fists and wrists. Our rig gave 24 isolated secondary chains that Tripo can't provide.

**Not a controlled test:** the fox has 13k vertices against the Fixer's 57k, and the Fixer wears gloves. The cheap control, a 20-credit auto-rig on the same fox mesh, was never run. The premise "we do a better job at rigging" was accepted without testing.

---

## 3. Animation mishaps

| # | Incident | Found / cost | Status |
|---|---|---|---|
| A1 | **GASP transition clips with large hips origins:** Sparrow walk stop Y −318 cm, pivot −651 cm; fox originals −278 to −570 cm. Overlays slide the body off-camera | Live since `490cde9` (11:43). CLIPS session 7's probe never sampled them (see A6). Found on Sparrow about 18:35; Fixer and Courier visually in AnimMatch session 2 at 19:58 | Fixer and Courier: 14 centred AM3 copies. Fox: centred from the start. **Champion and Angel: unfixed**; Champion's AnimMatch S3 regression failed |
| A2 | Hips-as-root workarounds: Champion v1 floated about 1 m (root-motion op added hip height twice); loop drift corrected on six loops (CLIPS session 4); `ANIM_FIRST_FRAME` locks; the CHARS session 3 loop model failed (Fixer residual 5.26 cm) | Several sessions | Worked around per clip; root cause is R8 |
| A3 | AnimMatch rollbacks: session 2's hold-base transition fix was rejected (bodies displaced, pace lag). Session 3's playback patch passed for Fixer and Courier, failed the Champion regression, and was archived; source restored byte for byte. The restore build failed (UHT timestamp, exit 6), and a recovery build was needed | 3 sessions, about 70 worker-min | **The live game runs centred clips on the rolled-back playback code, and that combination has never been captured** (Claude, 21:22) |
| A4 | Zero-chain heroes (Fixer, Courier) ran `AnimSingleNodeInstance`, with no start, stop or pivot overlays. Claude's own hookup routed overlays only to heroes with secondary chains | AnimMatch session 1 | Routing fixed in session 2 |
| A5 | **Sparrow:** her own jog is a bow-drawn combat run (swapped for the GASP run); the bow reads as a diagonal line while running (unresolved); the AutoWalk camera sat under her feet. Setting pitch −15 once did nothing, then Claude's `TickDebugDrivers` pitch fix worked | 4 sessions | The bow is still open |
| A6 | **GASP overreach:** the user said "delegate it" (10:11), but the 22-chunk, roughly 8-hour scope was only stated after dispatch; the user stopped it at 10:13 and asked what the benefit was. The direct migration closure was 1.08 GB / 1,187 packages. "Borrow a few clips" then took 7 CLIPS sessions; session 7 stopped on a self-imposed 1 cm hips assertion before reaching any transition clip | About 3 h of sessions | Shelved. The probe would probably have exposed A1 about 7 hours earlier without that assertion (inference) |
| A7 | **Advanced movement:** slide holds a tucked jump pose and mantle is an upright lift (placeholders); auto-mantle fires at walking speed against ledges 0.8–2.25 m high; LeftControl is double-bound; tested only on Champion | Sonnet review 22:21 | Fix list pending |

**The propagation failure in A1 matters more than the bug.** When Sparrow's offsets were measured, nobody asked, "Which other heroes play these same clips?" Every hero played them.

---

## 4. Teal-wanderer: the first UE5 Mannequin hero (Nov 6 23:03 – Nov 7 00:38)

**What it took:**
- **Worker sessions:** five Astra sessions, 88 worker-minutes in all, and none hit the 30-minute limit: eye 1 `f9ba849a` 11.8 min; rig prep `91e86f68` 20.9; eye 2 `7c62f7bb` 15.9; polish `35a05eae` 15.6; hookup `1ac7c99b` 24.0.
- **Reviews:** four Sol reviews (`37929c81`, `d9004cc0`, `58e13d83`, `f0ea098b`).
- **Claude's own work:** a merge step and a pipeline flag.
- **Credits:** worker credits 0; the user's own Studio clicks cost 160.

**Sources:** `game-asset-workflow/work/repairs/teal-wanderer/` (PROGRESS.md, DIAGNOSIS.md, the Sol reviews, `rig-prep/`, `eye2/`, `polish/`, `merge/merge_eyes.py`), `evidence/teal-wanderer-polish.md`, the run folders under `assets/teal-wanderer/runs/`, `docs/WANDERER-HOOKUP-PROGRESS.md` and `Saved/WandererHookup/session-1/`.

| # | Incident | Evidence | Root cause | Fix / encoded? |
|---|---|---|---|---|
| T1 | User generated, rigged (UE5 Mannequin preset) and test-animated her in Studio; all of it recorded **retroactively** | Ledger 23:05 (120) and 23:16 (rig 20, animate 20; per-step split assumed). Studio reached 1,100 of 1,110; "no more budget" paused both scopes at 23:26 | The user's clicks bypass the preflight path | Ledger accepts retroactive rows; **no pre-click capture** |
| T2 | Eye defect: overlapping generator eye patches, each on its own UV island with blurry paint, plus a raised strip | DIAGNOSIS.md | Generator output, not the rig | See below. Engine eye passes at gameplay distance; **rim visible close up** |
| T3 | Tripo UE5 auto-weights pulled the skirt with the hands | Rig prep: 2,366 skirt/cloth vertices with arm influence → 0; 3,086 hair vertices had arm influence; 124 hand vertices had hip/thigh spill removed. Sol `d9004cc0` confirms the skirt fix | Auto-weights in the A-pose, hands touching the side panels | **Fixed** by connectivity and region over 3 candidate rounds (`359bdb` → `4f2a21` → `866e3a`). Not yet an automatic intake heatmap |
| T4 | **Self-inflicted regression:** rig prep weighted the shoulder ruffles 100% to new clavicle chains with **zero arm influence**, so they stayed by the bodice when the arms lifted | Sol `d9004cc0`; `rig-prep/report.json`. Polish restored the 3,499 original Tripo rows and removed the six ruffle bones; they now match the original rig within 1.1e-6 m | Our brief invited "shoulder ruffles… if they'd look better moving". The chain-isolation test (bend one chain, nothing outside moves) passed, but it never asked whether attached cloth still follows the arm | Fixed in polish. **Not encoded**: no rule that attached cloth keeps a blend from the body bone it rides on |
| T5 | Pipeline rejected a deliberate bone removal | Runs `d04a8d` and `bef25d` failed with "Blender exited 1"; re-evaluated as `3096a6` | The new rest-bone preflight (`rig_failures` in `blender_worker.py`) treats any missing bone as damage; there was no way to declare an intended change | `--remove-bones` added to `pipeline.py` (checked against the parent's bones, recorded in lineage). **Encoded**, uncommitted |
| T6 | Eye cards imported as **separate SkeletalMesh assets** with messy names | `merge_eyes.py` docstring; split import moved to `Saved/AssetImport/superseded/teal-wanderer-split-eyes-1614` | Interchange makes one SkeletalMesh per skinned mesh node | Joined into the body as a second material slot (`33b409`; no vertex, UV, weight or image change) and re-imported. **Not in intake** |
| T7 | Roster `OverrideMaterial` painted over every slot, eyes included | WANDERER-HOOKUP-BRIEF.md | Override written for single-slot heroes | `KeepMaterialSlots` (`SeleneCharacterSettings.h:98`, `SeleneCharacter.cpp:361`). **Encoded** |
| T8 | Eyes rendered grey: the imported `M_GLTF` parent lacks `used_with_skeletal_mesh` | Hookup checkpoint 00:26; grey-eye witness retained | Same class as R13. `fix_material_usage.py` from play test 1 was not applied to this new import (inference: it isn't part of the import step) | Hookup made Wanderer-owned copies: `M_Wanderer_Eyes`, the eye MI and **`SK_Wanderer`, a duplicate mesh** the roster points at. **Stale-copy risk:** a re-import updates `/Game/Assets/teal-wanderer/…`, not the copy |
| T9 | Retarget operator misconfiguration: choosing `root` as the IK retarget root also set the target pelvis to `root` for Pelvis Motion; the zero root travel looked like a win | Hookup's own final audit (00:32), `ops-audit/report.json` | Default operator wiring when a rig has a real root | Pelvis Motion → `pelvis`, Root Motion → `root`; outputs in `RootSeparated/Anims`. Lives in session tools only |
| T10 | Hot-reload library mismatch: game launches loaded the old `.dylib` | Hookup checkpoint 00:26 | Editor hot-reload naming | Rebuilt with `-NoHotReloadFromIDE -NoHotReload` |

**T2, the eye, in detail:**
1. **Geometry push.** Moving the iris forward 4.5 mm (run `ebdf8b`) made it worse; Sol rejected it.
2. **Fox-eye transplant.** Projecting the fox's eye surface (`0b67a4`) followed the old fragmented depth, giving a corrugated upper edge and a zigzag iris; rejected.
3. **Eye cards.** Curved cards with the fox iris recoloured amber (`26fdc6`) read as matching eyes. Sol `58e13d83` said needs-work: a domed insert with a lower rim at ¾-right and +40°.
4. **Polish.** Two rounds reduced the fullness by up to 4.76 mm, but Sol `f0ea098b` still said needs-work on seating. `26fdc6` and the merged `33b409` were recorded `accepted_local` over that verdict. The polish worker flagged that its brief called the parent "accepted" while PROGRESS and Sol said needs-work (`evidence/teal-wanderer-polish.md`, line 5).
5. **Lesson:** for generator face defects, go straight to a replacement (cards), and budget one regeneration for hero faces.

**UE5 Mannequin against Mixamo, measured** (`WANDERER-HOOKUP-PROGRESS.md`).

*Not needed:*
- the manual chain map: Unreal's mannequin template recognized the rig with all 7 secondary chains;
- hips-key centring;
- linear hips loop correction;
- a corrective facing yaw: the default mesh yaw −90° matched travel in front and side captures.

*Still needed:*
- bind-pose alignment to Manny, because her arm rest pose differs;
- the explicit pelvis/root operator mapping (T9).

*Transition offsets are still authored into the GASP clips* (walk stop −272 cm, run pivot −416 cm, walk pivot −556 cm). They were removed with ordinary settings, `force_root_lock=True` with `root_motion_root_lock=REF_POSE`, not per-clip key surgery.

*The result:* the hookup finished in one 23-minute session. The Fixer and Courier took three CHARS sessions plus three AnimMatch sessions. Caveat: this is one character, and the preset doesn't improve deformation. Knees are still angular at a maximum flexion of 142.8°.

**Still open:**
- **Crouch:** there is no crouch clip, and slow crouch is disabled in `SeleneMovementComponent.cpp`.
- **Skirt:** the panels lift and lose thigh coverage in run and sprint; clipping-free behaviour isn't established.
- **Knees:** angular.
- **Eyes:** the rim shows close up.
- **Pivot routing:** the shared router requests no pivot montage with advanced movement off. This is a shared runtime limitation, not specific to the Wanderer.

---

## 5. Process, tooling and MCP hiccups

### Orchestrator and transport

**Six jobs were killed at the 1,800 s limit:**
- `53529e08` and `cf289923` (04:33);
- `f4126aec` (08:07; 110 building credits had already settled, and the last review was lost);
- `4fea30e5`, `30b7ff20` and `26ad74f0`.

**`[Errno 1] Operation not permitted`.** The live session told the user this followed "right after Astra cancelled a duplicate Sol review". That holds for two of three: `57922c32` falls inside fox session 1 and `1fa89567` inside fox session 2. The movement job `26ad74f0` has no child review, but it also ran exactly 30.0 minutes. The common factor is the deadline.

In `adapters/base.py:118–131`, the timeout handler's final `os.killpg(…, SIGKILL)` catches only `ProcessLookupError`. On macOS that call can raise `PermissionError` (EPERM), which would escape and replace the typed `execution_timeout` with `execution_failed [Errno 1]` (inference; reproduce before fixing). Errno 1 only appears after the reliability commit `710a6d0` was loaded at 20:43. Each time, the work itself had been checkpointed.

**Two separate orchestrator bugs:**
1. The review adapter retried a Sol review after `turn.completed`; see fox `PROGRESS.md`, job `57922c32`. The worker had to recover the answer from the log and cancel the duplicate.
2. The timeout cause was masked as `Errno 1`, above.

**Provider disconnects ("Reconnecting… 2/5"):** 8 jobs. `68e5d640`, `931624ae`, `7678ec1e` (ground: partial assets), `38f319d4`, `12e6220c`, `d3665cf6` (Sparrow session 2), `909dc8bc` and `47d0f915` (both fox reference Sol reviews).

**Browser:**
- **Champion P2: 4 stops, 0 credits.** `d77b067e` (tab owned by a dead session), `d1dd1e1d` (Node REPL timeout), `a7d5b2c5` (cleanup of its own tab), `6330e7f6` (blank candidate page).
- **Fixer and Courier: 5 interruptions.**
  - `5f3a9596` and `e4c1092b` stopped on two bugs in the new `paid_preflight` code. Codex had added it uncommitted mid-session, and Claude fixed it at 17:18 and 17:22.
  - Three Chrome drops followed, ending with `12e6220c` failing. Claude finished the last three paid steps in its own Chrome.

**MCP reloads:**
- `/reload-plugins` doesn't restart MCP servers (20:41).
- A real reload kills child jobs. Fox session 2 (`8cf26b18`) was cancelled at 3 minutes for the user's reload.
- The user had to hold off a reload for about 30 minutes once (20:11–20:40). The second time, the in-flight job was cancelled instead.

**What the Codex "Review Selene MCP Failures" chat concluded.** The MCP layer itself is fast: about 12 ms to enqueue and about 0.1 s of measured overhead. The recurring failure was **a success signal describing the process while the work had failed**:
- `done` hid stopped jobs, which the panel showed as "Awaiting review";
- shell chains returned exit 0 after failed builds and retargets;
- stale screenshots were taken after a failed rebuild.

It also flagged:
- approval drift: B2's missing face limit; "pick two buildings" treated as approval for 110 new credits; deferred B3 props relaunched;
- a serial wait that hid a finished job for about 21 minutes;
- CLI and MCP isolation behaving differently;
- images published outside the staging folder.

Its fixes landed as orchestrator commits `710a6d0` and `bb6e562`. The asset-workflow and Selene changes (paid preflight, checked stage runner, rig preflight) remain uncommitted. Still unproven: a matched benchmark of delegation against a single agent.

### Workflow and process

- **Over-reading "stop on failure".**
  - Movement session 1 stopped on an ordinary compile error after spending its one fix on a capture timeout, and reached no mechanic in 11 minutes. The brief was clarified to "one fix per distinct diagnosed failure", and session 2 then built all six moves.
  - CLIPS session 4 stopped because the `pgrep` guard matched **Claude's own** `dress_route.py` Unreal workflow (PID 30713).
- **Self-imposed numeric gates.**
  - Bad ones: the 0.001 cm loop model, CLIPS session 7's 1 cm hips assertion, and the Angel 0.01 mm rest tolerance.
  - A good one discarded: the facing gate (R2).
  - The briefs now say "numbers are evidence, renders are acceptance". That fixes the first problem and invites the second.
- **Approval and long tests.** A 2-hour unattended checkpoint run started at 05:43, before the blockout was approved, and died at launch. A shorter rerun then exited 0 with zero shots and zero measurements. The user called it out, and that is now a memory rule.
- **Budget.**
  - B2: 180 CLI credits wasted, then 180 more to regenerate (CLI at 360 of 400).
  - Studio is now at 1,100 of 1,110.
  - The user's own clicks were recorded **retroactively**: fox texture 20 (20:35), then teal-wanderer generation and texture 120, rig 20 and animate 20 (23:05, 23:16). The per-step split of the last 40 is assumed.
- **Concurrency.** Codex implemented the reliability plan in the asset workflow and Selene (16:47–20:08) while this session was using both. That caused the `paid_preflight` crashes and the shared-file uncertainty Claude noted ("other uncommitted changes I didn't make"). Unreal access is serialized by `/tmp/selene-unreal.lock` plus `pgrep`, and the guard can't tell a user's game from another agent's run.
- **Commit hygiene.** Since `cd8ab98`, the AnimMatch, movement and fox hookup work, 14 + 11 new clips, the pipeline fixes and the Codex changes are all uncommitted, across two repos.

---

## 6. What worked (keep these)

- **Smaller, single-purpose sessions.** None of the five teal-wanderer sessions hit the 30-minute limit, and each ended at a reviewed checkpoint.

- **Briefs that carried the lessons.** The fox hookup (`89bbbcf2`) was playable in one 16-minute session: correct facing, centred transitions, 24 tuned chains, and Sparrow and Champion regressions captured.
- **The AnimMatch front/side/back harness with contact sheets.** It was the first tool to catch both facing and transition displacement, and it compares against Sparrow directly.
- **Bounded sessions writing PROGRESS checkpoints.** Every timeout and Errno 1 left resumable, honest state, such as `failed_visual_regression` rather than a fake pass.
- **Immutable versions with checks on the exported, re-imported file.** Fox rig-v10's weights match their authored bytes exactly; the tail tool's 2,319-record export drift was caught that way.
- **Independent reviewers.** Sol and Sonnet corrected Claude twice ("tails joined", "side-view arms"), and their verdicts converged.
- **Cheap research before spending.** The Blendable GBuffer finding rescued Substrate toon on Metal for free.
- **Paid clicks done one at a time** with balance checks before and after, by whichever operator had a working browser.

---

## 7. Recommendations (prioritized, with owners)

### P0: intake gates (before any rig or engine work)

1. **`intake_character.py`**, run by `pipeline.py process` on every character, which **fails** (not warns) on:
   - forward not −Y when derived from the skeleton (left = LeftUpLeg/thigh_l − RightUpLeg/thigh_r; forward = left × up), with Mixamo and UE5 name maps;
   - any non-unit node scale;
   - height outside ±2% of spec;
   - triangle count below the character floor (≥25k; quads converted to triangles);
   - any import without `disable_bone_shape=True`;
   - **more than one skinned mesh node** (T6). Unreal would import each as its own SkeletalMesh. The script joins head-only accessories, as `merge_eyes.py` does, or fails;
   - bone additions or removals not declared in the lineage (T5; uses `--remove-bones`).

   It also outputs:
   - **a connected-component count with a coloured parts render**, compared against the parts list in `DESIGN.md`;
   - clay and textured renders from front, side and back;
   - **weight-spill heatmaps** for hand, forearm, thigh, pelvis and head.

   *Owner: asset-workflow scripts (Claude implements; Sol reviews).*
2. **A paid-click preflight that covers the user's clicks too.**
   - Read the settings panel within 60 seconds of the click: model, topology type and count, privacy, texture.
   - Store it in the reservation and compare it with the brief.
   - When the user clicks, Claude re-reads the panel immediately before saying "ready", and reads the task page right after the click.
   - Record spend before the click, not after. If the user works in Studio on their own, as with teal-wanderer (T1), ask them to note the planned spend first; the alternative is a retroactive record.

   *Owner: the studio-pipeline skill and `pipeline.py`.*
3. **Make the Tripo UE5 Mannequin preset the default now.** Teal-wanderer validated it in engine (section 4), though it's one character. Use Mixamo only by explicit, recorded decision. Move the Wanderer recipe from session tools into `character_retarget.py` as the standard UE5 path:
   - Unreal's mannequin template for the chains;
   - a bind pose aligned to Manny;
   - Pelvis Motion → `pelvis` and Root Motion → `root`, with the audit check that caught T9;
   - GASP clips with `force_root_lock=True` and `REF_POSE` root lock.

   The preset doesn't fix auto-weights, so T3-style spill checks still apply.

   *Owner: Claude, Selene `Tools/Unreal`.*
4. **A post-import engine check that is part of the import step, not a later fix-up script.**
   - Every material on a skeletal mesh must have `used_with_skeletal_mesh` (T8, R13). Set it on a project-owned parent that the imported instance is re-pointed to, by a re-runnable script.
   - **Don't duplicate meshes.** Fix the Wanderer's stale-copy risk: the roster points at the duplicate `SK_Wanderer`, so re-point it at the imported mesh once the parent fix is in place. Until then, any re-import must re-run the hookup's copy step.
   - The import must produce exactly one SkeletalMesh per character.

   *Owner: Selene `Tools/Unreal` import script.*
5. **Centre transitions at clip-import time.**
   - `gasp_clip_retarget.py` measures every non-loop clip's first-frame hips XY, writes centred copies, and **fails if any roster clip is more than 5 cm off**.
   - Run it now on Champion and Angel, then re-apply the archived playback patch and capture all heroes.

   *Owner: an Astra session; Claude reviews the sheets.*
6. **Engine acceptance standard.**
   - No hero change is accepted without AnimMatch captures (front, side, back × idle, walk, run, sprint, start, stop, pivot, jump) beside Sparrow.
   - Back-only verdicts are invalid.
   - The reviewer names which views were opened.

   *Owner: Claude (controller); written into every brief.*
7. **Orchestrator fixes.**
   - Catch `PermissionError` in the timeout `killpg` and report `execution_timeout` (reproduce first).
   - Never retry a review after `turn.completed`.
   - Expose the deadline to workers so they checkpoint at about 25 minutes.
   - Make jobs survive an MCP restart, or refuse a reload while jobs are live.

   *Owner: orchestrator repo.*

### P1: process

8. **One `LESSONS.md` in the asset workflow, included verbatim** in every rig and hookup brief (not retyped; the P2 brief kept an obsolete +X rule). Each lesson names the gate that enforces it. *Owner: Claude.*
9. **A propagation rule.** A defect found on one hero triggers a same-session check across the roster, for any shared clip, setting or script. *Owner: Claude (controller).*
10. **Gate policy.**
   - "One fix per distinct diagnosed failure."
   - Every numeric gate states its assumption.
   - **Never remove a failing gate without showing the measurement is wrong.** The −149° reading correctly detected the facing mismatch that AnimMatch later fixed.

   *Owner: the brief template.*
11. **Hybrid rig policy.**
    - Tripo Auto Rig (UE5) for the body, plus our chain tools for tails, cloth and hair.
    - A hand-built body only after a same-mesh auto-rig control on that mesh is rendered pose for pose.

    *Owner: the studio-pipeline skill.*
12. **Weight edits by connectivity and region only.** Verify spill heatmaps before and after on the re-imported GLB, and keep every vertex outside the selection byte-identical. This is already practised; make it a script default.
    - **Cloth attached to a limb keeps a blend from that limb's bone** (T4).
    - Every new chain is posed against the **original rig** in arm and leg poses, not only bent in isolation. Isolation proves a chain moves nothing else; it doesn't prove the cloth still follows the body.

    *Owner: `_shared` tools and rig briefs.*
13. **Generator face defects:** replace (eye cards or a transplant) rather than move geometry in place. Budget one regeneration for hero faces. *Owner: the studio-pipeline skill.*
14. **One writer per repo.** Claude and Codex sessions take a repo lock. Agent launches mark their Unreal processes so the guard can tell agents from the user. Commit at each verified checkpoint. *Owner: user and Claude; the Selene launchers.*
15. **Scope before plans.** Long migrations and unattended runs get a one-line cost and benefit statement and user approval before any briefing. *Owner: Claude (memory rule exists; make it a brief prerequisite).*
