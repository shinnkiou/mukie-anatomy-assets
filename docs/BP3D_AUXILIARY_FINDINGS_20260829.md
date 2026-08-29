# BP3D Auxiliary Findings — 2026-08-29

Source: GitHub Actions run `33241120235`, artifact `9711542214`, branch `bp3d-online-segmentation-20260829`.

This document contains public-safe aggregate results only. It does **not** contain the user's textbook images, Victoria 4 images, original Special Suit texture, user MASTER blend, or user ABC/ABCD data.

## Safety invariants

- Source MakeHuman CC0 base SHA-256: `8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c`
- `source_unchanged=true`
- `source_master_modified=false`
- `abc_abcd_modified=false`
- Technical PASS is not anatomical approval.

## Five-cycle result

The best automatic correction cycle was R5 with score `104.076`. Fragment excess fell from 17 in R1 to 9 in R5 while unresolved faces remained 0 in the BALANCED candidate.

## Final hypotheses

| Mode | Score | Mean confidence | Unresolved | Fragment excess | Sliver labels | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| SAFE | 90.555 | 0.8518 | 5.4119% | 30 | 0 | Stable macro fallback, but transition bands are too coarse in several zones. |
| BALANCED | 104.076 | 0.8493 | 0% | 9 | 0 | Current baseline. Best compromise between drawing anatomy and stable surface partition. |
| FINE | 91.629 | 0.8362 | 2.1976% | 35 | 2 | Useful as a donor for hand/foot detail, but too fragmented in shoulder/hip/knee. |

## Zone findings

BALANCED has zero unresolved faces in all 11 review zones. Highest local priority for real-rig validation remains `SHOULDER_AXILLA`, `ARM/ELBOW`, and `KNEE` because the online run uses motion proxies, not the user's real Armature.

SAFE has large unresolved bands in `SHOULDER_AXILLA` (~17.04%), `ARM` (~27.41%), `HIP_GLUTEAL` (~30.64%), and especially `KNEE` (~71.43%). SAFE hand and foot are stable because they are macro groups, not proof that fine digits are solved.

FINE has unresolved `SHOULDER_AXILLA` (~19.28%), `HIP_GLUTEAL` (~30.64%), and `KNEE` (~66.23%). `HAND` has 0% unresolved but fragment/sliver counts of 6/4, so detailed finger labels should be selectively transferred into BALANCED rather than adopting the entire FINE model. FINE `FOOT` is stable in the current proxy test and is a good detail donor candidate.

## Motion interpretation

`SHOULDER_RAISE` and `ELBOW_BEND` produce extreme maximum stretch/collapse values (~63.9x and ~59.85x). Visual review confirms fan/diamond-like proxy deformation. These values are treated as **proxy limitations** until the local Armature repeats the same poses. Do not prematurely classify them as weight-paint failure.

BALANCED `ANKLE_TOE` is very stable (`bad_edge_pct ~0.0075%`), and FINE reaches 0% in the current proxy. BALANCED knee bend has only a small number of severe edges but must still be checked for ring-cut behavior in the real rig.

## Local Blender transfer order

1. Copy `BP3D_BALANCED_FINAL_R5.glb` / face-ID data into a new `EDITABLE_WORK` generation.
2. Re-run real Armature `SHOULDER_RAISE` and `ELBOW_FLEX` first; separate WEIGHT problems from RESPLIT problems.
3. Preserve SAFE unresolved bands as alternative masks around shoulder/axilla, inguinal/hip, and knee.
4. Selectively transplant FINE hand/finger and foot/toe candidates into BALANCED only after connectivity/sliver QA.
5. Create two derivative Special Suit copies: HUMAN_REVIEW (thick boundaries + large color fields) and MACHINE_ID (part-ID colors + thin boundary + explicit unresolved color). Never overwrite the source texture.

## Base44 ingestion

The auxiliary integration populates `BP3DZoneReviewRun` (33 records = 3 modes × 11 zones), `BP3DMotionBreakFinding` (30 records), and `BP3DArtifactRef`. The Zone Segmentation Tutor now filters by SAFE/BALANCED/FINE and can locally load the three GLBs into a Three.js comparison viewer with fixed camera views and Zone highlighting based on material/part names.

## Current transport limitation

The Base44 sandbox cannot directly fetch the authenticated GitHub Actions ZIP: unauthenticated GitHub artifact access returns 401, and a connector-issued temporary download URL returned 403 from the sandbox. The supported fallback is Drive archival + metadata URLs + local GLB upload in the Three.js viewer until a Base44 Google Drive/GitHub OAuth connector is authorized.
