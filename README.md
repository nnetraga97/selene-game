# Selene

Selene is an Unreal Engine 5.8 C++ anime seaside-town visual demo. The live playable area is **TownV2**, a Kailua-Kona-inspired waterfront town. It is a visual/demo project rather than a finished game; the current town pass and several animation-polish tasks are still in progress.

## Build and run

Use a UE 5.8 installation with the plugins declared in `Selene.uproject`. From the project root, the existing project tooling uses:

```sh
ENGINE=/Users/Shared/Epic\ Games/UE_5.8
"$ENGINE/Engine/Build/BatchFiles/Mac/Build.sh" SeleneEditor Mac Development "$PWD/Selene.uproject" -waitmutex
"$ENGINE/Engine/Binaries/Mac/UnrealEditor" "$PWD/Selene.uproject" /Game/Selene/Maps/TownV2 -game
```

Do not start another editor while a Selene editor process or `/tmp/selene-unreal.lock` exists. In particular, TownV2 sessions 6 and 7 are active as of 2026-11-07; leave `Saved/TownV2/**` alone while they write their evidence.

## Controls

| Input | Action |
| --- | --- |
| WASD / mouse | Move / look |
| Shift | Dash on press; sprint while held |
| Ctrl | Slide |
| CapsLock | Walk toggle |
| Space | Jump |
| V | Toggle camera |
| C | Cycle hero |
| M | Toggle top-down map |
| F | Toggle FPS counter |
| Esc | Pause menu |

The pause-menu text is implemented in `Source/Selene/SSelenePauseMenu.cpp`; map and FPS UI live in `Source/Selene/UI/`.

## Heroes

The roster is Champion, Angel, Sparrow, Fixer, Courier, Fox (Lysara), Wanderer, and Ysolde. Ysolde is the newest hero: an original harbour council envoy rigged in-house on the UE5 Mannequin skeleton. Her setup and outstanding mesh/weight findings are in `docs/YSOLDE-HOOKUP-BRIEF.md` and `docs/YSOLDE-HOOKUP-PROGRESS.md`.

## Where things live

| Area | Location |
| --- | --- |
| Playable map | `Content/Selene/Maps/TownV2` (`/Game/Selene/Maps/TownV2`) |
| Game code and roster runtime | `Source/Selene/` and `Config/DefaultGame.ini` |
| UI | `Source/Selene/UI/` and `Source/Selene/SSelenePauseMenu.cpp` |
| Selene-authored characters, animation, materials, and environment | `Content/Selene/` |
| Imported character and building assets | `Content/Assets/` |
| Raw/source art | `SourceArt/` |
| Current town automation | `Tools/Unreal/town_v2_*.py` |
| Project documentation | `docs/` — start at `docs/INDEX.md` and `docs/STATUS.md` |

`M_Character_Toon` is now a standard-lit Substrate Slab material with a rim term, rebuilt by `Tools/Unreal/rebuild_character_lit.py`. The prior Toon BSDF materials are retained under `Content/Selene/Materials/Character/Backup_ToonBSDF`.

The newly imported building families are under `Content/Assets/`: `seaside-guesthouse`, `seaside-lighthouse-house`, `harbour-boathouse`, `artdeco-tower`, and the `metro-*` assets. Their live placement work belongs to the TownV2 session 6/7 records.

For the governing visual scope, see [VISUAL-DEMO-BRIEF.md](VISUAL-DEMO-BRIEF.md), [art direction](docs/ART-DIRECTION.md), and the [documentation index](docs/INDEX.md).
