from __future__ import annotations

from csmc_p4_tail_rewrite_profile import analyze_tail_rewrites


def q(v: int) -> bytes:
    return int(v & ((1 << 64) - 1)).to_bytes(8, "little")


def main() -> None:
    starts = [0, 6]
    lengths = [6, 6]
    delta = 20
    a = bytearray((delta + 20) * 8)
    b = bytearray((delta + 20) * 8)

    vals_a = [
        [1, 2, 0x1111111111111111, 0x0123456789ABCDEF, 0xAAAAAAAAAAAAAAAA, 0x13579BDF2468ACE0],
        [3, 4, 0x2222222222222222, 0x0F0E0D0C0B0A0908, 0xBBBBBBBBBBBBBBBB, 0xCAFEBABE12345678],
    ]
    vals_b = [
        [1, 2, 0x1111111111111111, 0xFEDCBA9876543210, 0x1234567890ABCDEF, 0x0ECA86420DB97531],
        [3, 4, 0x2222222222222222, 0xF0F1F2F3F4F5F6F7, 0x02468ACE13579BDF, 0x3141592653589793],
    ]
    for rec, start in enumerate(starts):
        for rel, value in enumerate(vals_a[rec]):
            a[(start + rel) * 8:(start + rel + 1) * 8] = q(value)
        for rel, value in enumerate(vals_b[rec]):
            b[(start + delta + rel) * 8:(start + delta + rel + 1) * 8] = q(value)

    out = analyze_tail_rewrites(bytes(a), bytes(b), starts, lengths, delta, tail_start_block=2)
    assert out["nonexact_qwords"] == 6
    assert out["classes"]["6"]["tail_qwords_total"] == 8
    assert out["classes"]["6"]["tail_qwords_exact"] == 2
    assert out["classes"]["6"]["tail_qwords_rewritten"] == 6
    assert out["xor_masks"]["distinct"] >= 4
    assert out["interpretation"]["guardrail"].startswith("This does not prove encryption")
    print("PASS: synthetic P4 tail rewrite statistical profile")


if __name__ == "__main__":
    main()
