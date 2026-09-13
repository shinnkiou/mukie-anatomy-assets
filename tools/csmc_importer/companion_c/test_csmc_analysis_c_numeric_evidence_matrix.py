from csmc_analysis_c_numeric_evidence_matrix import analyze, classify

def test_exact_active_codec_confirms_encoding_only():
    e={"active_observation":True,"exact_length_fit_count":7,"decoder_rule":"u32be+be_f64/f32","schema_hint":True,"pattern_consistent":True}
    assert classify(e)=="CONFIRMED_ENCODING"
    out=analyze({"evidence":[e]})
    assert out["semantic_promotion_count"]==0

def test_schema_hint_is_not_current_payload_semantics():
    e={"schema_hint":True,"active_observation":False,"pattern_consistent":True,"semantic_slot":"hierarchy"}
    assert classify(e)=="SCHEMA_HINT"

def test_semantics_need_controlled_current_known_input_correlation():
    e={"controlled_differential":True,"current_payload_mapping":True,"known_input_correlation":True,"semantic_slot":"transform"}
    assert classify(e)=="CONFIRMED_SEMANTIC"
    out=analyze({"evidence":[e]})
    assert out["semantic_slots_promoted"]==["transform"]
