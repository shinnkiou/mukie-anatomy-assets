#!/usr/bin/env python3
"""Build a small project-owned Sponge .schem fixture representing a two-storey storefront.

Purpose: exercise the *building* path with a rights-clean binary schematic before importing
third-party building schematics. This is a regression fixture, not a final NEVER TEAR model.
The authored block arrangement is project-owned and may be treated as CC0 for pipeline tests.
"""
from __future__ import annotations

import argparse
import gzip
import io
from pathlib import Path

try:
    import nbtlib
    from nbtlib import Compound, Int, Short, String, ByteArray
except ImportError as e:
    raise SystemExit("Missing dependency: nbtlib") from e


def encode_varints(values: list[int]) -> list[int]:
    out: list[int] = []
    for value in values:
        v = int(value)
        while True:
            b = v & 0x7F
            v >>= 7
            if v:
                out.append(b | 0x80)
            else:
                out.append(b)
                break
    return [b if b < 128 else b - 256 for b in out]


def build(width: int = 12, height: int = 8, length: int = 6):
    states: dict[tuple[int,int,int], str] = {}
    def put(x: int, y: int, z: int, state: str):
        if 0 <= x < width and 0 <= y < height and 0 <= z < length:
            states[(x,y,z)] = state

    for x in range(width):
        for z in range(length): put(x, 0, z, "minecraft:stone_bricks")
    for y in range(1, 7):
        wall = "minecraft:spruce_planks" if y <= 3 else "minecraft:white_concrete"
        for x in range(width): put(x, y, 0, wall); put(x, y, length-1, wall)
        for z in range(1, length-1): put(0, y, z, wall); put(width-1, y, z, wall)
    put(1, 1, 0, "minecraft:oak_door[facing=south,half=lower,hinge=left,open=false,powered=false]")
    put(1, 2, 0, "minecraft:oak_door[facing=south,half=upper,hinge=left,open=false,powered=false]")
    for x in (3,4,7,8,9): put(x, 1, 0, "minecraft:glass"); put(x, 2, 0, "minecraft:glass")
    for x in (2,3,5,6,8,9): put(x, 4, 0, "minecraft:glass"); put(x, 5, 0, "minecraft:glass")
    for x in (2,3,7,8): put(x, 4, length-1, "minecraft:glass"); put(x, 5, length-1, "minecraft:glass")
    for z in (2,3): put(0, 4, z, "minecraft:glass"); put(width-1, 4, z, "minecraft:glass")
    for x in range(width): put(x, 3, 0, "minecraft:polished_andesite_slab[type=bottom,waterlogged=false]")
    for x in range(4, 8): put(x, 3, 0, "minecraft:dark_oak_sign[rotation=0,waterlogged=false]")
    for x in range(width):
        for z in range(length): put(x, 7, z, "minecraft:deepslate_tile_slab[type=bottom,waterlogged=false]")
    put(width-1, 2, 2, "minecraft:iron_block")
    put(width-1, 3, 2, "minecraft:iron_bars")
    put(width-1, 2, 3, "minecraft:lantern[hanging=false,waterlogged=false]")

    palette_states = ["minecraft:air"] + sorted(set(states.values()))
    palette = {state: i for i, state in enumerate(palette_states)}
    ids: list[int] = []
    for y in range(height):
        for z in range(length):
            for x in range(width): ids.append(palette.get(states.get((x,y,z), "minecraft:air"), 0))

    root = Compound({
        "Version": Int(2), "DataVersion": Int(3700),
        "Width": Short(width), "Height": Short(height), "Length": Short(length),
        "PaletteMax": Int(len(palette)),
        "Palette": Compound({k: Int(v) for k, v in palette.items()}),
        "BlockData": ByteArray(encode_varints(ids)),
        "Metadata": Compound({"Name": String("NEVER_TEAR_VOXEL_FIXTURE_R1"), "Author": String("ChatGPT Blender integration project"), "License": String("CC0-1.0 project-owned fixture")}),
    })
    return root, len(states), len(palette)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); args = ap.parse_args()
    root, block_count, palette_size = build()
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    raw = io.BytesIO(); nbtlib.File(root).write(raw)
    with out.open('wb') as dst:
        with gzip.GzipFile(filename='', mode='wb', fileobj=dst, mtime=0) as gz:
            gz.write(raw.getvalue())
    print(f"PASS {out} blocks={block_count} palette={palette_size}")

if __name__ == "__main__": main()
