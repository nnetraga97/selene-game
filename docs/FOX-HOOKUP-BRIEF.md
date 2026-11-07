# Fox (Lysara Vey) hookup: brief (Astra, xhigh, bounded sessions)

## Goal

Make `fox-spirit-sovereign` (Lysara Vey) a playable hero in Selene, cycled with C like the others. She should move as close to the **Sparrow** reference as our pipeline allows. Her nine tails, sleeves, tabards, hair and tassels should move with Kawaii secondary motion.

Then answer the one open question from the rig reviews: **do the knee spikes at 130° show through the tabards in real play?**

Each session is killed at 30 minutes. Stop at a verified checkpoint and append to `docs/FOX-HOOKUP-PROGRESS.md` (create it):
- what is done;
- the evidence;
- the exact next step.

## What exists

- **Imported mesh:**
  - `/Game/Assets/fox-spirit-sovereign/fox-spirit-sovereign/SkeletalMeshes/fox-spirit-sovereign`, with its skeleton, PhysicsAsset, material instance and 4K base-colour texture (`.../Textures/kitsune_fantasy_character_3d_model_basecolor`).
  - The import report is `docs/engine-checks/fox-spirit-sovereign.json`: 1.75 m tall, 0 errors. One known warning: "skinned mesh node is not root".
- **The rig is hand-built**, not Tripo Auto Rig: 160 bones.
  - The body uses the Mixamo contract: 65 `mixamorig_*` bones with Hips as the root, matching the Fixer's names and hierarchy. The bind pose faces −Y in Blender (Unreal +Y), the Manny-compatible facing.
  - 24 secondary chains:
    - 9 tails, `tail_0_00..04` to `tail_8_00..04`, rooted on Hips;
    - 4 sleeve panels rooted on the ForeArm;
    - 4 tabards rooted on Hips;
    - 4 hair groups rooted on Head;
    - 2 tassels and 1 sash chain.
- **Rig report and proposed roster snippet:**
  - Report: `/Users/nicknetraganti/Desktop/Developer Stuff/game-asset-workflow/work/repairs/fox-spirit-sovereign/rig-v10/report.json` (full hierarchy plus the proposed `SecondaryChains` / `SecondaryColliders`) and `.../REPORT.md`.
  - Delivery provenance: `SourceArt/Assets/fox-spirit-sovereign/fox-spirit-sovereign.provenance.json`, run `20261106T220404-a52fa1`.
- **Patterns to reuse (read first):**
  - The Fixer/Courier hookup: `docs/CHARS-PROGRESS.md`, `Tools/Unreal/character_retarget.py` (MIXAMO_CHAINS by bone name; retarget root `mixamorig_Hips`), `chars_session3_*.py`, `chars_loops_linear_in_place.py`, `chars_toon_instances.py`, `gasp_clip_retarget.py`.
  - AnimMatch: `docs/ANIM-MATCH-PROGRESS.md`. This covers the facing fix through the target retarget pose (−90° hips turn) and the centred stop/pivot transition copies (`anim_match_s3_normalize.py`).
  - Kawaii and roster: `docs/KAWAII-PHYSICS.md`, `Source/Selene/Animation/SeleneSecondaryAnimInstance.*` and the existing roster lines in `Config/DefaultGame.ini`.
  - Sparrow: `docs/SPARROW-PROGRESS.md`. The AnimMatch comparison harness (`selene.AnimMatch`) shoots front, side and back.

## Lessons (each one cost a session; don't repeat them)

1. **Facing.**
   - Fixer and Courier played sideways, and we missed it by checking only back views.
   - Judge facing from **side and front** captures, with the mesh's forward compared to the travel direction.
   - Fix facing through the retarget pose (not MeshRotation) as AnimMatch did, if needed. Her bind pose should already face Manny's way, so verify that before changing anything.
