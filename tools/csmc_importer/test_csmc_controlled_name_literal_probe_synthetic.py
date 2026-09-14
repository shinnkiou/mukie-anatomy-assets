#!/usr/bin/env python3
from csmc_controlled_name_literal_probe import count_literal_hits


def test_zero():
    out = count_literal_hits(b"opaque bytes only", ["MODEL_A", "BONE_001"])
    assert out["identifier_count"] == 2
    assert out["identifiers_with_any_hit"] == 0
    assert out["literal_occurrences_total"] == 0


def test_ascii_hit():
    out = count_literal_hits(b"xxMODEL_Ayy", ["MODEL_A"])
    assert out["identifiers_with_any_hit"] == 1
    assert out["literal_occurrences_by_encoding"]["ascii"] == 1


def test_utf16le_hit():
    out = count_literal_hits(b"xx" + "BONE_001".encode("utf-16le") + b"yy", ["BONE_001"])
    assert out["identifiers_with_any_hit"] == 1
    assert out["literal_occurrences_by_encoding"]["utf-16le"] == 1


def test_utf16be_hit():
    out = count_literal_hits(b"xx" + "UV_MAIN".encode("utf-16be") + b"yy", ["UV_MAIN"])
    assert out["identifiers_with_any_hit"] == 1
    assert out["literal_occurrences_by_encoding"]["utf-16be"] == 1


def main():
    test_zero()
    test_ascii_hit()
    test_utf16le_hit()
    test_utf16be_hit()
    print("SELF_TEST_PASS")


if __name__ == "__main__":
    main()
