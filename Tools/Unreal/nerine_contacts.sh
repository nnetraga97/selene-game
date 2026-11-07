#!/bin/bash
# Copied Ysolde contact-sheet recipe; immutable evidence, no screenshot edits.
set -eu
out="$PWD/Saved/NerineHookup/session-1"
mkdir -p "$out/swift-cache"
for view in front side back; do
 swift -module-cache-path "$out/swift-cache" Tools/Unreal/nerine_detail_contacts.swift "$view" details-gameplay
 swift -module-cache-path "$out/swift-cache" Tools/Unreal/nerine_detail_contacts.swift "$view" ysolde-details-gameplay
done
