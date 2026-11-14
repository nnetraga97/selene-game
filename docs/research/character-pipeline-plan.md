# Character pipeline plan

Written 2026-11-09. Scope: characters only (model, face, rig, animation, shading). The town and game systems are out of scope. Nothing here has been built or tested yet; it is a plan for approval.

## 1. The short version

The characters look lifeless because the pipeline treats one image-to-3D output as the finished character. A studio treats that kind of output as a rough sculpt, roughly step 2 of 9. The steps that give a character a face that moves, joints that bend well and motion with personality do not exist in our pipeline at all, so no amount of tuning the current steps will fix it.

The plan is to stop making new characters, take **one** hero to a high bar, and build her the way studios do: in separate layers (body, head, eyes, hair, each garment), on a clean base mesh that already has a face rig. Unreal 5.8's Mesh to MetaHuman is the fastest way to get that base, and it is installed on this Mac. A short, free test decides whether it can hold our art style. If it can't, the fallback is a stylized base head built in Blender.

## 2. What the codebase shows

I read the ten character files in `SourceArt/Assets/`, the hookup and progress records, the retrospective and four capture sheets (Champion idle, Ysolde close front and side, Ysolde against Sparrow).

| Finding | Evidence | Effect |
| --- | --- | --- |
| No face rig on any character | All ten GLBs: 0 morph targets, 0 face bones (no jaw, eyelid, brow or eye bones) | The face cannot move. No blink, no eye movement, no mouth. This alone explains "expressionless". |
| Eyes, teeth and mouth interior are not objects | Eyes are painted onto the head surface. The Wanderer's had to be replaced with cards (`workflow-retrospective.md`, T2) | Eyes can't look anywhere or catch light. |
| One fused mesh per character | Body, hair, face and clothes are one surface in 7 of 10 files | Clothes can't slide over the body, hair can't be shaded as hair, and weights bleed (skirt followed the hands, R9). |
| Generator topology | 46–78k triangles with no edge loops at joints or around eyes and mouth; the Fox is 10k, the base body 6.7k | Knees spike, fingers can't curl, and no face rig could be added even by hand. |
| Lighting baked into one colour texture | One image per character; 7 of 10 have no normal map | Painted shadows fight the scene lighting. Faces go flat or muddy in engine. |
| Everyone shares one borrowed motion set | 11–15 GASP locomotion clips retargeted from Manny for every hero; no bespoke idle, ability, emote, hand or face animation | All heroes move the same way, as an average man. |
| No character shading model | `M_Character_Toon` is a standard-lit slab with a rim term; no face, eye, hair or skin treatment | Nothing protects the face from harsh shadows, which is the first thing anime and stylized games solve. |
| Gates measure plumbing, not appeal | Checks cover height, bone count, facing and loop seams | Ten characters passed in two days without anyone approving a face close-up. |

The effort so far went into hookup work (scale, facing, retargeting, loop centring). That work was real, but it sits downstream of the asset. The asset itself never went through the stages that make it good.

## 3. How studios build a hero

No public Valve write-up of Deadlock's pipeline turned up. The stages below are consistent across the sources I did find (Blizzard, NetEase, Tango, Epic) and standard practice.

