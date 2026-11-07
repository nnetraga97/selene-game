#!/usr/bin/env bash
# Move only the DELETE rows from docs/CLEANUP-PLAN.md to the macOS Trash.
# Deliberately requires --apply and refuses to run during a Selene editor session.
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ! -f "$project_root/Selene.uproject" ]]; then
    printf 'Expected a Selene project root; refusing to continue.\n' >&2
    exit 2
fi

targets=(
    'Intermediate'
    'Saved/StagedBuilds'
    'Packaged/Development'
    'Saved/Cooked'
    'Saved/Shaders'
    'Saved/AutoShots_clips_Angel'
    'Saved/AutoShots_Champion'
    'Saved/AutoShots_clips_Champion'
    'Saved/AutoShots_Angel'
    'Saved/FaceCheck'
    'Saved/FaceCheck2'
    'Saved/FaceCheck3'
    'Saved/FaceCheck4'
    'Saved/FaceCheck5'
    'Saved/AssetImport/superseded'
    'DerivedDataCache'
)

if [[ "${1:-}" != '--apply' || "$#" -ne 1 ]]; then
    printf 'Dry listing only. To move these cleanup-plan rows to ~/.Trash, run:\n'
    printf '  bash Tools/cleanup_candidates.sh --apply\n\n'
    printf '%s\n' "${targets[@]}"
    exit 0
fi

if [[ -e /tmp/selene-unreal.lock ]]; then
    printf 'Selene Unreal lock exists; refusing to move build/cache data.\n' >&2
    exit 3
fi

if pgrep -fl 'UnrealEditor(-Cmd)?.*Selene\.uproject' >/dev/null; then
    printf 'A Selene Unreal process is running; refusing to move build/cache data.\n' >&2
    exit 3
fi

trash_dir="$HOME/.Trash"
if [[ ! -d "$trash_dir" ]]; then
    printf 'macOS Trash directory is unavailable: %s\n' "$trash_dir" >&2
    exit 4
fi

timestamp="$(date +%Y%m%dT%H%M%S)"
for relative_path in "${targets[@]}"; do
    source_path="$project_root/$relative_path"
    if [[ ! -e "$source_path" && ! -L "$source_path" ]]; then
        printf 'Already absent; skipped: %s\n' "$relative_path"
        continue
    fi

    destination="$trash_dir/selene-cleanup-${timestamp}-$(basename "$relative_path")"
    if [[ -e "$destination" || -L "$destination" ]]; then
        printf 'Trash destination already exists; refusing partial cleanup: %s\n' "$destination" >&2
        exit 5
    fi

    printf 'Moving to Trash: %s\n' "$relative_path"
    mv "$source_path" "$destination"
done

printf 'Completed. All listed paths were moved to %s and remain recoverable there.\n' "$trash_dir"
