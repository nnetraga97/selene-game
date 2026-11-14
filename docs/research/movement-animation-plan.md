# Movement, body animation and abilities plan

Written 2026-11-09. Scope: how heroes move, animate and use abilities in the final game (a separate project, hero shooter in the spirit of Deadlock). Faces are out of scope here. Nothing in this document has been built or changed; it is a plan for approval.

## 1. The short version

The clips we borrowed are not the problem. GASP and Paragon are studio-grade animation. What makes the result feel unrefined is the thing playing them: Selene plays **one clip at a time**, picked by speed, with short overlays on a single slot. A hero shooter needs a layered animation graph: the legs follow movement in any direction while the upper body aims, fires and casts, and procedural corrections keep the feet planted. Selene has none of those layers, no ability system, and uses a small fraction of the animation it already owns.

The plan is to stop extending Selene's clip player and build the final game's hero framework from Epic's production parts: the GASP locomotion setup on Character Movement, the Gameplay Ability System for abilities, and our own movement mechanics ported in. Sparrow is hero 1 because she already ships everything a hero needs. One of our own heroes follows on the same framework.

## 2. What the codebase shows

| Area | Today | Effect |
| --- | --- | --- |
| Animation player | `UpdateSingleNodeAnimation` in `SeleneCharacter.cpp`: one loop chosen by speed with a play-rate scale; starts, stops and pivots as `DefaultSlot` overlays | No strafing or backpedalling, no blend between gaits, no upper/lower body split, no aim, no turn in place, no lean, no foot placement on slopes |
| GASP usage | 19 clips retargeted offline per hero (forward walk, run, sprint, starts, stops, pivots, turns, slide) | The GASP sample on disk has about 2,300 animation assets, including crouch, slide, jump, traversal and aim offsets, with a motion-matching graph that picks among them. We use under 1% and none of the graph |
| Sparrow usage | About ten clips: travel idle, forward sprint, jump, plus four GASP clips | Her pack has 125 animations, 32 aim-offset poses, slope-lean blend spaces and her own animation blueprint (`Sparrow_AnimBlueprint`). The roster leaves `AnimClass` unset because the Kawaii chains need the single-node path, so her blueprint never runs |
| Movement mechanics | `USeleneMovementComponent`: momentum carry, dash with stamina charges, slide, extra jump, wall jump, mantle; each accepted in isolation on a test course | A sound prototype of the right kit. Single-player only, tested on the Champion, and the slide and mantle animations are placeholders |
| Abilities | None | No ability system, no cast or fire animation, no hit reaction, no VFX or sound hookup |
| Feedback | A field-of-view kick on dash and a camera drop on slide | No camera shake, landing weight, dust, trails or sound tied to movement |
| Per-hero cost | Every clip is retargeted and corrected offline for each hero | Slow, and each hero ends up with the same forward-only set |

Sparrow looks best because her mesh, rig and clips were made for each other. Even so, Selene shows roughly a tenth of what she can do.

## 3. How studios build this

- **Gameplay owns the timing.** An ability is specified as startup, active and recovery time, and the animation is built to fit. Dota's wiki calls the moment the effect lands the cast point and notes the animation usually runs longer than it. Blizzard's animators lock down basic movement before any ability work.
- **A layered animation graph.** Epic's Lyra sample, which Epic says is inspired by Paragon and Fortnite, layers upper-body actions such as firing over full-body locomotion with a per-bone blend. It uses distance matching for starts and stops, stride and orientation warping to cover any direction from four authored ones, turn-in-place, and a separate animation layer per weapon.
- **Motion matching for locomotion.** GASP replaces hand-built state machines with a search over a large clip set. In the installed 5.8 its plugins (Pose Search, Chooser, Blend Stack, Animation Warping) are marked production.
- **An ability system.** Lyra runs most gameplay through the Gameplay Ability System, marked production in 5.8. An ability plays a montage; markers in the montage trigger effects and sound; movement abilities such as dashes go through root motion sources that Character Movement predicts over the network.
- **Deadlock's movement kit**, as the feature target: dash and one air dash per jump on stamina, slide that is free at speed or downhill, dash-jump, wall jump, mantle with a speed spike, and ziplines that keep momentum.

## 4. Three ways to build the framework

| | A. GASP on Character Movement, plus the ability system (recommended) | B. Lyra as the base | C. Paragon-native |
| --- | --- | --- | --- |
| What it is | Start the new project from the GASP sample's Character Movement pawn and motion-matching graph; add the Gameplay Ability System; port our dash, slide, wall-jump and mantle code | Start from Lyra's full shooter framework (abilities, weapons, teams, UI) and replace its locomotion | Use Sparrow's own animation blueprint as the template for every hero |
| Gets us | The largest locomotion and traversal set, any-direction movement, runtime retargeting to other skeletons, the smallest amount of new code for movement | Networking, weapons and match structure on day one | Her authored, characterful set exactly as Epic built it |
| Cost | Match structure, weapons and UI are ours to build later | Heavy to learn and reshape; its animation set is small | Only Paragon heroes have such sets; no slide, dash or mantle clips |
| Fits if | Movement and animation feel are the priority now | The priority is a playable networked match | We only ever ship Paragon heroes |

Two things to avoid: **Mover** and the **Unreal Animation Framework** are both marked experimental in the installed 5.8. GASP ships a Mover pawn as well; use its Character Movement pawn.

