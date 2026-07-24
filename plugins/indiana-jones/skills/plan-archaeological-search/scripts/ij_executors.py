from __future__ import annotations

import time
import urllib.error
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ij_acceptance import evaluate_acceptance
from ij_artifacts import read_json, write_json
from ij_ingest import acquire_and_normalize, reconcile_artifacts
from ij_journal import file_sha256
from ij_results import run_path
from ij_runtime_integrity import (
    normalized_artifact_errors,
    sealed_reconciliation_artifacts,
)
from ij_source_contract import verify_source_acquisition


def _remove_work(paths: list[Path]) -> None:
    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _completed_replay(
    events: list[dict[str, Any]],
    state: dict[str, Any],
    action_id: str,
) -> dict[str, Any] | None:
    action = state["actions"].get(action_id)
    if not isinstance(action, dict) or action.get("status") != "completed":
        return None
    attempts = action.get("attempts")
    results = action.get("resultRefs")
    if (
        not isinstance(attempts, list)
        or not attempts
        or not isinstance(results, list)
        or not results
    ):
        raise ValueError(f"completed action {action_id} lacks replayable result state")
    attempt_id = attempts[-1].get("attemptId")
    completion = next(
        (
            event
            for event in reversed(events)
            if event.get("eventType") == "action-completed"
            and event.get("payload", {}).get("actionId") == action_id
            and event.get("payload", {}).get("attemptId") == attempt_id
        ),
        None,
    )
    if completion is None:
        raise ValueError(f"completed action {action_id} lacks a journal event")
    return {
        "result": results[-1],
        "journalEventSha256": completion["eventHash"],
        "run": state,
        "replayed": True,
    }


def execute(run_dir: Path, action_id: str) -> dict[str, Any]:
    from ij_runtime import (
        _DETERMINISTIC_COMPLETION,
        complete_action,
        fail_action,
        load_run,
        start_action,
    )

    _, events, state = load_run(run_dir)
    completed = _completed_replay(events, state, action_id)
    if completed is not None:
        return completed
    action_state = state["actions"].get(action_id)
    replay_key = None
    if isinstance(action_state, dict) and action_state.get("status") == "running":
        replay_key = action_state["attempts"][-1]["idempotencyKey"]
    started = start_action(run_dir, action_id, replay_key)
    attempt_id = started["attemptId"]
    packet_action = started["action"]
    inputs = packet_action["execution"]["inputs"]
    executor = packet_action["execution"]["executor"]
    work_paths: list[Path] = []
    try:
        plan, _, state = load_run(run_dir)
        action = next(
            item for item in plan["actions"] if item.get("actionId") == action_id
        )
        deadline = float(started["leaseExpiresAt"])
        remaining_bytes = (
            state["budgets"]["maxResultBytes"] - state["usage"]["resultBytes"]
        )
        if remaining_bytes < 1:
            raise ValueError("budget-exhausted:max-result-bytes")
        artifact_path = run_dir / "work" / f"{action_id}-{attempt_id}.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        work_paths.append(artifact_path)
        if executor == "ingest-source":
            source_id = inputs["sourceId"]
            source = next(
                (item for item in plan["sources"] if item.get("sourceId") == source_id),
                None,
            )
            if source is None:
                raise ValueError(f"unknown source: {source_id}")
            acquisition = source.get("acquisition")
            if not isinstance(acquisition, dict):
                raise ValueError(
                    f"source {source_id} lacks a declared acquisition contract"
                )
            if acquisition.get("locator") != inputs.get("locator") or acquisition.get(
                "format"
            ) != inputs.get("format"):
                raise ValueError(
                    f"action acquisition does not match declared source {source_id}"
                )
            locator = str(inputs["locator"])
            if not urlparse(locator).scheme:
                locator = str(run_path(run_dir, locator))
            verify_source_acquisition(
                source,
                actual_locator=locator,
                inputs=inputs,
            )
            raw_limit = min(int(inputs.get("maxBytes", 10_000_000)), remaining_bytes)
            timeout_seconds = min(30.0, deadline - time.time())
            if timeout_seconds <= 0:
                raise TimeoutError("action lease expired before source acquisition")
            artifact = acquire_and_normalize(
                source=source,
                locator=locator,
                format_name=str(inputs["format"]),
                out=artifact_path,
                max_bytes=raw_limit,
                max_records=min(
                    int(inputs.get("maxRecords", 5_000)),
                    int(started["budgetReservation"]["recordLimit"]),
                ),
                query=inputs.get("query", {}),
                timeout_seconds=timeout_seconds,
            )
            raw_path = artifact_path.with_suffix(artifact_path.suffix + ".raw")
            work_paths.append(raw_path)
            synthetic_ref = {
                "attachments": [{"sha256": file_sha256(raw_path)}],
            }
            errors = normalized_artifact_errors(
                artifact,
                {item["sourceId"] for item in plan["sources"]},
                synthetic_ref,
            )
            if errors:
                raise ValueError("; ".join(errors))
            summary = f"Ingested and normalized public source {source_id}."
            source_ids = [source_id]
            attachments = [raw_path]
        elif executor == "reconcile-records":
            paths = inputs.get("artifacts")
            if not isinstance(paths, list) or not paths:
                raise ValueError("reconcile-records requires input artifacts")
            artifacts, _ = sealed_reconciliation_artifacts(
                run_dir,
                plan,
                state,
                action,
                paths,
            )
            reconciliation = reconcile_artifacts(artifacts)
            write_json(artifact_path, reconciliation)
            summary = (
                f"Reconciled {reconciliation['recordCount']} sealed catalogue records."
            )
            source_ids = sorted(
                {
                    source_id
                    for entity in reconciliation["entities"]
                    for source_id in entity["sourceIds"]
                }
            )
            attachments = []
        else:
            raise ValueError(
                "codex-research actions require agent-executed evidence work"
            )
        if time.time() > deadline:
            raise TimeoutError("action lease expired before result sealing")
        acceptance_evidence = evaluate_acceptance(action, read_json(artifact_path))
        result = complete_action(
            run_dir,
            action_id,
            attempt_id,
            result_path=artifact_path,
            summary=summary,
            source_ids=source_ids,
            acceptance_evidence=acceptance_evidence,
            attachment_paths=attachments,
            _executor_token=_DETERMINISTIC_COMPLETION,
        )
        _remove_work(work_paths)
        return result
    except Exception as error:
        _remove_work(work_paths)
        _, current_events, current_state = load_run(run_dir)
        if _completed_replay(current_events, current_state, action_id) is None:
            fail_action(
                run_dir,
                action_id,
                attempt_id,
                error=str(error),
                retryable=isinstance(
                    error,
                    (OSError, TimeoutError, ConnectionError, urllib.error.URLError),
                ),
            )
        raise
