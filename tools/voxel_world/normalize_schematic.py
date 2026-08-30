#!/usr/bin/env python3
"""Normalize Sponge .schem (v2/v3) or legacy .schematic into voxel-world-normalized-v1 JSON.

Design contract:
- Preserve only static block geometry. Entities/mobs are intentionally ignored.
- Keep source block-state string for traceability.
- Classify blocks into reusable geometry roles; material variants stay separate from geometry IDs.
- Output is deterministic JSON consumed by Base44 Voxel World Foundation.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

try:
    import nbtlib
except ImportError as e:
    raise SystemExit("Missing dependency: nbtlib. Install with: python3 -m pip install nbtlib") from e

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}


def role_for(state: str) -> tuple[str, str]:
    s = state.lower()
    base = s.split("[", 1)[0]
    if base in AIR:
        return "AIR", "air"
    if "glass" in base:
        return "WINDOW", "glass"
    if "door" in base or "trapdoor" in base:
        return "DOOR", "wood" if any(x in base for x in ["oak", "spruce", "birch", "jungle", "acacia", "mangrove", "cherry", "bamboo"]) else "metal"
    if "stairs" in base:
        return "STAIR", "stone" if any(x in base for x in ["stone", "brick", "deepslate", "quartz", "sandstone"]) else "wood"
    if "slab" in base:
        return "TRIM", "stone" if any(x in base for x in ["stone", "brick", "deepslate", "quartz", "sandstone"]) else "wood"
    if any(x in base for x in ["fence", "wall"]):
        return "RAILING", "stone" if "wall" in base and not any(x in base for x in ["wood", "oak", "spruce"]) else "wood"
    if any(x in base for x in ["log", "wood", "planks", "bamboo_block"]):
        return "WALL_WOOD", "wood"
    if any(x in base for x in ["bricks", "brick", "terracotta"]):
        return "WALL_BRICK", "brick"
    if any(x in base for x in ["iron", "copper", "chain", "anvil"]):
        return "WALL", "metal"
    if any(x in base for x in ["stone", "cobblestone", "deepslate", "andesite", "diorite", "granite", "quartz", "sandstone", "concrete"]):
        return "WALL", "stone"
    if any(x in base for x in ["sign", "banner"]):
        return "SIGN", "wood"
    if any(x in base for x in ["lantern", "torch", "light"]):
        return "LIGHT", "metal"
    return "WALL", "plaster"


def decode_varints(raw) -> list[int]:
    data = [int(x) & 0xFF for x in raw]
    out, value, shift = [], 0, 0
    for b in data:
        value |= (b & 0x7F) << shift
        if b & 0x80:
            shift += 7
            if shift > 35:
                raise ValueError("Invalid varint stream")
        else:
            out.append(value)
            value, shift = 0, 0
    if shift:
        raise ValueError("Truncated varint stream")
    return out


def unwrap_root(doc):
    root = doc.root if hasattr(doc, "root") else doc
    return root["Schematic"] if "Schematic" in root else root


def parse_sponge(root, source_name: str):
    width, height, length = int(root["Width"]), int(root["Height"]), int(root["Length"])
    version = int(root.get("Version", 2))
    blocks_container = root.get("Blocks") if version >= 3 and "Blocks" in root else root
    palette = blocks_container.get("Palette") or blocks_container.get("BlockPalette") or root.get("Palette") or root.get("BlockPalette")
    data = blocks_container.get("Data") or root.get("BlockData")
    if palette is None or data is None:
        raise ValueError("Sponge palette/data not found")
    palette_map = {str(k): int(v) for k, v in palette.items()}
    reverse = {v: k for k, v in palette_map.items()}
    ids = decode_varints(data)
    expected = width * height * length
    if len(ids) != expected:
        raise ValueError(f"Block data length mismatch: {len(ids)} != {expected}")
    blocks, role_counts = [], {}
    for idx, palette_id in enumerate(ids):
        state = reverse.get(palette_id, f"unknown:{palette_id}")
        role, material = role_for(state)
        if role == "AIR":
            continue
        x = idx % width
        z = (idx // width) % length
        y = idx // (width * length)
        blocks.append({"x": x, "y": y, "z": z, "role": role, "material": material, "source_block": state})
        role_counts[role] = role_counts.get(role, 0) + 1
    return {
        "schema": "voxel-world-normalized-v1",
        "title": source_name,
        "size": {"x": width, "y": height, "z": length},
        "blocks": blocks,
        "metadata": {"input_format": f"sponge_v{version}", "source_file": source_name, "dynamic_entities": False, "ignored_entities": True, "palette_size": len(palette_map), "role_counts": role_counts},
    }


def parse_legacy(root, source_name: str):
    width, height, length = int(root["Width"]), int(root["Height"]), int(root["Length"])
    raw = [int(x) & 0xFF for x in root["Blocks"]]
    expected = width * height * length
    if len(raw) != expected:
        raise ValueError(f"Legacy Blocks length mismatch: {len(raw)} != {expected}")
    blocks = []
    for idx, block_id in enumerate(raw):
        if block_id == 0:
            continue
        x = idx % width
        z = (idx // width) % length
        y = idx // (width * length)
        blocks.append({"x": x, "y": y, "z": z, "role": "WALL", "material": "stone", "source_block": f"legacy_id:{block_id}"})
    return {"schema": "voxel-world-normalized-v1", "title": source_name, "size": {"x": width, "y": height, "z": length}, "blocks": blocks, "metadata": {"input_format": "legacy_schematic", "source_file": source_name, "dynamic_entities": False, "ignored_entities": True, "legacy_id_mapping_required": True}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    src, out = Path(args.input), Path(args.out)
    root = unwrap_root(nbtlib.load(src, gzipped=True))
    if ("Palette" in root or "BlockPalette" in root or "BlockData" in root or ("Blocks" in root and "Data" in root.get("Blocks", {}))):
        result = parse_sponge(root, src.name)
    elif "Blocks" in root and "Materials" in root:
        result = parse_legacy(root, src.name)
    else:
        raise SystemExit("Unsupported schematic structure")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "input": str(src), "output": str(out), "blocks": len(result["blocks"]), "size": result["size"], "format": result["metadata"]["input_format"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
