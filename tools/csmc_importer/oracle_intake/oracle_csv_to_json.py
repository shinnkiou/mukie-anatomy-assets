#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict

from completion_gate import validate_physical_completion_gate
from oracle_intake import (
    OracleIntakeRejected,
    SOURCE_BATCH_ID,
    SOURCE_MANIFEST_SHA256,
    validate_oracle_observation,
)
from oracle_intake_cli import read_json_with_raw_sha256

REQUIRED_COLUMNS = {
    "variant_id",
    "source_offset",
    "structural_region",
    "variant_file_sha256",
    "variant_character_blob_sha256",
    "oracle_result",
    "visible_effect",
    "error_class",
    "process_survival",
    "evidence_strength",
    "save_action_performed",
    "observer_session_id",
    "observed_at",
}

OPTIONAL_COLUMNS = {
    "error_text_sha256",
    "load_time_ms",
    "affected_visible_component",
    "viewport_result_sha256",
    "screenshot_sha256",
}

OBSERVATION_COLUMNS = {
    "oracle_result",
    "visible_effect",
    "error_class",
    "process_survival",
    "evidence_strength",
    "observer_session_id",
    "observed_at",
    *OPTIONAL_COLUMNS,
}


def _none_if_blank(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value if value else None
    return value


def _parse_false(value: Any) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"false", "0", "no"}:
        return False
    raise OracleIntakeRejected("save_action_performed must be explicitly FALSE/0/NO")


def _parse_float_or_none(value: Any) -> float | None:
    value = _none_if_blank(value)
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise OracleIntakeRejected("load_time_ms must be numeric or blank") from exc
    if result < 0:
        raise OracleIntakeRejected("load_time_ms must be nonnegative")
    return result


def _row_has_observation_data(row: Dict[str, str]) -> bool:
    for key in OBSERVATION_COLUMNS:
        if _none_if_blank(row.get(key)) is not None:
            return True
    return False


def build_observation_from_csv(
    source_manifest: Dict[str, Any],
    csv_path: Path,
    *,
    require_complete: bool,
) -> Dict[str, Any]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise OracleIntakeRejected(f"CSV missing required columns: {missing}")

        observations = []
        for csv_row in reader:
            variant_id = (_none_if_blank(csv_row.get("variant_id")) or "")
            oracle_result = _none_if_blank(csv_row.get("oracle_result"))

            if oracle_result is None:
                if _row_has_observation_data(csv_row):
                    raise OracleIntakeRejected(
                        f"{variant_id or '<blank>'}: observation fields present but oracle_result is blank"
                    )
                continue

            try:
                source_offset = int(str(csv_row.get("source_offset", "")).strip())
            except ValueError as exc:
                raise OracleIntakeRejected(f"{variant_id}: source_offset must be an integer") from exc

            row: Dict[str, Any] = {
                "variant_id": variant_id,
                "source_offset": source_offset,
                "structural_region": (_none_if_blank(csv_row.get("structural_region")) or ""),
                "variant_file_sha256": (_none_if_blank(csv_row.get("variant_file_sha256")) or ""),
                "variant_character_blob_sha256": (
                    _none_if_blank(csv_row.get("variant_character_blob_sha256")) or ""
                ),
                "oracle_result": oracle_result,
                "visible_effect": (_none_if_blank(csv_row.get("visible_effect")) or "UNKNOWN"),
                "error_class": (_none_if_blank(csv_row.get("error_class")) or "NONE"),
                "process_survival": (_none_if_blank(csv_row.get("process_survival")) or "UNKNOWN"),
                "evidence_strength": (
                    _none_if_blank(csv_row.get("evidence_strength")) or "UNKNOWN"
                ),
                "save_action_performed": _parse_false(csv_row.get("save_action_performed")),
                "observer_session_id": (
                    _none_if_blank(csv_row.get("observer_session_id")) or ""
                ),
                "observed_at": (_none_if_blank(csv_row.get("observed_at")) or ""),
            }

            for key in (
                "error_text_sha256",
                "affected_visible_component",
                "viewport_result_sha256",
                "screenshot_sha256",
            ):
                row[key] = _none_if_blank(csv_row.get(key))
            row["load_time_ms"] = _parse_float_or_none(csv_row.get("load_time_ms"))
            observations.append(row)

    observation = {
        "schema_version": "csmc_f02_mutation_oracle_30_v1",
        "source_batch_id": SOURCE_BATCH_ID,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "save_actions_performed": False,
        "semantic_promotion": False,
        "blender_emit": False,
        "runtime_mutation": False,
        "observations": observations,
    }

    validation = validate_oracle_observation(
        source_manifest,
        SOURCE_MANIFEST_SHA256,
        observation,
        require_complete=require_complete,
    )
    validate_physical_completion_gate(
        observation,
        validation,
        require_complete=require_complete,
    )
    return observation


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert the public-safe F02 manual oracle CSV into validated intake JSON."
    )
    ap.add_argument("source_manifest", type=Path)
    ap.add_argument("csv_input", type=Path)
    ap.add_argument("json_output", type=Path)
    ap.add_argument("--partial", action="store_true", help="emit only rows that have oracle_result")
    args = ap.parse_args()

    source_manifest, computed_sha = read_json_with_raw_sha256(args.source_manifest)
    if computed_sha != SOURCE_MANIFEST_SHA256:
        raise OracleIntakeRejected(
            f"source manifest raw SHA256 mismatch: expected {SOURCE_MANIFEST_SHA256}, got {computed_sha}"
        )

    observation = build_observation_from_csv(
        source_manifest,
        args.csv_input,
        require_complete=not args.partial,
    )
    args.json_output.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(observation['observations'])} validated observation rows to {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
