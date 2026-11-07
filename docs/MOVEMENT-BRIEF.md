# Advanced hero movement: brief (Astra, xhigh, bounded sessions)

## Goal

The user wants **fast, skill-based hero movement in the spirit of hero shooters like Deadlock**:
- momentum you can chain;
- dashes;
- slides;
- extra jumps;
- wall and ledge play.

The aim is the same *feel* and genre mechanics, built from scratch for Selene. Do **not** copy another game's names, numbers, UI, assets or exact tuning. Every value is ours, tuned to Selene's scale (sprint about 6 m/s).

Selene is a UE 5.8.4 C++ anime-town demo at `/Users/nicknetraganti/Desktop/Developer Stuff/Misc/selene-game`, with a six-hero roster: Manny, Champion, Angel, Sparrow, Fixer and Courier.

Each session is killed at **30 minutes**. Stop at a verified checkpoint and append to `docs/MOVEMENT-PROGRESS.md` (create it):
- what is done;
- the evidence (captures and logs);
- the exact next step.

## What exists (read first)

- **Character and movement:**
  - `Source/Selene/SeleneCharacter.{h,cpp}` (748 lines): paces Walk 150 / Jog 350 / Sprint 600 cm/s; third- and first-person cameras (V); character cycle (C); single-node locomotion with DefaultSlot montage overlays.
  - Debug harnesses: the cvars `selene.AutoWalk`, `selene.AutoShots` and `selene.AnimMatch`.
  - Roster fields: `Source/Selene/SeleneCharacterSettings.h`. Roster: `Config/DefaultGame.ini`.
- **Input:** `Source/Selene/SelenePlayerController.cpp` builds a runtime Enhanced Input context. Current keys:
  - WASD, mouse, Space = jump
  - **LeftShift = sprint, LeftControl = walk toggle**
  - V = camera, C = character cycle, Esc = menu
  - gamepad equivalents
- **Animation:**
  - `Source/Selene/Animation/SeleneSecondaryAnimInstance.*`: native graph SingleNode → DefaultSlot → Kawaii chains. Keep it working on Champion, Angel and Sparrow.
  - GASP clips are retargeted per hero under `Content/Selene/Characters/<Hero>/Anims/GASP/`; see `docs/GASP-INTEGRATION.md` and `docs/CLIPS-PROGRESS.md`.
  - The GASP sample project at `/Users/nicknetraganti/Documents/Unreal Projects/GameAnimationSample/` has crouch and traversal clips. Our migration left traversal out.
- **Work in progress you must not break or overwrite:**
  - The AnimMatch work (`docs/ANIM-MATCH-PROGRESS.md`) is uncommitted and touches `SeleneCharacter.cpp`.
  - An archived playback patch (`Saved/AnimMatch/session-3/unaccepted-playback.patch`) also touches `SeleneCharacter.{h,cpp}` and `SeleneSecondaryAnimInstance.*`.
  - **Keep your edits to those files to small, clearly marked hooks.** Put the movement logic in new files.

## Design: session 1 builds the mechanics, not the animation polish

Build a custom movement component, `USeleneMovementComponent` (a `UCharacterMovementComponent` subclass, in new files), installed through the `ASeleneCharacter` constructor's ObjectInitializer.

- Single-player only, but write the movement code the standard CMC way (custom movement modes, `PhysCustom`), not as ad-hoc actor ticking.
- Expose every tunable as a `UPROPERTY` in one place.
- Add a cvar `selene.AdvancedMovement 1/0` (default **1**). With 0, movement must behave exactly as today, so the town-walk demo stays as it is.

### Mechanics, in priority order

Get each one verified before starting the next.

1. **Momentum model.** No hard cap from the advanced moves:
   - ground friction and braking that keep speed on landing for a short window;
   - responsive air control without full air acceleration;
   - a speed bonus from chaining moves that decays back toward sprint speed.
2. **Dash.**
   - A short, fast burst in the input direction (camera forward when there is no input), on the ground or in the air.
   - It costs one **stamina** charge: 2–3 charges that regenerate over time.
   - A small camera FOV kick.
   - **Dash-jump:** jumping during or just after a dash carries the extra speed into the air.
