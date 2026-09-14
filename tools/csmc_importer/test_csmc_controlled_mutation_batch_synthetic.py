#!/usr/bin/env python3
from csmc_controlled_mutation_batch import (
    MUTATIONS, EXPECTED_LOGICAL, EXPECTED_STORED, INVARIANT_START,
    ALIGN8_LOGICAL, FRAMING_REMAINDER_START, align8,
)

def main():
    assert len(MUTATIONS) == 30
    offsets=[x[1] for x in MUTATIONS]
    assert len(set(offsets)) == 30
    assert all(0 <= x < EXPECTED_STORED for x in offsets)
    assert align8(EXPECTED_LOGICAL) == ALIGN8_LOGICAL
    assert FRAMING_REMAINDER_START == ALIGN8_LOGICAL
    assert sum(1 for _,_,r in MUTATIONS if r == 'PREFIX_INTERIOR') == 10
    assert sum(1 for _,_,r in MUTATIONS if r == 'INVARIANT_BOUNDARY') == 7
    assert sum(1 for _,_,r in MUTATIONS if r == 'INVARIANT_INTERIOR') == 4
    assert sum(1 for _,_,r in MUTATIONS if r == 'ALIGNMENT_EXTENSION') == 1
    assert sum(1 for _,_,r in MUTATIONS if r == 'FRAMING_REMAINDER') == 8
    assert min(x for _,x,r in MUTATIONS if r == 'INVARIANT_BOUNDARY') < INVARIANT_START
    assert max(x for _,x,r in MUTATIONS if r == 'INVARIANT_BOUNDARY') > INVARIANT_START
    print('SELF_TEST_PASS')

if __name__ == '__main__':
    main()
