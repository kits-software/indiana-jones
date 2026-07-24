from __future__ import annotations

from pathlib import Path
from typing import Any

from ij_artifacts import read_json
from ij_results import run_path


def _qualified_snapshot(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.rsplit(":", 1)
    return (
        len(parts) == 2
        and parts[0].startswith("snapshot:")
        and len(parts[1]) == 64
        and all(character in "0123456789abcdef" for character in parts[1])
    )


def artifact_lineage(value: dict[str, Any]) -> tuple[set[str], set[str]]:
    snapshots: set[str] = set()
    records: set[str] = set()
    schema = value.get("schemaVersion")
    if schema == "archaeological-find-records-1.0":
        query = value.get("queryArtifact")
        if isinstance(query, dict):
            source_id = query.get("sourceId")
            raw_hash = query.get("rawArtifactSha256")
            if isinstance(source_id, str) and isinstance(raw_hash, str):
                snapshots.add(f"snapshot:{source_id}:{raw_hash}")
            if isinstance(raw_hash, str):
                snapshots.add(f"sha256:{raw_hash}")
        for record in value.get("records", []):
            if isinstance(record, dict) and isinstance(record.get("recordId"), str):
                records.add(record["recordId"])
    elif schema == "archaeological-find-reconciliation-1.0":
        for entity in value.get("entities", []):
            if not isinstance(entity, dict):
                continue
            records.update(
                record_id
                for record_id in entity.get("recordIds", [])
                if isinstance(record_id, str)
            )
    return snapshots, records


def sealed_lineage_registry(
    run_dir: Path,
    plan: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, set[str]]:
    snapshots: set[str] = set()
    records: set[str] = set()
    action_map = {
        item.get("actionId"): item
        for item in plan.get("actions", [])
        if isinstance(item, dict) and isinstance(item.get("actionId"), str)
    }
    pending = list(action.get("prerequisites", []))
    visited: set[str] = set()
    while pending:
        action_id = pending.pop()
        if not isinstance(action_id, str) or action_id in visited:
            continue
        visited.add(action_id)
        declared = action_map.get(action_id)
        if isinstance(declared, dict):
            pending.extend(declared.get("prerequisites", []))
        runtime = state.get("actions", {}).get(action_id)
        if not isinstance(runtime, dict) or runtime.get("status") != "completed":
            continue
        for result_ref in runtime.get("resultRefs", []):
            if not isinstance(result_ref, dict):
                continue
            seal = result_ref.get("seal")
            if isinstance(seal, dict):
                snapshots.update(
                    value
                    for value in seal.get("sourceSnapshotIds", [])
                    if _qualified_snapshot(value)
                )
                records.update(
                    value
                    for value in seal.get("normalizedRecordIds", [])
                    if isinstance(value, str)
                )
            relative = result_ref.get("path")
            if not isinstance(relative, str):
                continue
            value = read_json(run_path(run_dir, relative))
            artifact_snapshots, artifact_records = artifact_lineage(value)
            snapshots.update(artifact_snapshots)
            records.update(artifact_records)
    return {"sourceSnapshotIds": snapshots, "normalizedRecordIds": records}
