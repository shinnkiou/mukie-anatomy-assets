#!/usr/bin/env python3
from csmc_render_part_residual_probe import triple_common_block, scalar_value

def q(x):
    return int(x).to_bytes(8,"little")

def test_common():
    # Use L=2 in synthetic test; common exact block is 5 qwords.
    common=[q(101),q(102),q(103),q(104),q(105)]
    a=[q(1),q(2)]+common+[q(3)]
    b=[q(9),q(8),q(7)]+common+[q(6)]
    c=[q(4)]+common+[q(5)]
    out=triple_common_block(a,b,c,L=2)
    assert out is not None
    assert out["start_qwords"]=={"F03":2,"F06":3,"F07":1}
    assert out["exact_length_qwords"]==5
    assert out["window_run_count"]==4

def test_scalar():
    p=b"\x01\x00\x00\x00\x08\x00"
    assert scalar_value(p,0,1,"little")==1
    assert scalar_value(p,0,2,"little")==1
    assert scalar_value(p,4,2,"little")==8
    assert scalar_value(p,-1,1,"little") is None

if __name__=="__main__":
    test_common()
    test_scalar()
    print("PASS synthetic render-part residual probe")