1. **Design package.** Not one illustration: front, side and back views in a neutral pose, a face close-up, an expression sheet, and a breakdown of costume layers and materials. Blizzard defines a hero's personality and how they move before any animation starts.
2. **High-detail sculpt.** Shape only. This is the stage AI image-to-3D now covers reasonably well.
3. **Retopology.** A clean, low-polygon mesh is rebuilt over the sculpt with rings of edges around the eyes and mouth and at every joint. The body, head, eyeballs, teeth, tongue, hair and each garment are separate meshes.
4. **Bake and texture.** Fine detail is baked into normal maps. Colour, roughness and so on are separate maps with **no lighting painted in**.
5. **Shading.** A character-specific shader. Marvel Rivals blends toon shading with physically based highlights. Anime-style games control face shadows directly, with a hand-authored shadow map or edited normals, so the face never gets ugly shadows. Hi-Fi Rush's team presented their version at GDC 2024.
6. **Body rig.** A shared skeleton across the roster, with helper joints and corrective shapes at shoulders, elbows, knees and wrists.
7. **Face rig.** Dozens to hundreds of controls built from blendshapes (sculpted face poses), joints, or both. 52 ARKit shapes is the practical minimum; MetaHuman has far more. Separate eyes with look-at and eyelids that follow them.
8. **Animation.** Per hero: idle, locomotion, each ability, emotes and hero-select poses, built on strong key poses with exaggeration. Overwatch's animators describe deliberately breaking the rig for snappier motion. Shared mocap is a base layer at most.
9. **Engine integration.** Cloth and hair simulation, levels of detail, animation layering, and review at the real gameplay camera.

We do steps 2 and 9, a thin version of 6, and step 8 with borrowed clips.

## 4. What changed in the tools

- **Mesh to MetaHuman, Unreal 5.8.** It takes a humanoid head and body mesh in any topology, including AI output, and returns it on MetaHuman topology with the full face and body rig. Epic says it handles stylized humanoids. Forum reports say extreme proportions (a tiny button nose) twist the result, and that textures do not transfer. This one tool covers steps 3, 6 and 7.
- **It is on this Mac.** `Engine/Plugins/MetaHuman/MetaHumanCharacter` ships Mac binaries in the installed 5.8, and MetaHuman Animator lists Mac as supported. I have not run either here.
- **MetaHuman Animator** turns a phone or webcam video, or just audio, into face animation. Face capture runs on macOS in 5.8. Single-camera body capture is experimental and Windows-only.
- **The MetaHuman body uses the UE5 skeleton family.** The Wanderer result (playable in 95 minutes, no loop surgery) suggests the retarget workarounds go away.
- **Tripo** now has part-by-part generation habits worth adopting (bald base body, each garment separate), a newer humanoid rig model and hand bones. It still produces no face rig.
- **Research tools** for automatic face rigging on arbitrary meshes exist (OmniFaceRig) but are not shipping products.

## 5. Three routes

| | A. MetaHuman base (recommended first) | B. Stylized base head in Blender | C. Contract artist for hero 1 |
| --- | --- | --- | --- |
| How | Generated bald head and body → Mesh to MetaHuman → our own materials, hair and clothes on top | One clean anime-style head with ARKit shapes, eyes and teeth; fit it to each character's head in Blender; shared base body | A character artist builds hero 1 from our design package; we learn the bar and reuse the base |
| Gets us | Topology, face rig, eyes, teeth, body correctives, levels of detail, native skeleton | Full control of the look; works in any engine | The actual studio answer; a gold standard to compare against |
| Risk | May not hold strongly anime faces (large eyes, small nose). Realistic by default, so the look must come from our shader and textures. Heavier at runtime. | Much more of our own work. Face rig quality depends on one base head being good. | Money and lead time |
| Fits if | The target is semi-realistic stylized, like the Champion concept, Aion 2 or Deadlock | The target is strongly anime, like Honkai: Star Rail | You want the bar set by a professional |

These combine: A or B supplies the base, and C can be bought later for the one piece that falls short. A is first because a free test tells us in one session whether it works.

## 6. The plan

### Phase 0. Free tests, then you choose (no credits)

1. **Conform test.** In Unreal 5.8, run Mesh to MetaHuman on a head and body we already have (bald base body, and the Champion head cut off in Blender). Record whether it runs on the Mac and how much of the face shape survives.
2. **Face motion test.** Drive the result with a 10-second phone clip and one audio line through MetaHuman Animator. Capture a close-up.
3. **Fallback test, only if 1 fails on style.** Fit a clean stylized head with ARKit shapes to the Champion head in Blender and drive it with the same clip.
4. **You look at the close-ups and pick route A or B.**

