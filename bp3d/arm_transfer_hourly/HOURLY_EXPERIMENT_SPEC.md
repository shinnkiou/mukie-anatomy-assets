# BP3D Hourly Arm Transfer Experiment

Status: active scheduled experiment specification.

## Reference canon
- Drive folder: `1pJwsreBKCY1ptW3Ull8luM2TmmAZh98J`
- ZIP: `1ehbeZKb-3JBRelJH7x8KKrUl2UUx9oDZ`
- Manifest: `1MV2b_M1bRfPNwP9C7V0fkSemGW7hy-Yt`
- Target scope: right arm first — shoulder/deltoid + upper arm + forearm.

## Per-run loop
1. Load the previous best derived arm-only build and reference manifest.
2. Hide every body region except the target arm.
3. Align orthographic cameras by shoulder, elbow, wrist, and arm-axis landmarks.
4. Build/project a dense semantic transfer cage from the reference image.
5. Move cage points camera-forward until first surface hit; reject grazing, back-side, or visibility-invalid hits.
6. Fuse FRONT, FRONT_OBLIQUE_30, RADIAL, BACK_OBLIQUE_30, BACK, ULNAR, FRONT_HIGH_15, BACK_HIGH_15 observations using confidence-weighted voting.
7. Render all views with black internal muscle boundaries only.
8. Measure overflow, contradictory labels, side leakage, boundary discontinuity, silhouette/reference mismatch, and view-to-view disagreement.
9. Accept only if the objective score improves without a safety regression. Otherwise rollback to the previous best.
10. Save run metrics, screenshots, error notes, and artifact references.

## Guards
- Face ownership is a coarse address, not final visual border.
- MASTER writes: 0.
- R7 writes: 0.
- Production14 writes: 0 / HOLD.
- Production13: forbidden.
- One bounded iteration per hourly automation run; recurrence provides indefinite experimentation until the task is disabled.
