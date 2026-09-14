from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Mapping

from oracle_intake import OracleIntakeRejected


def _parse_offset_aware_iso8601(value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise OracleIntakeRejected("observed_at required")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise OracleIntakeRejected("observed_at must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise OracleIntakeRejected("observed_at must include a UTC offset")


def validate_physical_completion_gate(
    observation: Mapping[str, Any],
    validation_result: Mapping[str, Any],
    *,
    require_complete: bool,
) -> Dict[str, Any]:
    """Apply the physical-completion gate after provenance/schema validation.

    The base validator intentionally understands UNKNOWN as a legal classification.
    This gate prevents a 30-row placeholder/ambiguous sheet from being reported as a
    completed physical oracle. Partial checkpoints may still contain UNKNOWN values,
    but every submitted row must carry an offset-aware observation timestamp.
    """

    rows = observation.get("observations", [])
    unresolved_rows = []
    direct_rows = 0

    for row in rows:
        _parse_offset_aware_iso8601(row.get("observed_at"))

        reasons = []
        if row.get("oracle_result") == "UNKNOWN":
            reasons.append("oracle_result")
        if row.get("visible_effect") == "UNKNOWN":
            reasons.append("visible_effect")
        if row.get("process_survival") == "UNKNOWN":
            reasons.append("process_survival")
        if row.get("evidence_strength") != "DIRECT_PHYSICAL_OBSERVATION":
            reasons.append("evidence_strength")

        if row.get("evidence_strength") == "DIRECT_PHYSICAL_OBSERVATION":
            direct_rows += 1
        if reasons:
            unresolved_rows.append({"variant_id": row.get("variant_id"), "reasons": reasons})

    coverage_complete = bool(validation_result.get("complete"))
    physical_complete = coverage_complete and not unresolved_rows and direct_rows == len(rows)

    if require_complete:
        if not coverage_complete:
            raise OracleIntakeRejected("physical completion requires full M01..M30 coverage")
        if unresolved_rows:
            summary = ", ".join(
                f"{item['variant_id']}:{'/'.join(item['reasons'])}" for item in unresolved_rows
            )
            raise OracleIntakeRejected(
                "physical completion cannot contain unresolved/non-direct rows: " + summary
            )

    return {
        "coverage_complete": coverage_complete,
        "physical_complete": physical_complete,
        "observed_count": len(rows),
        "direct_observation_count": direct_rows,
        "unresolved_row_count": len(unresolved_rows),
        "unresolved_rows": unresolved_rows,
        "classification": (
            "PHYSICAL_ORACLE_COMPLETE"
            if physical_complete
            else "PHYSICAL_ORACLE_PARTIAL_OR_UNRESOLVED"
        ),
    }