### Phase 1. One hero to the bar: the Festival Champion

Each step ends with a few images for your approval before the next starts.

1. **Design package.** From the existing concept: front, side and back in A-pose; face front and side, neutral; a sheet of 6–8 expressions; bald base body; hair alone; each garment alone. Add a one-page movement brief: posture, tempo, three adjectives.
2. **Base.** Generate the bald head and body, then conform (route A) or fit (route B). Approval is a grey, untextured close-up with the face moving.
3. **Hair and costume as separate meshes.** Generate each piece on its own with a stated triangle limit, clean it in Blender, add joint loops, fit it to the base body, and copy skin weights from the body instead of auto-rigging the garment. Hair gets bone chains; long cloth gets simulation.
4. **Textures and shader.** Remove painted lighting or repaint flat colours; separate maps. Build one character shader: controlled face shadow, eye with separate iris and highlight, hair highlight, soft skin ramp. Approval is the face under noon, shade and night lighting.
5. **Face life.** Always on: blinks, eye darts, look-at and breathing. Then a small library of expression poses from the sheet, driven by game state (aiming, hit, ability, win). Then captured performances for hero-select and emotes.
6. **Body animation.** Keep motion matching for locomotion. Add what makes her hers: a posture layer over the shared locomotion, and bespoke idle, hero-select intro, primary attack, two abilities and an ultimate. Author these by keyframing in Unreal's Control Rig or Cascadeur, starting from video reference.
7. **Showcase check.** A 15-second clip at the gameplay camera and the hero-select camera, next to the concept sheet and a reference hero.

### Phase 2. Make it repeatable

Write the working steps into the `studio-pipeline` skill and the intake checks. Build hero 2 with it and compare the time taken. Only then scale the roster or move to the new game project.

### New acceptance gates

- A face close-up from three angles under three lightings, approved by you, before any rigging hookup.
- An expression sheet rendered from the rig, next to the concept expression sheet.
- A range-of-motion clip (deep squat, arms overhead, fist, twist) before any gameplay animation.
- Existing checks for scale, facing and triangle limits stay, as automatic intake checks.

## 7. Limits and open questions

- **Triple-A parity is not something a pipeline delivers.** A studio hero takes specialists a long time, and the last stretch is taste in the sculpt and the animation. This plan should get one hero from "generated asset" to a credible stylized character with a living face. If the result still falls short after Phase 1, the gap is most likely animation or sculpt polish, and that is where a contractor is worth paying for.
- Mesh to MetaHuman on macOS is unverified until Phase 0 runs.
- How far MetaHuman can be pushed toward anime proportions is unknown; the forum evidence is one unresolved thread.
- MetaHuman runtime cost for a 12-player match needs measuring. 5.8 added bone reduction and per-platform levels of detail for this.
- If the final game leaves Unreal, route A needs a licence check. Route B is portable.
- Paid generation will be quoted before any spend, with triangle limits set and verified.

## 8. Phase 0 results, 2026-11-09

