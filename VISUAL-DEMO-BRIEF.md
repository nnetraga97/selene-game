# AI-built town visual demonstration

Confirmed user direction, November 5, 2026 (revised after review the same day). This brief supersedes earlier assumptions that the first town requires working economies, quests or elaborate NPC simulation. It does not itself submit jobs or edit any ledger.

## Where this brief lives

This brief and its `concepts/` folder will move together into a new, empty project folder that becomes the Unreal game project. Keep every path in this brief relative to that folder (`concepts/...`). Do not depend on files from the asset-workflow repo by relative path.

All 3D asset production goes through the global **`studio-pipeline`** skill, available in every Claude session. It owns the shared credit ledger, the asset archive, review records, `deliver` into the game and the headless Unreal import. Never generate 3D with orchestrator `generate_3d`, Mesh Bench or a generic 3D MCP.

## Purpose and priorities

Demonstrate the visual quality an AI agent can achieve when given a style, Unreal and access to 3D creation tools. The main acceptance criteria are town fidelity, look, feel and atmosphere. Game systems are not the focus, and the eventual game loop is undecided.

**The approved concepts define the look and the scope.** Earlier words such as "cyberpunk" or an open-world, Elden Ring-scale game do not apply to this demonstration. Kingdom Come: Deliverance II and Cyberpunk 2077 were only ever rendering-quality inspirations, not a mandate for gritty, neon or photoreal art.

The user considers questions about personal time, staffing and external production budget irrelevant to this demonstration. Do not reopen them as prerequisites. Schedules and durations in any plan are for humans; agents work through the steps without waiting on calendar time.

## Town scope

- One central plaza.
- Two residential areas.
- One commercial area.
- One industrial area.
- A few enterable, visually finished interiors, with no loading transitions. The blockout proposes how many and which buildings open; the user approves at the blockout checkpoint.
- Shops need only be convincing locations; purchase menus, economy, stock and opening-hour systems are unnecessary.
- NPC logic is low priority. Characters supply scale, atmosphere and animation rather than elaborate simulation.
- Four main character designs and two reusable NPC designs. **The user will describe each character**; the agent turns those descriptions into style-B references and models. The concept pair illustrates style, not the cast.
- Primarily third-person viewing, switchable to first-person.
- Continuous day/night cycle: **a full day lasts 24 real minutes by default**, with a debug control to pause, change speed or jump to any time of day.
- Street population at peak in the busiest area (the plaza): **about 15–25 people**, like the concepts, adjustable down for performance.

**Town size: medium, about a 5–6 minute walk across at normal pace** (roughly 400–500 m edge to edge). Area dimensions, building counts, concurrent population and exact interiors are set by the blockout and approved at its checkpoint. Do not reinterpret the five areas as five large districts.

## Approved visual direction

The user strongly approved the town concepts in `concepts/town-style-study-01/`, selected character treatment **B — Soft cinematic anime** in `concepts/character-style-study-01/`, and approved the two environment images in `concepts/environment-style-B-01/`.

Keep the town's stylization close to the initial ZZZ-inspired direction, with its own identity: cream rounded architecture, petrol-blue trim, coral accents, substantial readable props, welcoming inhabited streets and vegetation. Use richer shading, soft cinematic gradients, warm light, cool shadow fill and distinct restrained materials. Preserve anime character design and silhouettes.

**Character wardrobe (user direction, November 5):** clothes may show more skin, in the stylish modern anime-game manner of popular gacha characters: bare shoulders and arms, crop tops, shorts, coats worn off the shoulder. Characters are clearly adults; keep it tasteful and non-explicit. Each design keeps one silhouette hook, the town palette with a single saturated accent, and one signature accessory. Designs are original: draw on what makes popular Zenless Zone Zero and Honkai: Star Rail characters appealing, never their specific looks, names or outfits.

Reference images establish the look, feel and vibe. Exact camera matching, street layout, building placement and architectural replication are **not required**. Adjust geometry and composition for a coherent playable 3D town. The day/night cycle must keep that visual identity beyond the two reference lighting states.

## Engine and performance

Primary target: the user's M3 Max MacBook Pro (30-core GPU, 36 GB unified memory), Unreal 5.8.4.

- **Requirement: 60 fps minimum** on the target Mac, from the start, not deferred to a later optimization phase.
- **Ideal: 120 fps.** Not required now, but keep it reachable: prefer choices that scale (scalability tiers, instancing, material and light budgets) over ones that lock the frame rate down.
- Visual quality remains the priority. Measure; do not assume. Establish output and internal resolution, upscaling and scalability settings, and report them with benchmarks. Evaluate frame pacing on representative interiors and exteriors in a packaged build; a still image or editor average is insufficient.
- A continuous day/night cycle rules out fully baked lighting, so dynamic GI (Lumen) and dynamic shadows are expected. Confirm the lighting method on the representative route and record its cost.

Proceed with Unreal, custom art materials and automation. **Do not add a preliminary Unreal smoke test:** the user has used Unreal repeatedly. A custom engine is not requested.

## Generation allocation

Total **1,400 credits: 1,000 Studio and 400 CLI**, on top of the 110 Studio credits already spent on earlier tests. The ledger's Studio budget is therefore 1,110 and the CLI budget 400. Keep the pools distinct and follow the `studio-pipeline` skill and its ledger rules:
- Studio is the default pool. Its credits expire on **2026-11-14**.
- The CLI pool is only for small-tier assets, and CLI spend can never pass settled Studio spend.
- Record the real budgets in the ledger before spending. Never silently repurpose or overwrite earlier test records.

