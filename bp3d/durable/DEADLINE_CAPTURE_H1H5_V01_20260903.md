# BP3D Deadline Capture H1–H5 V0.1 — Durable Record

Status: `DURABLE_H1H5_CAPTURE_SIDECAR_READBACK_PASS`

- Drive ZIP: `15LpdSuVxeWPn0_mlJCiAYH5pEv5ehIy-`
- SHA sidecar: `1QHLvw3_MLHErAR3uAgZxj2-O2JAiF0kt`
- Blender Python: `1EkNf0oK22mQx_FtNDzFoud7FCEjr18rD`
- ZIP size: 5,019 bytes
- SHA-256: `bd1df815d515400f68de9866421cf4519a5ac59901a88525aa48bf30eec8fd95`
- Drive exact-byte readback: PASS
- ZIP CRC: PASS
- Python syntax: PASS

## Capture geometry

The existing graduation-project 26-view pattern is preserved without inventing unsupported numeric H-elevation angles.

- H1: lower pole ×1
- H2: lower ring ×8 at 45° azimuth steps
- H3: horizontal/middle ring ×8
- H4: upper ring ×8 at 45° azimuth steps
- H5: upper pole ×1
- total: 26 views
- anatomical front: `NEGATIVE_Y`

H2/H4 use `R/sqrt(2)` horizontal radius and vertical offset. H1/H5 use poles. The sidecar renders from Graduation Deadline Build V0.2 and does not mutate canonical/source geometry.

## Source guards

- MASTER writes: 0
- R7 writes: 0
- Production13: FORBIDDEN
- Production14: HOLD
- pre-V45 rollback: FORBIDDEN
- semantic mutation: 0
- source mesh mutation: 0

This remains part of Draft PR #8 until the V0.2 real-Blender QA gate passes.
