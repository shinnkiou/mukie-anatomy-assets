# BP3D Visual Transfer Durable Sync — 2026-09-02

Status: `DURABLE_SYNC_MAINLINE_RECORD`

This record synchronizes the durable artifacts that were recovered or generated after the earlier Work run stopped. It does **not** modify canonical Face ownership.

## Immutable guards
- anatomical front = `NEGATIVE_Y`
- pre-V45 rollback = `FORBIDDEN`
- MASTER write = 0
- R7 write = 0
- Production14 = `HOLD`
- Production13 = `FORBIDDEN`
- canonical Face assignment change by visual layer = 0
- external-author pixels remain disabled unless rights are VERIFIED

## Arm durable geometry best
Run: `ARM_TRANSFER_DURABLE_REGEN_20260902T052130Z`

- external-pixel-free shape-aware row-wise warp
- hit rate: `0.9869281045751634`
- overflow: `0.013071895424836602`
- geometry score: `0.898139331790019`
- old geometry score: `0.8045`
- Drive ZIP: `1IcFuyrEbmE9xG_KatW0QsWgzpbGe-3Ue`
- SHA-256: `8a66b899b4d9bd5b364e0d35ea96e201a2f3a5d348b439521756d81be41fc2c1`
- Drive exact-byte readback: PASS

Historical RUN_0002 remains separately preserved for audit only because its source artwork pixels are rights-gated.

## Arm 3-view fusion
Run: `ARM_3VIEW_FUSION_20260902T054013Z`

Required views: FRONT + FRONT_OBLIQUE_30 + RADIAL.

- source Faces: 1,002
- CONFIRMED by >=2-view unanimity: 394
- UNKNOWN: 608
  - insufficient views: 562
  - source unresolved: 46
- conflicts: 0
- texture bake: 0
- canonical Face assignment change: 0
- Drive folder: `1VvBmE1NNuiedB1p7-Qdw3uQSHEey0bTD`
- Drive ZIP: `1zMvy8-5JzQBDFrqlTISG_xn_Euw8CzW4`
- SHA-256: `d51b054e4ef5b110346f323a5d370f88a3ba74ef838f36cec9d2485ba6dc6772`
- Drive exact-byte readback: PASS

## Leg durable geometry baseline
Run: `LEG02_RUN_0001_20260902_1250JST`

- score: `0.9680600700192865`
- Face coverage: `0.9980582524271845`
- surface coverage: `0.9995184731381808`
- >=2-view Face fraction: `0.9145631067961165`
- >=2-view area fraction: `0.916740084602283`
- original unseen Faces: 922, 951
- Drive ZIP: `12_LyXGhHTiNSVs6cLByW1AZJ1M8iU7_2`
- SHA-256: `2304674999b7a6b8f4c69b536a08052ccf67d8c55d07ee991447b28cd94cdf7a`
- Drive exact-byte readback + ZIP CRC: PASS

Adaptive recovery:
- accepted durable view: `POSTERIOR_MEDIAL_LOW_30` (RUN_0003)
- later minimal-view re-eval: `POSTERIOR_MEDIAL_LOW_15` also recovered Faces 922/951, but raw artifact was not yet durable-saved at that point; it must not replace RUN_0001 or RUN_0003 solely from text metrics.

## Foot / Lower-leg V01.1 durable candidate
Run: `FOOT_LOWERLEG_V011_20260902_2348JST`

This is a display-field cleanup derived from V01 / Final-v3 / V45. No re-segmentation.

- selected Faces: 2,378
- selected vertices: 2,404
- non-boundary dark pixels (<80): 64,406 -> 223
- dark-pixel reduction: 99.6538%
- nearest intended-palette mean RGB error: 58.699 -> 19.664
- palette-error reduction: 66.4997%
- outside probability removed from internal RGB black mixing
- high-confidence transitions winner-sharpened
- muscle-to-ankle display/relief decay added
- ANKLE / FOOT_DORSUM / FOOT_PLANTAR / HEEL / HALLUX / TOES remain near-flat geography
- black boundary remains continuous-probability ridge, not Face-edge snap
- external-author pixel transfer: 0
- canonical Face assignment change: 0
- status: `DURABLE_CANDIDATE_QA_PASS_NOT_FINAL_PROMOTED`
- Drive folder: `1j6YuR8VUxplrpHGIF5_R_KAL-uqFapdo`
- Drive ZIP: `1G_6Q0Lm7ismhnZq-i6QZbGLW8jvOmITd`
- ZIP size: 2,794,638 bytes
- SHA-256: `c1d962e6a32bbc52e564fdf962bc6a6dd6fa3682565a0406879d916afacd41c7`
- Drive exact-byte readback + ZIP CRC: PASS

## Current schedule / next action
- 2026-09-02–05: Foot/Lower-leg V01.1 QA + Arm visual QA
- 2026-09-06–11: Foot/Lower-leg durable visual best + Arm final QA
- 2026-09-12–18: thigh -> pelvis -> torso visual layer
- 2026-09-19–24: H1–H5 / poses / closeups / output
- 2026-09-25–29: submission freeze / QA
- 2026-09-30: internal deadline; no large algorithm changes

Next execution should prioritize finishing the V01.1 same-view anatomy/readability review and turning it into the lower-leg deadline visual best only if the comparison remains visibly better. Do not restart segmentation.