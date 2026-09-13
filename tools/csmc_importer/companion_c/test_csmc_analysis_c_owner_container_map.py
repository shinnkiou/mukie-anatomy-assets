import pytest
from csmc_analysis_c_owner_container_map import analyze, validate_edge

def test_live_resolved_route_becomes_importer_route_without_semantics():
    g={"edges":[{"level":"LIVE_RESOLVED_EDGE","source":"A.field","relation":"external_ref","target":"ext1","target_kind":"scene","importer_route":"scene"}]}
    out=analyze(g)
    assert out["importer_routes"]["scene"]["target_kind"]=="scene"
    assert out["importer_routes"]["scene"]["semantic_payload_role"]=="UNRESOLVED"
    assert out["payload_semantics_claimed"] is False

def test_schema_only_cannot_masquerade_as_live():
    with pytest.raises(ValueError,match="schema-only"):
        validate_edge({"level":"SCHEMA_ONLY_EDGE","source":"A","relation":"link","target":"B","schema_only":False})

def test_unresolved_route_cannot_claim_target_kind():
    with pytest.raises(ValueError,match="target_kind"):
        validate_edge({"level":"UNRESOLVED_ROUTE","source":"A.field","relation":"external_ref","target":"unknown","target_kind":"character"})
