from csmc_analysis_c_size_law_negative_control_c063 import reconcile

BASE = {
    "candidate_family": {
        "single_strides_bytes": [4,8,12,16],
        "vertex_strides_bytes": [12,16],
        "index_widths_bytes": [2,4],
        "triangle_strides_bytes": [4,8,12,16],
    },
    "geometry_whole_stored_single_count_exact_models": [],
    "same_phase_geometry": {
        "pair": "F02_F04",
        "prefix_delta_bytes": 864,
        "teacher_deltas": {"vertices":22,"triangles":46,"corners":138},
        "pure_single_count_exact_models": [],
        "vertex_plus_corner_index_exact_models": [],
        "vertex_plus_triangle_exact_models": [],
    },
    "rig_whole_stored_single_count_exact_models": [],
    "rig_whole_stored_bone_plus_weight_exact_models": [],
    "simple_geometry_size_law_rejected": True,
    "simple_rig_size_law_rejected": True,
    "interpretation": "WHOLE_STORED_AND_PHASE_PREFIX_SIZE_NOT_SINGLE_SIMPLE_FIXED_STRIDE_ARRAY",
    "semantic_promotion": False,
    "blender_emit_ready": False,
    "raw_values_embedded": False,
}
C062 = {"classification":"PHASE_CORE_EXCLUSION_MASK_EXTENDED_PHASE3_READY","remaining_search_qwords":537774,"semantic_promotion_count":0}

def cp():
    import copy
    return copy.deepcopy(BASE)

def test_accepts_exact_public_safe_contract():
    out = reconcile(cp(), C062)
    assert out["classification"] == "BOUNDED_SIMPLE_FIXED_STRIDE_SIZE_LAW_REJECTED"
    assert out["mask_changed"] is False
    assert out["semantic_promotion_count"] == 0

def test_rejects_stride_family_widening():
    x=cp(); x["candidate_family"]["single_strides_bytes"].append(24)
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_geometry_model_presence():
    x=cp(); x["geometry_whole_stored_single_count_exact_models"]=[{"field":"vertices"}]
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_prefix_model_presence():
    x=cp(); x["same_phase_geometry"]["pure_single_count_exact_models"]=[{"field":"vertices"}]
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_vertex_corner_model_presence():
    x=cp(); x["same_phase_geometry"]["vertex_plus_corner_index_exact_models"]=[{"x":1}]
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_vertex_triangle_model_presence():
    x=cp(); x["same_phase_geometry"]["vertex_plus_triangle_exact_models"]=[{"x":1}]
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_rig_single_model_presence():
    x=cp(); x["rig_whole_stored_single_count_exact_models"]=[{"x":1}]
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_rig_two_factor_model_presence():
    x=cp(); x["rig_whole_stored_bone_plus_weight_exact_models"]=[{"x":1}]
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_semantic_promotion():
    x=cp(); x["semantic_promotion"]=True
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_blender_emit():
    x=cp(); x["blender_emit_ready"]=True
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_raw_value_publication():
    x=cp(); x["raw_values_embedded"]=True
    import pytest
    with pytest.raises(ValueError): reconcile(x,C062)

def test_rejects_mask_drift():
    import pytest
    bad=dict(C062); bad["remaining_search_qwords"]=1
    with pytest.raises(ValueError): reconcile(cp(),bad)
