#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a topology-only signature for the immutable MakeHuman CC0 base.obj.

The signature deliberately ignores vertex coordinates so a shaped MakeHuman body can
still match the base topology. It verifies source face-index correspondence by hashing,
for every face index, the sorted 0-based vertex IDs belonging to that polygon.

Public-safe: reads only the downloaded CC0 base.obj.
"""
from pathlib import Path
import argparse, hashlib, json

EXPECTED_OBJ_SHA256 = "8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c"
EXPECTED_VERTICES = 19158
EXPECTED_FACES = 18486
EXPECTED_CLEAN_PREFIX_FACES = 13378


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_obj(path: Path):
    vertex_count = 0
    faces = []
    with path.open("r", encoding="utf-8", errors="strict") as f:
        for line in f:
            if line.startswith("v "):
                vertex_count += 1
            elif line.startswith("f "):
                ids = []
                for token in line.split()[1:]:
                    raw = token.split("/", 1)[0]
                    idx = int(raw)
                    if idx < 0:
                        idx = vertex_count + idx
                    else:
                        idx -= 1
                    ids.append(idx)
                faces.append(ids)
    return vertex_count, faces


def sequence_hash(faces):
    h = hashlib.sha256()
    for fi, verts in enumerate(faces):
        # sorted membership ignores winding/cyclic start but preserves face index and vertex IDs
        row = f"{fi}:" + ",".join(str(v) for v in sorted(verts)) + "\n"
        h.update(row.encode("ascii"))
    return h.hexdigest()


def membership_multiset_hash(faces):
    # Additional order-independent diagnostic: useful if only face order differs.
    rows = [",".join(str(v) for v in sorted(verts)) for verts in faces]
    rows.sort()
    h = hashlib.sha256()
    for row in rows:
        h.update((row + "\n").encode("ascii"))
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("obj")
    ap.add_argument("out")
    ns = ap.parse_args()
    obj = Path(ns.obj)
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    obj_hash = file_sha256(obj)
    if obj_hash != EXPECTED_OBJ_SHA256:
        raise SystemExit(f"unexpected base.obj SHA256: {obj_hash}")

    vertex_count, faces = parse_obj(obj)
    if vertex_count != EXPECTED_VERTICES:
        raise SystemExit(f"unexpected vertex count: {vertex_count}")
    if len(faces) != EXPECTED_FACES:
        raise SystemExit(f"unexpected face count: {len(faces)}")

    clean = faces[:EXPECTED_CLEAN_PREFIX_FACES]
    helper = faces[EXPECTED_CLEAN_PREFIX_FACES:]
    doc = {
        "schema_version": "bp3d_topology_signature_v1",
        "source": "MakeHuman CC0 makehuman/data/3dobjs/base.obj",
        "source_obj_sha256": obj_hash,
        "vertex_count": vertex_count,
        "face_count": len(faces),
        "clean_body_expected_face_id_range": [0, EXPECTED_CLEAN_PREFIX_FACES - 1],
        "clean_body_expected_face_count": EXPECTED_CLEAN_PREFIX_FACES,
        "excluded_non_body_expected_face_id_range": [EXPECTED_CLEAN_PREFIX_FACES, EXPECTED_FACES - 1],
        "excluded_non_body_expected_face_count": len(helper),
        "face_index_vertex_membership_sequence_sha256": sequence_hash(faces),
        "clean_prefix_face_index_vertex_membership_sequence_sha256": sequence_hash(clean),
        "face_vertex_membership_multiset_sha256": membership_multiset_hash(faces),
        "clean_prefix_face_vertex_membership_multiset_sha256": membership_multiset_hash(clean),
        "local_gate": {
            "required": True,
            "method": "On the local fresh MASTER body object, hash each polygon as face_index:sorted(vertex_ids) using the same algorithm. Direct R7 source_face_index transfer is allowed only when vertex_count, face_count, clean-body face set, and full sequence hash all match.",
            "on_mismatch": "STOP. Do not coerce face indices; emit topology correspondence report instead."
        }
    }
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
