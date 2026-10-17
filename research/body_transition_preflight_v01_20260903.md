# BP3D BODY / Thigh / Pelvis / Torso Geometry Preflight V0.1 — 2026-09-03

Status: `DURABLE_GEOMETRY_PREFLIGHT_READBACK_PASS`

Foot/Lower-leg V01.1 has been promoted as the derived Deadline Visual Best, so the BODY gate is lifted. This run moves BODY/TORSO from specification-only work to actual self-derived geometry observation.

## Authority / guards
- semantic authority: Final-v3 + V45
- R5 GLB is observer geometry only; R5 zone names are **not** semantic truth
- canonical anatomical front remains `NEGATIVE_Y`
- R5 observer-export coordinate adapter notes anterior surface at `-Z`; this does not rewrite semantic axes
- canonical Face change: 0
- external-author pixels: 0
- MASTER/R7 writes: 0
- Production14: HOLD
- Production13: FORBIDDEN
- pre-V45 rollback: FORBIDDEN

## Base 8-view observation
Run: `BODY_TRANSITION_PREFLIGHT_V01_20260903`

Target envelope: shoulder/chest + abdomen + upper/lower back + pelvis + bilateral thigh transitions.

- observer nodes: 22
- vertices: 9,632
- triangle Faces: 4,816
- Face coverage: `98.4219269%`
- area coverage: `99.5799997%`
- >=2-view Face fraction: `97.2591362%`
- >=2-view area fraction: `99.0525436%`
- unseen Faces: 76
- normal gate: `|n·ray| >= 0.25`

Group area coverage:
- SHOULDER_CHEST: 98.8262%
- ABDOMEN: 100%
- UPPER_BACK: 99.8787%
- LOWER_BACK: 100%
- PELVIS: 99.0048%
- THIGH: 100%

Bilateral paired observer zones were symmetric to numerical tolerance except tiny source rounding in oblique/latissimus pairs.

Drive folder: `1BEihdHLc7LGMLqrDY77VIPnt0OhQFSXL`
Drive ZIP: `1N6tPLLc3LhY71-wiZfF6IOPhHZNd78zP`
ZIP SHA-256: `725305af2072545efc406273692e8d4d103cf86feea8d9f020d12ba2017abbda`
Drive readback: PASS
8-view montage: `1PhnzsdBV6r4PZC7dM_Yyf02AIQqdiLBn`

## Adaptive auxiliary observation
Run: `BODY_ADAPTIVE_PREFLIGHT_V01_20260903`

Useful candidates were tested without semantic changes. Greedy auxiliary set:
1. `BACK_LOW_15`
2. `BACK_HIGH_15`
3. `AXILLA_LOW_15`

After these three views:
- unseen Faces: `76 -> 18`
- Face coverage: `99.6262458%`
- area coverage: `99.9271129%`
- >=2-view Face fraction: `98.5049834%`
- >=2-view area fraction: `99.5517629%`

The remaining 18 observer Faces represent ~0.073% of target surface area; they remain observation-limited/UNKNOWN rather than being filled by semantic guesswork.

Adaptive Drive ZIP: `1qK28dVpkfZR6K6bSMDpnT9nno0myP1YJ`
Adaptive SHA-256: `219ade45e94645c38cfaa11cfb3be4ba7d76adad4f9e6fc1a7ba9e8ed58a1240`
Drive readback: PASS

## Decision
Accept the observation envelope and advance to thigh -> pelvis -> torso **derived display integration**. Do not restart segmentation and do not treat R5 observer-zone labels as canonical semantics.
