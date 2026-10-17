# BP3D Foot / Lower-leg V01.1 Deadline Visual Best Promotion — 2026-09-03

Status: `PROMOTED_AS_DERIVED_DEADLINE_VISUAL_BEST`

This is a **display-layer promotion only**. Final-v3/V45 remain semantic authority and canonical Face ownership is unchanged.

## Guards
- anatomical front = `NEGATIVE_Y` in canonical authority
- pre-V45 rollback = forbidden
- MASTER/R7 writes = 0
- Production14 = HOLD
- Production13 = FORBIDDEN
- external-author pixel transfer = 0
- old R6 FINE FOOT re-segmentation = forbidden

## V01.1 durable artifact
- run: `FOOT_LOWERLEG_V011_20260902_2348JST`
- Drive folder: `1j6YuR8VUxplrpHGIF5_R_KAL-uqFapdo`
- Drive ZIP: `1G_6Q0Lm7ismhnZq-i6QZbGLW8jvOmITd`
- ZIP SHA-256: `c1d962e6a32bbc52e564fdf962bc6a6dd6fa3682565a0406879d916afacd41c7`
- ZIP size: 2,794,638 bytes
- Drive exact-byte readback + ZIP CRC: PASS

## Same-view actual texture QA
V01 and V01.1 were rendered from the actual OBJ+UV+4K textures in the same eight software-rasterized observation views.

- non-boundary dark pixels <80: `64,406 -> 223` (99.65% reduction)
- nearest intended-palette mean RGB error: `58.699 -> 19.664` (66.50% reduction)
- muddy lower-leg center band is materially reduced
- shin-to-ankle display readability is materially improved
- residual foot/tendon simplification remains explicitly display-only / non-semantic

Actual comparison:
- Drive ID: `10136_YTKuBEm7s8fViS4paKw0zscFh41`
- SHA-256: `d2f8ebd993ee9890f61ecc1414488e6d9dfd171756ccaf8e71af3270f5c59fe1`

Promotion record:
- Drive ID: `16-HlsXKlT09lG75yJjeq7I1duLKOaze4`
- Supabase run: `FOOT_LOWERLEG_V011_ACTUAL_8VIEW_PROMOTION_20260903`

## Decision
Accept V01.1 as the current Foot/Lower-leg **Deadline Visual Best** and freeze further lower-leg algorithm branching unless a concrete Blender rendering blocker appears.

Next mainline: thigh -> pelvis -> torso visual layer / BODY observation contract.