3. **Slide.**
   - Crouch while moving fast to slide: low capsule, low friction, speeding up downhill, slowing on flat ground or uphill.
   - **Slide-jump** keeps the momentum.
   - Crouch while slow just crouches (or does nothing, if crouch animations aren't ready), stated clearly.
4. **Double jump.** One extra jump in the air, which costs stamina. Its direction can be redirected toward the input.
5. **Wall jump.** In the air against a wall, jump kicks off the wall (away from it and upward). Limit repeats on the same wall.
6. **Mantle / ledge climb.** Moving into a ledge between about chest and overhead height pulls the character up onto it. Use a capsule trace and motion warp, or a scripted root move.

### Input

- Decide the bindings and document them. They must not conflict with the existing keys.
- My suggestion:
  - Dash: **LeftAlt** or **Q** (LeftShift stays sprint).
  - Crouch/slide: **move walk-toggle off LeftControl** to another key such as **CapsLock**, and use LeftControl for crouch/slide, as most shooters do.
  - Gamepad: B / face-right for crouch/slide, and the left bumper or right-stick click for dash.
- The user can override this choice. Note it in the progress file.

### Feedback (cheap but important for feel)

- A minimal stamina indicator on screen, in the existing HUD/Slate style (see `SSelenePauseMenu.*`). No decorative pulsing status dots.
- Camera:
  - FOV kick on dash;
  - lower camera height during a slide;
  - a slight roll or tilt on wall jumps, if it's easy and doesn't cause discomfort;
  - first person must feel right too.
- **Animation for now:** reuse what exists.
  - Jump/fall/land clips for double and wall jumps, played as DefaultSlot montages.
  - Mantle and slide may use the closest available clip or a simple pose montage.
  - List exactly which clips each move uses and which **new clips are needed** (crouch, slide, dash and mantle from GASP or Sparrow's set). Proper per-hero retargeting of those clips is a later session; don't start it in session 1 unless the mechanics are all verified.

## Testing (the captures are the acceptance test)

- **Test level.** Build a small headless-generated test level, `Content/Selene/Maps/MovementTest`, with a Python script under `Tools/Unreal/`:
  - flat run-up lane;
  - a ramp for slope sliding;
  - walls for wall jumps;
  - ledges at 1.0 / 1.4 / 1.8 / 2.2 m for mantles;
  - a gap that needs a dash-jump;
  - a platform that needs a double jump.

  Don't edit the Town map.
- **Scripted run.** Add a cvar, `selene.MoveTest`, that drives the pawn through a fixed sequence:
  1. sprint, then slide down the ramp;
  2. slide-jump;
  3. dash;
  4. dash-jump across the gap;
  5. double jump to the platform;
  6. wall jump;
  7. mantle each ledge.
- **Evidence:**
  - Log a per-frame trace (time, move state, speed, position, stamina) to `Saved/MovementTest/<label>/trace.csv`.
  - Take screenshots at key moments, in third person and first person.
  - Build contact sheets (Swift helpers like `Tools/Unreal/anim_match_contacts.swift` work; macOS has no Pillow).
- **Acceptance:**
  - Each mechanic triggers when it should, and only then.
  - Speeds stay sensible.
  - No falling through the floor, no stuck capsules.
  - Mantles end on top of the ledge.
  - The trace and the screenshots agree.
- **Regression:**
  - With `selene.AdvancedMovement 0`, a normal walk/run/sprint capture of Sparrow and Champion matches today's behaviour.
  - With it on, Kawaii chains stay active and every hero can still cycle (C).

## Rules

- **Unreal launches.** Guard every Selene launch:
  1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If an instance is running, the user may be playing: wait up to 15 minutes, then stop and report. **Never kill it.**
  2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it afterwards, including on failure.
  3. Wrap the run in `perl -e 'alarm N; exec @ARGV' ...`. For game runs use alarm 75–120; exit code 142 is expected.

  Build with `Build.sh SeleneEditor Mac Development`. Never edit a launcher script while it's running.
- Known Python startup errors (`EditorToolset`/`ToolsetRegistry`, AgentSkill, PythonTestRunner) already exist and are cleared. They aren't failures.
- **Files you may touch:**
  - new `Source/Selene/**` files, plus small marked hooks in the existing character, controller and anim-instance files;
  - `Config/DefaultGame.ini`, for new movement settings only;
  - `Config/DefaultInput.ini`, if needed;
  - `Tools/Unreal/**`
  - `Content/Selene/Maps/MovementTest*` and `Content/Selene/Movement/**`
  - `docs/MOVEMENT-PROGRESS.md`
- **Never:**
  - touch `Config/DefaultEngine.ini`;
  - modify, move or delete anything in `/Game/ParagonSparrow`, `/Game/Assets/*` or existing `Content/Selene` assets;
  - commit, use the browser, download anything, or use paid services.
- The user's rule: **if something fails, stop and report.** Don't retry variations. One recorded fix of an obvious, diagnosed cause is fine. Judge by the captures, not by numeric gates you invented.
- No long test runs beyond the scripted sequence without asking.
- **Final reply:**
  - which mechanics work, with evidence paths;
  - the key bindings;
  - the tunables and their values;
  - the clips each move uses and which new clips are needed;
  - regression results;
  - what still feels off;
  - the exact next step.

---

## Session 2: clarification from Claude (2026-11-06)

**The failure rule means one fix per distinct, diagnosed failure. It is not one fix per session.**

- **Compile errors:** fix them normally whenever the compiler message makes the cause clear, for example an incomplete type, a missing include or a wrong signature. Session 1 stopped on such an error, and that was more cautious than the user intends.
- **When to stop and report:**
  - the same failure comes back after its fix;
  - you can't diagnose the cause;
  - a fix would mean trying variations;
  - a runtime or visual result is wrong in a way you can't explain.

Continue from the "Exact next step" in `docs/MOVEMENT-PROGRESS.md`:
1. Restore `Saved/MovementTest/session-1/unaccepted-momentum/candidate.patch`.
2. Fix the incomplete-type build error.
3. Build, generate the MovementTest map, and capture momentum.
4. Then dash, stamina/HUD/FOV and input.
5. Then slide, extra jump, wall jump and mantle, verifying each before the next.
