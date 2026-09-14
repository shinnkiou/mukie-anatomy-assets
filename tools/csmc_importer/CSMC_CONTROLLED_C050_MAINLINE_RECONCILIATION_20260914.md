# CSMC Mainline — Companion C C-050 Reconciliation — 2026-09-14

## Scope

Reference-only consumption of Companion C C-050. Mainline does not rerun the same all-pair controlled comparison and does not merge the Companion branch wholesale.

## Provenance

- Controlled fixture ZIP SHA-256: `be6132ef83959167ffd19218810e099f0bd164714fbd1ec4770f9296b38643b6`
- Companion C branch: `csmc-analysis-companion-c-20260913`
- Companion C verified head: `dd58c29c504c54f00e3d2506204b8097d5b5aef9`
- C-050 result path: `tools/csmc_importer/companion_c/CSMC_ANALYSIS_C_RUN050_CONTROLLED_FIXTURE_RESULT_20260914.json`
- C-050 report path: `tools/csmc_importer/companion_c/CSMC_ANALYSIS_C_RUN050_CONTROLLED_FIXTURE_REPORT_20260914.md`
- Raw/private fixture bytes published by C-050: false

## Accepted reference facts

1. DATA2 framing independently agrees with mainline intake: offset 57 logical length, offset 61 stored/framed length, body at 65, `stored = align8(logical)+8` for all 13 fixtures.
2. A recurring 2456-byte / 307-qword cadence is reported in the controlled corpus.
3. Observed cadence count matches `2 + render-part count` in all 13 fixtures:
   - one-part geometry/rig fixtures: cadence 3;
   - F06 two material partitions: cadence 4;
   - F07 two mesh objects: cadence 4;
   - VRoid teacher: 8 material/render parts -> cadence 10.
4. Geometry complexity, UV edit and rig/weight changes do not alter cadence count in their corresponding controls.
5. This is accepted as `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE`, confidence Level 4 under the mainline ladder: controlled relationship + negative controls + independent VRoid consistency.

## Not accepted / not promoted

- No direct material field binding is confirmed.
- No vertex/index/UV/bone/weight field is confirmed.
- `render_part_cardinality` is not Level 5 because owner/consumer binding and stricter same-identity controls are still absent.
- No Blender emit gate is changed.
- No runtime/MODELER/Worker policy is changed.

## Mainline effect

- Structural IR v0.1 meanings remain unchanged.
- Controlled-evidence sidecar may attach the Level-4 render-part-cardinality candidate.
- Importer work may parse and expose the outer envelope immediately.
- Content-semantic emit remains blocked.
- Semantic promotion count remains 0.
