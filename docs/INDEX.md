# Documentation index

Status labels: **live** governs work currently in progress; **current** is retained operational guidance or an open record; **historical** records completed, superseded, or reference-only work.

## Project-root companion documents

| Document | Status | One-line description |
| --- | --- | --- |
| [`README.md`](../README.md) | current | Project overview, build/run command, controls, roster, and directory guide. |
| [`VISUAL-DEMO-BRIEF.md`](../VISUAL-DEMO-BRIEF.md) | current | Governing visual-demo scope and acceptance intent. |

## Current and live records

| Document | Status | One-line description |
| --- | --- | --- |
| [`ANIM-MATCH-BRIEF.md`](ANIM-MATCH-BRIEF.md) | current | Scope for aligning the playable heroes with Sparrow's movement presentation. |
| [`ANIM-MATCH-PROGRESS.md`](ANIM-MATCH-PROGRESS.md) | current | Accepted facing fixes plus outstanding transition, clip, and foot-sliding work. |
| [`ART-DIRECTION.md`](ART-DIRECTION.md) | current | Approved rendering, UI, and soft-cinematic anime direction. |
| [`CHARS-PROGRESS.md`](CHARS-PROGRESS.md) | current | Stopped Fixer/Courier integration record and its diagnosed next action. |
| [`CLIPS-BRIEF.md`](CLIPS-BRIEF.md) | current | Bounded plan for adopting GASP clips without breaking the native player path. |
| [`CLIPS-PROGRESS.md`](CLIPS-PROGRESS.md) | current | Clip/slot research record; the gameplay C++ hookup remains unfinished. |
| [`CLEANUP-PLAN.md`](CLEANUP-PLAN.md) | current | Non-destructive cleanup inventory, exclusions, and trash-only execution plan. |
| [`ENVIRONMENT-ASSET-LIST-DRAFT.md`](ENVIRONMENT-ASSET-LIST-DRAFT.md) | current | Draft inventory and sourcing considerations for environment assets. |
| [`FOX-HOOKUP-BRIEF.md`](FOX-HOOKUP-BRIEF.md) | current | Scope for the Fox (Lysara) playable-character hookup. |
| [`FOX-HOOKUP-PROGRESS.md`](FOX-HOOKUP-PROGRESS.md) | current | Fox playable checkpoint, visual findings, and required follow-up. |
| [`GASP-BRIEF.md`](GASP-BRIEF.md) | current | Standing rules and architectural choice for a potential GASP migration. |
| [`GASP-INTEGRATION.md`](GASP-INTEGRATION.md) | current | Detailed GASP integration options, dependencies, and implementation constraints. |
| [`GASP-PROGRESS.md`](GASP-PROGRESS.md) | current | Controller setup log; the migration itself has not been completed. |
| [`INDEX.md`](INDEX.md) | current | This status-labelled map of project documentation and archived moves. |
| [`INTERVENTION-LOG.md`](INTERVENTION-LOG.md) | current | Decision and remediation history retained as project evidence. |
| [`KAWAII-PHYSICS.md`](KAWAII-PHYSICS.md) | current | Kawaii Physics installation evidence and proposed native hookup. |
| [`MANIFEST.md`](MANIFEST.md) | current | Intended reproducible manifest for asset/system provenance. |
| [`MOVEMENT-BRIEF.md`](MOVEMENT-BRIEF.md) | current | Advanced-movement design and bounded-session rules. |
| [`MOVEMENT-PROGRESS.md`](MOVEMENT-PROGRESS.md) | current | Accepted isolated movement mechanics and the remaining integration checks. |
| [`REFERENCE-SOURCES.md`](REFERENCE-SOURCES.md) | current | Source/reuse guidance for original futuristic-anime references. |
| [`SPARROW-BRIEF.md`](SPARROW-BRIEF.md) | current | Scope for making Sparrow playable and validating her presentation. |
| [`SPARROW-PROGRESS.md`](SPARROW-PROGRESS.md) | current | Sparrow integration evidence with the unresolved weapon follow-up. |
| [`STATUS.md`](STATUS.md) | current | Short current-state summary, known limits, and next steps. |
| [`TOWN-V2-BRIEF.md`](TOWN-V2-BRIEF.md) | live | Live TownV2 charter; its session 6 and 7 scopes are currently running. |
| [`TOWN-V2-PROGRESS.md`](TOWN-V2-PROGRESS.md) | live | Verified TownV2 sessions 1–5; results for current sessions are not yet appended. |
| [`WANDERER-HOOKUP-BRIEF.md`](WANDERER-HOOKUP-BRIEF.md) | current | Scope for integrating the teal Wanderer hero. |
| [`WANDERER-HOOKUP-PROGRESS.md`](WANDERER-HOOKUP-PROGRESS.md) | current | Wanderer playable checkpoint with crouch and mesh-polish limitations. |
| [`YSOLDE-HOOKUP-BRIEF.md`](YSOLDE-HOOKUP-BRIEF.md) | current | Scope for the in-house-rigged Ysolde UE5-Mannequin hookup. |
| [`YSOLDE-HOOKUP-PROGRESS.md`](YSOLDE-HOOKUP-PROGRESS.md) | current | Ysolde playable checkpoint and documented coat/trouser/hand defects. |

## Research and reference history

| Document | Status | One-line description |
| --- | --- | --- |
| [`research/after-the-wind-workflow.md`](research/after-the-wind-workflow.md) | historical | External AI-assisted 3D workflow research and lessons. |
| [`research/multi-tail-3d.md`](research/multi-tail-3d.md) | historical | Earlier six-tail character-generation research for Lysara. |
| [`research/town-quality.md`](research/town-quality.md) | historical | Assessment of the old Town presentation and its phased improvement strategy. |
| [`research/workflow-retrospective.md`](research/workflow-retrospective.md) | historical | Retrospective on Nov. 5–6 asset and animation workflow failures. |

## Archived Town v1 records

| Document | Status | One-line description |
| --- | --- | --- |
| [`archive/TOWN-BRIEF.md`](archive/TOWN-BRIEF.md) | historical | Superseded brief for the original `Town` map. |
| [`archive/TOWN-PROGRESS.md`](archive/TOWN-PROGRESS.md) | historical | Original Town session-1 checkpoint; it is not the active TownV2 map. |

Moved into `docs/archive/` with plain `mv` on 2026-11-07:

- `docs/TOWN-BRIEF.md` → `docs/archive/TOWN-BRIEF.md`
- `docs/TOWN-PROGRESS.md` → `docs/archive/TOWN-PROGRESS.md`

No other brief/progress pair was moved: AnimMatch, Clips, GASP, Sparrow, Fox, Wanderer, and movement records have open work; Ysolde and TownV2 were explicitly protected.

## Machine-readable evidence

| File | Status | One-line description |
| --- | --- | --- |
| [`engine-checks/fox-spirit-sovereign.json`](engine-checks/fox-spirit-sovereign.json) | historical | Offline engine-check data for the imported Fox asset. |
| [`engine-checks/teal-wanderer.json`](engine-checks/teal-wanderer.json) | historical | Offline engine-check data for the imported Wanderer asset. |
