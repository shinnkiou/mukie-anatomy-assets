#!/usr/bin/env python3
from csmc_consumer_constrained_lab import (
    canonical_behavior_key,
    classify_consumer_compatibility,
    synthetic_generation_summary,
)

def run():
    contradicted = {
        "candidate_id":"T_BAD",
        "family":"READER_WIDTH_ENDIAN",
        "consumer_scope":"MODELDATA_CONSUMER_PATH",
        "externalchunk_corridor":False,
        "modeldata_loader_binding":"OtherLoader",
    }
    r = classify_consumer_compatibility(contradicted)
    assert r["result_class"] == "CONSUMER_CONTRADICTED"
    assert r["hard_reject"] is True

    compatible = {
        "candidate_id":"T_GOOD",
        "family":"READER_WIDTH_ENDIAN",
        "consumer_scope":"MODELDATA_CONSUMER_PATH",
        "externalchunk_corridor":True,
        "modeldata_loader_binding":"Canvas3DModelLoader",
        "external_lookup_mode":"EXTERNAL_ID_TO_OFFSET",
    }
    r = classify_consumer_compatibility(compatible)
    assert r["result_class"] == "CONSUMER_COMPATIBLE"
    assert r["hard_reject"] is False
    assert r["consumer_bonus"] == 0

    unrelated = {
        "candidate_id":"T_UNRELATED",
        "family":"LOCAL_BLOCK_LAYOUT",
        "consumer_scope":"UNRELATED_RECORD_FAMILY",
        "externalchunk_corridor":False,
    }
    r = classify_consumer_compatibility(unrelated)
    assert r["result_class"] == "CONSUMER_UNRESOLVED"
    assert r["hard_reject"] is False
    assert r["applicable_constraints"] == []

    a = {
        "candidate_id":"SEM_A","family":"READER_WIDTH_ENDIAN",
        "consumer_scope":"MODELDATA_CONSUMER_PATH","externalchunk_corridor":False,
        "read_width":4,"endianness":"LE","count_source":"local_count",
        "grouping":"scalar","relationship":"local_stride","destination_kind":"array",
        "external_lookup_mode":None,"modeldata_loader_binding":"Canvas3DModelLoader",
        "semantic_label":"STRUCTURAL_ONLY","visual_similarity":0.0,
    }
    b = dict(a, candidate_id="SEM_B", semantic_label="GEOMETRY_OR_TOPOLOGY_TARGET")
    assert canonical_behavior_key(a) == canonical_behavior_key(b)

    visual = dict(a, candidate_id="VIS_B", visual_similarity=1.0)
    assert canonical_behavior_key(a) == canonical_behavior_key(visual)
    assert classify_consumer_compatibility(visual)["visual_score_delta"] == 0

    summary = synthetic_generation_summary()
    assert summary["input_count"] == 50
    assert 0 < summary["survivor_count"] < 50
    assert summary["hard_reject_count"] > 0
    assert summary["duplicate_count"] > 0
    assert summary["fill_to_50_after_prune"] is False
    assert summary["classic_ga"] is False
    assert summary["semantic_promotion"] is False
    print("CONSUMER_CONSTRAINED_SYNTHETIC_PASS", summary["input_count"], summary["survivor_count"], summary["hard_reject_count"], summary["duplicate_count"])

if __name__ == "__main__":
    run()
