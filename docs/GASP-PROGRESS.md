# GASP migration progress log

Append one section per session (newest last). Plan: `docs/GASP-INTEGRATION.md`. Standing brief: `docs/GASP-BRIEF.md`.

## 2026-11-06 — controller setup (Claude)
- State at start: HEAD 8f3e45f. Kawaii Physics 1.21 builds (editor + Shipping); native `USeleneSecondaryAnimInstance` drives Champion (13 chains) and Angel (12 chains) on the old single-node blend space; play-tested and tuned. Ground materials applied. Material usage flags fixed.
- Decisions recorded in GASP-BRIEF.md (Option A; native follower anim instance with `FAnimNode_RetargetPoseFromMesh` + Kawaii instead of follower AnimBPs).
- Next: chunk 1 (baseline and conflict audit).
