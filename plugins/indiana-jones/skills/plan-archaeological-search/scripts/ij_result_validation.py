from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from ij_journal import value_sha256
from ij_safety import SENSITIVITIES


DISCLOSURES = {"public", "restricted", "heritage-authority-only"}
HEX_DIGITS = set("0123456789abcdef")
SENSITIVITY_PRIORITY = {
    "public": 0,
    "restricted": 1,
    "non-public": 2,
    "vulnerable": 3,
    "sacred": 4,
    "burial": 5,
}


def _string_array(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        qualifier = "non-empty " if not allow_empty else ""
        raise ValueError(f"{label} must be a {qualifier}string array")
    return value


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validated_source_snapshots(
    value: Any,
    source_map: dict[str, dict[str, Any]],
    action_sources: set[str],
) -> tuple[set[str], set[str]]:
    if value is None:
        return set(), set()
    if not isinstance(value, list):
        raise ValueError("sourceSnapshots must be an array")
    snapshot_ids: set[str] = set()
    source_ids: set[str] = set()
    for index, snapshot in enumerate(value):
        if not isinstance(snapshot, dict):
            raise ValueError(f"sourceSnapshots[{index}] must be an object")
        source_id = snapshot.get("sourceId")
        source = source_map.get(source_id)
        if source is None or source_id not in action_sources:
            raise ValueError(
                f"sourceSnapshots[{index}] cites a source not declared by the action"
            )
        digest = snapshot.get("contentSha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in HEX_DIGITS for character in digest)
        ):
            raise ValueError(
                f"sourceSnapshots[{index}].contentSha256 must be a lowercase SHA-256"
            )
        content = snapshot.get("content")
        if not isinstance(content, str) or not content:
            raise ValueError(
                f"sourceSnapshots[{index}].content must preserve the captured source text"
            )
        if hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
            raise ValueError(
                f"sourceSnapshots[{index}].contentSha256 does not match content"
            )
        expected_id = f"snapshot:{source_id}:{digest}"
        if snapshot.get("snapshotId") != expected_id:
            raise ValueError(
                f"sourceSnapshots[{index}].snapshotId does not bind source and content hash"
            )
        if snapshot.get("originFamilyId") != source.get("originFamilyId"):
            raise ValueError(
                f"sourceSnapshots[{index}].originFamilyId does not match the plan"
            )
        if snapshot.get("accessBasis") != source.get("accessBasis"):
            raise ValueError(
                f"sourceSnapshots[{index}].accessBasis does not match the plan"
            )
        if not _valid_timestamp(snapshot.get("retrievedAt")):
            raise ValueError(
                f"sourceSnapshots[{index}].retrievedAt requires a timezone-aware ISO timestamp"
            )
        if expected_id in snapshot_ids:
            raise ValueError(f"sourceSnapshots[{index}].snapshotId is duplicated")
        snapshot_ids.add(expected_id)
        source_ids.add(source_id)
    return snapshot_ids, source_ids


def validate_agent_result(
    result_path: Path,
    action: dict[str, Any],
    plan: dict[str, Any],
    *,
    allowed_source_snapshot_ids: set[str] | None = None,
    allowed_normalized_record_ids: set[str] | None = None,
) -> dict[str, Any]:
    try:
        value = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"research result is invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("research result root must be an object")
    if value.get("schemaVersion") != "research-result-2.0":
        raise ValueError("manual research result must use research-result-2.0")
    if value.get("actionId") != action.get("actionId"):
        raise ValueError("research result actionId does not match the active action")
    observations = value.get("observations")
    if not isinstance(observations, list):
        raise ValueError("research result observations must be an array")
    negative = _string_array(value.get("negativeResults"), "negativeResults")
    warnings = _string_array(value.get("warnings"), "warnings")
    errors = _string_array(value.get("errors"), "errors")
    source_snapshots = _string_array(
        value.get("sourceSnapshotIds"),
        "sourceSnapshotIds",
        allow_empty=False,
    )
    normalized_ids = _string_array(
        value.get("normalizedRecordIds"),
        "normalizedRecordIds",
    )
    acceptance = _string_array(
        value.get("acceptanceEvidence"),
        "acceptanceEvidence",
        allow_empty=False,
    )
    criteria = action.get("execution", {}).get("acceptanceCriteria", [])
    if len(acceptance) != len(criteria):
        raise ValueError("research result requires one acceptance evidence item per criterion")
    source_map = {
        source.get("sourceId"): source
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    known_sources = set(source_map)
    action_sources = {
        source_id for source_id in action.get("sourceIds", []) if isinstance(source_id, str)
    }
    local_snapshot_ids, local_snapshot_sources = _validated_source_snapshots(
        value.get("sourceSnapshots"),
        source_map,
        action_sources,
    )
    cited: set[str] = set()
    origin_families: set[str] = set()
    claim_ids = {
        "negative:"
        + value_sha256(
            {
                "statement": statement.strip(),
                "sourceSnapshotIds": sorted(set(source_snapshots)),
            }
        )
        for statement in negative
    }
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            raise ValueError(f"observation {index} must be an object")
        if not isinstance(observation.get("statement"), str) or not observation[
            "statement"
        ].strip():
            raise ValueError(f"observation {index} requires a statement")
        sources = _string_array(
            observation.get("sourceIds"),
            f"observation {index}.sourceIds",
            allow_empty=False,
        )
        if any(source_id not in known_sources for source_id in sources):
            raise ValueError(f"observation {index} cites an unknown source")
        if action_sources and not action_sources.intersection(sources):
            raise ValueError(f"observation {index} cites no source declared by the action")
        cited.update(sources)
        origins = _string_array(
            observation.get("originFamilyIds", []),
            f"observation {index}.originFamilyIds",
            allow_empty=False,
        )
        expected_origins = {
            source_map[source_id].get("originFamilyId")
            for source_id in sources
            if isinstance(source_map[source_id].get("originFamilyId"), str)
        }
        if set(origins) != expected_origins:
            raise ValueError(
                f"observation {index} originFamilyIds do not match its cited sources"
            )
        origin_families.update(origins)
        claim_ids.add(
            "observation:"
            + value_sha256(
                {
                    "statement": observation["statement"].strip(),
                    "sourceIds": sorted(set(sources)),
                    "originFamilyIds": sorted(set(origins)),
                }
            )
        )
    if not observations and not negative:
        raise ValueError("research result requires an observation or negative result")
    permitted_snapshots = set(allowed_source_snapshot_ids or set())
    permitted_snapshots.update(local_snapshot_ids)
    if any(snapshot not in permitted_snapshots for snapshot in source_snapshots):
        raise ValueError("sourceSnapshotIds contain an unresolved or unsealed reference")
    for source_id in cited:
        prefix = f"snapshot:{source_id}:"
        if not any(
            snapshot == f"snapshot:{source_id}" or snapshot.startswith(prefix)
            for snapshot in source_snapshots
        ):
            raise ValueError(f"sourceSnapshotIds do not cover cited source {source_id}")
    permitted_records = allowed_normalized_record_ids or set()
    if any(record_id not in permitted_records for record_id in normalized_ids):
        raise ValueError("normalizedRecordIds contain an unresolved or unsealed reference")
    for key in ("methodVersion", "adapterVersion"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(f"research result {key} is required")
    sensitivity = value.get("resultSensitivity")
    if sensitivity not in SENSITIVITIES:
        raise ValueError("research result has invalid resultSensitivity")
    disclosure = value.get("disclosureDecision")
    if disclosure not in DISCLOSURES:
        raise ValueError("research result has invalid disclosureDecision")
    case = plan.get("case", {})
    case_disclosure = case.get("disclosure") if isinstance(case, dict) else None
    if case_disclosure != "public" and disclosure == "public":
        raise ValueError("restricted case result cannot silently become public")
    evidence_sources = set(cited) | local_snapshot_sources
    for source_id in known_sources:
        prefix = f"snapshot:{source_id}:"
        if any(
            snapshot == f"snapshot:{source_id}" or snapshot.startswith(prefix)
            for snapshot in source_snapshots
        ):
            evidence_sources.add(source_id)
    protected_sources = {
        source_id
        for source_id in evidence_sources
        if source_map[source_id].get("sensitivity") != "public"
    }
    if protected_sources and (sensitivity == "public" or disclosure == "public"):
        raise ValueError(
            "result cannot publish evidence from a non-public source: "
            + ", ".join(sorted(protected_sources))
        )
    required_sensitivity = max(
        (
            source_map[source_id].get("sensitivity", "restricted")
            for source_id in evidence_sources
        ),
        default="public",
        key=lambda item: SENSITIVITY_PRIORITY.get(
            item,
            SENSITIVITY_PRIORITY["restricted"],
        ),
    )
    if (
        SENSITIVITY_PRIORITY.get(sensitivity, 0)
        < SENSITIVITY_PRIORITY.get(required_sensitivity, 1)
    ):
        raise ValueError(
            "resultSensitivity downgrades source sensitivity "
            f"{required_sensitivity!r}"
        )
    if (
        required_sensitivity in {"non-public", "vulnerable", "sacred", "burial"}
        and disclosure != "heritage-authority-only"
    ):
        raise ValueError(
            "protected source evidence requires heritage-authority-only disclosure"
        )
    authorization = value.get("authorization")
    required = action.get("authorization", {}).get("required")
    if required != "none":
        if not isinstance(authorization, dict):
            raise ValueError("research result requires its authorization record")
        if authorization != action.get("authorization"):
            raise ValueError("research result authorization is stale or mismatched")
    return {
        "observations": len(observations),
        "negativeResults": negative,
        "warnings": warnings,
        "errors": errors,
        "sourceSnapshotIds": source_snapshots,
        "normalizedRecordIds": normalized_ids,
        "originFamilyIds": sorted(origin_families),
        "claimIds": sorted(claim_ids),
        "objectIds": [],
        "contradictionIds": [],
        "citedSourceIds": sorted(cited),
        "methodVersion": value["methodVersion"],
        "adapterVersion": value["adapterVersion"],
        "resultSensitivity": sensitivity,
        "disclosureDecision": disclosure,
        "authorization": authorization if isinstance(authorization, dict) else None,
        "acceptanceEvidence": acceptance,
    }


def build_result_seal_context(
    state: dict[str, Any],
    action: dict[str, Any],
    attempt: dict[str, Any],
    metadata: dict[str, Any],
    evidence: list[str],
    budget_usage: dict[str, Any],
    retained_bytes: int,
    ended_at: float,
) -> dict[str, Any]:
    return {
        "runId": state["runId"],
        "sourcePlanSha256": state["sourcePlanSha256"],
        "journalHeadSha256": state["journalHeadSha256"],
        "actionId": action["actionId"],
        "actionSha256": value_sha256(action),
        "attemptId": attempt["attemptId"],
        "commandId": attempt["idempotencyKey"],
        "inputHashes": {
            "execution": value_sha256(action["execution"]),
            "acceptanceEvidence": value_sha256(evidence),
        },
        "adapterVersion": metadata["adapterVersion"],
        "methodVersion": metadata["methodVersion"],
        "startedAt": attempt["startedAt"],
        "endedAt": ended_at,
        "consumedBudget": {
            "seconds": max(0.0, ended_at - float(attempt["startedAt"])),
            "retainedBytes": retained_bytes,
        },
        "budgetUsage": budget_usage,
        "sourceSnapshotIds": metadata["sourceSnapshotIds"],
        "normalizedRecordIds": metadata["normalizedRecordIds"],
        "warnings": metadata["warnings"],
        "errors": metadata["errors"],
        "authorization": metadata["authorization"],
        "resultSensitivity": metadata["resultSensitivity"],
        "disclosureDecision": metadata["disclosureDecision"],
    }


def deterministic_result_metadata(
    plan: dict[str, Any],
    action: dict[str, Any],
    source_ids: list[str],
    *,
    source_snapshot_ids: set[str] | None = None,
) -> dict[str, Any]:
    case = plan.get("case")
    case_disclosure = case.get("disclosure") if isinstance(case, dict) else None
    if case_disclosure not in DISCLOSURES:
        raise ValueError("deterministic result requires a declared case disclosure")
    source_map = {
        source.get("sourceId"): source
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    source_sensitivities = [
        source_map[source_id].get("sensitivity", "restricted")
        for source_id in source_ids
        if source_id in source_map
    ]
    source_sensitivity = max(
        source_sensitivities or ["public"],
        key=lambda item: SENSITIVITY_PRIORITY.get(
            item,
            SENSITIVITY_PRIORITY["restricted"],
        ),
    )
    if case_disclosure != "public":
        result_sensitivity = "restricted"
        disclosure = case_disclosure
    elif source_sensitivity == "public":
        result_sensitivity = "public"
        disclosure = "public"
    else:
        result_sensitivity = source_sensitivity
        disclosure = (
            "heritage-authority-only"
            if source_sensitivity in {"non-public", "vulnerable", "sacred", "burial"}
            else "restricted"
        )
    return {
        "sourceSnapshotIds": sorted(
            source_snapshot_ids
            if source_snapshot_ids is not None
            else {f"snapshot:{source_id}" for source_id in source_ids}
        ),
        "normalizedRecordIds": [],
        "originFamilyIds": [],
        "claimIds": [],
        "objectIds": [],
        "contradictionIds": [],
        "warnings": [],
        "errors": [],
        "methodVersion": str(action.get("method")),
        "adapterVersion": str(action.get("execution", {}).get("executor")),
        "resultSensitivity": result_sensitivity,
        "disclosureDecision": disclosure,
        "authorization": action.get("authorization"),
    }
