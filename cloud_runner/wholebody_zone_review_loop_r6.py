# -*- coding: utf-8 -*-
"""R7-compatible Face-ID repair wrapper for BP3D R5/R6 zone review.

Verified defect:
- R5 artifacts: BP3D_SOURCE_FACE_ID reads as label_id for all 13,378 faces.
- R6 attempt 1: forcing source INT/FACE values makes label INT/FACE values wrong.
- R6 attempt 2: immediately after original apply_labels creates the second INT/FACE
  layer, BP3D_LABEL_ID itself is wrong for all 13,378 faces.

Therefore this wrapper never creates a second INT/FACE label attribute.
Authoritative storage becomes:
- source polygon address: BP3D_SOURCE_FACE_ID (single INT/FACE layer) + embedded Text + JSON
- semantic label: face-label JSON + materials/material_index
- confidence: FLOAT/FACE layer

This preserves R7 binding quarantine principles while regenerating a one-to-one remap.
"""
from pathlib import Path
import importlib.util
import json
import hashlib

HERE = Path(__file__).resolve().parent
CORE_PATH = HERE / "wholebody_zone_review_loop.py"
SPEC = importlib.util.spec_from_file_location("bp3d_r5_core", CORE_PATH)
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)

SOURCE_FACE_IDS = None
SOURCE_FACE_MAP_SHA256 = None
ATTR_DIAGNOSTICS = []
FACE_ID_FIX_REVISION = "R7_FACEID_SINGLE_INT_REMAP_20260830"
TEXT_BLOCK_NAME = "BP3D_SOURCE_FACE_MAP_R7.json"

_orig_copy_component = core.copy_component
_orig_write_json = core.write_json


def _mapping_doc():
    return {
        "schema_version": "bp3d_clean_to_source_face_v2",
        "revision": FACE_ID_FIX_REVISION,
        "authority": "SOURCE_INT_PLUS_JSON_PLUS_BLEND_TEXT",
        "clean_face_count": len(SOURCE_FACE_IDS or []),
        "source_face_ids": list(SOURCE_FACE_IDS or []),
        "label_storage": "FACE_LABEL_JSON_AND_MATERIAL_INDEX_NO_SECOND_INT_FACE_LAYER",
        "reason": "Two INT/FACE custom attributes alias in the observed Blender 4.2.23 pipeline; source address and semantic label must not share that storage pattern.",
    }


def _embed_mapping_text(obj):
    global SOURCE_FACE_MAP_SHA256
    payload = json.dumps(_mapping_doc(), ensure_ascii=False, separators=(",", ":"))
    SOURCE_FACE_MAP_SHA256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    txt = core.bpy.data.texts.get(TEXT_BLOCK_NAME) or core.bpy.data.texts.new(TEXT_BLOCK_NAME)
    txt.clear(); txt.write(payload)
    obj["BP3D_SOURCE_FACE_MAP_TEXT"] = TEXT_BLOCK_NAME
    obj["BP3D_SOURCE_FACE_MAP_SHA256"] = SOURCE_FACE_MAP_SHA256
    obj["BP3D_SOURCE_FACE_MAP_REVISION"] = FACE_ID_FIX_REVISION
    obj["BP3D_SOURCE_FACE_MAP_COUNT"] = len(SOURCE_FACE_IDS)
    obj["BP3D_LABEL_STORAGE"] = "JSON_AND_MATERIAL_INDEX"


def fixed_copy_component(src, face_ids):
    global SOURCE_FACE_IDS
    SOURCE_FACE_IDS = [int(x) for x in face_ids]
    if len(SOURCE_FACE_IDS) != len(set(SOURCE_FACE_IDS)):
        raise RuntimeError("source face ID list is not unique")
    obj = _orig_copy_component(src, face_ids)
    if len(obj.data.polygons) != len(SOURCE_FACE_IDS):
        raise RuntimeError("clean-face/source-face length mismatch")
    src_attr = obj.data.attributes.get("BP3D_SOURCE_FACE_ID")
    if src_attr is None:
        raise RuntimeError("source face attribute missing after clean copy")
    bad = sum(int(src_attr.data[i].value) != SOURCE_FACE_IDS[i] for i in range(len(SOURCE_FACE_IDS)))
    if bad:
        raise RuntimeError(f"source face attribute invalid immediately after copy: {bad}")
    _embed_mapping_text(obj)
    return obj


