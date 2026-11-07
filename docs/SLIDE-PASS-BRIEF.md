# GASP slide pass (Astra, xhigh, bounded sessions)

## Goal

Replace Selene's placeholder slide with real GASP slide animation on **every roster hero**: Champion, Angel, Sparrow, Fixer, Courier, Fox, Wanderer, Ysolde, Nerine and Base.

Today, `USeleneMovementComponent::PlaySlidePose` in `Source/Selene/Movement/SeleneMovementComponent.cpp` plays the hero's **Jump** clip as a stand-in for up to 0.52 s. `TrySlide`/`StopSlide` also drop the mesh by `SlidePoseMeshDrop` (32 cm) to fake a crouched body. The slide physics (`PhysSlide`, capsule shrink, Ctrl input) are fine and stay as they are; **only the animation side changes**.

The user only cares about dash and slide. **The dash is out of scope**: don't touch it.

Each session is killed at 30 minutes. Stop at a verified checkpoint by about 25 minutes. Append to `docs/SLIDE-PASS-PROGRESS.md`: what is done, the evidence paths and the exact next step.

## Clips

The source is the GASP project: `/Users/nicknetraganti/Documents/Unreal Projects/GameAnimationSample`, under `Content/Characters/UEFN_Mannequin/Animations/Slide/`.

Use the **Neutral KneesOut** set:

| Phase | Clip |
|---|---|
| Into | `M_Neutral_Slide_KneesOut_Into_Lfoot` |
| Loop | `M_Neutral_Slide_KneesOut_Loop` |
| Out, still moving | `M_Neutral_Slide_KneesOut_Out_Moving_Run` |
| Out, stopping | `M_Neutral_Slide_KneesOut_Out_Idle_Stand` |

- Switch to the matching `FootOut` clips only if KneesOut clearly fails in the captures, for example legs through the floor on most heroes. Record why.
- Reuse the existing GASP clip tooling in `Tools/Unreal/gasp_clip_*.py`, `gasp_loop_in_place.py` and the session run scripts. `docs/GASP-INTEGRATION.md` and the latest session scripts show how the 15 locomotion clips were exported, imported onto Manny, and retargeted per hero.
- Use each hero's **existing** retargeter. Name outputs like the locomotion clips (`<clip>_<Hero>`, beside that hero's other GASP clips).
- Settings are as for locomotion: `force_root_lock`, `REF_POSE` root lock, and **in place, with no root motion**. The C++ movement drives the slide speed.

## Code

1. **Roster fields.** In `FSelenePlayableCharacter` (`Source/Selene/SeleneCharacterSettings.h`), add 4 optional soft `UAnimSequence` fields: `SlideInto`, `SlideLoop`, `SlideOutMoving` and `SlideOutStand`. Fill them for every hero in `Config/DefaultGame.ini`.
   - Edit **only** by appending these fields to the existing `+Roster=` lines.
   - Claude may add a new roster line, for a "Nerine v2" hero, while you work. Re-read the file just before editing and preserve any line you didn't write.
2. **Slide animation.** Replace the Jump stand-in in `PlaySlidePose` with three phases, played through the existing `DefaultSlot` dynamic-montage path:
   - Into, then Loop for as long as the slide lasts.
   - On `StopSlide`, play Out: `SlideOutMoving` if the player is still giving movement input or the speed is above walk; otherwise `SlideOutStand`.
   - A falling exit (sliding off a ledge) just blends out, as now.
   - Blend times: short, tuned by captures.
3. **Mesh drop.** The clips lower the hips themselves, so remove or retune `SlidePoseMeshDrop` so the body sits on the ground. Judge by side captures.
4. **Fallback.** A hero with empty slide fields keeps the current behaviour, so nothing breaks.
5. Build with `Build.sh SeleneEditor Mac Development`.

## Verification (judge by captures)

- **Per hero:** an offscreen slide sequence of a run into the slide, the loop, an exit back to running, and an exit to standing, in **side and front views**. Put all 10 heroes on one contact sheet under `Saved/SlidePass/`.
- **Check each hero for:**
  - hips and knees on or near the ground line with no sinking through the floor;
  - no T-pose or reference-pose flashes;
  - no pop between phases;
  - the exit back into running looks continuous.
- **Clothing:** note cloth or skirt clipping per hero (Ysolde's coat, Wanderer's skirt, Nerine's skirt) as **observations only**. Mesh fixes are out of scope.
- **Regression:** the walk, run, sprint and jump capture for Ysolde and Sparrow is unchanged.
- **Review:** one Sol review (`openai/gpt-6.1-sol`) of the sheets, at most 2 rounds of one stated change each. The verdict must cite the sheet panels.

## Unreal launches (headless only; no editor UI, no computer use)

1. Run `pgrep -f "UnrealEditor.*Selene.uproject"`. If Selene is open, do the non-Unreal work first (clip list, C++ edits). Then wait up to 20 minutes for it to close, checking every 60 s. If it is still open, stop and report. **Never kill or close it.**
2. Take the lock with `until mkdir /tmp/selene-unreal.lock 2>/dev/null; do sleep 15; done`, and `rmdir` it on exit (trap EXIT). Claude may be importing a hero at the same time; the lock handles it.
3. Wrap each run in `perl -e 'alarm N; exec @ARGV'`, and run offscreen or `-nullrhi` as the earlier session scripts do.
4. The GASP project is a separate project: guard it the same way with `pgrep -f "UnrealEditor.*GameAnimationSample"`.

## Rules

- **You may touch only:**
  - `Source/Selene/Movement/SeleneMovementComponent.*`;
  - `Source/Selene/SeleneCharacterSettings.h`;
  - the slide fields in `Config/DefaultGame.ini`;
  - new slide clip assets under `Content/`;
  - new `Tools/Unreal/slide_*` scripts;
  - `Saved/SlidePass/`;
  - `docs/SLIDE-PASS-PROGRESS.md`.
- **Never:**
  - `Config/DefaultEngine.ini`;
  - edit existing clips, retargeters, meshes or materials;
  - Blender, commits, the browser, or paid services;
  - the dash.
- **Failure rule:** one fix per distinct, diagnosed failure. Clear script errors are normal work. Stop and report on a repeat.
- **Final reply:**
  - the clips used;
  - the code change summary;
  - the contact sheet paths;
  - per-hero observations (one line each);
  - Sol's verdict;
  - the exact next step.
