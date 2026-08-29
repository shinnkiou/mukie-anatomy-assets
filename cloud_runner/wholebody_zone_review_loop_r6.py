# -*- coding: utf-8 -*-
"""R6 safety wrapper for BP3D R5 zone review.

Purpose:
- preserve the exact source polygon index list from the largest connected component;
- rewrite BP3D_SOURCE_FACE_ID after label attributes are created;
- validate that source-face IDs and label IDs are independent columns;
- keep the R5 segmentation/classification logic unchanged.

This is public-safe and only wraps cloud_runner/wholebody_zone_review_loop.py.
"""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
CORE_PATH = HERE / "wholebody_zone_review_loop.py"
SPEC = importlib.util.spec_from_file_location("bp3d_r5_core", CORE_PATH)
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)

SOURCE_FACE_IDS = None
FACE_ID_FIX_REVISION = "R6_FACEID_REPAIR_20260830"

_orig_copy_component = core.copy_component
_orig_apply_labels = core.apply_labels
_orig_write_json = core.write_json


def fixed_copy_component(src, face_ids):
    global SOURCE_FACE_IDS
    SOURCE_FACE_IDS = [int(x) for x in face_ids]
    if len(SOURCE_FACE_IDS) != len(set(SOURCE_FACE_IDS)):
        raise RuntimeError("source face ID list is not unique")
    obj = _orig_copy_component(src, face_ids)
    if len(obj.data.polygons) != len(SOURCE_FACE_IDS):
        raise RuntimeError("clean-face/source-face length mismatch")
    return obj


def fixed_apply_labels(obj, labels, conf, revision):
    meta = _orig_apply_labels(obj, labels, conf, revision)
    if SOURCE_FACE_IDS is None:
        raise RuntimeError("source face IDs were not captured")
    if len(labels) != len(SOURCE_FACE_IDS) or len(obj.data.polygons) != len(SOURCE_FACE_IDS):
        raise RuntimeError("face identity length mismatch after labeling")

    src_attr = obj.data.attributes.get("BP3D_SOURCE_FACE_ID")
    if src_attr is None:
        src_attr = obj.data.attributes.new("BP3D_SOURCE_FACE_ID", "INT", "FACE")
    for i, src_id in enumerate(SOURCE_FACE_IDS):
        src_attr.data[i].value = src_id

    label_attr = obj.data.attributes.get("BP3D_LABEL_ID")
    if label_attr is None:
        raise RuntimeError("BP3D_LABEL_ID missing after apply_labels")

    bad_src = sum(int(src_attr.data[i].value) != SOURCE_FACE_IDS[i] for i in range(len(labels)))
    bad_lab = sum(int(label_attr.data[i].value) != int(labels[i]) for i in range(len(labels)))
    if bad_src or bad_lab:
        raise RuntimeError(f"attribute validation failed: source={bad_src}, label={bad_lab}")
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
        if len(source_values) != len(set(source_values)):
            raise RuntimeError("repaired source_face_index is not unique")
        if all(int(r.get("source_face_index", -1)) == int(r.get("label_id", -2)) for r in rows):
            raise RuntimeError("source_face_index still aliases label_id")
        doc["face_identity_schema"] = "bp3d_clean_to_source_face_v2"
        doc["face_identity_fix_revision"] = FACE_ID_FIX_REVISION
        doc["source_face_index_unique_count"] = len(set(source_values))
        doc["source_face_mapping"] = "largest_connected_component_original_source_polygon_index"
    _orig_write_json(path, doc)


core.copy_component = fixed_copy_component
core.apply_labels = fixed_apply_labels
core.write_json = fixed_write_json

if __name__ == "__main__":
    core.main()
