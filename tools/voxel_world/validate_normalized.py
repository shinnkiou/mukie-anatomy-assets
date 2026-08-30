#!/usr/bin/env python3
"""Deterministic QA for voxel-world-normalized-v1.

Data/geometry preflight before Three.js/Blender realistic exterior conversion.
Final visual delivery still requires at least three reviews: structure, material, visual/detail.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

TRANSPARENT_MATERIALS = {"glass", "glass_clear", "glass_frosted", "water", "lava"}
STRUCTURAL_ROLES = {"WALL", "WALL_BRICK", "WALL_WOOD", "FOUNDATION", "COLUMN", "BEAM", "ROOF", "ROOF_EDGE", "TRIM"}
FACE_DIRS = ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1))


def validate(data: dict[str, Any]) -> dict[str, Any]:
    errors, warnings = [], []
    blocks = data.get("blocks") if isinstance(data.get("blocks"), list) else []
    size = data.get("size") if isinstance(data.get("size"), dict) else {}
    sx, sy, sz = (int(size.get(k, 0) or 0) for k in ("x", "y", "z"))
    if data.get("schema") != "voxel-world-normalized-v1": errors.append("schema must be voxel-world-normalized-v1")
    if blocks and min(sx, sy, sz) <= 0: errors.append("non-empty world requires positive x/y/z size")

    seen = set(); duplicate_count = out_of_bounds = missing_trace = transparent_structural = invalid_coordinate = 0
    role_counter, material_counter = Counter(), Counter()
    for i, b in enumerate(blocks):
        try:
            x,y,z=b.get("x"),b.get("y"),b.get("z")
            if isinstance(x,bool) or isinstance(y,bool) or isinstance(z,bool): raise ValueError
            xi,yi,zi=int(x),int(y),int(z)
            if (xi,yi,zi)!=(x,y,z): raise ValueError
        except Exception:
            invalid_coordinate += 1; continue
        pos=(xi,yi,zi)
        if pos in seen: duplicate_count += 1
        seen.add(pos)
        if not (0<=xi<sx and 0<=yi<sy and 0<=zi<sz): out_of_bounds += 1
        role=str(b.get("role","")).upper(); material=str(b.get("material",""))
        role_counter[role]+=1; material_counter[material]+=1
        if role=="AIR": errors.append(f"AIR block leaked into normalized blocks at index {i}")
        if not role: errors.append(f"missing role at index {i}")
        if not material: errors.append(f"missing material at index {i}")
        if role in STRUCTURAL_ROLES and material in TRANSPARENT_MATERIALS: transparent_structural += 1
        if not b.get("source_block"): missing_trace += 1
    if invalid_coordinate: errors.append(f"invalid/non-integer coordinates: {invalid_coordinate}")
    if duplicate_count: errors.append(f"duplicate occupied cells: {duplicate_count}")
    if out_of_bounds: errors.append(f"out-of-bounds blocks: {out_of_bounds}")
    if transparent_structural: errors.append(f"transparent material assigned to structural cells: {transparent_structural}")
    if missing_trace: warnings.append(f"source_block trace missing on {missing_trace} blocks")

    metadata=data.get("metadata") if isinstance(data.get("metadata"),dict) else {}
    if metadata.get("dynamic_entities") not in (False,0,None): errors.append("dynamic_entities must be false")
    if metadata.get("ignored_entities") is not True: warnings.append("ignored_entities is not explicitly true")
    if not metadata.get("license"): warnings.append("license provenance missing")
    if not metadata.get("source_url") and metadata.get("license") not in ("internal-test","SYNTHETIC_INTERNAL"): warnings.append("source_url provenance missing")

    exposed_faces=0
    for x,y,z in seen:
        for dx,dy,dz in FACE_DIRS:
            if (x+dx,y+dy,z+dz) not in seen: exposed_faces += 1
    boundary={"x_min":0,"x_max":0,"y_min":0,"y_max":0,"z_min":0,"z_max":0}
    for x,y,z in seen:
        if x==0: boundary["x_min"]+=1
        if x==sx-1: boundary["x_max"]+=1
        if y==0: boundary["y_min"]+=1
        if y==sy-1: boundary["y_max"]+=1
        if z==0: boundary["z_min"]+=1
        if z==sz-1: boundary["z_max"]+=1
    return {"status":"PASS" if not errors else "FAIL","schema":data.get("schema"),"title":data.get("title",""),"size":{"x":sx,"y":sy,"z":sz},"block_count":len(blocks),"unique_cells":len(seen),"role_counts":dict(sorted(role_counter.items())),"material_counts":dict(sorted(material_counter.items())),"exposed_faces":exposed_faces,"boundary_occupancy":boundary,"errors":errors,"warnings":warnings,"review_contract":{"preflight":"this validator","review_1_structure":"gaps/backface/opening/intersection/duplicate","review_2_material":"opacity/double-surface/UV/missing texture/base-wall fallback","review_3_visual":"lighting/detail/scale/repetition","minimum_visual_reviews":3}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--out",default=""); args=ap.parse_args()
    report=validate(json.loads(Path(args.input).read_text(encoding="utf-8"))); text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).write_text(text,encoding="utf-8")
    print(text); raise SystemExit(0 if report["status"]=="PASS" else 2)

if __name__=="__main__": main()
