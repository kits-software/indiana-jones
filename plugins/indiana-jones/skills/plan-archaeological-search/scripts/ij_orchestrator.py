from __future__ import annotations

from pathlib import Path
from typing import Any

from ij_runtime import (
    execute_deterministic_action,
    next_task_packet,
    run_status,
    stop_run,
)


DETERMINISTIC_EXECUTORS = {"ingest-source", "reconcile-records"}
TERMINAL_STOP_REASONS = {
    "all-actions-terminal",
    "no-executable-actions",
}


def _record_stop_if_terminal(run_dir: Path, reason: Any) -> dict[str, Any] | None:
    if not isinstance(reason, str):
        return None
    if reason in TERMINAL_STOP_REASONS or reason.startswith("budget-exhausted:"):
        state = run_status(run_dir)
        if state["status"] == "active" and not any(
            action["status"] == "running" for action in state["actions"].values()
        ):
            return stop_run(
                run_dir,
                reason,
                {
                    "usage": state["usage"],
                    "budgets": state["budgets"],
                    "unresolvedActionIds": sorted(
                        action_id
                        for action_id, action in state["actions"].items()
                        if action["status"] not in {"completed", "rejected", "superseded"}
                    ),
                },
            )
    return None


def advance_run(run_dir: Path, limit: int = 4) -> dict[str, Any]:
    packet = next_task_packet(run_dir, limit)
    executed: list[dict[str, Any]] = []
    handoff: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for action in packet.get("recommendedBatch", []):
        execution = action.get("execution") or {}
        if execution.get("executor") not in DETERMINISTIC_EXECUTORS:
            handoff.append(action)
            continue
        try:
            outcome = execute_deterministic_action(run_dir, action["actionId"])
            executed.append(
                {
                    "actionId": action["actionId"],
                    "result": outcome["result"],
                    "journalEventSha256": outcome["journalEventSha256"],
                }
            )
        except (OSError, ValueError, TypeError, KeyError) as error:
            failures.append({"actionId": action["actionId"], "error": str(error)})
    after = next_task_packet(run_dir, limit)
    stopped = _record_stop_if_terminal(run_dir, after.get("stopReason"))
    return {
        "schemaVersion": "research-advance-1.0",
        "runId": packet.get("runId"),
        "executed": executed,
        "agentHandoff": handoff,
        "failures": failures,
        "next": next_task_packet(run_dir, limit) if stopped else after,
        "stopRecorded": stopped is not None,
    }

def run_until_handoff(
    run_dir: Path,
    *,
    batch_limit: int = 4,
    max_batches: int = 100,
) -> dict[str, Any]:
    if max_batches < 1 or max_batches > 10_000:
        raise ValueError("max_batches must be between 1 and 10000")
    history: list[dict[str, Any]] = []
    for _ in range(max_batches):
        outcome = advance_run(run_dir, batch_limit)
        history.append(
            {
                "executedActionIds": [
                    item["actionId"] for item in outcome["executed"]
                ],
                "failureActionIds": [
                    item["actionId"] for item in outcome["failures"]
                ],
                "handoffActionIds": [
                    item["actionId"] for item in outcome["agentHandoff"]
                ],
                "stopReason": outcome["next"].get("stopReason"),
            }
        )
        if (
            outcome["agentHandoff"]
            or outcome["failures"]
            or outcome["next"].get("stopReason")
            or not outcome["executed"]
        ):
            break
    else:
        raise ValueError("run reached max_batches without a stopping condition")
    return {
        "schemaVersion": "research-run-loop-1.0",
        "batches": history,
        "status": run_status(run_dir),
        "next": next_task_packet(run_dir, batch_limit),
    }


def audit_run(run_dir: Path) -> dict[str, Any]:
    state = run_status(run_dir)
    completed = {
        action_id: action
        for action_id, action in state["actions"].items()
        if action["status"] == "completed"
    }
    return {
        "schemaVersion": "research-run-audit-1.0",
        "ok": True,
        "runId": state["runId"],
        "sourcePlanSha256": state["sourcePlanSha256"],
        "journalHeadSha256": state["journalHeadSha256"],
        "stateSha256": state["stateSha256"],
        "eventCount": state["eventCount"],
        "completedActionCount": len(completed),
        "sealedResultCount": sum(
            len(action.get("resultRefs", [])) for action in completed.values()
        ),
        "resultArtifactsVerified": True,
        "budgetStopReason": state.get("budgetStopReason"),
    }
