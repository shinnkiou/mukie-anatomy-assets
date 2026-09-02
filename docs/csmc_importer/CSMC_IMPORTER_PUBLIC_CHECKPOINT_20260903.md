# CSMC/CS3C Importer Public-Safe Checkpoint — 2026-09-03

This checkpoint records interoperability research progress without embedding proprietary/purchased model data.

## Durable code already on branch
Branch: `csmc-importer-experimental-20260902`
- `tools/csmc_importer/csmc_core.py`
- `tools/csmc_importer/test_probe_synthetic.py`

## New verified research directions
- CLIP `.clip` is a `CSFCHUNK` container with an internal SQLite section and external chunks; a 3D model can be referenced from `Canvas3DModelLoader`, with separate CELSYS `catalog_character` and `scene` payloads.
- A read-only Windows runtime observer can attach to the real `CLIPStudioModeler.exe` and locate `CLIP_STUDIO_3D_DATA2` / character metadata and variant-name strings in readable process memory.
- The runtime process loads FBX SDK, image decoder/compression, and graphics libraries; their exact role remains under investigation.
- Long scans must report percentage/progress and explicit COMPLETE/PARTIAL status.

## Next implementation priority
1. Targeted runtime `character` blob capture with strict header/GUID validation and 0–100% progress.
2. A/B/C differential: original saved CSMC vs controlled modified saved CSMC vs runtime character blob.
3. `.clip` catalog_character vs scene differential for one-variable pose/variant experiments.
4. Continue Blender-independent core and add Blender 4.2 import UI only for decoded fields; never fabricate geometry.
5. Keep Mesh/Index and Texture recovery as parallel major milestones.

## Safety / repository rule
No purchased `.cs3c/.csmc/.clip` files, extracted mesh/texture, private captures, credentials, or proprietary payload bytes are committed to public GitHub. Only code, synthetic fixtures, hashes, and public-safe specifications belong here.
