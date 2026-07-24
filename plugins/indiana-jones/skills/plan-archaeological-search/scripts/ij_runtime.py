from __future__ import annotations

import copy, json, os, shutil, time, uuid
from pathlib import Path
from typing import Any

from ij_artifacts import plan_sha256, read_json, write_json
from ij_budgets import (
    actions_terminal,
    action_stop_reason,
    apply_completion_usage,
    apply_start_reservation,
    build_budget_limits,
    completion_budget_usage,
    completion_problem,
    global_stop_reason,
    initial_run_state,
    release_record_reservation,
    reservation_for_action,
    validate_budget_limits,
    working_plan,
)
from ij_execution_spec import execution_readiness_errors, validate_execution_spec
from ij_frontier import build_frontier
from ij_journal import append_event, read_events, run_lock, value_sha256
from ij_lineage import artifact_lineage, sealed_lineage_registry
from ij_plan import validate_plan
from ij_readiness import readiness_errors
from ij_result_validation import (
    build_result_seal_context,
    deterministic_result_metadata,
    validate_agent_result,
)
from ij_results import (
    prospective_result_bytes,
    remove_result_artifacts,
    replayed_result_matches,
    store_result,
    verify_result_artifacts,
)
from ij_runtime_integrity import verify_candidate_freeze, verify_run_candidate_freeze

