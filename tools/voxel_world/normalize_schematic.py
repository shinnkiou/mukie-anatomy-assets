#!/usr/bin/env python3
"""Normalize Minecraft schematic formats into voxel-world-normalized-v1 JSON.

Supported inputs:
- Sponge .schem v2/v3
- legacy MCEdit .schematic (geometry preserved; numeric IDs flagged for later mapping)
- Litematica .litematic (single or multi-region)

Design contract:
- Static building/exterior geometry only. Entities and mobs are ignored by design.
- Preserve source block-state strings for traceability.
- Geometry role and material variant are separate.
- Output is deterministic and carries source/license provenance when supplied.
- Do not embed or redistribute Mojang textures/models.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

try:
    import nbtlib
except ImportError as e:
    raise SystemExit("Missing dependency: nbtlib. Install with: python3 -m pip install nbtlib") from e

AIR = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}
WOOD_WORDS = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "bamboo", "crimson", "warped")
STONE_WORDS = ("stone", "brick", "deepslate", "quartz", "sandstone", "andesite", "diorite", "granite", "cobblestone")


def role_for(state: str) -> tuple[str, str]:
    """Map a Minecraft state to a reusable geometry role + material family."""
    s = state.lower()
    base = s.split("[", 1)[0]
    if base in AIR:
        return "AIR", "air"
    if any(x in base for x in ("glass", "pane")):
        return "WINDOW", "glass"
    if "door" in base or "trapdoor" in base:
        return "DOOR", "wood" if any(x in base for x in WOOD_WORDS) else "metal"
    if "stairs" in base:
        return "STAIR", "stone" if any(x in base for x in STONE_WORDS) else "wood"
    if "slab" in base:
        return "TRIM", "stone" if any(x in base for x in STONE_WORDS) else "wood"
    if "fence_gate" in base:
        return "DOOR", "wood"
    if "iron_bars" in base:
        return "RAILING", "metal"
    if "fence" in base or base.endswith("_wall"):
        return "RAILING", "stone" if base.endswith("_wall") and not any(x in base for x in WOOD_WORDS) else "wood"
    if any(x in base for x in ("log", "wood", "planks", "bamboo_block", "stem", "hyphae")):
        return "WALL_WOOD", "wood"
    if any(x in base for x in ("bricks", "brick", "terracotta")):
        return "WALL_BRICK", "brick"
    if any(x in base for x in ("iron", "copper", "chain", "anvil")):
        return "WALL", "metal"
    if "concrete" in base:
        return "WALL", "concrete"
    if any(x in base for x in ("stone", "cobblestone", "deepslate", "andesite", "diorite", "granite", "quartz", "sandstone")):
        return "WALL", "stone"
    if "sign" in base or "banner" in base:
        return "SIGN", "wood"
    if any(x in base for x in ("lantern", "torch", "light")):
        return "LIGHT", "metal"
    if any(x in base for x in ("leaves", "sapling", "flower", "grass", "vine")):
        return "LANDSCAPE", "plant"
    if any(x in base for x in ("water", "lava")):
        return "LIQUID", "water" if "water" in base else "lava"
    return "WALL", "plaster"


def decode_varints(raw: Iterable[Any]) -> list[int]:
    data = [int(x) & 0xFF for x in raw]
    out: list[int] = []
    value = shift = 0
    for b in data:
        value |= (b & 0x7F) << shift
        if b & 0x80:
            shift += 7
            if shift > 35:
                raise ValueError("Invalid varint stream")
        else:
            out.append(value)
            value = shift = 0
    if shift:
        raise ValueError("Truncated varint stream")
    return out


def unwrap_root(doc):
    root = doc.root if hasattr(doc, "root") else doc
    return root["Schematic"] if "Schematic" in root else root


def state_from_palette_entry(entry: Any) -> str:
    """Convert Litematica BlockStatePalette Compound to canonical state string."""
    name = str(entry.get("Name", "minecraft:air"))
    props = entry.get("Properties")
    if not props:
        return name
    items = sorted((str(k), str(v)) for k, v in props.items())
    return name + "[" + ",".join(f"{k}={v}" for k, v in items) + "]"


def unpack_litematic_states(raw_longs: Iterable[Any], volume: int, palette_size: int) -> list[int]:
    """Decode Litematica's packed long-array palette indices.

    Litematica uses at least 2 bits per entry and packs little-bit-endian inside each 64-bit word.
    Values may straddle word boundaries. nbtlib exposes signed longs, so normalize to unsigned.
    """
    bits = max(2, int(math.ceil(math.log2(max(2, palette_size)))))
    mask = (1 << bits) - 1
    words = [int(v) & 0xFFFFFFFFFFFFFFFF for v in raw_longs]
    out: list[int] = []
    for i in range(volume):
        bit_index = i * bits
        word_index = bit_index >> 6
        start = bit_index & 63
        if word_index >= len(words):
            raise ValueError(f"Litematic BlockStates too short at block {i}/{volume}")
        value = (words[word_index] >> start) & mask
        spill = start + bits - 64
        if spill > 0:
            if word_index + 1 >= len(words):
                raise ValueError("Litematic BlockStates truncated across word boundary")
            value |= (words[word_index + 1] & ((1 << spill) - 1)) << (bits - spill)
        out.append(value)
    return out


def _source_metadata(input_format: str, source_name: str, source_url: str, license_name: str) -> dict[str, Any]:
    return {
        "input_format": input_format,
        "source_file": source_name,
        "source_url": source_url or "",
        "license": license_name or "UNSPECIFIED",
        "dynamic_entities": False,
        "ignored_entities": True,
    }


def parse_sponge(root, source_name: str, source_url: str = "", license_name: str = "") -> dict[str, Any]:
    width, height, length = int(root["Width"]), int(root["Height"]), int(root["Length"])
    version = int(root.get("Version", 2))
    blocks_container = root.get("Blocks") if version >= 3 and "Blocks" in root and hasattr(root.get("Blocks"), "get") else root
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
    blocks: list[dict[str, Any]] = []
    role_counts: dict[str, int] = {}
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
    meta = _source_metadata(f"sponge_v{version}", source_name, source_url, license_name)
    meta.update({"palette_size": len(palette_map), "role_counts": role_counts})
    return {"schema": "voxel-world-normalized-v1", "title": source_name, "size": {"x": width, "y": height, "z": length}, "blocks": blocks, "metadata": meta}


def parse_legacy(root, source_name: str, source_url: str = "", license_name: str = "") -> dict[str, Any]:
    width, height, length = int(root["Width"]), int(root["Height"]), int(root["Length"])
    raw = [int(x) & 0xFF for x in root["Blocks"]]
    expected = width * height * length
    if len(raw) != expected:
        raise ValueError(f"Legacy Blocks length mismatch: {len(raw)} != {expected}")
    blocks: list[dict[str, Any]] = []
    for idx, block_id in enumerate(raw):
        if block_id == 0:
            continue
        x = idx % width
        z = (idx // width) % length
        y = idx // (width * length)
        blocks.append({"x": x, "y": y, "z": z, "role": "WALL", "material": "stone", "source_block": f"legacy_id:{block_id}"})
    meta = _source_metadata("legacy_schematic", source_name, source_url, license_name)
    meta["legacy_id_mapping_required"] = True
    return {"schema": "voxel-world-normalized-v1", "title": source_name, "size": {"x": width, "y": height, "z": length}, "blocks": blocks, "metadata": meta}


def parse_litematic(root, source_name: str, source_url: str = "", license_name: str = "") -> dict[str, Any]:
    regions = root.get("Regions")
    if not regions:
        raise ValueError("Litematic Regions not found")

    raw_blocks: list[dict[str, Any]] = []
    role_counts: dict[str, int] = {}
    region_meta: list[dict[str, Any]] = []
    global_min = [10**18, 10**18, 10**18]
    global_max = [-10**18, -10**18, -10**18]

    for region_name, reg in regions.items():
        pos = reg.get("Position", {})
        size = reg.get("Size", {})
        sx, sy, sz = int(size.get("x", 0)), int(size.get("y", 0)), int(size.get("z", 0))
        ax, ay, az = abs(sx), abs(sy), abs(sz)
        if ax == 0 or ay == 0 or az == 0:
            continue
        px, py, pz = int(pos.get("x", 0)), int(pos.get("y", 0)), int(pos.get("z", 0))
        palette_entries = reg.get("BlockStatePalette") or []
        palette = [state_from_palette_entry(e) for e in palette_entries]
        volume = ax * ay * az
        ids = unpack_litematic_states(reg.get("BlockStates") or [], volume, len(palette))
        entities_count = len(reg.get("Entities") or [])
        tile_entities_count = len(reg.get("TileEntities") or [])
        region_meta.append({"name": str(region_name), "position": {"x": px, "y": py, "z": pz}, "signed_size": {"x": sx, "y": sy, "z": sz}, "size": {"x": ax, "y": ay, "z": az}, "palette_size": len(palette), "ignored_entities": entities_count, "tile_entities": tile_entities_count})

        x0 = px if sx >= 0 else px + sx + 1
        y0 = py if sy >= 0 else py + sy + 1
        z0 = pz if sz >= 0 else pz + sz + 1

        for idx, palette_id in enumerate(ids):
            if palette_id >= len(palette):
                state = f"unknown_palette:{palette_id}"
            else:
                state = palette[palette_id]
            role, material = role_for(state)
            if role == "AIR":
                continue
            lx = idx % ax
            lz = (idx // ax) % az
            ly = idx // (ax * az)
            wx, wy, wz = x0 + lx, y0 + ly, z0 + lz
            raw_blocks.append({"wx": wx, "wy": wy, "wz": wz, "role": role, "material": material, "source_block": state, "source_region": str(region_name)})
            global_min[0] = min(global_min[0], wx); global_min[1] = min(global_min[1], wy); global_min[2] = min(global_min[2], wz)
            global_max[0] = max(global_max[0], wx); global_max[1] = max(global_max[1], wy); global_max[2] = max(global_max[2], wz)
            role_counts[role] = role_counts.get(role, 0) + 1

    if not raw_blocks:
        size_out = {"x": 0, "y": 0, "z": 0}
        blocks: list[dict[str, Any]] = []
        origin = {"x": 0, "y": 0, "z": 0}
    else:
        origin = {"x": global_min[0], "y": global_min[1], "z": global_min[2]}
        size_out = {"x": global_max[0] - global_min[0] + 1, "y": global_max[1] - global_min[1] + 1, "z": global_max[2] - global_min[2] + 1}
        blocks = [{"x": b["wx"] - global_min[0], "y": b["wy"] - global_min[1], "z": b["wz"] - global_min[2], "role": b["role"], "material": b["material"], "source_block": b["source_block"], "source_region": b["source_region"]} for b in raw_blocks]

    meta = _source_metadata(f"litematic_v{int(root.get('Version', 0))}", source_name, source_url, license_name)
    meta.update({"regions": region_meta, "region_count": len(region_meta), "normalized_world_origin": origin, "role_counts": role_counts, "minecraft_data_version": int(root.get("MinecraftDataVersion", 0))})
    title = str(root.get("Metadata", {}).get("Name", source_name)) if hasattr(root.get("Metadata", {}), "get") else source_name
    return {"schema": "voxel-world-normalized-v1", "title": title, "size": size_out, "blocks": blocks, "metadata": meta}


def contextualize_roles(result: dict[str, Any]) -> dict[str, Any]:
    """Add conservative architectural context without destroying source trace.

    Minecraft block IDs describe materials/shapes, not architectural intent. A slab can be a
    floor trim or a roof. This pass only applies high-confidence envelope rules on structures
    at least 3 blocks tall, so flat parser fixtures (e.g. 1-high circles) remain unchanged.
    """
    size = result.get("size", {})
    sx, sy, sz = int(size.get("x", 0)), int(size.get("y", 0)), int(size.get("z", 0))
    if sy < 3:
        return result
    changed = 0
    contextual_counts: dict[str, int] = {}
    structural = {"WALL", "WALL_BRICK", "WALL_WOOD", "TRIM"}
    for b in result.get("blocks", []):
        original = b.get("role", "WALL")
        role = original
        y = int(b.get("y", 0)); x = int(b.get("x", 0)); z = int(b.get("z", 0))
        src = str(b.get("source_block", "")).lower()
        if y == 0 and original in structural:
            role = "FOUNDATION"
        elif y == sy - 1 and original in structural and any(k in src for k in ("slab", "stairs", "tile", "shingle", "brick", "stone", "plank")):
            role = "ROOF_EDGE" if x in (0, sx-1) or z in (0, sz-1) else "ROOF"
        if role != original:
            b["source_role"] = original
            b["role"] = role
            b["role_inference"] = "envelope_context_v1"
            changed += 1
        contextual_counts[b.get("role", role)] = contextual_counts.get(b.get("role", role), 0) + 1
    result.setdefault("metadata", {})["contextual_roles"] = True
    result["metadata"]["contextual_role_changes"] = changed
    result["metadata"]["role_counts"] = contextual_counts
    return result


def detect_and_parse(root, source_name: str, ext: str, source_url: str, license_name: str) -> dict[str, Any]:
    ext = ext.lower()
    if ext == ".litematic" or "Regions" in root:
        result = parse_litematic(root, source_name, source_url, license_name)
    elif "Materials" in root and "Blocks" in root and "Palette" not in root and "BlockPalette" not in root:
        result = parse_legacy(root, source_name, source_url, license_name)
    else:
        is_sponge = (
            "Palette" in root or "BlockPalette" in root or "BlockData" in root or
            ("Blocks" in root and hasattr(root.get("Blocks"), "get") and ("Data" in root.get("Blocks", {}) or "Palette" in root.get("Blocks", {})))
        )
        if not is_sponge:
            raise ValueError("Unsupported schematic/NBT structure")
        result = parse_sponge(root, source_name, source_url, license_name)
    return contextualize_roles(result)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-url", default="")
    ap.add_argument("--license", default="")
    args = ap.parse_args()

    src, out = Path(args.input), Path(args.out)
    doc = nbtlib.load(src, gzipped=True)
    root = unwrap_root(doc)
    result = detect_and_parse(root, src.name, src.suffix, args.source_url, args.license)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "input": str(src), "output": str(out), "blocks": len(result["blocks"]), "size": result["size"], "format": result["metadata"]["input_format"], "license": result["metadata"].get("license")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
