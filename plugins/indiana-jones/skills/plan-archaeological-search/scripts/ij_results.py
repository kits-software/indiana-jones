from __future__ import annotations

import shutil
import time
import uuid
import json
from pathlib import Path
from typing import Any

from ij_artifacts import write_json
from ij_journal import file_sha256, value_sha256


def run_path(run_dir: Path, relative: str) -> Path:
    root = run_dir.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError("run artifact path escapes the run directory") from error
    return path


def verify_result_artifacts(
    run_dir: Path,
    state: dict[str, Any],
    events: list[dict[str, Any]] | None = None,
) -> None:
    completion_heads = {
        (
            event.get("payload", {}).get("actionId"),
            event.get("payload", {}).get("attemptId"),
        ): event.get("previousEventHash")
        for event in events or []
        if event.get("eventType") == "action-completed"
    }
    for action_id, action in state["actions"].items():
        for result in action.get("resultRefs", []):
            relative = result.get("path")
            expected = result.get("sha256")
            if not isinstance(relative, str) or not isinstance(expected, str):
                raise ValueError("result reference is incomplete")
            path = run_path(run_dir, relative)
            if not path.is_file() or file_sha256(path) != expected:
                raise ValueError(f"result artifact is missing or changed: {relative}")
            seal = result.get("seal")
            if (
                not isinstance(seal, dict)
                or seal.get("schemaVersion") != "research-result-seal-2.0"
                or result.get("sealSha256") != value_sha256(seal)
                or seal.get("runId") != state.get("runId")
                or seal.get("sourcePlanSha256") != state.get("sourcePlanSha256")
                or seal.get("actionId") != action_id
                or seal.get("journalHeadSha256")
                != completion_heads.get((action_id, seal.get("attemptId")))
                or seal.get("outputHashes", {}).get("result") != expected
                or seal.get("retainedBytes") != result.get("bytes")
            ):
                raise ValueError(f"result seal is invalid: {relative}")
            for attachment in result.get("attachments", []):
                if not isinstance(attachment, dict):
                    raise ValueError("result attachment reference is invalid")
                attachment_path = run_path(run_dir, str(attachment.get("path", "")))
                if (
                    not attachment_path.is_file()
                    or file_sha256(attachment_path) != attachment.get("sha256")
                ):
                    raise ValueError(
                        f"result attachment is missing or changed: {attachment.get('path')}"
                    )
            sealed_attachments = seal.get("outputHashes", {}).get("attachments")
            actual_attachments = [
                {"path": item.get("path"), "sha256": item.get("sha256")}
                for item in result.get("attachments", [])
                if isinstance(item, dict)
            ]
            if sealed_attachments != actual_attachments:
                raise ValueError(f"result attachment seal is invalid: {relative}")


