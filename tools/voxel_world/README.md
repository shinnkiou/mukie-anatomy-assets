# Voxel World Foundation

Purpose: convert CC0/public-domain voxel or Minecraft-style schematic structures into a license-tracked normalized block plan, preview them in Three.js, and later translate exterior block plans into realistic modular architecture.

## Core rules
- Building exterior pipeline only for block-to-real conversion. Do not reuse the voxel/block method for detailed interiors or human anatomy.
- Dynamic entities/mobs are excluded by design.
- Geometry ID and material variant are separate. Do not duplicate identical geometry only because texture/material differs.
- Preserve source URL, license declaration, author/provider, input format and conversion history.
- Planet Minecraft is NOT treated as site-wide CC0. Only individual pages with explicit public-domain declarations may be imported as public-domain sources.
- Do not redistribute Mojang textures/models. Use CC0 replacement materials or project-owned materials.
- Pipeline: source/license check -> schematic parse -> normalized JSON -> virtual-world preview -> reusable exterior modules -> continuous-surface refinement -> lighting -> QA.
- Final deliverables require at least 3 QA/review passes: structure, material/texture, visual/detail.

## Canonical normalized format
```json
{
  "schema":"voxel-world-normalized-v1",
  "title":"...",
  "size":{"x":12,"y":8,"z":5},
  "blocks":[{"x":0,"y":0,"z":0,"role":"WALL","material":"brick","source_block":"minecraft:bricks"}],
  "metadata":{"source_url":"...","license":"...","dynamic_entities":false}
}
```

## Base44
Creative Ops Lab includes `/voxel-world-lab`: source registry, normalized JSON import/export, Three.js block preview, and a first realistic-exterior base mode.

## Converter
`scripts/normalize_schematic.py` is designed for Sponge `.schem` v2/v3 and legacy `.schematic`. It intentionally ignores entities and keeps source block-state strings for traceability.
