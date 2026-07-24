from __future__ import annotations

import re
from typing import Any


CHECKS_BY_EXECUTOR = {
    "ingest-source": {"ingest-lineage", "ingest-bounds", "record-count-min"},
    "reconcile-records": {
        "reconciliation-lineage",
        "reconciliation-conflicts",
        "record-count-min",
    },
}


def acceptance_check_errors(action: dict[str, Any]) -> list[str]:
    spec = action.get("execution")
    if not isinstance(spec, dict) or spec.get("executor") not in CHECKS_BY_EXECUTOR:
        return []
    action_id = action.get("actionId", "<unknown>")
    criteria = spec.get("acceptanceCriteria")
    checks = spec.get("acceptanceChecks")
    if not isinstance(checks, list) or not isinstance(criteria, list):
        return [f"action {action_id} deterministic execution requires acceptanceChecks"]
    if len(checks) != len(criteria):
        return [f"action {action_id} requires one machine check per acceptance criterion"]
    errors: list[str] = []
    allowed = CHECKS_BY_EXECUTOR[str(spec["executor"])]
    for index, check in enumerate(checks):
        if not isinstance(check, dict) or check.get("kind") not in allowed:
            errors.append(f"action {action_id} acceptanceChecks[{index}] is unsupported")
            continue
        if check.get("kind") == "record-count-min":
            minimum = check.get("minimum")
            if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
                errors.append(
                    f"action {action_id} acceptanceChecks[{index}].minimum is invalid"
                )
    return errors


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _ingest_lineage(artifact: dict[str, Any]) -> str:
    query = artifact.get("queryArtifact")
    records = artifact.get("records")
    if not isinstance(query, dict) or not isinstance(records, list):
        raise ValueError("ingest artifact lacks query or records")
    source_id = query.get("sourceId")
    if not isinstance(source_id, str) or not _sha256(query.get("rawArtifactSha256")):
        raise ValueError("ingest artifact lacks source and raw-response hash")
    if any(
        not isinstance(record, dict)
        or record.get("sourceId") != source_id
        or not isinstance(record.get("originFamilyId"), str)
        or not _sha256(record.get("rawRecordSha256"))
        for record in records
    ):
        raise ValueError("ingest records lack source, origin-family, or raw-record lineage")
    return f"Verified source and origin lineage for {len(records)} normalized records."


def _ingest_bounds(artifact: dict[str, Any]) -> str:
    query = artifact.get("queryArtifact")
    records = artifact.get("records")
    if not isinstance(query, dict) or not isinstance(records, list):
        raise ValueError("ingest artifact lacks bounded query metadata")
    required = ("query", "pagination", "resultCount", "truncated", "maxRecords")
    if any(key not in query for key in required) or query.get("resultCount") != len(records):
        raise ValueError("ingest artifact has incomplete or inconsistent query bounds")
    if not isinstance(query.get("truncated"), bool):
        raise ValueError("ingest artifact truncation state is not explicit")
    return (
        f"Verified query bounds: {len(records)} records, "
        f"truncated={query['truncated']}, maxRecords={query['maxRecords']}."
    )


def _reconciliation_lineage(artifact: dict[str, Any]) -> str:
    entities = artifact.get("entities")
    if not isinstance(entities, list) or artifact.get("entityCount") != len(entities):
        raise ValueError("reconciliation entity count is inconsistent")
    if any(
        not isinstance(entity, dict)
        or not isinstance(entity.get("sourceIds"), list)
        or not entity["sourceIds"]
        or not isinstance(entity.get("originFamilyIds"), list)
        or not entity["originFamilyIds"]
        or not all(_sha256(value) for value in entity.get("originRecordHashes", []))
        for entity in entities
    ):
        raise ValueError("reconciled entities lack source or origin lineage")
    return f"Verified source and origin lineage for {len(entities)} reconciled entities."


def _reconciliation_conflicts(artifact: dict[str, Any]) -> str:
    entities = artifact.get("entities")
    if not isinstance(entities, list) or any(
        not isinstance(entity, dict)
        or not isinstance(entity.get("fieldConflicts"), dict)
        or entity.get("canonicalStatus") not in {
            "single-record",
            "consensus",
            "unresolved-conflicts",
        }
        for entity in entities
    ):
        raise ValueError("reconciliation does not explicitly preserve conflict state")
    unresolved = sum(
        entity.get("canonicalStatus") == "unresolved-conflicts" for entity in entities
    )
    return f"Verified explicit conflict state; {unresolved} entities remain unresolved."


def evaluate_acceptance(
    action: dict[str, Any],
    artifact: dict[str, Any],
) -> list[str]:
    checks = action["execution"].get("acceptanceChecks", [])
    evidence: list[str] = []
    for check in checks:
        kind = check["kind"]
        if kind == "ingest-lineage":
            evidence.append(_ingest_lineage(artifact))
        elif kind == "ingest-bounds":
            evidence.append(_ingest_bounds(artifact))
        elif kind == "reconciliation-lineage":
            evidence.append(_reconciliation_lineage(artifact))
        elif kind == "reconciliation-conflicts":
            evidence.append(_reconciliation_conflicts(artifact))
        elif kind == "record-count-min":
            count = artifact.get("recordCount")
            if count is None:
                count = artifact.get("queryArtifact", {}).get("resultCount")
            if not isinstance(count, int) or count < check["minimum"]:
                raise ValueError(
                    f"acceptance check requires at least {check['minimum']} records; got {count}"
                )
            evidence.append(f"Verified record count {count} >= {check['minimum']}.")
    return evidence