## 5. The framework, in layers

1. **Movement.** A Character Movement subclass with our modes (dash, slide, wall jump, mantle, air dash), written for network prediction from the start.
2. **Base locomotion.** Motion matching over the GASP set, retargeted at runtime to each hero. A hero with her own set, like Sparrow, overrides this layer with it.
3. **Upper body.** Aim offset, plus an upper-body slot for firing and casting while moving, and a full-body slot for abilities that commit the whole character.
4. **Procedural polish.** Orientation and stride warping, foot placement, lean into turns, turn-in-place, landing compression.
5. **Abilities.** One data record per ability: startup, active and recovery times, the montage, the effects and sounds it triggers, any movement it applies, and what it can cancel or be cancelled by.
6. **Feedback.** Camera shake and field-of-view changes, dust and trails, footsteps and whooshes, hit pause. This is a large part of what reads as polish.
7. **Secondary motion.** Hair and cloth as a post-process step on the mesh, so it no longer forces the single-clip player.

## 6. The plan

Each step ends with a short clip at the gameplay camera for approval.

### Step 0. See the difference first (free, one short session)

Capture three clips of the same moves: Sparrow in Selene today; Sparrow in her own Paragon test map on her own animation blueprint; the GASP sample pawn. This shows how much of the gap is the player and which base feel you prefer before anything is built.

### Step 1. Locomotion on the framework

New project from the GASP sample. Sparrow moving in eight directions while facing the camera, with starts, stops, pivots, turn-in-place, aim offset, jump and land, and slopes.

### Step 2. The movement kit

Port the accepted mechanics. Give each one a real animation (GASP has slide and traversal sets), a camera response, a sound and a ground effect. Add air dash and dash-jump. Tune on a movement course.

### Step 3. The ability pipeline, using Sparrow's kit

Her pack already contains the animation, effects and audio for a primary shot at three speeds, a charged shot (draw, hold, fire), a targeted area ability, an ultimate, four-direction hit reactions, knockbacks, stun and death. Wire these through the ability system with explicit timing. The result is the template every later hero fills in.

### Step 4. Network check

Two players with simulated lag: dash, slide and one ability must stay in sync without rubber-banding.

### Step 5. One of our own heroes

Put a UE5-skeleton hero (the Wanderer) on the framework. Base locomotion comes from the shared set. Her abilities need new animation, authored by keyframing in Control Rig or Cascadeur from video reference, or bought as a pack. My estimate, not a sourced figure, is 25 to 40 clips for a full Deadlock-style hero: fire, alternate fire, reload, light and heavy melee, parry, four abilities with startup, hold and release, hit reactions and emotes.

## 7. Limits and open questions

- The new project starts as a movement and animation testbed. Match rules, weapons framework and UI come later, or from Lyra if route B is chosen.
- Sparrow is a stand-in for workflow, not a hero in our art style. Paragon assets are licensed for Unreal projects; check the terms before shipping anything derived from them.
- Her effects are older Cascade particle systems. They still run; converting to Niagara is optional work.
- Motion matching retargeted onto our own heroes will only look as good as their rigs allow. The hand and knee defects recorded earlier still apply.
- I have not run the GASP sample or Sparrow's blueprint in this session. Step 0 is where that happens.

## Sources

- [Animation in Lyra, Epic documentation](https://dev.epicgames.com/documentation/unreal-engine/animation-in-lyra-sample-game-in-unreal-engine)
- [Adapting Lyra animation to your UE5 game, Epic](https://www.unrealengine.com/tech-blog/adapting-lyra-animation-to-your-ue5-game)
- [Abilities in Lyra, Epic documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/abilities-in-lyra-in-unreal-engine)
- [Understanding the Gameplay Ability System, Epic documentation](https://dev.epicgames.com/documentation/unreal-engine/understanding-the-unreal-engine-gameplay-ability-system)
- [Game Animation Sample updated for UE 5.8, Epic](https://www.unrealengine.com/tech-blog/download-the-latest-game-animation-sample-project-now-updated-for-ue-5-8)
- [Game Animation Sample Project, Epic documentation](https://dev.epicgames.com/documentation/unreal-engine/game-animation-sample-project-in-unreal-engine?lang=en-US)
- [Motion Matching in Unreal Engine, Epic documentation](https://dev.epicgames.com/documentation/unreal-engine/motion-matching-in-unreal-engine?lang=en-US)
- [Forum: root motion source rubber-banding with abilities](https://forums.unrealengine.com/t/gameplay-ability-root-motion-source-rubber-banding/254732)
- [Forum: Mover 2.0 upgrade path](https://forums.unrealengine.com/t/mover-2-0-upgrade-path/2691288)
- [Deadlock wiki: Mechanics](https://deadlock.wiki/Mechanics)
- [Deadlock movement guide, Mobalytics](https://mobalytics.gg/deadlock/guides/movement-guide)
- [Deadlock movement guide, metabot](https://metabot.gg/en/deadlock/guides/deadlock-movement-mechanics-guide)
- [Dota 2 wiki: cast point and backswing](https://liquipedia.net/dota2/Cast_backswing)
- [Blizzard: Overwatch animation blog](https://news.blizzard.com/en-us/article/24239492/1)