Do not spend on unrequested game systems. Judge generation by accepted, visually useful assets and credits per accepted asset, not by generation counts.

## Choosing the route per asset

There is no fixed rule that some kinds of asset are generated and others are modelled. For each asset (or each part of a character), the agent decides whether Tripo or its own Blender work will produce the better result, based on the task:
- **Lean towards Tripo** for organic, detailed or irregular shapes: props, set dressing, vegetation pieces, character bodies and clothing. The user observes Tripo is usually slightly better.
- **Lean towards Blender** where precision and reuse matter more than surface detail: modular architecture kits that must snap together, collision and blockout geometry, and repairs to generated meshes (topology, rig weights, pivots, scale).
- **Combine them** where that is better: for example a Tripo-generated character with Blender topology and weight cleanup, or a Blender kit with Tripo-generated trim pieces.
- When unsure, try both on one example and keep the better one.
- Record each decision and its reason in the manifest, so the intervention log shows where generation won and where hand-made work did.

Blender-made assets go through the same asset pipeline as generated ones (check renders, review record, delivery), with their `.blend` source and script recorded as the origin.

## Reference images for generation

The concept images are scene-level look references. They are **not** generation inputs: Tripo needs one clean, single-object reference per asset.
- Make each asset's reference with an image model: orchestrator `generate_image` (OpenAI image route), or an OpenAI worker generating its own. The configured image route has a daily limit (40 images per day at the time of writing), so plan references per batch and reuse them.
- Match each reference to the approved style, and record it with the asset (prompt, model, file) in the manifest.

## Production sequence, with user checkpoints

1. **Blockout.** Connect the five areas with representative dimensions, interior openings and camera routes. **Checkpoint: user approves the blockout** before set dressing begins.
2. **Representative route.** Build the look on a demanding route: a plaza edge with a broad town view leading seamlessly into a café or workshop. Include vegetation, glass, restrained damp surface accents, practical and emissive lights, and one representative B-style character. Inspect moving first- and third-person views, close details and indoor/outdoor transitions. An easy isolated corner or two attractive stills is not a substitute. **Checkpoint: user approves the route's look and its measured frame rate.**
3. **Lighting cycle.** Author the continuous cycle deliberately: sun, sky, exposure, artificial lights and emissive curves. Review intermediate times, interiors and transitions for lost detail, flattened anime shading, flicker or abrupt changes.
4. **Expansion.** Grow reusable Blender architecture kits, shared materials and selectively generated props across the five areas. Preserve editability, source files and rejected attempts in the asset archive.
5. **Characters.** Establish one character's modelling, shading, rig and basic motion, choosing the route per part as above (Tripo is usually the stronger starting point). Anime B-style shading needs its own Unreal material and post-process setup. Verify a second distinct silhouette with the same pipeline before expanding to four main designs and two reusable NPC designs. Lightweight idle and walk animation is enough; keep visible population adjustable. **Checkpoint: user approves the first character** before the rest are built.
6. **Performance throughout.** Profile representative content density (instances, materials, lights, skinned actors) against the 60 fps requirement without silently degrading the agreed look. Package and evaluate the completed town in motion across all five areas, both cameras, interiors and the full lighting cycle.

Basic movement, camera switching, collision, interior access and the time-of-day controller support the visual evaluation. Combat, quests, a shop economy, relationship systems, complex NPC schedules and multiplayer are out of scope.

## What goes into the game repo

Commit only what the final game needs:
- Unreal project files, code, config, and the `Content/` assets actually used in the town.
- A small provenance record per used asset (source run, checksum), so the game can be traced back to the asset archive.

Do **not** commit every reference image, concept variation, rejected or superseded GLB, or intermediate export. Those stay in the asset-workflow archive, which already preserves sources, runs and rejected attempts. Use Git LFS for binaries that are committed.

## Evidence of success

- A locally runnable Unreal demonstration and repeatable creation and import steps.
- Strong resemblance to the approved visual language across all five areas, judged by the user at the checkpoints.
- Seamless access to the selected interiors.
- Readable character and environment integration using B's shading direction.
- A continuous lighting cycle that stays attractive throughout.
- Recorded performance at explicit settings, including slow scenes and transition points: at least 60 fps, with the gap to 120 fps reported. Report any failure to meet the minimum.
- A reproducible manifest of source references, prompts, asset versions, generation settings, scripts, material and lighting settings, and engine imports.
- An intervention log separating agent-completed steps, human corrections, failed assets and unresolved defects, so the demonstration shows what the AI workflow actually achieved.

## Decisions recorded

- Studio budget for the town is a fresh 1,000 on top of the earlier 110 test spend; CLI 400.
- Route per asset is the agent's call (Tripo, Blender or both), recorded with a reason.
- Blender-made assets go through the asset pipeline with their own origin record.
- Town size: medium, about a 5–6 minute walk across.
- Cast: the user describes the four main characters and two NPCs.
- Interiors: the blockout proposes them.
- Day length: 24 real minutes by default, adjustable.
- Plaza crowd at peak: about 15–25 people.

This revision applies the user's answers to the November 5 review. It performs no implementation, generation, account action or budget change.