RUN_SCHEMA_VERSION = "1.0"
_DETERMINISTIC_COMPLETION = object()
def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass

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
        "budgets": validate_budget_limits(payload["budgets"]),
    }
    state = initial_run_state(plan, started, RUN_SCHEMA_VERSION)
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
            action = next(item for item in plan["actions"] if item["actionId"] == action_id)
            apply_start_reservation(state, plan, action, data.get("budgetReservation"))
            action_state["status"] = "running"
            action_state["attempts"].append(
                {
                    "attemptId": data["attemptId"],
                    "idempotencyKey": data["idempotencyKey"],
                    "startedAt": event["occurredAt"],
                    "leaseExpiresAt": data["leaseExpiresAt"],
                    "budgetReservation": copy.deepcopy(data["budgetReservation"]),
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
                action = next(item for item in plan["actions"] if item["actionId"] == action_id)
                seal = result.get("seal")
                if not isinstance(seal, dict):
                    raise ValueError(f"completed action {action_id} lacks a result seal")
                apply_completion_usage(
                    state,
                    action,
                    seal.get("budgetUsage"),
                    attempt["budgetReservation"],
                )
                attempt["status"] = "completed"
                attempt["completedAt"] = event["occurredAt"]
                attempt["resultSha256"] = result.get("sha256")
                action_state["status"] = "completed"
                action_state["resultRefs"].append(result)
                state["usage"]["actionsCompleted"] += 1
                state["usage"]["resultBytes"] += int(result.get("bytes", 0))
            else:
                release_record_reservation(state, attempt["budgetReservation"])
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
    state["stateSha256"] = value_sha256({key: value for key, value in state.items() if key != "stateSha256"})
    return state

def _load(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    plan = read_json(run_dir / "plan.json")
    events = read_events(run_dir / "events.jsonl")
    verify_run_candidate_freeze(plan, run_dir, events[0].get("payload", {}))
    state = replay_state(plan, events)
    verify_result_artifacts(run_dir, state, events)
    _atomic_json(run_dir / "state.json", state)
    return plan, events, state

def load_run(
    run_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    return _load(run_dir)

def initialize_run(
    plan: dict[str, Any],
    run_dir: Path,
    *,
    max_actions: int,
    max_attempts: int,
    max_result_bytes: int,
    max_seconds: int,
    max_requests: int | None = None,
    max_requests_per_provider: int | None = None,
    max_records: int | None = None,
    max_consecutive_no_novelty: int | None = None,
    candidate_artifact: Path | None = None,
    candidate_seal: Path | None = None,
) -> dict[str, Any]:
    if plan.get("schemaVersion") != "2.0":
        raise ValueError("execution requires schema 2.0; migrate the plan first")
    validation = validate_plan(plan)
    if not validation.valid:
        raise ValueError("plan is invalid: " + "; ".join(validation.errors))
    readiness = readiness_errors(plan) + execution_readiness_errors(plan)
    if readiness:
        raise ValueError("plan is not execution-ready: " + "; ".join(readiness))
    invalid_states = [
        action.get("actionId", "<unknown>")
        for action in plan.get("actions", [])
        if isinstance(action, dict)
        and action.get("status") not in {"planned", "completed-unverified"}
    ]
    if invalid_states:
        raise ValueError(
            "run initialization refuses plan-supplied runtime states: "
            + ", ".join(invalid_states)
        )
    freeze = verify_candidate_freeze(plan, candidate_artifact, candidate_seal)
    budgets = build_budget_limits(
        max_actions=max_actions,
        max_attempts=max_attempts,
        max_result_bytes=max_result_bytes,
        max_seconds=max_seconds,
        max_requests=max_requests,
        max_requests_per_provider=max_requests_per_provider,
        max_records=max_records,
        max_consecutive_no_novelty=max_consecutive_no_novelty,
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / "plan.json", plan)
    freeze_payload = None
    if freeze is not None:
        candidate_dir = run_dir / "candidates"
        candidate_dir.mkdir()
        artifact_destination = candidate_dir / "candidates.json"
        seal_destination = candidate_dir / "freeze-seal.json"
        shutil.copyfile(freeze["artifactPath"], artifact_destination)
        shutil.copyfile(freeze["sealPath"], seal_destination)
        freeze_payload = {
            "artifactPath": str(artifact_destination.relative_to(run_dir)),
            "artifactSha256": freeze["artifactSha256"],
            "sealPath": str(seal_destination.relative_to(run_dir)),
            "sealSha256": freeze["sealSha256"],
        }
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
            "candidateFreeze": freeze_payload,
        },
        occurred_at=started_at,
    )
    _, _, state = _load(run_dir)
    return state


def next_task_packet(run_dir: Path, limit: int) -> dict[str, Any]:
    if limit < 1:
        raise ValueError("limit must be positive")
    plan, _, state = _load(run_dir)
    if state["status"] != "active":
        return {"run": state, "stopReason": state.get("stop"), "recommendedBatch": []}
    budget = global_stop_reason(state, time.time())
    if budget:
        return {"run": state, "stopReason": budget, "recommendedBatch": []}
    working = working_plan(plan, state)
    frontier = build_frontier(working, max(limit, len(working["actions"])))
    action_map = {action["actionId"]: action for action in working["actions"]}
    available: list[dict[str, Any]] = []
    budget_blocked: list[dict[str, Any]] = []
    for ranked in frontier["recommendedBatch"] + frontier["readyUnscheduled"]:
        reason = action_stop_reason(plan, state, action_map[ranked["actionId"]])
        if reason:
            budget_blocked.append(
                {"actionId": ranked["actionId"], "reasons": [reason]}
            )
        else:
            available.append(ranked)
    batch: list[dict[str, Any]] = []
    for ranked in available[:limit]:
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
    terminal = actions_terminal(state)
    stop_reason = "all-actions-terminal" if terminal else None
    if not batch and not stop_reason:
        stop_reason = (
            sorted(item["reasons"][0] for item in budget_blocked)[0]
            if budget_blocked
            else "no-executable-actions"
        )
    return {
        "schemaVersion": "research-task-packet-1.0",
        "runId": state["runId"],
        "sourcePlanSha256": state["sourcePlanSha256"],
        "journalHeadSha256": state["journalHeadSha256"],
        "scoreMeaning": frontier["scoreMeaning"],
        "recommendedBatch": batch,
        "blockedActions": frontier["blockedActions"] + budget_blocked,
        "usage": state["usage"],
        "budgets": state["budgets"],
        "stopReason": stop_reason,
    }

def start_action(
    run_dir: Path,
    action_id: str,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        validation = validate_plan(plan)
        if not validation.valid:
            raise ValueError("run plan is no longer valid: " + "; ".join(validation.errors))
        if state["status"] != "active":
            raise ValueError("run is not active")
        if idempotency_key is not None and (
            len(idempotency_key) < 8
            or len(idempotency_key) > 128
            or any(
                character
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
                for character in idempotency_key
            )
        ):
            raise ValueError("idempotency_key must be a safe 8-128 character identifier")
        if idempotency_key is not None:
            for existing_id, existing in state["actions"].items():
                for attempt in existing["attempts"]:
                    if attempt["idempotencyKey"] != idempotency_key:
                        continue
                    if existing_id != action_id:
                        raise ValueError("idempotency_key was already used for another action")
                    action = next(
                        item for item in plan["actions"] if item["actionId"] == action_id
                    )
                    return {
                        "attemptId": attempt["attemptId"],
                        "idempotencyKey": idempotency_key,
                        "leaseExpiresAt": attempt["leaseExpiresAt"],
                        "budgetReservation": copy.deepcopy(
                            attempt["budgetReservation"]
                        ),
                        "journalEventSha256": state["journalHeadSha256"],
                        "action": copy.deepcopy(action),
                        "run": state,
                        "replayed": True,
                    }
        budget = global_stop_reason(state, time.time())
        if budget:
            raise ValueError(budget)
        action = next(item for item in plan["actions"] if item["actionId"] == action_id)
        action_budget = action_stop_reason(plan, state, action)
        if action_budget:
            raise ValueError(action_budget)
        packet = next_task_packet(run_dir, max(1, len(plan.get("actions", [])) * 2))
        ready = {item["actionId"]: item for item in packet["recommendedBatch"]}
        if action_id not in ready:
            raise ValueError(f"action is not ready: {action_id}")
        spec_errors = validate_execution_spec(action)
        if spec_errors:
            raise ValueError("; ".join(spec_errors))
        attempt_number = len(state["actions"][action_id]["attempts"]) + 1
        max_attempts = int(action["execution"]["maxAttempts"])
        if attempt_number > max_attempts:
            raise ValueError(f"action {action_id} exhausted its retry limit")
        attempt_id = f"{action_id}.attempt-{attempt_number:03d}"
        idempotency_key = idempotency_key or value_sha256(
            {
                "runId": state["runId"],
                "planSha256": state["sourcePlanSha256"],
                "actionId": action_id,
                "attempt": attempt_number,
                "execution": action["execution"],
            }
        )
        now = time.time()
        lease_expires_at = min(
            now + int(action["execution"]["timeoutSeconds"]),
            state["startedAt"] + state["budgets"]["maxSeconds"],
        )
        if lease_expires_at <= now:
            raise ValueError("budget-exhausted:max-seconds")
        reservation = reservation_for_action(plan, action, state)
        event = append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "action-started",
            {
                "actionId": action_id,
                "attemptId": attempt_id,
                "idempotencyKey": idempotency_key,
                "leaseExpiresAt": lease_expires_at,
                "budgetReservation": reservation,
            },
        )
        _, _, updated = _load(run_dir)
        return {
            "attemptId": attempt_id,
            "idempotencyKey": idempotency_key,
            "leaseExpiresAt": lease_expires_at,
            "budgetReservation": reservation,
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
    _executor_token: object | None = None,
) -> dict[str, Any]:
    if not summary.strip():
        raise ValueError("result summary is required")
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        action_state = state["actions"].get(action_id)
        if (
            action_state
            and action_state["status"] == "completed"
            and action_state["attempts"][-1]["attemptId"] == attempt_id
        ):
            result = action_state["resultRefs"][-1]
            if not replayed_result_matches(
                result,
                result_path,
                summary,
                source_ids,
                attachment_paths,
                acceptance_evidence,
            ):
                raise ValueError("completed attempt was replayed with a different payload")
            return {"result": result, "run": state, "replayed": True}
        if not action_state or action_state["status"] != "running":
            raise ValueError(f"action is not running: {action_id}")
        attempt = action_state["attempts"][-1]
        if attempt["attemptId"] != attempt_id:
            raise ValueError("attempt_id does not match the active attempt")
        if time.time() > float(attempt["leaseExpiresAt"]):
            raise TimeoutError("action lease expired before result completion")
        action = next(item for item in plan["actions"] if item["actionId"] == action_id)
        validation = validate_plan(plan)
        if not validation.valid:
            raise ValueError("run plan is no longer valid: " + "; ".join(validation.errors))
        known_sources = {source["sourceId"] for source in plan.get("sources", [])}
        if not source_ids:
            raise ValueError("result must cite at least one declared source")
        if any(source_id not in known_sources for source_id in source_ids):
            raise ValueError("result references an unknown source")
        action_sources = {
            source_id
            for source_id in action.get("sourceIds", [])
            if isinstance(source_id, str)
        }
        if action_sources and not action_sources.intersection(source_ids):
            raise ValueError("result must cite at least one source declared by the action")
        executor = action.get("execution", {}).get("executor")
        if executor == "codex-research":
            if _executor_token is not None:
                raise ValueError("agent results cannot use an executor completion token")
            if result_path is None:
                raise ValueError("codex-research completion requires a structured result file")
            lineage = sealed_lineage_registry(run_dir, plan, state, action)
            metadata = validate_agent_result(
                result_path, action, plan,
                allowed_source_snapshot_ids=lineage["sourceSnapshotIds"],
                allowed_normalized_record_ids=lineage["normalizedRecordIds"])
            sealed_evidence = metadata["acceptanceEvidence"]
            if acceptance_evidence is not None and acceptance_evidence != sealed_evidence:
                raise ValueError("acceptance evidence differs from the sealed result")
            evidence = sealed_evidence
            if not set(source_ids).issubset(metadata["citedSourceIds"]):
                raise ValueError("result sourceIds are not supported by sealed observations")
        else:
            if _executor_token is not _DETERMINISTIC_COMPLETION:
                raise ValueError(
                    "deterministic actions can only complete through their bound executor"
                )
            lineage = sealed_lineage_registry(run_dir, plan, state, action)
            artifact_snapshots: set[str] = set()
            if result_path is not None:
                result_value = read_json(result_path)
                artifact_snapshots, _ = artifact_lineage(result_value)
            metadata = deterministic_result_metadata(
                plan,
                action,
                source_ids,
                source_snapshot_ids=(
                    lineage["sourceSnapshotIds"] | artifact_snapshots
                ),
            )
            evidence = acceptance_evidence or []
        criteria = action.get("execution", {}).get("acceptanceCriteria", [])
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
        budget_usage = completion_budget_usage(action, metadata, result_path)
        budget_problem = completion_problem(
            state,
            action,
            budget_usage,
            attempt["budgetReservation"],
        )
        if budget_problem:
            raise ValueError(budget_problem)
        prospective_bytes = prospective_result_bytes(
            action_id,
            attempt_id,
            result_path,
            summary,
            source_ids,
            attachment_paths,
            criteria,
            evidence,
        )
        if (
            state["usage"]["resultBytes"] + prospective_bytes
            > state["budgets"]["maxResultBytes"]
        ):
            raise ValueError("result would exceed max_result_bytes")
        ended_at = time.time()
        seal_context = build_result_seal_context(
            state,
            action,
            attempt,
            metadata,
            evidence,
            budget_usage,
            prospective_bytes,
            ended_at,
        )
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
            seal_context,
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


def resume_run(
    run_dir: Path,
    *,
    override_stop: bool = False,
    now: float | None = None,
) -> dict[str, Any]:
    with run_lock(run_dir):
        plan, _, state = _load(run_dir)
        current_time = time.time() if now is None else now
        if state["status"] == "stopped" and not override_stop:
            raise ValueError("stopped run requires override_stop to resume")
        live = [
            action_id
            for action_id, action_state in state["actions"].items()
            if action_state["status"] == "running"
            and float(action_state["attempts"][-1]["leaseExpiresAt"]) > current_time
        ]
        if live:
            raise ValueError("cannot resume while action leases are active: " + ", ".join(live))
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
                occurred_at=current_time,
            )
            work_dir = run_dir / "work"
            if work_dir.is_dir():
                for path in work_dir.glob(f"{action_id}-*"):
                    if path.is_file():
                        path.unlink()
        append_event(
            run_dir / "events.jsonl",
            state["runId"],
            "run-resumed",
            {"overrideStop": override_stop},
            occurred_at=current_time,
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
    from ij_executors import execute

    return execute(run_dir, action_id)


def run_status(run_dir: Path) -> dict[str, Any]:
    _, events, state = _load(run_dir)
    state["eventCount"] = len(events)
    state["budgetStopReason"] = global_stop_reason(state, time.time())
    return state
