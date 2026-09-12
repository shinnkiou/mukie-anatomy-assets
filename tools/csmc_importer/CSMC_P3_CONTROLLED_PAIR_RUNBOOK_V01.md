# CSMC P3 controlled one-variable pair runbook v0.1

Status: `READY_FOR_PRIVATE_TARGET_EXECUTION`

Purpose: generate reproducible teacher pairs that isolate one semantic change at a time before any new broad x64dbg/decompiler search. Purchased model bytes stay private; GitHub stores only tools, manifests, hashes, and public-safe reports.

## Core sequence per experiment

Use four saves whenever practical:

`A0 baseline -> C0 no-change control -> B0 one-variable change -> R0 return to baseline`

Compare:

- `A0 vs C0`: serialization/noise control
- `C0 vs B0`: intended semantic change
- `A0 vs R0`: reversibility check

If the control pair changes broadly, do not interpret the variable pair yet. If the return pair does not semantically return, treat the run as contaminated until the cause is understood.

## Planned experiments

| ID | Only intended change | Primary question | Hypothesis only — not acceptance truth |
|---|---|---|---|
| P3-CONTROL-001 | Save again with no intentional change | How much deterministic/noise drift exists? | Scene/model should be mostly or exactly stable |
| P3-CAMERA-001 | Change one camera angle or camera position only | Which SQL/scene surfaces carry camera state? | Character catalog should stay unchanged; scene/camera state should change |
| P3-BONE-001 | Rotate one known bone by one controlled amount/axis only | Where does pose state live? | Scene is the first candidate; `NodeRotationR/VXYZ` is only a semantic map until proven |
| P3-TRANS-001 | Translate the character/root in one axis only | Where does placement transform live? | Scene/transform state should change without geometry identity change |
| P3-VARIANT-001 | `パーツ分け小` -> `筋肉脂肪` only | Does body variant alter catalog character, scene, or both? | Unknown; record rather than assume |
| P3-MATERIAL-001 | On a self-authored known fixture, change one material or one known texture only | Which payload region carries material/texture state? | Use a synthetic teacher model if the purchased target does not expose editable texture children |

## Required capture fields

Every save must record:

- experiment id and stage (`A0`, `C0`, `B0`, `R0`)
- source file name and SHA-256
- output `.clip` file name, size, SHA-256
- exact one-variable operation performed
- application/version and relevant target variant/pose state
- `Canvas3DModelLoader.ModelData` external ref + payload metadata
- `Manager3DOd.SceneData` external ref + payload metadata
- `ModelData3D.Layer3DModelData` and `Canvas3DModelBank.BankData` liveness classification
- schema-only vs table-empty vs live-row status for focus 3D tables
- `clip_3d_diff.py` result
- Evidence Probe v0.2 result
- contamination verdict and next action

## Diff acceptance rules

A run is interpretable only when all applicable controls pass:

1. identity routing still points to the intended character;
2. unrelated Canvas / CanvasItem / LayerObject / CharacterInfo controls remain stable unless the operation logically requires a change;
3. camera controls stay stable for non-camera experiments;
4. no-change control drift is measured before variable-specific differences are interpreted;
5. repeated identical semantic changes should show a stable structural pattern even if exact bytes are not identical;
6. a change is not called vertex/index/bone/weight/UV/material evidence until an independently known input value correlates with a concrete decoded field, buffer, or reproducible differential pattern.

## Private artifact naming

Recommended private Drive names:

- `P3_<TYPE>_<NNN>_A0.clip`
- `P3_<TYPE>_<NNN>_C0.clip`
- `P3_<TYPE>_<NNN>_B0.clip`
- `P3_<TYPE>_<NNN>_R0.clip`
- `P3_<TYPE>_<NNN>_REPORT.json`
- `P3_<TYPE>_<NNN>_DIFF.json`

Do not upload purchased `.clip`, CSMC, extracted model data, or private runtime captures to the public GitHub repository.

## Decision logic

- If camera-only changes isolate to scene/control fields: use those fields as a validated scene serializer anchor.
- If one-bone rotation produces a repeatable scene-only delta with controls invariant: test candidate numeric families against the known rotation amount.
- If the variant changes catalog-character but not scene: prioritize character-payload differential work for variants.
- If the variant changes scene only: prioritize scene serializer semantics.
- If a self-authored material/texture teacher pair yields an image/material boundary before mesh is decoded, integrate that result immediately; mesh and texture remain parallel breakthrough tracks.
- If all file-side pairs remain opaque after controlled repetition, return to static/runtime tracing with the exact changed payload and operation as the search anchor rather than a generic MODELER scan.

## Gate to P4

Move P4 static/runtime tracing back to the mainline only after at least one P3 pair produces a repeatable, contamination-controlled semantic delta, or after the fresh P1/P2 target scan proves there is no additional useful file-side route to exploit.
