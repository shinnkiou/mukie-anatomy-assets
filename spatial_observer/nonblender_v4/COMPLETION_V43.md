# BP3D Evidence + Practical Split Audit v4.3 — 2026-09-02

Status: **PASS_WITH_REFINEMENT_GAPS**

Canonical geometry/ownership remains unchanged. All 13,378 source Faces are assigned exactly once in the canonical Detail partition, with no missing or duplicate Face IDs.

## Separate the meanings of completion

- Canonical Face coverage: **100%**.
- HYPOTHESIS-free Detail labels: **52/56 = 92.9%**.
- Existing area-weighted project evidence confidence: **78.55%**.
- Visible textbook 1:1 detailed split coverage: **28/39 = 71.8%**.
- Visible textbook exact + group/context representation: **33/39 = 84.6%**.

These are project audit metrics, not clinical diagnostic probabilities.

## Practical output

- 112 left/right Detail OBJ files.
- 128 single-connected-shell OBJ files.
- 246 OBJ files import-readiness checked in total including review candidates.
- 0 invalid index files.
- UV corner data preserved.
- 127 Detail adjacency pairs graph-colored with five colors and zero touching same-color conflicts.

## New textbook-driven review gaps

Independent surface refinement is still missing/simplified for serratus anterior, sartorius, pectineus, leg extensor digitorum longus, extensor hallucis longus and fibularis/peroneal structures. Six conservative noncanonical candidate overlays were generated where defensible; EHL and deep rotator-cuff/teres-major skin splits were deliberately not forced.

## Head

Frontalis/corrugator, masseter, nasalis/levator complex and temporalis retain HYPOTHESIS status. Medical references support the regional anatomy but not the exact current Face boundaries. The current temporalis selection is specifically downgraded in interpretation to **SEED_ONLY_NOT_FULL_EXTENT**.

## Blender

Blender is optional for semantic completion. For practical Blender 4.2 use, import the 112 side objects and use Collections/View Layers for isolation. Four shared evidence materials read per-object custom color through the Shader Attribute node. Display helper supports ADJACENCY, EVIDENCE and CONFIDENCE modes.

## Canonical package

- Drive ID: `1GM3kIz6ySOTgMIn3Jy_z8z7BayuD0rA-`
- SHA-256: `e5298195cf7ad59f61d038b0577bc4134e83a8a68fa5d32cbec7cde37a083669`
- Drive raw readback: PASS
- ZIP CRC: PASS

Source writes remain MASTER=0, R7=0, Production14=0. Production13 remains permanently forbidden.