Free local tests on a Tripo "modular" anime head and hand the user generated (10 credits, user's own clicks). Evidence and worker reports: `game-asset-workflow/work/spikes/2026-11-09-face-hand/` (`RESULTS.md` is the summary). No independent reviewer ran.

- **Tripo head: a shape and style target, not a riggable head.** The skin has no eye openings (the "eyes" are caps floating in front of it) and the mouth is a sealed groove. Blink tears the mesh and an open mouth rips it. Smile and brows work.
- **Tripo hand: better mesh, unproven in motion.** Even quads with rings at the knuckles, against sliver triangles on the Champion. With a quick scripted rig its fist was worse than the Champion's auto-rigged fist, so the test measured the rig more than the mesh. Not fit as a base hand until it gets a comparable rig from a flat rest pose.
- **Mesh to MetaHuman: in the Mac build, wrong fit for this style.** The fit step is scriptable and local. The face rig needs an Epic sign-in and cloud service, textures do not transfer, and the fit is built on real human faces. Not run.

**Effect on the plan:** for a strongly anime look, route B (a clean stylized base head in Blender) is the route. The open item is where the clean base comes from, since single-shot generation did not produce lids, a mouth or closed eyeballs.

### Against the base model and the rest of the roster

Same day, all nine rigged characters plus the two new parts through one script (sheets and table in the spike folder's `roster-compare/` and `RESULTS.md`).

- **Head.** The new Tripo head is the best wrap target we have: bald, 4,106 vertices against the Base model's 933, no sliver faces. Nerine is the only hero whose hair is a separate piece. Every other head is fused with its hair. No head in the roster has a morph target or face bone.
- **Hand mesh.** The new hand (1,396 vertices, 72% quads) and the Angel's (805 vertices, 72% quads) are the two clean ones. The Base model's hand is 249 vertices and the Fox's 127.
- **Hand in motion.** The five Tripo auto-rigged hands that have enough geometry (Base, Wanderer, Fixer, Courier, Champion) make a compact fist. The hands rigged or re-weighted in house (Ysolde, Nerine, the new hand's quick rig) do not. The rig decided the result more than the mesh did.
- **The Base model is too coarse to be the roster base** (6,772 triangles in all).

## Sources

- [MetaHuman 5.8 release notes](https://dev.epicgames.com/documentation/metahuman/metahuman-5-8-release-notes-in-unreal-engine?lang=en-US)
- [MetaHuman 5.8 is now available](https://www.metahuman.com/news/metahuman-5-8-is-now-available)
- [Unreal Engine 5.8 announcement](https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available)
- [Forum: conforming MetaHuman to a stylized mesh, 5.8.2](https://forums.unrealengine.com/t/tips-on-conforming-metahuman-to-a-custom-stylized-mesh-5-8-2/2769797)
- [Forum: Mesh to MetaHuman feedback for stylized characters](https://forums.unrealengine.com/t/mesh-to-metahuman-feedback-in-ue5-main-early-ue-5-8-for-stylized-characters/2707537)
- [Inside Marvel Rivals' character art pipeline, 80.lv](https://80.lv/articles/inside-marvel-rivals-character-art-vfx-destruction-pipeline)
- [The making of Hi-Fi Rush's toon rendering, 80.lv](https://80.lv/articles/the-making-of-hi-fi-rush-s-3d-toon-rendering-style)
- [Blender NPR: recreating the Genshin Impact shader](https://bjayers.artstation.com/blog/category/5)
- [GDC: The Animation Pipeline of Overwatch](https://www.gdcvault.com/play/1024267/The-Animation-Pipeline-of-Overwatch)
- [How Overwatch's first-person animation breathed life into heroes](https://www.invenglobal.com/articles/1187/how-overwatchs-first-person-animation-breathed-life-into-heroes)
- [David Gibson on animating Mei, 80.lv](https://80.lv/articles/david-gibson-animating-mei-in-overwatch)
- [Deadlock's Mina with a Blender face rig, 80.lv](https://80.lv/articles/see-how-expressive-deadlock-s-mina-s-face-can-be-with-this-blender-rig)
- [Reallusion: generative AI with Character Creator 5 and Headshot 3](https://magazine.reallusion.com/2026/09/04/ai-holy-grail-mastering-generative-ai-with-3d-assets-and-ai-studio/)
- [OmniFaceRig paper](https://arxiv.org/html/2606.08043v1)
- [Tripo rigging and text-to-motion update](https://spatialinsiders.com/stories/tripo-rigging-animation-text-to-motion)
- [Tripo developer changelog](https://developers.tripo3d.ai/en/docs/changelog)
- [CG Channel, 2 November 2026 round-up](https://www.cgchannel.com/2026/11/new-cg-software-you-may-have-missed-2-november-2026/)
