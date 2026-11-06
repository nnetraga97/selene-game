# Game rendering and interface direction

**Current prototype scope:** read [VISUAL-DEMO-BRIEF.md](../VISUAL-DEMO-BRIEF.md) first. The user approved the town concepts and soft cinematic character style B. This is an AI-built visual town demonstration with a few seamless interiors and lightweight NPC presence; game-system development is not its focus. That brief supersedes earlier provisional scope assumptions below.

## Confirmed intent

An original futuristic anime game; its scope is set by the approved concepts and VISUAL-DEMO-BRIEF.md, not an open-world or Elden Ring scale. Anime/design references are Honkai: Star Rail and Aion 2. Kingdom Come: Deliverance II and Cyberpunk are **render-fidelity inspirations**. “UI” includes both the game's interface and its rendering/presentation. This is a direction brief, not a claim that the pipeline already delivers those games' fidelity.

## Proposed interpretation for the first playable area

Keep stylized character proportions, attractive face shapes and deliberate color design. Give the world convincing scale, carefully authored surfaces, contact shadows and lighting that makes forms readable. Choose the character shader separately from the environment shader; photorealistic pores and heavy grime are not automatic requirements for anime faces.

Translate the inspirations into reviewable goals:

| Focus | Proposed quality target |
| --- | --- |
| Outdoor grounding | Natural light variation, readable distant landmarks, plausible wear and believable terrain/structure contact |
| Futuristic atmosphere | Selective emissive accents, layered architectural depth, coherent metal/ceramic/glass response and intentional night lighting |
| Anime identity | Clean silhouette, deliberate large/medium/small shapes, expressive faces, controlled gradients and readable costume layers |
| Material fidelity | Roughness and normal detail support the geometry; textures do not fake essential volume or carry unwanted baked highlights |
| Composition | A focal hierarchy at gameplay distance; detail concentrated where the player can see it |
| Motion | Stable shading, clean deformation, restrained bloom, no distracting temporal shimmer or disocclusion artifacts |

Start with one small original waystation or district vignette. Approve a daylight, dusk and artificial-light view before expanding into more biomes. Avoid generating hundreds of mismatched objects to imply world scale.

## Game UI

Develop an original, refined visual identity: a strong type hierarchy, restrained accent color, characterful iconography, confident spacing and responsive motion. Use player tasks to establish layout before ornament. HUD and menu elements should feel like parts of the same world.

- Combat HUD: essential health/ability/objective information readable against bright sky, dark interiors and emissive effects.
- Inventory/character: clear item hierarchy, meaningful comparisons, rich character presentation without obstructing interaction.
- World map: stable navigation, legible labels and useful landmark hierarchy at different zoom levels.
- Keyboard/mouse and controller focus: unmistakable selection, consistent back behavior and no hover-only information.
- Scale and motion: test at actual target resolution and UI scale; support reduced motion and text scaling where feasible.
- No gratuitous animated status dots, decorative telemetry, illegible microtype, or perpetual animation on every element.

This project intentionally does not implement a separate workflow dashboard. A game UI prototype belongs in the eventual game project once the engine and core player interactions are selected.

## References to collect before production

For each target asset, save one approved primary concept and any consistent alternate views. Annotate what matters: silhouette, proportion, palette, material roles, size, pivot and gameplay use. Collect game-render examples separately from asset-shape references so cinematic lighting does not get baked into generation inputs.

The user's [Corgo's 77 Collection resource](REFERENCE-SOURCES.md) is indexed for category and design research. Keep research-only images distinct from approved Studio inputs and record the particular image source.

For the UI, collect examples of the exact screen/task being designed and record what is useful about each. References should guide an original design rather than a collage of unrelated game interfaces.

## Required rendering proof

The neutral Blender turntable is a diagnostic tool. It does not validate the final game presentation. The eventual engine scene must test the same accepted assets under daylight and artificial lighting, with gameplay camera distances, actual materials, representative instance counts and frame-time measurements on chosen target hardware.

Unreal is the current candidate; a custom engine remains undecided. Retain editable Blender sources, embedded-texture GLBs and FBX exports. Shader graphs, animation systems and postprocessing are engine-specific work; a neutral file format alone does not make these portable.