def prospective_result_bytes(
    action_id: str,
    attempt_id: str,
    result_path: Path | None,
    summary: str,
    source_ids: list[str],
    attachment_paths: list[Path] | None,
    acceptance_criteria: list[str],
    acceptance_evidence: list[str],
) -> int:
    if result_path is None:
        payload = {
            "schemaVersion": "research-result-1.0",
            "actionId": action_id,
            "attemptId": attempt_id,
            "summary": summary,
            "sourceIds": source_ids,
            "acceptanceCriteria": acceptance_criteria,
            "acceptanceEvidence": acceptance_evidence,
        }
        size = len(
            (
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
        )
    else:
        if not result_path.is_file():
            raise ValueError(f"result artifact does not exist: {result_path}")
        size = result_path.stat().st_size
    for attachment in attachment_paths or []:
        if not attachment.is_file():
            raise ValueError(f"result attachment does not exist: {attachment}")
        size += attachment.stat().st_size
    return size


def replayed_result_matches(
    result: dict[str, Any],
    result_path: Path | None,
    summary: str,
    source_ids: list[str],
    attachment_paths: list[Path] | None,
    acceptance_evidence: list[str] | None,
) -> bool:
    supplied_hash = (
        file_sha256(result_path)
        if result_path is not None and result_path.is_file()
        else None
    )
    supplied_attachments = [
        file_sha256(path) for path in attachment_paths or [] if path.is_file()
    ]
    sealed_attachments = [
        item.get("sha256")
        for item in result.get("attachments", [])
        if isinstance(item, dict)
    ]
    return (
        result.get("summary") == summary
        and result.get("sourceIds") == sorted(set(source_ids))
        and supplied_hash == result.get("sha256")
        and supplied_attachments == sealed_attachments
        and (
            acceptance_evidence is None
            or acceptance_evidence == result.get("acceptanceEvidence")
        )
    )


def store_result(
    run_dir: Path,
    action_id: str,
    attempt_id: str,
    result_path: Path | None,
    summary: str,
    source_ids: list[str],
    attachment_paths: list[Path] | None = None,
    acceptance_criteria: list[str] | None = None,
    acceptance_evidence: list[str] | None = None,
    seal_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    suffix = result_path.suffix if result_path is not None else ".json"
    destination = results_dir / f"{action_id}-{attempt_id.rsplit('-', 1)[-1]}{suffix}"
    if result_path is None:
        write_json(
            destination,
            {
                "schemaVersion": "research-result-1.0",
                "actionId": action_id,
                "attemptId": attempt_id,
                "summary": summary,
                "sourceIds": source_ids,
                "acceptanceCriteria": acceptance_criteria or [],
                "acceptanceEvidence": acceptance_evidence or [],
            },
        )
    else:
        if not result_path.is_file():
            raise ValueError(f"result artifact does not exist: {result_path}")
        with destination.open("xb") as output, result_path.open("rb") as source:
            shutil.copyfileobj(source, output)
    size = destination.stat().st_size
    attachments: list[dict[str, Any]] = []
    for index, attachment_path in enumerate(attachment_paths or [], 1):
        if not attachment_path.is_file():
            raise ValueError(f"result attachment does not exist: {attachment_path}")
        attachment_destination = (
            results_dir
            / f"{action_id}-{attempt_id.rsplit('-', 1)[-1]}-attachment-{index:03d}"
            f"{attachment_path.suffix}"
        )
        with attachment_destination.open("xb") as output, attachment_path.open("rb") as source:
            shutil.copyfileobj(source, output)
        attachment_size = attachment_destination.stat().st_size
        size += attachment_size
        attachments.append(
            {
                "path": str(attachment_destination.relative_to(run_dir)),
                "sha256": file_sha256(attachment_destination),
                "bytes": attachment_size,
                "sourceName": attachment_path.name,
            }
        )
    result = {
        "resultId": f"result_{uuid.uuid4().hex}",
        "path": str(destination.relative_to(run_dir)),
        "sha256": file_sha256(destination),
        "bytes": size,
        "summary": summary,
        "sourceIds": sorted(set(source_ids)),
        "recordedAt": time.time(),
        "attachments": attachments,
        "acceptanceCriteria": acceptance_criteria or [],
        "acceptanceEvidence": acceptance_evidence or [],
    }
    seal = {
        "schemaVersion": "research-result-seal-2.0",
        **(seal_context or {}),
        "outputHashes": {
            "result": result["sha256"],
            "attachments": [
                {"path": item["path"], "sha256": item["sha256"]}
                for item in attachments
            ],
        },
        "retainedBytes": size,
    }
    result["seal"] = seal
    result["sealSha256"] = value_sha256(seal)
    return result


def remove_result_artifacts(run_dir: Path, result: dict[str, Any]) -> None:
    paths = [result.get("path")] + [
        attachment.get("path")
        for attachment in result.get("attachments", [])
        if isinstance(attachment, dict)
    ]
    for relative in paths:
        if isinstance(relative, str):
            try:
                run_path(run_dir, relative).unlink()
            except FileNotFoundError:
                pass
