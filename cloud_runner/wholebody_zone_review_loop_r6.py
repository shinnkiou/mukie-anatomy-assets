# -*- coding: utf-8 -*-
"""R6 safety wrapper for BP3D R5 zone review.

Purpose:
- preserve the exact source polygon index list from the largest connected component;
- keep label generation unchanged;
- avoid relying on two coexisting INT/FACE custom attributes for source-ID + label-ID,
  because the R5 artifact and R6 attempt 1 prove those layers alias in this pipeline;
- make the repaired face-label JSON the authoritative machine mapping;
- also embed the clean->source map as a Blender Text datablock for local recovery;
- keep the R5 segmentation/classification logic unchanged.

Public-safe: wraps cloud_runner/wholebody_zone_review_loop.py and only uses MakeHuman CC0 base.obj.
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
FACE_ID_FIX_REVISION = "R6_FACEID_SIDECAR_REPAIR_20260830"
TEXT_BLOCK_NAME = "BP3D_SOURCE_FACE_MAP_R6.json"

_orig_copy_component = core.copy_component
_orig_apply_labels = core.apply_labels
_orig_write_json = core.write_json


def _mapping_doc():
    return {
        "schema_version": "bp3d_clean_to_source_face_v2",
        "revision": FACE_ID_FIX_REVISION,
        "authority": "SIDECAR_JSON_AND_BLEND_TEXT",
        "clean_face_count": len(SOURCE_FACE_IDS or []),
        "source_face_ids": list(SOURCE_FACE_IDS or []),
        "note": "Do not treat BP3D_SOURCE_FACE_ID INT/FACE mesh attribute as authoritative in R5/R6-attempt1; it aliases BP3D_LABEL_ID in this pipeline.",
    }


def _embed_mapping_text(obj):
    global SOURCE_FACE_MAP_SHA256
    payload = json.dumps(_mapping_doc(), ensure_ascii=False, separators=(",", ":"))
    SOURCE_FACE_MAP_SHA256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    txt = core.bpy.data.texts.get(TEXT_BLOCK_NAME) or core.bpy.data.texts.new(TEXT_BLOCK_NAME)
    txt.clear()
    txt.write(payload)
    obj["BP3D_SOURCE_FACE_MAP_TEXT"] = TEXT_BLOCK_NAME
    obj["BP3D_SOURCE_FACE_MAP_SHA256"] = SOURCE_FACE_MAP_SHA256
    obj["BP3D_SOURCE_FACE_MAP_REVISION"] = FACE_ID_FIX_REVISION
    obj["BP3D_SOURCE_FACE_MAP_COUNT"] = len(SOURCE_FACE_IDS)


def fixed_copy_component(src, face_ids):
    global SOURCE_FACE_IDS
    SOURCE_FACE_IDS = [int(x) for x in face_ids]
    if len(SOURCE_FACE_IDS) != len(set(SOURCE_FACE_IDS)):
        raise RuntimeError("source face ID list is not unique")
    obj = _orig_copy_component(src, face_ids)
    if len(obj.data.polygons) != len(SOURCE_FACE_IDS):
        raise RuntimeError("clean-face/source-face length mismatch")
    _embed_mapping_text(obj)
    return obj


def fixed_apply_labels(obj, labels, conf, revision):
    """Validate labels, but never rewrite the source INT/FACE layer after labels exist.

    R6 attempt 1 showed that rewriting BP3D_SOURCE_FACE_ID makes all 13,378
    BP3D_LABEL_ID values invalid. Therefore source IDs are authoritative only in
    sidecar/Text mapping; the mesh source INT layer is retained for diagnosis only.
    """
    meta = _orig_apply_labels(obj, labels, conf, revision)
    if SOURCE_FACE_IDS is None:
        raise RuntimeError("source face IDs were not captured")
    if len(labels) != len(SOURCE_FACE_IDS) or len(obj.data.polygons) != len(SOURCE_FACE_IDS):
        raise RuntimeError("face identity length mismatch after labeling")

    label_attr = obj.data.attributes.get("BP3D_LABEL_ID")
    if label_attr is None:
        raise RuntimeError("BP3D_LABEL_ID missing after apply_labels")
    bad_lab = sum(int(label_attr.data[i].value) != int(labels[i]) for i in range(len(labels)))
    if bad_lab:
        raise RuntimeError(f"label attribute validation failed: {bad_lab}")

    src_attr = obj.data.attributes.get("BP3D_SOURCE_FACE_ID")
    if src_attr is not None:
        src_values = [int(src_attr.data[i].value) for i in range(len(labels))]
        alias_count = sum(a == int(b) for a, b in zip(src_values, labels))
        correct_source_count = sum(a == b for a, b in zip(src_values, SOURCE_FACE_IDS))
        ATTR_DIAGNOSTICS.append({
            "revision": int(revision),
            "rows": len(labels),
            "source_attr_equals_label_count": alias_count,
            "source_attr_matches_true_source_count": correct_source_count,
            "source_attr_unique_count": len(set(src_values)),
            "policy": "DIAGNOSTIC_ONLY_NOT_AUTHORITATIVE",
        })
    meta["face_identity_storage"] = "SIDECAR_JSON_AND_BLEND_TEXT"
    meta["source_face_map_sha256"] = SOURCE_FACE_MAP_SHA256
    return meta


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
        doc["face_identity_authority"] = "THIS_JSON"
        doc["blend_embedded_mapping_text"] = TEXT_BLOCK_NAME
        doc["source_face_map_sha256"] = SOURCE_FACE_MAP_SHA256
        doc["source_face_index_unique_count"] = len(set(source_values))
        doc["source_face_mapping"] = "largest_connected_component_original_source_polygon_index"
        doc["mesh_source_face_int_attribute_policy"] = "DIAGNOSTIC_ONLY_NOT_AUTHORITATIVE"
        doc["attribute_alias_diagnostics"] = list(ATTR_DIAGNOSTICS)
    _orig_write_json(path, doc)


core.copy_component = fixed_copy_component
core.apply_labels = fixed_apply_labels
core.write_json = fixed_write_json

if __name__ == "__main__":
    core.main()
