# BP3D Segmentation Straight Route — 2026-08-29

This branch is the public-safe online experiment lane. User-specific `.blend`, Special Suit texture, DAZ/V4 assets, and private textbook photographs MUST NOT be committed here.

## Single route

1. Freeze a hierarchical part naming convention and zone taxonomy.
2. Build textbook + web evidence rules per zone.
3. Generate static segmentation candidates from the immutable MakeHuman CC0 base mesh.
4. Apply adjacency-safe colors: directly adjacent parts must never share a color.
5. Review by zones, not only whole body: SHOULDER_AXILLA, ARM, HAND, BACK, HIP_THIGH, KNEE_LEG, FOOT, TORSO, HEAD_NECK.
6. Run motion-proxy checks for shoulder raise, elbow bend, hip flexion, knee bend, and ankle/toe motion. The CC0 base has no authoritative user rig, so online motion tests are explicitly proxies; final validation must later run on the duplicated user master.
7. For each failure, emit image + JSON + Markdown report with cause, evidence, and proposed remedy. Allowed remedies: relabel/resplit, texture boundary change, geometry-copy adjustment, weight-policy adjustment, or unresolved transition band.
8. Iterate automatically up to five correction cycles. Keep every cycle; never overwrite earlier evidence.
9. Produce three final hypotheses: SAFE (conservative), BALANCED (recommended compromise), FINE (detail-first), each with predicted success/failure modes.
10. Save artifacts to GitHub Actions and private Drive. Base44 is the review/history UI.
11. After the pipeline exists and has run, schedule a recurring improvement loop. It may continue evidence collection and bounded reruns, but must not modify original masters or canonical ABC/ABCD points.

## Safety invariants

- Source master / CC0 source input hash before and after must match.
- User originals are immutable. Modification permission applies only to explicit duplicates/copies.
- Canonical ABC/ABCD points are fixed and are not regenerated or moved by this lane.
- Public GitHub contains public-safe code/metadata only.
- Private textbook photos remain private in Google Drive.
- A technical PASS is not anatomical approval.

## Stop / retry policy

A recoverable implementation error is diagnosed, patched, and rerun without asking the user. Try bounded repairs first. Only mark a method IMPOSSIBLE after repeated failure and after testing a materially different method. Anatomical uncertainty is not silently forced: keep an unresolved band and report it.
