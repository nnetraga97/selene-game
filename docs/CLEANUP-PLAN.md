# Selene cleanup plan — no deletion performed

Surveyed on 2026-11-07 with `du` and `find`; no Unreal process, map, or asset was opened. `Saved` measured **6.7 GB**, `Content` **6.5 GB**, `Packaged` **1.9 GB**, `Intermediate` **1.9 GB**, and `SourceArt` **608 MB**. `Binaries` is also **2.7 GB** and `.git` **6.4 GB**, but neither is a delete row.

`Saved/TownV2/**` is deliberately excluded: TownV2 sessions 6 and 7 are active. The static reference audit used only `.ini`, `.py`, and `.json` files, as required. That cannot establish whether an asset is referenced by a `.umap`; therefore no Content asset is recommended for deletion merely because it appears unused.

## Candidate table

Sizes are allocated `du` sizes at survey time; they may change before a later cleanup.

| Candidate path(s) | Size | Why it is a candidate | Risk | Recommendation |
| --- | ---: | --- | --- | --- |
| `Intermediate/` | 1.94 GiB | Generated build intermediates; no static reference found. | Next build recompiles generated/C++ intermediates; unsafe while an editor/build is active. | **delete** after all sessions stop |
| `Saved/StagedBuilds/` | 1.76 GiB | Temporary staging output from 2026-11-06; no static reference found. | Removes staged build files; repackage to recreate. | **delete** |
| `Packaged/Development/` | 1.08 GiB | 2026-11-05 development package; it predates the current work and has no static reference. | Removes a locally runnable development build; repackage to recreate. | **delete** |
| `Saved/Cooked/` | 0.43 GiB | Generated cook output; no static reference found. | Next cook takes longer. | **delete** |
| `Saved/Shaders/` | 0.19 GiB | Regenerable local shader cache; no static reference found. | Initial editor launch recompiles shaders. | **delete** |
| `Saved/AutoShots_clips_Angel/`, `Saved/AutoShots_Champion/`, `Saved/AutoShots_clips_Champion/`, `Saved/AutoShots_Angel/` | 0.18 GiB | Old named capture scratch folders; no exact current-doc or static-tool reference. | Loses raw screenshots not retained as the current named hookup/AnimMatch evidence. | **delete** |
| `Saved/FaceCheck/`, `Saved/FaceCheck2/`, `Saved/FaceCheck3/`, `Saved/FaceCheck4/`, `Saved/FaceCheck5/` | 0.15 GiB | Disposable material/face test captures; no current-doc reference. The material helper can recreate its output location. | Loses raw test images and logs. | **delete** |
| `Saved/AssetImport/superseded/` | 0.03 GiB | Explicitly superseded import artifacts. A retrospective mentions one old split-eye path, but no live setup points to it. | Removes historical raw import evidence. | **delete** |
| `DerivedDataCache/` | 0.002 GiB | Regenerable derived cache; no static reference found. | Initial asset access rebuilds it. | **delete** |
| `Binaries/` | 2.70 GiB | Generated binaries are theoretically rebuildable, but current tooling references them and they may back a running editor. | Rebuild required; can disrupt active tools/editor. | **keep** |
| `Packaged/Shipping/` | 0.79 GiB | Static performance-run JSON points to this package. | Would invalidate a recorded local packaged-build reference. | **keep** |
| `Saved/Town/` | 0.24 GiB | Old Town v1 evidence, but current TownV2 documentation and `Tools/Town/contact_sheet.py` still reference it as fallback/comparison evidence. | Breaks existing current-document/tool references. | **keep** |
| `Saved/AnimMatch/`, `Saved/Sparrow/`, `Saved/YsoldeHookup/`, `Saved/WandererHookup/`, `Saved/MovementTest/`, `Saved/Clips/`, `Saved/FoxHookup/`, `Saved/Chars/` | 2.86 GiB combined | These are named evidence roots for incomplete/current progress records. | Would discard current evidence and in several cases break current documentation links. | **keep** |
| `Content/Selene/Materials/Character/OneSidedTest/` | 52 KiB | No permitted static reference was found; it looks like test content. | A map reference cannot be ruled out without an Unreal asset-reference check. | **ask** |
| `Content/ParagonSparrow/Characters/Global/Hair/TestContent/` | 10 MiB | Imported test content is a plausible cleanup target. | Dependencies/map references cannot be ruled out under the offline-only rule. | **ask** |
| `Content/`, `SourceArt/`, `Plugins/`, `.git/`, `Saved/TownV2/**` | 6.5 GB / 608 MB / 1.5 GB / 6.4 GB / excluded | Active assets, source art, dependencies, history, or live TownV2 evidence. | High: asset, source, dependency, history, or active-session loss. | **keep** |

The Toon BSDF backup named in the current material workflow is also **keep**, regardless of its size. It is an intentional rollback asset, not duplicate test content.

## Reclaimable total

The nine **delete** rows total **6,049,164 KiB (5.77 GiB)** at the time of this survey. This excludes every **keep** and **ask** row, including all Content candidates and all TownV2 data.

## Preconditions and execution order

1. Wait for TownV2 sessions 6/7 and any other Selene editor/build/cook to finish.
2. Keep `Saved/TownV2/**` untouched. Do not add Content candidates until an authorized Unreal reference check has cleared them.
3. Review this table, then run `bash Tools/cleanup_candidates.sh --apply` from the project root.
4. The script refuses to run while the Selene editor/process lock is present and moves only the nine **delete** rows to `~/.Trash`; it does not use `rm`.
5. Empty Trash only after a successful rebuild/cook/package check chosen by the project owner.

`Tools/cleanup_candidates.sh` was written for this plan and was **not run**.
