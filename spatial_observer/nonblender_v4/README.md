# BP3D Non-Blender Observer v4 — 2026-09-01

Final v3 was independently observed without Blender by reading the derived OBJ / Face-ID / UV / cut-guide data directly.

## Result

- Validation: **PASS**
- Faces: 13,378 / 13,378
- Production labels: 41
- Detail labels: 56
- Closed 2-manifold: V=13,380 / E=26,756 / F=13,378 / Euler chi=2 / genus=0
- Open edges: 0
- Non-manifold edges: 0
- Production cut boundary edges: 2,108
- Ordered world cut toolpaths: 186 paths covering all 2,108 segments
- UV-seam production boundary edges: 76
- Mirror audit: missing 0 / Production mismatch 0 / Detail mismatch 0
- 42-direction surface-normal observation proxy: all Production faces observable
- Diagnostic output: 12 whole-body views + 7 high-risk region closeups + Production/Detail UV atlases + cut overlay

## Observer repair

The initial centroid mirror checker produced false missing reports because of decimal rounding boundaries (16 faces, then 4 faces on retry). Those observer-only errors were preserved. The final checker uses cKDTree nearest mirrored-centroid lookup with a 1e-9 m tolerance; max measured mirror-centroid error is 4.449591077262561e-16 m and all label mismatches are zero.

## Safety

MASTER write = 0. R7 write = 0. Production14 write = 0. Production13 remains permanently forbidden.

## Canonical artifact

Google Drive file ID: `1FQoDVi5C9td7NuAR6ESNN82rlv6Jlsrw`

SHA-256: `ac5fd46e9e32cf086a1a51850a4a13a2de400caef600c36c9c71e727ee984aaf`

The Drive ZIP contains the reproducible non-Blender observer script, geometry/component metrics, boundary-chain metrics, ordered cut toolpaths, UV boundary segments, observation profiles, diagnostics, validation, manifests, and preserved observer error reports.
