#!/usr/bin/env python3
"""Fail-closed mainline importer intake for validated controlled CSMC envelopes.

This adapter joins the legacy container probe with the controlled-fixture
envelope parser. It emits public-safe structural metadata only. It never
returns payload bytes and never authorizes semantic projection or Blender emit.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from csmc_core import probe
from csmc_controlled_envelope import EnvelopeError, parse_csmc_file

SCHEMA_VERSION = "csmc_import_intake_v0_3"
PIPELINE_STAGE = "STRUCTURAL_ONLY"


class ImportIntakeError(ValueError):
    pass


@dataclass(frozen=True)
class ImportIntake:
    schema_version: str
    source_sha256: str
    sqlite_table: str
    blob_column: str
    outer_version: int
    magic: str
    kind: str
    guid_hex: str
    inner_version: int
    logical_length: int
    aligned_logical_length: int
    alignment_extension_length: int
    logical_mod8_phase: int
    stored_length: int
    framing_remainder_length: int
    payload_offset: int
    payload_size_available: int
    frame_rule: str
    frame_rule_holds: bool
    payload_sha256: str
    raw_payload_embedded: bool
    pipeline_stage: str
    semantic_promotion_count: int
    geometry: str
    index_topology: str
    blender_emit_ready: bool

    def to_public_dict(self) -> dict:
        return asdict(self)


def inspect_csmc(path: str | Path) -> ImportIntake:
    """Validate the controlled outer route and produce semantics-free intake."""
    core = probe(path)
    try:
        env = parse_csmc_file(path)
    except EnvelopeError as exc:
        raise ImportIntakeError(f"controlled envelope rejected: {exc}") from exc

    if core.sqlite_table != "character" or core.blob_column != "character":
        raise ImportIntakeError(
            f"unsupported controlled route: {core.sqlite_table}.{core.blob_column}"
        )
    if core.outer_version is None:
        raise ImportIntakeError("outer version missing")

    checks = {
        "file_sha256": core.sha256 == env.file_sha256,
        "outer_version": int(core.outer_version) == env.outer_version,
        "magic": core.magic == env.magic,
        "kind": core.payload_kind == env.kind,
        "guid": core.guid_hex == env.guid_hex,
        "inner_version": core.inner_version == env.inner_version,
        "logical_length": core.logical_size == env.logical_length,
        "stored_length": core.stored_size == env.stored_length,
        "payload_offset": core.payload_offset == env.payload_offset,
        "payload_size_available": core.payload_size_available == env.stored_length,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ImportIntakeError(
            "core/envelope disagreement: " + ", ".join(sorted(failed))
        )
    if not env.align8_plus8_holds:
        raise ImportIntakeError("validated align8(logical)+8 frame rule does not hold")
    if env.framing_remainder_length != 8:
        raise ImportIntakeError("validated framing remainder is not 8 bytes")

    return ImportIntake(
        schema_version=SCHEMA_VERSION,
        source_sha256=core.sha256,
        sqlite_table=core.sqlite_table,
        blob_column=core.blob_column,
        outer_version=env.outer_version,
        magic=env.magic,
        kind=env.kind,
        guid_hex=env.guid_hex,
        inner_version=env.inner_version,
        logical_length=env.logical_length,
        aligned_logical_length=env.aligned_logical_length,
        alignment_extension_length=env.alignment_extension_length,
        logical_mod8_phase=env.logical_length % 8,
        stored_length=env.stored_length,
        framing_remainder_length=env.framing_remainder_length,
        payload_offset=env.payload_offset,
        payload_size_available=core.payload_size_available,
        frame_rule="stored_length = align8(logical_length) + 8",
        frame_rule_holds=True,
        payload_sha256=env.payload_sha256,
        raw_payload_embedded=False,
        pipeline_stage=PIPELINE_STAGE,
        semantic_promotion_count=0,
        geometry="unresolved",
        index_topology="unresolved",
        blender_emit_ready=False,
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Public-safe controlled CSMC importer intake"
    )
    ap.add_argument("path", type=Path)
    ns = ap.parse_args()
    try:
        result = inspect_csmc(ns.path)
    except (ImportIntakeError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "error": str(exc)}, indent=2))
        return 2
    print(
        json.dumps(
            {"status": "ACCEPTED_STRUCTURAL_ONLY", **result.to_public_dict()},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
