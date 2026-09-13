#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from csmc_p4_unaligned_kmer_extinction_probe import analyze


def main() -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        clip = root / "clip.bin"
        csmc = root / "csmc.bin"

        motif = b"Q7m!9Zx?"
        clip_range = b"AAAA" + motif + b"BBBBBBBBBBBB"
        csmc_range = b"CCCCCCCCCCCCCCCCCCCCCCCC"

        clip_bytes = b"prefix-clip-0123" + clip_range + b"-clip-tail"
        # Place motif at a deliberately unaligned absolute byte offset.
        csmc_bytes = b"xyz" + motif + b"-middle-" + csmc_range + b"-tail"
        clip.write_bytes(clip_bytes)
        csmc.write_bytes(csmc_bytes)

        clip_start = len(b"prefix-clip-0123")
        clip_end = clip_start + len(clip_range)
        csmc_start = len(b"xyz" + motif + b"-middle-")
        csmc_end = csmc_start + len(csmc_range)

        result = analyze(
            clip,
            csmc,
            clip_start,
            clip_end,
            csmc_start,
            csmc_end,
            [5, 6, 7, 8],
            1024,
            "python",
        )

        rows = {row["k_bytes"]: row for row in result["results"]}
        assert rows[8]["clip_range_to_full_csmc"]["matched_occurrences"] >= 1
        assert rows[8]["clip_range_to_full_csmc"]["matched_distinct_kmers"] >= 1
        assert rows[8]["clip_range_to_full_csmc"]["engine"] == "python"
        assert result["guardrails"]["raw_kmers_emitted"] is False
        assert result["guardrails"]["raw_payload_bytes_emitted"] is False

        rendered = json.dumps(result, sort_keys=True)
        assert motif.decode("ascii") not in rendered
        assert "Q7m!9Zx?" not in rendered

    print("PASS: unaligned aggregate-only k-mer probe detects synthetic byte-phase reuse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
