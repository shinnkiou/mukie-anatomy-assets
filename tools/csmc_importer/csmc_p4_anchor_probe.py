from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import struct
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

CSF_MAGIC = b"CSFCHUNK"
CHNK_EXTA = b"CHNKExta"
CHNK_FOOT = b"CHNKFoot"
C3D_MAGIC = b"CLIP_STUDIO_3D_DATA2"


@dataclass
class SurfaceMeta:
    source: str
    container: str
    selector_kind: str | None
    table: str | None
    column: str | None
    external_id: str | None
    blob_size: int
    blob_sha256: str
    magic: str | None
    kind: str | None
    guid_hex: str | None
    inner_version: int | None
    logical_size: int | None
    stored_size: int | None
    payload_offset: int | None
    payload_size_available: int | None
    stored_minus_align8_logical: int | None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_lp(blob: bytes, off: int) -> tuple[bytes, int]:
    if off + 4 > len(blob):
        raise ValueError("truncated LP length")
    n = struct.unpack_from("<I", blob, off)[0]
    start = off + 4
    end = start + n
    if end > len(blob):
        raise ValueError("truncated LP value")
    return blob[start:end], end


def parse_c3d(blob: bytes) -> dict:
    out = {
        "magic": None,
        "kind": None,
        "guid_hex": None,
        "inner_version": None,
        "logical_size": None,
        "stored_size": None,
        "payload_offset": None,
        "payload_size_available": None,
        "stored_minus_align8_logical": None,
    }
    try:
        magic, off = read_lp(blob, 0)
        kind, off = read_lp(blob, off)
        out["magic"] = magic.decode("ascii", "replace")
        out["kind"] = kind.decode("ascii", "replace")
        if magic == C3D_MAGIC and off + 28 <= len(blob):
            out["guid_hex"] = blob[off:off + 16].hex()
            version, logical, stored = struct.unpack_from("<III", blob, off + 16)
            out["inner_version"] = version
            out["logical_size"] = logical
            out["stored_size"] = stored
            out["payload_offset"] = off + 28
            out["payload_size_available"] = len(blob) - (off + 28)
            out["stored_minus_align8_logical"] = stored - (((logical + 7) // 8) * 8)
    except Exception:
        pass
    return out


def iter_chunks(raw: bytes) -> Iterable[tuple[int, bytes, bytes]]:
    if not raw.startswith(CSF_MAGIC):
        raise ValueError("not a CSFCHUNK file")
    pos = 24
    while pos + 16 <= len(raw):
        tag = raw[pos:pos + 8]
        size = int.from_bytes(raw[pos + 8:pos + 16], "big")
        start = pos + 16
        end = start + size
        if end > len(raw):
            raise ValueError(f"chunk exceeds file at offset {pos}")
        yield pos, tag, raw[start:end]
        pos = end
        if tag == CHNK_FOOT:
            break


def parse_exta(payload: bytes) -> tuple[str, bytes]:
    if len(payload) < 16:
        raise ValueError("truncated CHNKExta")
    n = int.from_bytes(payload[:8], "big")
    p = 8
    if p + n + 8 > len(payload):
        raise ValueError("truncated CHNKExta id")
    ext_id = payload[p:p + n].decode("ascii", "replace")
    p += n
    m = int.from_bytes(payload[p:p + 8], "big")
    p += 8
    blob = payload[p:p + m]
    if len(blob) != m:
        raise ValueError("truncated CHNKExta data")
    return ext_id, blob


def load_clip_surface(path: Path, wanted_kind: str | None) -> tuple[bytes, SurfaceMeta]:
    raw = path.read_bytes()
    candidates: list[tuple[str, bytes, dict]] = []
    for _, tag, payload in iter_chunks(raw):
        if tag != CHNK_EXTA:
            continue
        ext_id, blob = parse_exta(payload)
        meta = parse_c3d(blob)
        if meta["magic"] == C3D_MAGIC.decode("ascii"):
            candidates.append((ext_id, blob, meta))

    if not candidates:
        raise ValueError("no CELSYS 3D CHNKExta payload found")

    selected = None
    if wanted_kind is not None:
        selected = next((c for c in candidates if c[2]["kind"] == wanted_kind), None)
        if selected is None:
            kinds = sorted({str(c[2]["kind"]) for c in candidates})
            raise ValueError(f"requested kind {wanted_kind!r} not found; available={kinds}")
    elif len(candidates) == 1:
        selected = candidates[0]
    else:
        kinds = [c[2]["kind"] for c in candidates]
        raise ValueError(f"multiple CELSYS 3D payloads found; specify --kind. available={kinds}")

    ext_id, blob, parsed = selected
    sm = SurfaceMeta(
        source=str(path),
        container="clip_csfchunk",
        selector_kind=wanted_kind,
        table=None,
        column=None,
        external_id=ext_id,
        blob_size=len(blob),
        blob_sha256=sha256_bytes(blob),
        **parsed,
    )
    return blob, sm


def load_sqlite_surface(path: Path, wanted_kind: str | None) -> tuple[bytes, SurfaceMeta]:
    con = sqlite3.connect(str(path))
    try:
        tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
        candidates = [
            ("character", "character"),
            ("character", "catalog_data"),
            ("catalog_character", "catalog_data"),
        ]
        found: list[tuple[str, str, bytes, dict]] = []
        for table, col in candidates:
            if table not in tables:
                continue
            cols = {r[1] for r in con.execute(f'pragma table_info("{table}")')}
            if col not in cols:
                continue
            row = con.execute(f'select "{col}" from "{table}" limit 1').fetchone()
            if not row or row[0] is None:
                continue
            blob = bytes(row[0])
            parsed = parse_c3d(blob)
            if parsed["magic"] == C3D_MAGIC.decode("ascii"):
                found.append((table, col, blob, parsed))

        if not found:
            raise ValueError("no supported CELSYS 3D SQLite payload found")

        selected = None
        if wanted_kind is not None:
            selected = next((c for c in found if c[3]["kind"] == wanted_kind), None)
            if selected is None:
                kinds = sorted({str(c[3]["kind"]) for c in found})
                raise ValueError(f"requested kind {wanted_kind!r} not found; available={kinds}")
        elif len(found) == 1:
            selected = found[0]
        else:
            kinds = [c[3]["kind"] for c in found]
            raise ValueError(f"multiple CELSYS 3D SQLite payloads found; specify --kind. available={kinds}")

        table, col, blob, parsed = selected
        sm = SurfaceMeta(
            source=str(path),
            container="sqlite",
            selector_kind=wanted_kind,
            table=table,
            column=col,
            external_id=None,
            blob_size=len(blob),
            blob_sha256=sha256_bytes(blob),
            **parsed,
        )
        return blob, sm
    finally:
        con.close()


def load_surface(path: str | Path, wanted_kind: str | None = None) -> tuple[bytes, SurfaceMeta]:
    p = Path(path)
    raw_head = p.read_bytes()[:24]
    if raw_head.startswith(CSF_MAGIC):
        return load_clip_surface(p, wanted_kind)
    if raw_head.startswith(b"SQLite format 3\x00"):
        return load_sqlite_surface(p, wanted_kind)

    blob = p.read_bytes()
    parsed = parse_c3d(blob)
    if parsed["magic"] != C3D_MAGIC.decode("ascii"):
        raise ValueError("raw input is not a CELSYS 3D payload")
    if wanted_kind is not None and parsed["kind"] != wanted_kind:
        raise ValueError(f"requested kind {wanted_kind!r} does not match raw blob kind {parsed['kind']!r}")
    return blob, SurfaceMeta(
        source=str(p),
        container="raw_blob",
        selector_kind=wanted_kind,
        table=None,
        column=None,
        external_id=None,
        blob_size=len(blob),
        blob_sha256=sha256_bytes(blob),
        **parsed,
    )


def stored_payload(blob: bytes, meta: SurfaceMeta) -> bytes:
    if meta.payload_offset is None:
        raise ValueError("CELSYS payload offset unavailable")
    payload = blob[meta.payload_offset:]
    if meta.stored_size is not None:
        if meta.stored_size > len(payload):
            raise ValueError("stored_size exceeds available payload")
        payload = payload[:meta.stored_size]
    return payload


def mix64(x: int) -> int:
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return x ^ (x >> 31)


def sampled_unique_blocks(payload: bytes, mask_bits: int) -> tuple[dict[int, int], dict]:
    if mask_bits < 0 or mask_bits > 24:
        raise ValueError("mask_bits must be in 0..24")
    block_count = len(payload) // 8
    mask = (1 << mask_bits) - 1 if mask_bits else 0
    first: dict[int, int] = {}
    counts: dict[int, int] = {}
    sampled_occurrences = 0
    view = memoryview(payload)[:block_count * 8]
    for i, (value,) in enumerate(struct.iter_unpack("<Q", view)):
        if mask and (mix64(value) & mask) != 0:
            continue
        sampled_occurrences += 1
        if value in counts:
            counts[value] += 1
        else:
            counts[value] = 1
            first[value] = i
    unique = {v: first[v] for v, count in counts.items() if count == 1}
    return unique, {
        "total_blocks": block_count,
        "mask_bits": mask_bits,
        "sampled_occurrences": sampled_occurrences,
        "sampled_unique_values": len(unique),
    }


def expand_equal_run(a: memoryview, b: memoryview, ai: int, bi: int) -> tuple[int, int, int]:
    na = len(a) // 8
    nb = len(b) // 8
    left = 0
    while ai - left - 1 >= 0 and bi - left - 1 >= 0:
        aa = (ai - left - 1) * 8
        bb = (bi - left - 1) * 8
        if a[aa:aa + 8] != b[bb:bb + 8]:
            break
        left += 1
    right = 0
    while ai + right + 1 < na and bi + right + 1 < nb:
        aa = (ai + right + 1) * 8
        bb = (bi + right + 1) * 8
        if a[aa:aa + 8] != b[bb:bb + 8]:
            break
        right += 1
    return ai - left, bi - left, left + 1 + right


def anchor_relation(pa: bytes, pb: bytes, mask_bits: int, top_peaks: int, runs_per_peak: int) -> dict:
    ia, sa = sampled_unique_blocks(pa, mask_bits)
    ib, sb = sampled_unique_blocks(pb, mask_bits)
    shared = set(ia).intersection(ib)
    deltas = Counter(ib[v] - ia[v] for v in shared)
    peaks = []
    av = memoryview(pa)
    bv = memoryview(pb)

    for delta, count in deltas.most_common(top_peaks):
        anchors = [(ia[v], ib[v]) for v in shared if ib[v] - ia[v] == delta]
        seen_runs: set[tuple[int, int, int]] = set()
        runs = []
        for ai, bi in anchors:
            run = expand_equal_run(av, bv, ai, bi)
            if run in seen_runs:
                continue
            seen_runs.add(run)
            a_start, b_start, blocks = run
            runs.append({
                "a_start_block": a_start,
                "b_start_block": b_start,
                "delta_blocks_b_minus_a": b_start - a_start,
                "length_blocks": blocks,
                "length_bytes": blocks * 8,
            })
        runs.sort(key=lambda r: (-r["length_blocks"], r["a_start_block"], r["b_start_block"]))
        peaks.append({
            "delta_blocks_b_minus_a": delta,
            "delta_bytes": delta * 8,
            "sampled_unique_anchor_count": count,
            "longest_exact_runs": runs[:runs_per_peak],
        })

    union = len(set(ia).union(ib))
    return {
        "a_sampling": sa,
        "b_sampling": sb,
        "shared_sampled_unique_anchors": len(shared),
        "sampled_unique_anchor_jaccard": len(shared) / union if union else None,
        "top_position_delta_peaks": peaks,
    }


def compare_surfaces(
    a_path: str | Path,
    b_path: str | Path,
    a_kind: str | None,
    b_kind: str | None,
    mask_bits: int,
    top_peaks: int,
    runs_per_peak: int,
) -> dict:
    a_blob, a_meta = load_surface(a_path, a_kind)
    b_blob, b_meta = load_surface(b_path, b_kind)
    pa = stored_payload(a_blob, a_meta)
    pb = stored_payload(b_blob, b_meta)
    return {
        "probe_version": "csmc_p4_anchor_probe_v0.1",
        "scope": "metadata_and_structural_fingerprints_only",
        "a": asdict(a_meta),
        "b": asdict(b_meta),
        "payload_relation": {
            "a_stored_payload_bytes": len(pa),
            "b_stored_payload_bytes": len(pb),
            "length_delta_b_minus_a": len(pb) - len(pa),
            "anchor_relation": anchor_relation(pa, pb, mask_bits, top_peaks, runs_per_peak),
        },
        "interpretation_guardrail": (
            "Matching opaque 8-byte blocks/runs are structural fingerprints only. "
            "They do not identify a transform, cipher, compressor, vertex/index layout, or DRM mechanism."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Read-only structural anchor probe for CELSYS 3D payloads in .clip, CSMC/CS3C SQLite, or raw blobs"
    )
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--a-kind", default=None, help="CELSYS kind to select from input A, e.g. catalog_character")
    ap.add_argument("--b-kind", default=None, help="CELSYS kind to select from input B, e.g. character")
    ap.add_argument("--mask-bits", type=int, default=8, help="Sample roughly 1/2**N block values (0 = all)")
    ap.add_argument("--top-peaks", type=int, default=10)
    ap.add_argument("--runs-per-peak", type=int, default=5)
    ap.add_argument("--out", default=None, help="Optional JSON output path")
    args = ap.parse_args()

    result = compare_surfaces(
        args.a,
        args.b,
        args.a_kind,
        args.b_kind,
        args.mask_bits,
        args.top_peaks,
        args.runs_per_peak,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