2. **Transition clips.** Retargeted GASP stop and pivot clips carry large hips offsets (−300 to −650 cm), which slide the hero off-camera. Make centred copies with the AnimMatch session-3 normalization from the start.
3. **Loops in place.** Mixamo Hips is the root, so remove hips XY drift from the loops (`chars_loops_linear_in_place.py` pattern). Measure the loop speeds for the roster.
4. **The extra secondary bones break the template matcher.** Define the IK Rig chains by bone name (as `mixamo_chains()` does), never by auto template.
5. **Don't invent numeric gates. The captures are the acceptance test.**

## Steps

1. **Retarget and clips.**
   - Create `IK_Fox` and `RTG_Manny_To_Fox`.
   - Retarget the same GASP set the other heroes use: idle, walk/run/sprint loops, starts, stops, pivots, turns, plus jump, fall and land.
   - Make the centred transition copies and the in-place loops, and measure the speeds.
   - Output goes to `Content/Selene/Characters/Fox/`.
2. **Material.** Create `MI_Toon_Fox` from `M_Character_Toon` with her base-colour texture, verified by reading it back (`chars_toon_instances.py` pattern).
3. **Roster.** Add one roster line for `Fox` in `Config/DefaultGame.ini`, plus any cook directories the other heroes have. Copy MeshOffset, EyeHeight and BoomLength from comparable heroes and adjust from the captures.
4. **Kawaii.**
   - Start from the rig report's snippet.
   - **Add colliders the snippet lacks:** forearms (so sleeve chains don't clip the arms) and a hips/thigh coverage check under the tabards.
   - **Give tails, cloth and hair their own values** instead of the identical placeholders. Tails should be loose and heavy-ish; tabards and sleeves cloth-like; hair lighter.
   - Tail-to-tail contact is accepted for now.
   - Note the performance: about 100 simulated bones per hero. Propose (don't build yet) distance/LOD gating of the cloth chains.
5. **Captures with the `selene.AnimMatch` harness**, comparing Fox and Sparrow from front, side and back:
   - idle, walk, run, sprint, stop, pivot, jump.
   - Then a dedicated look at **the knees under the tabards while running and landing**, side and front, with Kawaii on.
   - Contact sheets; the Swift helpers work. Also run a regression capture of Sparrow and Champion so nothing else changed.

## Rules

- **Coordination:**
  - The movement job (`docs/MOVEMENT-BRIEF.md`) may have changed `SeleneCharacter.*` and `SelenePlayerController.*`. Read `docs/MOVEMENT-PROGRESS.md` first, and don't touch those files.
  - Only add the Fox roster line and cook directories to `DefaultGame.ini`. Leave every other line as you find it.
- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, the user may be playing: wait up to 15 minutes, then stop and report. Never kill it.
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it afterwards, including on failure.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV'`. For game runs use alarm 75–120; exit code 142 is expected.

  Headless Python writes its results to files. Known startup errors (AgentSkill, PythonTestRunner, `EditorToolset`/`ToolsetRegistry`) are already cleared.
- **Files you may touch:**
  - `Content/Selene/Characters/Fox/**`
  - `Content/Selene/Materials/Character/MI_Toon_Fox`
  - `Config/DefaultGame.ini` (the Fox line and cook directories only)
  - `Tools/Unreal/**` (new fox scripts)
  - `docs/FOX-HOOKUP-PROGRESS.md`
- **Never:**
  - touch `Config/DefaultEngine.ini`;
  - modify, move or delete `/Game/Assets/*`, `/Game/ParagonSparrow` or any other hero's assets;
  - make Blender edits to the delivered mesh. Rig or weight problems go in the report;
  - commit, use the browser, download anything, or use paid services.
- **Failure rule:** one fix per distinct, diagnosed failure. Clear compile and script errors are normal work. Stop and report when a failure repeats, can't be diagnosed, or would need trying variations.
- **Final reply:**
  - what works;
  - contact-sheet paths (Fox vs Sparrow, plus the knee/tabard close-ups);
  - the roster line;
  - the Kawaii values chosen;
  - whether the knee spikes show in play;
  - what still differs from Sparrow;
  - the exact next step.
