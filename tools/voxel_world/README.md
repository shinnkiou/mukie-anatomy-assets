# Voxel World Foundation

Purpose: convert CC0/public-domain voxel or Minecraft-style schematic structures into a license-tracked normalized block plan, preview them in Three.js, and later translate exterior block plans into realistic modular architecture.

## Core rules
- Building exterior pipeline only for block-to-real conversion. Do not reuse the voxel/block method for detailed interiors or human anatomy.
- Dynamic entities/mobs are excluded by design.
- Geometry ID and material variant are separate. Do not duplicate identical geometry only because texture/material differs.
- Preserve source URL, license declaration, author/provider, input format, source SHA-256 and conversion history.
- Planet Minecraft is NOT treated as site-wide CC0. Only individual pages with explicit public-domain declarations may be imported as public-domain sources, and the page must be re-checked before production reuse.
- Do not redistribute Mojang textures/models. Use CC0 replacement materials or project-owned materials.
- Exterior walls use an opaque `BASE_WALL` fallback. Do not stack a second co-planar wall only to apply a texture/material.
- Pipeline: source/license check -> schematic parse -> normalized JSON -> deterministic data/structure QA -> virtual-world preview -> reusable exterior modules -> closed exterior skin -> continuous-surface refinement -> lighting -> visual QA.
- Final deliverables require at least 3 visual QA/review passes: structure, material/texture, visual/detail. High-quality building work may use up to 10 correction rounds.

## Canonical normalized format
```json
{
  "schema":"voxel-world-normalized-v1",
  "title":"...",
  "size":{"x":12,"y":8,"z":5},
  "blocks":[{
    "x":0,"y":0,"z":0,
    "role":"WALL",
    "material":"brick",
    "source_block":"minecraft:bricks"
  }],
  "metadata":{
    "source_url":"...",
    "license":"CC0-1.0",
    "dynamic_entities":false,
    "ignored_entities":true
  }
}
```

## Supported binary inputs
`normalize_schematic.py` currently supports:
- Sponge `.schem` v2/v3
- legacy MCEdit `.schematic` (geometry preserved; legacy numeric IDs are explicitly flagged for later mapping)
- Litematica `.litematic`, including packed `BlockStates`, signed region sizes and multiple regions

Entities/mobs are ignored intentionally. Source block-state strings remain in normalized JSON for traceability.

### Usage
```bash
python3 -m pip install -r tools/voxel_world/requirements.txt
python3 tools/voxel_world/normalize_schematic.py input.litematic \
  --out normalized.json \
  --source-url https://example.invalid/source \
  --license CC0-1.0
python3 tools/voxel_world/validate_normalized.py normalized.json --out qa.json
```

## Deterministic QA
`validate_normalized.py` checks the machine-verifiable preflight before Three.js/Blender work:
- schema/dimensions
- integer coordinates
- duplicate occupied cells
- out-of-bounds blocks
- AIR leakage
- missing role/material/source trace
- transparent material on structural cells
- dynamic-entity exclusion
- license/source provenance warnings
- exposed-face and boundary-occupancy metrics

A deterministic QA PASS does **not** replace the required three visual review passes after realistic exterior conversion.

## Real binary regression
`REAL_INPUT_REGRESSION_20260830.json` records real CC0 Litematica regression fixtures from `Greaby/minecraft-circles-schematics` (CC0-1.0):
- `circle-1x1.litematic`: 1 block, QA PASS
- `circle-10x10.litematic`: 24 blocks, QA PASS
- `circle-20x20.litematic`: 52 blocks, QA PASS

These files are parser fixtures, not production building assets. They prove that the Litematica adapter is no longer only a synthetic-NBT test.

## Base44
Creative Ops Lab `/voxel-world-lab` now includes:
- CC0/public-domain source registry
- reusable static Block/Object Library
- normalized JSON import/export
- Three.js block preview
- real-input regression records
- data/structure QA
- opaque `BASE_WALL` material fallback
- realistic exterior mode with an all-side exposed-structural-face skin prepass rather than a front-only facade skin

The exterior skin prepass is still a structural base. Continuous merged surfaces, high-quality PBR materials, detail assets and lighting remain separate later passes.

## Current next validation target
The next important step is a real **building** `.schem`/`.litematic` under a license that permits this workflow. Public-domain Planet Minecraft pages are catalogued, but the provider download endpoint was not directly retrievable in the 2026-08-30 run. The pipeline therefore switched to a verified-CC0 GitHub binary fixture instead of stopping. Do not label the parser as building-proven until an actual building binary passes normalize -> QA -> Three.js preview -> realistic exterior review.
