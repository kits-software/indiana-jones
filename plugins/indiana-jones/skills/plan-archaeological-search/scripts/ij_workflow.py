from __future__ import annotations

from pathlib import Path
from typing import Any

from ij_artifacts import plan_sha256
from ij_ingest import SUPPORTED_FORMATS
from ij_journal import value_sha256
from ij_runtime import execute_deterministic_action, next_task_packet, run_status


DETERMINISTIC_EXECUTORS = {"ingest-source", "reconcile-records"}


def discover_declared_sources(plan: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for source in plan.get("sources", []):
        if not isinstance(source, dict):
            continue
        acquisition = source.get("acquisition")
        adapter = acquisition.get("format") if isinstance(acquisition, dict) else None
        public = source.get("accessBasis") == "public"
        candidates.append(
            {
                "sourceId": source.get("sourceId"),
                "title": source.get("title"),
                "recordType": source.get("recordType"),
                "accessBasis": source.get("accessBasis"),
                "sensitivity": source.get("sensitivity"),
                "adapter": adapter,
                "ingestionEligible": public and adapter in SUPPORTED_FORMATS,
                "decision": (
                    "eligible-for-bounded-read"
                    if public and adapter in SUPPORTED_FORMATS
                    else "requires-agent-review-or-adapter-selection"
                ),
            }
        )
    return {
        "schemaVersion": "archaeological-source-discovery-1.0",
        "sourcePlanSha256": plan_sha256(plan),
        "supportedAdapters": sorted(SUPPORTED_FORMATS),
        "candidates": candidates,
        "warning": "Discovery records capability; it does not grant access or licence.",
    }


def extract_record_claims(artifact: dict[str, Any]) -> dict[str, Any]:
    records = artifact.get("records")
    if not isinstance(records, list):
        raise ValueError("normalized artifact must contain a records array")
    claims: list[dict[str, Any]] = []
    claim_fields = {
        "objectClass": "typed-as",
        "material": "made-of",
        "chronology": "dated-to",
        "archaeologicalContext": "reported-context",
        "repository": "held-by",
        "accessionNumber": "catalogued-as",
    }
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("normalized records must contain objects")
        for field, predicate in claim_fields.items():
            value = record.get(field)
            if value is None:
                continue
            basis = {
                "recordId": record.get("recordId"),
                "sourceId": record.get("sourceId"),
                "rawRecordSha256": record.get("rawRecordSha256"),
                "field": field,
                "value": value,
            }
            claims.append(
                {
                    "claimId": f"claim_{value_sha256(basis)[:20]}",
                    "subjectRecordId": record.get("recordId"),
                    "predicate": predicate,
                    "value": value,
                    "sourceId": record.get("sourceId"),
                    "recordLocator": field,
                    "extractionMethod": "deterministic-field-mapping",
                    "extractionVersion": "1.0",
                    "assertionStatus": "reported-unreviewed",
                    "rawRecordSha256": record.get("rawRecordSha256"),
                }
            )
    return {
        "schemaVersion": "archaeological-claims-1.0",
        "sourceArtifactSha256": value_sha256(artifact),
        "claimCount": len(claims),
        "claims": claims,
    }


def advance_run(run_dir: Path, limit: int = 4) -> dict[str, Any]:
    packet = next_task_packet(run_dir, limit)
    deterministic = [
        action
        for action in packet.get("recommendedBatch", [])
        if action.get("execution", {}).get("executor") in DETERMINISTIC_EXECUTORS
    ]
    results: list[dict[str, Any]] = []
    for action in deterministic:
        result = execute_deterministic_action(run_dir, action["actionId"])
        results.append(
            {
                "actionId": action["actionId"],
                "result": result["result"],
            }
        )
    next_packet = next_task_packet(run_dir, limit)
    return {
        "schemaVersion": "archaeological-run-advance-1.0",
        "executed": results,
        "taskPacket": next_packet,
        "pauseReason": (
            None
            if results
            else packet.get("stopReason") or "agent-action-required"
        ),
    }


def run_until_pause(run_dir: Path, max_steps: int = 100, limit: int = 4) -> dict[str, Any]:
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    executed: list[dict[str, Any]] = []
    for _ in range(max_steps):
        advanced = advance_run(run_dir, limit)
        executed.extend(advanced["executed"])
        if not advanced["executed"]:
            return {
                "schemaVersion": "archaeological-run-loop-1.0",
                "executed": executed,
                "pauseReason": advanced["pauseReason"],
                "taskPacket": advanced["taskPacket"],
                "run": run_status(run_dir),
            }
    return {
        "schemaVersion": "archaeological-run-loop-1.0",
        "executed": executed,
        "pauseReason": "max-steps-reached",
        "taskPacket": next_task_packet(run_dir, limit),
        "run": run_status(run_dir),
    }
