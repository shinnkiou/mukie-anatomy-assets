#!/usr/bin/env python3
from csmc_p4_i2_cross_constraint_audit import AMBIGUOUS_INDICES, SIG_A, SIG_B, audit, enumerate_assignments


def main() -> None:
    out = audit()
    assert out["status"] == "NO_DETERMINISTIC_REDUCTION"
    assert out["complete_assignments_after_all_direct_signature_constraints"] == 20
    assert out["forced_signature_rows"] == {}
    assignments = enumerate_assignments()
    assert len(assignments) == 20
    for idx in AMBIGUOUS_INDICES:
        assert {row[idx] for row in assignments} == {SIG_A, SIG_B}
    print("PASS: I2 cross-constraint audit preserves all 20 admissible 3/3 assignments")


if __name__ == "__main__":
    main()
