# CSMC VBO WRITER PROBE V1.6.2 — VALIDATED PLATEAU

## Purpose

V1.6.1 captured a formally complete CHANGED snapshot, but it was not physically plausible:

- changed position vertices: 35,933 / 36,254
- selected displacement: ~4.0e38

V1.6.2 therefore does **not** accept a candidate only because its upload size is 1,160,128 bytes.

## Validation

Each cached upload candidate is checked as stride-32:

- Position float3 @ 0
- Normal float3 @ 12
- UV float2 @ 24
- 36,254 vertices
- all floats must be finite
- absurd Position / Normal / UV magnitudes are rejected
- BASELINE prefers a repeated hash plateau
- CHANGED must have exactly the same UV SHA-256 as BASELINE
- CHANGED must alter 100..30,000 position vertices
- max position displacement must be <= 10,000
- repeated CHANGED hashes are preferred over one-off transition buffers

The changed-vertex monitor watches up to 8 distinct 4 KiB pages rather than a single vertex.

## Safety

This package:

- does not use Base44
- does not save or overwrite CSMC
- does not press Ctrl+S
- does not touch key/decryption routines
- does not install or remove OpenGL wrappers
- requires MODELER to be closed before launch
- aborts if a local opengl32.dll still exists beside MODELER
- keeps semantic_promotion=false

## Run order

1. Close CLIP STUDIO MODELER completely.
2. Run `00_RUN_VBO_WRITER_PROBE_V1_6_2.bat`.
3. MODELER starts automatically.
4. Open `POSE_00_BASE_TPOSE.csmc`.
5. Wait for T-pose to fully render, then wait about 3 seconds.
6. Return to console and press Enter for BASELINE validation.
7. Bend only the left elbow clearly.
8. Wait about 3 seconds.
9. Return to console and press Enter for CHANGED validation.
10. If CHANGED is accepted, keep the elbow bent.
11. At Round 1, press Enter first to ARM the writer watch.
12. Only after ARMED, return to MODELER and move the elbow toward T-pose.
13. Wait 2–3 seconds, return to console, press Enter.
14. Repeat controlled rounds if requested.
15. Send the generated `CSMC_VBO_WRITER_VALIDATED_*_SEND.zip`.

## Output

- SUMMARY.txt
- CANDIDATE_VALIDATION.tsv
- BASELINE_BODY.bin
- CHANGED_BODY.bin
- CHANGED_VERTICES.tsv
- UPLOADS.tsv
- WRITER_ACCESSES.tsv
- POINTER_REUSE.tsv
- EVENTS.jsonl
