# BP3D Cloud Smoke Runner

This directory contains only synthetic test code for validating headless Blender execution in GitHub Actions.

Safety constraints:
- Do not add user `.blend` files here.
- Do not add recovered BP3D ZIPs, textbook scans/images, credentials, tokens, or personal data.
- Smoke tests must generate geometry procedurally inside Blender.
- The first stage is intentionally small: one Blender job, no large matrix.

Target runtime:
- Blender 4.2.23
- `--factory-startup --background`
- synthetic mesh creation only
- JSON result + log artifact

The real BP3D model pipeline must not be moved into this public repository until a separate safe asset-transfer design is approved.
