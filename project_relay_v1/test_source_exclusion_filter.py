from source_exclusion_filter import filter_candidates, validate_adopted_sources


def test_origin_candidates_are_filtered_after_search():
    candidates = [
        {
            "id": "origin-official",
            "url": "https://www.gundam-the-origin.net/mechanical/0101.html",
            "title": "MS-05 ザクI｜MECHANICAL｜機動戦士ガンダム THE ORIGIN",
        },
        {
            "id": "origin-bandai-manual",
            "url": "https://manual.bandai-hobby.net/pdf/1011.pdf",
            "title": "MS-05 ZAKU I / HG GUNDAM THE ORIGIN / 1/144 SCALE",
        },
        {
            "id": "old-mg-zaku2",
            "url": "https://manual.bandai-hobby.net/pdf/410.pdf",
            "title": "MG 1/100 MS-06F/J ZAKU II",
            "source_family": "機動戦士ガンダム 1995 MG",
        },
        {
            "id": "old-mg-zaku1",
            "url": "https://manual.bandai-hobby.net/pdf/440.pdf",
            "title": "MG 1/100 MS-05B ZAKU I",
            "source_family": "機動戦士ガンダム 1999 MG",
        },
    ]
    result = filter_candidates(candidates, ["ジ・オリジン"])
    assert result["candidate_count"] == 4, result
    assert result["blocked_count"] == 2, result
    assert {x["id"] for x in result["blocked"]} == {"origin-official", "origin-bandai-manual"}, result
    assert {x["id"] for x in result["allowed"]} == {"old-mg-zaku2", "old-mg-zaku1"}, result


def test_final_adoption_audit_fails_if_origin_leaks():
    bad = [
        {"id": "old", "url": "https://manual.bandai-hobby.net/pdf/410.pdf", "title": "MG MS-06F/J ZAKU II"},
        {"id": "leak", "url": "https://gundam-the-origin.net/foo", "title": "Mechanical"},
    ]
    audit = validate_adopted_sources(bad, ["ジ・オリジン"])
    assert audit["valid"] is False, audit
    assert audit["result"] == "FAIL_EXCLUDED_SOURCE_ADOPTED", audit
    assert audit["excluded_adopted_count"] == 1, audit


def test_final_adoption_audit_passes_non_origin_sources():
    good = [
        {"id": "mg410", "url": "https://manual.bandai-hobby.net/pdf/410.pdf", "title": "MG MS-06F/J ZAKU II"},
        {"id": "mg440", "url": "https://manual.bandai-hobby.net/pdf/440.pdf", "title": "MG MS-05B ZAKU I"},
    ]
    audit = validate_adopted_sources(good, ["ジ・オリジン"])
    assert audit["valid"] is True, audit
    assert audit["result"] == "PASS", audit
    assert audit["excluded_adopted_count"] == 0, audit


def main():
    test_origin_candidates_are_filtered_after_search()
    test_final_adoption_audit_fails_if_origin_leaks()
    test_final_adoption_audit_passes_non_origin_sources()
    print("PROJECT RELAY SOURCE EXCLUSION FILTER TESTS PASS")


if __name__ == "__main__":
    main()
