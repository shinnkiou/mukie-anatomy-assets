#!/usr/bin/env python3
from csmc_p4_known_grammar_exclusion import analyze, fixture, self_test

self_test()

doc = fixture()
doc["known_always_preserved_qwords_per_record"] = 0
nout = analyze(doc)
assert nout["valid"] is False  # preregistered grammar floor must remain 23
print("EXTRA_TEST_PASS")
