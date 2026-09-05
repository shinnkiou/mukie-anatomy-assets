# BP3D Arm Continuous Texture v4.6.2

This pass adds black muscle-boundary guides requested for readability.

Important: the black lines are **not polygon/Face borders**. They are extracted from equality transitions in the smoothed continuous per-vertex muscle probability field, so the visual muscle contour can pass smoothly across original polygon ownership edges.

## Scope
This experiment covers the bilateral arm system: shoulder/deltoid, upper arm, and forearm. It is not forearm-only.

## Visual boundary policy
- Existing v4.6.1 continuous color/relief field retained.
- Black internal muscle boundaries: about 2.4 px core at 4K with a soft antialiased shoulder to about 4.7 px.
- Outer arm-to-context halo is not explicitly outlined.
- Relief/height is unchanged so the black line remains a readability/drawing guide, not a fake anatomical groove.
- 14 internal muscle-pair transitions are represented in the current continuous field.

## Source safety
- V45 Face ownership unchanged.
- v4.6.1 probability field unchanged.
- MASTER/R7/Production14 writes: 0.
- Production13 remains forbidden.

## Artifact authority
Google Drive RUN artifact: `1MSIgtHXNvddIkeck12iIxqCjqm_k1W7v`

SHA-256: `fe8c95734d8a2f89e44bb686b2d82bb23a6ad9fc60a4d586327fa01d1633e7a1`

The Drive ZIP contains the 4K outlined color texture, separate 4K black-boundary mask, unchanged relief map, directly textured derived OBJ/MTL, four-direction visual checks, validation, source field files, and duplicate-only Blender applicator.
