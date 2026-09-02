from __future__ import annotations

import struct
import tempfile
from pathlib import Path

MASK = (1 << 64) - 1


def lp(b: bytes) -> bytes:
    return struct.pack('<I', len(b)) + b


def make_payload(blocks: int = 131072) -> bytes:
    return b''.join(
        struct.pack('<Q', ((i * 0x9E3779B97F4A7C15) ^ 0xD1B54A32D192ED03) & MASK)
        for i in range(blocks)
    )


def make_blob(payload: bytes, logical: int | None = None) -> bytes:
    if logical is None:
        logical = max(0, len(payload) - 8)
    return (
        lp(b'CLIP_STUDIO_3D_DATA2')
        + lp(b'character')
        + bytes.fromhex('00112233445566778899aabbccddeeff')
        + struct.pack('<III', 2, logical, len(payload))
        + payload
    )


def main() -> None:
    import runtime_blob_compare as mod

    payload = make_payload()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        a = td / 'a.bin'
        ident = td / 'ident.bin'
        mut = td / 'mut.bin'
        ins = td / 'ins.bin'
        base = make_blob(payload)
        a.write_bytes(base)
        ident.write_bytes(base)

        mutated = bytearray(base)
        payload_off = 65
        mutated[payload_off + 1000] ^= 1
        mut.write_bytes(mutated)

        insert_at_payload = 131072
        new_payload = payload[:insert_at_payload] + b'INSERT08' + payload[insert_at_payload:]
        ins.write_bytes(make_blob(new_payload, logical=(len(payload) - 8) + 8))

        r0 = mod.compare(a, ident)
        assert r0['exact_equal'] is True
        assert r0['a']['stored_minus_align8_logical'] == 8
        assert r0['payload_relation']['aligned_8byte_equal_fraction'] == 1.0
        assert r0['payload_relation']['sampled_anchor_relation']['top_position_delta_peaks'][0]['delta_blocks_b_minus_a'] == 0

        r1 = mod.compare(a, mut)
        assert r1['exact_equal'] is False
        assert r1['different_bytes_including_length_delta'] == 1
        assert r1['first_difference'] == payload_off + 1000
        assert r1['payload_relation']['sampled_anchor_relation']['top_position_delta_peaks'][0]['delta_blocks_b_minus_a'] == 0

        r2 = mod.compare(a, ins)
        peaks = r2['payload_relation']['sampled_anchor_relation']['top_position_delta_peaks']
        assert r2['length_delta_b_minus_a'] == 8
        assert peaks[0]['delta_blocks_b_minus_a'] == 1
        assert any(p['delta_blocks_b_minus_a'] == 0 for p in peaks)
        print('PASS runtime blob comparator identity/mutation/insertion synthetic tests')
        print('shared anchors=', r2['payload_relation']['sampled_anchor_relation']['shared_unique_anchors'])
        print('insertion peaks=', peaks[:3])


if __name__ == '__main__':
    main()
