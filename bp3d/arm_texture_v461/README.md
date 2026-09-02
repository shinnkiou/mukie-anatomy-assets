# BP3D Arm Continuous Texture v4.6.1

Status: experimental derived PASS. This does **not** rewrite V45 semantic Face ownership, MASTER, R7, or Production14.

## Why this exists
The previous split used Face ownership as a hard visual boundary. v4.6/v4.6.1 instead treats those Face labels as a coarse teacher/address layer and builds a continuous muscle field over the surface.

## Method
- V45 Face ownership -> per-vertex muscle probability field.
- Graph diffusion with exact bilateral averaging.
- 2-ring virtual support halo outside the hard arm Face boundary.
- Elbow/wrist context is weakly anchored so adjacent muscle fields can blend through rather than form blank rings.
- Fiber direction is estimated by weighted PCA per muscle and side.
- A smooth muscle-belly relief/height texture is generated from the continuous field.
- Authored Exact Special Suit `UVMap` is used for the final bilateral 4K arm texture.
- Blender application duplicates the source object before applying material/bump; the source is not modified.

## User textbook constraints used
- p132: arm structure from multiple directions.
- p133: forearm rotation / view dependence.
- p85-87: shoulder movement and front/back visibility.

## Validation
- Exact bilateral probability error: 0.0.
- Outer hard-boundary opacity jump reduced by 24.01% vs v4.6.
- Seed vertices: 2,110.
- Virtual-support vertices: 2,450.
- Support faces used for texture interpolation: 2,606.
- V45 Face labels unchanged.
- MASTER/R7/Production14 writes: 0.

## Artifact authority
Google Drive RUN artifact: `1WbAXt5fmrYA9P8_6Cg5VrvokaSpwXpGF`

SHA-256: `e8ac1dd3af82971d7efa92daa6343ff558e86c4a130da7cae7589c1ce49b042b`

The ZIP contains the directly textured derived OBJ, 4K color/relief textures, continuous vertex field, fiber-direction field, multi-view comparison images, validation, and Blender duplicate-only application script.