def fixed_apply_labels(obj, labels, conf, revision):
    """Apply visual labels without creating BP3D_LABEL_ID INT/FACE."""
    if SOURCE_FACE_IDS is None:
        raise RuntimeError("source face IDs were not captured")
    mesh = obj.data
    if len(labels) != len(SOURCE_FACE_IDS) or len(mesh.polygons) != len(SOURCE_FACE_IDS):
        raise RuntimeError("face identity length mismatch before labeling")

    src_attr = mesh.attributes.get("BP3D_SOURCE_FACE_ID")
    if src_attr is None:
        raise RuntimeError("BP3D_SOURCE_FACE_ID missing before labeling")
    bad_before = sum(int(src_attr.data[i].value) != SOURCE_FACE_IDS[i] for i in range(len(labels)))
    if bad_before:
        raise RuntimeError(f"source face attribute invalid before labeling: {bad_before}")

    pairs = core.label_adjacency(mesh, labels)
    colors, conflicts = core.graph_colors(labels, pairs)

    # Keep confidence as FLOAT/FACE. Deliberately do NOT create a second INT/FACE layer.
    ca = mesh.attributes.get("BP3D_CONFIDENCE")
    if ca is None:
        ca = mesh.attributes.new("BP3D_CONFIDENCE", "FLOAT", "FACE")
    for i, c in enumerate(conf):
        ca.data[i].value = float(c)

    lab_order = sorted(set(labels)); midx = {}
    for lab in lab_order:
        c = core.PALETTE[colors[lab]]
        mesh.materials.append(core.make_material("BP3D_%d_%s" % (lab, core.N[lab]), c))
        midx[lab] = len(mesh.materials) - 1
    for p, lab in zip(mesh.polygons, labels):
        p.material_index = midx[lab]

    bad_after = sum(int(src_attr.data[i].value) != SOURCE_FACE_IDS[i] for i in range(len(labels)))
    conf_bad = sum(abs(float(ca.data[i].value) - float(conf[i])) > 1e-5 for i in range(len(labels)))
    if bad_after or conf_bad:
        raise RuntimeError(f"post-label storage validation failed: source={bad_after}, confidence={conf_bad}")
    if mesh.attributes.get("BP3D_LABEL_ID") is not None:
        raise RuntimeError("unsafe BP3D_LABEL_ID INT/FACE layer unexpectedly exists")

    ATTR_DIAGNOSTICS.append({
        "revision": int(revision),
        "rows": len(labels),
        "source_correct_before": len(labels) - bad_before,
        "source_correct_after": len(labels) - bad_after,
        "confidence_correct": len(labels) - conf_bad,
        "label_storage": "JSON_AND_MATERIAL_INDEX",
        "second_int_face_label_layer_created": False,
    })
    return {
        "adjacency_pairs": len(pairs),
        "color_conflicts": conflicts,
        "color_index": {str(k): v for k, v in colors.items()},
        "face_identity_storage": "SOURCE_INT_PLUS_JSON_PLUS_BLEND_TEXT",
        "semantic_label_storage": "JSON_AND_MATERIAL_INDEX",
        "source_face_map_sha256": SOURCE_FACE_MAP_SHA256,
    }


def fixed_write_json(path, doc):
    path = Path(path)
    if path.name.endswith("_face_labels.json") and isinstance(doc, dict) and isinstance(doc.get("faces"), list):
        if SOURCE_FACE_IDS is None:
            raise RuntimeError("cannot write face labels without source face IDs")
        rows = doc["faces"]
        if len(rows) != len(SOURCE_FACE_IDS):
            raise RuntimeError("face-label row count does not match source face IDs")
        for i, row in enumerate(rows):
            row["clean_face_index"] = i
            row["source_face_index"] = SOURCE_FACE_IDS[i]
        source_values = [int(r["source_face_index"]) for r in rows]
        label_values = [int(r["label_id"]) for r in rows]
        if len(source_values) != len(set(source_values)):
            raise RuntimeError("repaired source_face_index is not unique")
        if all(a == b for a, b in zip(source_values, label_values)):
            raise RuntimeError("source_face_index still aliases label_id")
        if min(source_values) < 0 or max(source_values) >= 18486:
            raise RuntimeError("source_face_index outside original source polygon range")
        doc["face_identity_schema"] = "bp3d_clean_to_source_face_v2"
        doc["face_identity_fix_revision"] = FACE_ID_FIX_REVISION
        doc["face_identity_authority"] = "SOURCE_INT_PLUS_THIS_JSON"
        doc["semantic_label_authority"] = "THIS_JSON_AND_MATERIAL_INDEX"
        doc["blend_embedded_mapping_text"] = TEXT_BLOCK_NAME
        doc["source_face_map_sha256"] = SOURCE_FACE_MAP_SHA256
        doc["source_face_index_unique_count"] = len(set(source_values))
        doc["source_face_mapping"] = "largest_connected_component_original_source_polygon_index"
        doc["mesh_source_face_int_attribute_policy"] = "AUTHORITATIVE_SINGLE_INT_FACE_LAYER"
        doc["mesh_label_int_attribute_policy"] = "FORBIDDEN_USE_JSON_AND_MATERIAL_INDEX"
        doc["attribute_alias_diagnostics"] = list(ATTR_DIAGNOSTICS)
    _orig_write_json(path, doc)


core.copy_component = fixed_copy_component
core.apply_labels = fixed_apply_labels
core.write_json = fixed_write_json

if __name__ == "__main__":
    core.main()
