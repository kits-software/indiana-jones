from __future__ import annotations

import copy
import json
import os
import re
import time
import urllib.error
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ij_artifacts import plan_sha256, read_json, write_json
from ij_frontier import build_frontier
from ij_ingest import (
    SUPPORTED_FORMATS,
    acquire_and_normalize,
    acquisition_binding_errors,
    reconcile_artifacts,
)
from ij_journal import append_event, read_events, run_lock, value_sha256
from ij_migrate import verify_candidate_freeze
from ij_plan import validate_plan
from ij_readiness import readiness_errors
from ij_results import (
    remove_result_artifacts,
    run_path,
    store_result,
    verify_result_artifacts,
)


RUN_SCHEMA_VERSION = "1.0"
TERMINAL_ACTION_STATES = {
    "completed",
    "completed-unverified",
    "blocked",
    "failed",
    "rejected",
    "cancelled",
    "superseded",
}
EXECUTORS = {"codex-research", "ingest-source", "reconcile-records"}


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        temp.write_text(
            json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _positive_int(value: Any, label: str, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer between 1 and {maximum}")
    return value


def validate_execution_spec(action: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    action_id = action.get("actionId", "<unknown>")
    if not isinstance(action_id, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", action_id
    ):
        errors.append("actionId must be a safe 1-128 character identifier")
    spec = action.get("execution")
    if not isinstance(spec, dict):
        return [f"action {action_id} requires an execution object"]
    executor = spec.get("executor")
    if executor not in EXECUTORS:
        errors.append(f"action {action_id} has unsupported executor")
    if not isinstance(spec.get("inputs"), dict):
        errors.append(f"action {action_id} execution.inputs must be an object")
    outputs = spec.get("outputs")
    if (
        not isinstance(outputs, list)
        or not outputs
        or any(not isinstance(item, str) or not item for item in outputs)
    ):
        errors.append(f"action {action_id} execution.outputs must be a non-empty string array")
    criteria = spec.get("acceptanceCriteria")
    if (
        not isinstance(criteria, list)
        or not criteria
        or any(not isinstance(item, str) or not item for item in criteria)
    ):
        errors.append(
            f"action {action_id} execution.acceptanceCriteria must be a non-empty string array"
        )
    timeout = spec.get("timeoutSeconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 86400:
        errors.append(f"action {action_id} execution.timeoutSeconds is invalid")
    attempts = spec.get("maxAttempts")
    if not isinstance(attempts, int) or isinstance(attempts, bool) or not 1 <= attempts <= 20:
        errors.append(f"action {action_id} execution.maxAttempts is invalid")
    inputs = spec.get("inputs")
    if isinstance(inputs, dict) and executor == "codex-research":
        if not isinstance(inputs.get("instruction"), str) or not inputs["instruction"].strip():
            errors.append(f"action {action_id} codex-research requires an instruction")
    elif isinstance(inputs, dict) and executor == "ingest-source":
        if not isinstance(inputs.get("sourceId"), str) or not inputs["sourceId"]:
            errors.append(f"action {action_id} ingest-source requires sourceId")
        if not isinstance(inputs.get("locator"), str) or not inputs["locator"]:
            errors.append(f"action {action_id} ingest-source requires locator")
        if inputs.get("format") not in SUPPORTED_FORMATS:
            errors.append(f"action {action_id} ingest-source has unsupported format")
        for key, maximum in (("maxBytes", 100_000_000), ("maxRecords", 100_000)):
            if key in inputs and (
                not isinstance(inputs[key], int)
                or isinstance(inputs[key], bool)
                or not 1 <= inputs[key] <= maximum
            ):
                errors.append(f"action {action_id} ingest-source has invalid {key}")
    elif isinstance(inputs, dict) and executor == "reconcile-records":
        artifacts = inputs.get("artifacts")
        if (
            not isinstance(artifacts, list)
            or not artifacts
            or any(not isinstance(path, str) or not path for path in artifacts)
        ):
            errors.append(f"action {action_id} reconcile-records requires artifact paths")
    return errors


def execution_readiness_errors(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for action in plan.get("actions", []):
        if isinstance(action, dict) and action.get("status") == "planned":
            errors.extend(validate_execution_spec(action))
    errors.extend(acquisition_binding_errors(plan))
    return errors


def _initial_state(plan: dict[str, Any], started: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": RUN_SCHEMA_VERSION,
        "runId": started["runId"],
        "sourcePlanSha256": started["sourcePlanSha256"],
        "status": "active",
        "startedAt": started["startedAt"],
        "updatedAt": started["startedAt"],
        "budgets": copy.deepcopy(started["budgets"]),
        "usage": {
            "uniqueActionsStarted": 0,
            "attemptsStarted": 0,
            "actionsCompleted": 0,
            "resultBytes": 0,
        },
        "actions": {
            action["actionId"]: {
                "status": action.get("status", "planned"),
                "attempts": [],
                "resultRefs": copy.deepcopy(action.get("resultRefs", [])),
                "lastError": None,
            }
            for action in plan.get("actions", [])
        },
        "stop": None,
    }


def replay_state(plan: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    first = events[0]
    if first.get("eventType") != "run-started":
        raise ValueError("journal must begin with run-started")
    payload = first.get("payload", {})
    if payload.get("sourcePlanSha256") != plan_sha256(plan):
        raise ValueError("run journal does not match the plan snapshot")
    started = {
        "runId": first.get("runId"),
        "sourcePlanSha256": payload["sourcePlanSha256"],
        "startedAt": payload["startedAt"],
        "budgets": payload["budgets"],
    }
    state = _initial_state(plan, started)
    seen_actions: set[str] = set()
    for event in events[1:]:
        if event.get("runId") != state["runId"]:
            raise ValueError("journal contains an event for another run")
        event_type = event.get("eventType")
        data = event.get("payload", {})
        action_id = data.get("actionId")
        action_state = state["actions"].get(action_id) if action_id else None
        if event_type == "action-started":
            if action_state is None:
                raise ValueError(f"journal references unknown action {action_id}")
            if action_state["status"] not in {"planned", "failed"}:
                raise ValueError(f"action {action_id} cannot start from {action_state['status']}")
            action_state["status"] = "running"
            action_state["attempts"].append(
                {
                    "attemptId": data["attemptId"],
                    "idempotencyKey": data["idempotencyKey"],
                    "startedAt": event["occurredAt"],
                    "status": "running",
                }
            )
            if action_id not in seen_actions:
                state["usage"]["uniqueActionsStarted"] += 1
                seen_actions.add(action_id)
            state["usage"]["attemptsStarted"] += 1
        elif event_type in {"action-completed", "action-failed", "action-interrupted"}:
            if action_state is None or not action_state["attempts"]:
                raise ValueError(f"journal transition for unstarted action {action_id}")
            attempt = action_state["attempts"][-1]
            if attempt["attemptId"] != data.get("attemptId") or attempt["status"] != "running":
                raise ValueError(f"journal has a stale attempt transition for {action_id}")
            if event_type == "action-completed":
                result = data.get("result")
                if not isinstance(result, dict):
                    raise ValueError(f"completed action {action_id} lacks a result")
                attempt["status"] = "completed"
                attempt["completedAt"] = event["occurredAt"]
                attempt["resultSha256"] = result.get("sha256")
                action_state["status"] = "completed"
                action_state["resultRefs"].append(result)
                state["usage"]["actionsCompleted"] += 1
                state["usage"]["resultBytes"] += int(result.get("bytes", 0))
            else:
                attempt["status"] = "failed" if event_type == "action-failed" else "interrupted"
                attempt["endedAt"] = event["occurredAt"]
                action_state["lastError"] = data.get("error")
                action_state["status"] = data.get("nextStatus", "failed")
        elif event_type == "action-blocked":
            if action_state is None:
                raise ValueError(f"journal references unknown action {action_id}")
            action_state["status"] = "blocked"
            action_state["lastError"] = data.get("reason")
        elif event_type == "run-resumed":
            if state["status"] == "stopped" and not data.get("overrideStop"):
                raise ValueError("stopped run requires overrideStop to resume")
            state["status"] = "active"
            state["stop"] = None
        elif event_type == "run-stopped":
            state["status"] = data.get("status", "stopped")
            state["stop"] = {
                "reason": data.get("reason"),
                "details": data.get("details", {}),
                "occurredAt": event["occurredAt"],
            }
        else:
            raise ValueError(f"unsupported journal event type: {event_type}")
        state["updatedAt"] = event["occurredAt"]
    state["journalHeadSha256"] = events[-1]["eventHash"]
    state["stateSha256"] = value_sha256(
        {key: value for key, value in state.items() if key != "stateSha256"}
    )
    return state


def _load(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    plan = read_json(run_dir / "plan.json")
    events = read_events(run_dir / "events.jsonl")
    state = replay_state(plan, events)
    verify_result_artifacts(run_dir, state)
    _atomic_json(run_dir / "state.json", state)
    return plan, events, state


def _working_plan(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    working = copy.deepcopy(plan)
    for action in working.get("actions", []):
        runtime = state["actions"][action["actionId"]]
        action["status"] = runtime["status"]
        action["resultRefs"] = copy.deepcopy(runtime.get("resultRefs", []))
        action["_runtimeEvidenceVerified"] = bool(
            runtime["status"] == "completed" and runtime.get("resultRefs")
        )
    return working


def initialize_run(
    plan: dict[str, Any],
    run_dir: Path,
    *,
    max_actions: int,
    max_attempts: int,
    max_result_bytes: int,
    max_seconds: int,
    candidate_artifact: Path | None = None,
    candidate_seal: Path | None = None,
) -> dict[str, Any]:
    validation = validate_plan(plan)
    if not validation.valid:
        raise ValueError("plan is invalid: " + "; ".join(validation.errors))
    readiness = readiness_errors(plan) + execution_readiness_errors(plan)
    if readiness:
        raise ValueError("plan is not execution-ready: " + "; ".join(readiness))
    verify_candidate_freeze(plan, candidate_artifact, candidate_seal)
    budgets = {
        "maxActions": _positive_int(max_actions, "max_actions", 100_000),
        "maxAttempts": _positive_int(max_attempts, "max_attempts", 1_000_000),
        "maxResultBytes": _positive_int(
            max_result_bytes, "max_result_bytes", 10_000_000_000
        ),
        "maxSeconds": _positive_int(max_seconds, "max_seconds", 31_536_000),
    }
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / "plan.json", plan)
    run_id = f"run_{uuid.uuid4().hex}"
    started_at = time.time()
    append_event(
        run_dir / "events.jsonl",
        run_id,
        "run-started",
        {
            "sourcePlanSha256": plan_sha256(plan),
            "startedAt": started_at,
            "budgets": budgets,
        },
        occurred_at=started_at,
    )
    _, _, state = _load(run_dir)
    return state


def _budget_reason(state: dict[str, Any], now: float | None = None) -> str | None:
    now = now if now is not None else time.time()
    usage = state["usage"]
    budgets = state["budgets"]
    if usage["uniqueActionsStarted"] >= budgets["maxActions"]:
        return "budget-exhausted:max-actions"
    if usage["attemptsStarted"] >= budgets["maxAttempts"]:
        return "budget-exhausted:max-attempts"
    if usage["resultBytes"] >= budgets["maxResultBytes"]:
        return "budget-exhausted:max-result-bytes"
    if now - state["startedAt"] >= budgets["maxSeconds"]:
        return "budget-exhausted:max-seconds"
    return None


def next_task_packet(run_dir: Path, limit: int) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be positive")
    plan, _, state = _load(run_dir)
    if state["status"] != "active":
        return {"run": state, "stopReason": state.get("stop"), "recommendedBatch": []}
    budget = _budget_reason(state)
    if budget:
        return {"run": state, "stopReason": budget, "recommendedBatch": []}
    working = _working_plan(plan, state)
    frontier = build_frontier(working, limit)
    action_map = {action["actionId"]: action for action in working["actions"]}
    batch: list[dict[str, Any]] = []
    for ranked in frontier["recommendedBatch"]:
        action = action_map[ranked["actionId"]]
        batch.append(
            {
                **ranked,
                "method": action.get("method"),
                "actionClass": action.get("actionClass"),
                "stage": action.get("stage"),
                "sourceIds": copy.deepcopy(action.get("sourceIds", [])),
                "authorization": copy.deepcopy(action.get("authorization", {})),
                "execution": copy.deepcopy(action.get("execution")),
            }
        )
    terminal = all(
        action["status"] in TERMINAL_ACTION_STATES for action in state["actions"].values()
    )
    stop_reason = "all-actions-terminal" if terminal else None
    if not batch and not stop_reason:
        stop_reason = "no-executable-actions"
    return {
        "schemaVersion": "research-task-packet-1.0",
        "runId": state["runId"],
        "sourcePlanSha256": state["sourcePlanSha256"],
        "journalHeadSha256": state["journalHeadSha256"],
        "scoreMeaning": frontier["scoreMeaning"],
        "recommendedBatch": batch,
        "blockedActions": frontier["blockedActions"],
        "usage": state["usage"],
        "budgets": state["budgets"],
        "stopReason": stop_reason,
    }


def start_action(run_dir: Path, action_id: str) -> dict[str, Any]:
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        if state["status"] != "active":
            raise ValueError("run is not active")
        budget = _budget_reason(state)
        if budget:
            raise ValueError(budget)
        packet = next_task_packet(run_dir, max(1, len(plan.get("actions", [])) * 2))
        ready = {item["actionId"]: item for item in packet["recommendedBatch"]}
        if action_id not in ready:
            raise ValueError(f"action is not ready: {action_id}")
        action = next(item for item in plan["actions"] if item["actionId"] == action_id)
        spec_errors = validate_execution_spec(action)
        if spec_errors:
            raise ValueError("; ".join(spec_errors))
        attempt_number = len(state["actions"][action_id]["attempts"]) + 1
        max_attempts = int(action["execution"]["maxAttempts"])
        if attempt_number > max_attempts:
            raise ValueError(f"action {action_id} exhausted its retry limit")
        attempt_id = f"{action_id}.attempt-{attempt_number:03d}"
        idempotency_key = value_sha256(
            {
                "runId": state["runId"],
                "planSha256": state["sourcePlanSha256"],
                "actionId": action_id,
                "attempt": attempt_number,
                "execution": action["execution"],
            }
        )
        event = append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "action-started",
            {
                "actionId": action_id,
                "attemptId": attempt_id,
                "idempotencyKey": idempotency_key,
            },
        )
        _, _, updated = _load(run_dir)
        return {
            "attemptId": attempt_id,
            "idempotencyKey": idempotency_key,
            "journalEventSha256": event["eventHash"],
            "action": ready[action_id],
            "run": updated,
        }


def complete_action(
    run_dir: Path,
    action_id: str,
    attempt_id: str,
    *,
    result_path: Path | None,
    summary: str,
    source_ids: list[str],
    acceptance_evidence: list[str] | None = None,
    attachment_paths: list[Path] | None = None,
) -> dict[str, Any]:
    if not summary.strip():
        raise ValueError("result summary is required")
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        action_state = state["actions"].get(action_id)
        if not action_state or action_state["status"] != "running":
            raise ValueError(f"action is not running: {action_id}")
        if action_state["attempts"][-1]["attemptId"] != attempt_id:
            raise ValueError("attempt_id does not match the active attempt")
        action = next(item for item in plan["actions"] if item["actionId"] == action_id)
        known_sources = {source["sourceId"] for source in plan.get("sources", [])}
        if any(source_id not in known_sources for source_id in source_ids):
            raise ValueError("result references an unknown source")
        action_sources = {
            source_id
            for source_id in action.get("sourceIds", [])
            if isinstance(source_id, str)
        }
        if action_sources and not action_sources.intersection(source_ids):
            raise ValueError("result must cite at least one source declared by the action")
        criteria = action.get("execution", {}).get("acceptanceCriteria", [])
        evidence = acceptance_evidence or []
        if (
            len(evidence) != len(criteria)
            or any(not isinstance(item, str) or not item.strip() for item in evidence)
        ):
            raise ValueError(
                "result requires one non-empty acceptance evidence item per criterion"
            )
        authorization = action.get("authorization", {})
        if authorization.get("required") != "none" and authorization.get("state") != "confirmed":
            raise ValueError("required authorization is not confirmed")
        result = store_result(
            run_dir,
            action_id,
            attempt_id,
            result_path,
            summary,
            source_ids,
            attachment_paths,
            criteria,
            evidence,
        )
        if state["usage"]["resultBytes"] + result["bytes"] > state["budgets"]["maxResultBytes"]:
            remove_result_artifacts(run_dir, result)
            raise ValueError("result would exceed max_result_bytes")
        event = append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "action-completed",
            {"actionId": action_id, "attemptId": attempt_id, "result": result},
        )
        _, _, updated = _load(run_dir)
        return {
            "result": result,
            "journalEventSha256": event["eventHash"],
            "run": updated,
        }


def fail_action(
    run_dir: Path,
    action_id: str,
    attempt_id: str,
    *,
    error: str,
    retryable: bool,
) -> dict[str, Any]:
    if not error.strip():
        raise ValueError("failure error is required")
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        action_state = state["actions"].get(action_id)
        if not action_state or action_state["status"] != "running":
            raise ValueError(f"action is not running: {action_id}")
        if action_state["attempts"][-1]["attemptId"] != attempt_id:
            raise ValueError("attempt_id does not match the active attempt")
        action = next(item for item in plan["actions"] if item["actionId"] == action_id)
        attempts_used = len(action_state["attempts"])
        can_retry = retryable and attempts_used < int(action["execution"]["maxAttempts"])
        event = append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "action-failed",
            {
                "actionId": action_id,
                "attemptId": attempt_id,
                "error": error,
                "nextStatus": "planned" if can_retry else "failed",
            },
        )
        _, _, updated = _load(run_dir)
        return {"journalEventSha256": event["eventHash"], "run": updated}


def resume_run(run_dir: Path, *, override_stop: bool = False) -> dict[str, Any]:
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        if state["status"] == "stopped" and not override_stop:
            raise ValueError("stopped run requires override_stop to resume")
        for action_id, action_state in state["actions"].items():
            if action_state["status"] != "running":
                continue
            action = next(item for item in plan["actions"] if item["actionId"] == action_id)
            attempts_used = len(action_state["attempts"])
            next_status = (
                "planned"
                if attempts_used < int(action["execution"]["maxAttempts"])
                else "failed"
            )
            append_event(
                run_dir / "events.jsonl",
                state["runId"],
                "action-interrupted",
                {
                    "actionId": action_id,
                    "attemptId": action_state["attempts"][-1]["attemptId"],
                    "error": "interrupted action recovered during resume",
                    "nextStatus": next_status,
                },
            )
        append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "run-resumed",
            {"overrideStop": override_stop},
        )
        _, _, updated = _load(run_dir)
        return updated


def stop_run(run_dir: Path, reason: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    if not reason.strip():
        raise ValueError("stop reason is required")
    with run_lock(run_dir):
        _, _, state = _load(run_dir)
        if any(action["status"] == "running" for action in state["actions"].values()):
            raise ValueError("cannot stop while an action is running; fail or resume it first")
        append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "run-stopped",
            {"status": "stopped", "reason": reason, "details": details or {}},
        )
        _, _, updated = _load(run_dir)
        return updated


def execute_deterministic_action(run_dir: Path, action_id: str) -> dict[str, Any]:
    started = start_action(run_dir, action_id)
    attempt_id = started["attemptId"]
    action = started["action"]
    spec = action["execution"]
    executor = spec["executor"]
    inputs = spec["inputs"]
    try:
        plan, _, _ = _load(run_dir)
        if executor == "ingest-source":
            source_id = inputs.get("sourceId")
            source = next(
                (item for item in plan["sources"] if item.get("sourceId") == source_id),
                None,
            )
            if source is None:
                raise ValueError(f"unknown source: {source_id}")
            acquisition = source.get("acquisition")
            if not isinstance(acquisition, dict):
                raise ValueError(f"source {source_id} lacks a declared acquisition contract")
            if (
                acquisition.get("locator") != inputs.get("locator")
                or acquisition.get("format") != inputs.get("format")
            ):
                raise ValueError(
                    f"action acquisition does not match declared source {source_id}"
                )
            artifact_path = run_dir / "work" / f"{action_id}-{attempt_id}.json"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            locator = str(inputs["locator"])
            if not urlparse(locator).scheme:
                locator = str(run_path(run_dir, locator))
            acquire_and_normalize(
                source=source,
                locator=locator,
                format_name=str(inputs["format"]),
                out=artifact_path,
                max_bytes=int(inputs.get("maxBytes", 10_000_000)),
                max_records=int(inputs.get("maxRecords", 5_000)),
                query=inputs.get("query", {}),
            )
            summary = f"Ingested and normalized public source {source_id}."
            source_ids = [source_id]
            attachment_paths = [artifact_path.with_suffix(artifact_path.suffix + ".raw")]
        elif executor == "reconcile-records":
            paths = inputs.get("artifacts")
            if not isinstance(paths, list) or not paths:
                raise ValueError("reconcile-records requires input artifacts")
            artifacts = [read_json(run_path(run_dir, str(path))) for path in paths]
            reconciled = reconcile_artifacts(artifacts)
            artifact_path = run_dir / "work" / f"{action_id}-{attempt_id}.json"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(artifact_path, reconciled)
            summary = f"Reconciled {reconciled['recordCount']} catalogue records."
            source_ids = sorted(
                {
                    source_id
                    for entity in reconciled["entities"]
                    for source_id in entity["sourceIds"]
                }
            )
            attachment_paths = []
        else:
            raise ValueError("codex-research actions require agent-executed evidence work")
        return complete_action(
            run_dir,
            action_id,
            attempt_id,
            result_path=artifact_path,
            summary=summary,
            source_ids=source_ids,
            acceptance_evidence=[
                f"Verified in sealed result artifact: {criterion}"
                for criterion in action["execution"]["acceptanceCriteria"]
            ],
            attachment_paths=attachment_paths,
        )
    except Exception as error:
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


def run_status(run_dir: Path) -> dict[str, Any]:
    _, events, state = _load(run_dir)
    state["eventCount"] = len(events)
    state["budgetStopReason"] = _budget_reason(state)
    return state
