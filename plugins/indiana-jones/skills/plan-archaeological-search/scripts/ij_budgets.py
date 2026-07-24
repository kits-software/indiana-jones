from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ij_journal import value_sha256


LIMIT_MAXIMUMS = {
    "maxActions": 100_000,
    "maxAttempts": 1_000_000,
    "maxResultBytes": 10_000_000_000,
    "maxSeconds": 31_536_000,
    "maxRequests": 1_000_000,
    "maxRequestsPerProvider": 1_000_000,
    "maxRecords": 100_000_000,
    "maxConsecutiveNoNovelty": 100_000,
}
GLOBAL_STOP_PRIORITY = (
    ("maxActions", "uniqueActionsStarted", "budget-exhausted:max-actions"),
    ("maxAttempts", "attemptsStarted", "budget-exhausted:max-attempts"),
    ("maxResultBytes", "resultBytes", "budget-exhausted:max-result-bytes"),
    ("maxRequests", "requestsStarted", "budget-exhausted:max-requests"),
    (
        "maxConsecutiveNoNovelty",
        "consecutiveNoNovelty",
        "stop:no-novelty-threshold",
    ),
)
_SAFE_PROVIDER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_TERMINAL_ACTION_STATES = {
    "completed",
    "completed-unverified",
    "blocked",
    "failed",
    "rejected",
    "cancelled",
    "superseded",
}


def _positive_int(value: Any, label: str, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ValueError(f"{label} must be an integer between 1 and {maximum}")
    return value


def build_budget_limits(
    *,
    max_actions: int,
    max_attempts: int,
    max_result_bytes: int,
    max_seconds: int,
    max_requests: int | None = None,
    max_requests_per_provider: int | None = None,
    max_records: int | None = None,
    max_consecutive_no_novelty: int | None = None,
) -> dict[str, int]:
    actions = _positive_int(max_actions, "max_actions", LIMIT_MAXIMUMS["maxActions"])
    attempts = _positive_int(
        max_attempts,
        "max_attempts",
        LIMIT_MAXIMUMS["maxAttempts"],
    )
    limits = {
        "maxActions": actions,
        "maxAttempts": attempts,
        "maxResultBytes": _positive_int(
            max_result_bytes,
            "max_result_bytes",
            LIMIT_MAXIMUMS["maxResultBytes"],
        ),
        "maxSeconds": _positive_int(
            max_seconds,
            "max_seconds",
            LIMIT_MAXIMUMS["maxSeconds"],
        ),
        "maxRequests": _positive_int(
            attempts if max_requests is None else max_requests,
            "max_requests",
            LIMIT_MAXIMUMS["maxRequests"],
        ),
        "maxRequestsPerProvider": _positive_int(
            attempts
            if max_requests_per_provider is None
            else max_requests_per_provider,
            "max_requests_per_provider",
            LIMIT_MAXIMUMS["maxRequestsPerProvider"],
        ),
        "maxRecords": _positive_int(
            100_000 if max_records is None else max_records,
            "max_records",
            LIMIT_MAXIMUMS["maxRecords"],
        ),
        "maxConsecutiveNoNovelty": _positive_int(
            actions
            if max_consecutive_no_novelty is None
            else max_consecutive_no_novelty,
            "max_consecutive_no_novelty",
            LIMIT_MAXIMUMS["maxConsecutiveNoNovelty"],
        ),
    }
    return limits


def validate_budget_limits(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != set(LIMIT_MAXIMUMS):
        raise ValueError("run budget object is incomplete or has unknown fields")
    return {
        key: _positive_int(value[key], key, maximum)
        for key, maximum in LIMIT_MAXIMUMS.items()
    }


def initial_usage() -> dict[str, Any]:
    return {
        "uniqueActionsStarted": 0,
        "attemptsStarted": 0,
        "actionsCompleted": 0,
        "resultBytes": 0,
        "requestsStarted": 0,
        "requestsByProvider": {},
        "recordsReserved": 0,
        "recordsReturned": 0,
        "noveltyKeysSeen": [],
        "consecutiveNoNovelty": 0,
        "exhaustedSourceQueries": [],
    }


def initial_run_state(
    plan: dict[str, Any],
    started: dict[str, Any],
    schema_version: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": schema_version,
        "runId": started["runId"],
        "sourcePlanSha256": started["sourcePlanSha256"],
        "status": "active",
        "startedAt": started["startedAt"],
        "updatedAt": started["startedAt"],
        "budgets": copy.deepcopy(started["budgets"]),
        "usage": initial_usage(),
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


def working_plan(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    working = copy.deepcopy(plan)
    for action in working.get("actions", []):
        runtime = state["actions"][action["actionId"]]
        action["status"] = runtime["status"]
        action["resultRefs"] = copy.deepcopy(runtime.get("resultRefs", []))
        action["_runtimeEvidenceVerified"] = bool(
            runtime["status"] == "completed" and runtime.get("resultRefs")
        )
    return working


def actions_terminal(state: dict[str, Any]) -> bool:
    return all(
        action["status"] in _TERMINAL_ACTION_STATES
        for action in state["actions"].values()
    )


def _source(plan: dict[str, Any], source_id: Any) -> dict[str, Any] | None:
    return next(
        (
            source
            for source in plan.get("sources", [])
            if isinstance(source, dict) and source.get("sourceId") == source_id
        ),
        None,
    )


def _safe_provider(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SAFE_PROVIDER.fullmatch(value):
        raise ValueError("provider identity must be a safe 1-128 character identifier")
    return value


def provider_for_action(plan: dict[str, Any], action: dict[str, Any]) -> str | None:
    spec = action.get("execution")
    inputs = spec.get("inputs") if isinstance(spec, dict) else {}
    executor = spec.get("executor") if isinstance(spec, dict) else None
    if executor == "reconcile-records":
        return None
    explicit = inputs.get("provider") if isinstance(inputs, dict) else None
    explicit = explicit or action.get("platform") or action.get("provider")
    if explicit is not None:
        return _safe_provider(explicit)
    if executor == "ingest-source" and isinstance(inputs, dict):
        source = _source(plan, inputs.get("sourceId"))
        acquisition = source.get("acquisition") if isinstance(source, dict) else None
        locator = inputs.get("locator")
        if isinstance(acquisition, dict):
            locator = acquisition.get("locator", locator)
        if isinstance(locator, str):
            host = urlparse(locator).hostname
            if host:
                return _safe_provider(host.casefold())
        source_id = inputs.get("sourceId")
        if isinstance(source_id, str):
            return _safe_provider(f"local:{source_id}")
    return _safe_provider(str(executor)) if isinstance(executor, str) else None


def source_query_key(action: dict[str, Any]) -> str | None:
    spec = action.get("execution")
    if not isinstance(spec, dict) or spec.get("executor") != "ingest-source":
        return None
    inputs = spec.get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("ingest action lacks execution inputs")
    return value_sha256(
        {
            "sourceId": inputs.get("sourceId"),
            "locator": inputs.get("locator"),
            "format": inputs.get("format"),
            "query": inputs.get("query", {}),
        }
    )


def reservation_for_action(
    plan: dict[str, Any],
    action: dict[str, Any],
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provider = provider_for_action(plan, action)
    query_key = source_query_key(action)
    record_limit = 0
    if query_key is not None:
        requested = int(action["execution"]["inputs"].get("maxRecords", 5_000))
        if state is None:
            record_limit = requested
        else:
            available = (
                state["budgets"]["maxRecords"]
                - state["usage"]["recordsReturned"]
                - state["usage"]["recordsReserved"]
            )
            record_limit = min(requested, max(0, available))
    return {
        "requests": 0 if provider is None else 1,
        "providerId": provider,
        "sourceQueryKey": query_key,
        "recordLimit": record_limit,
    }


def _validated_reservation(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "requests",
        "providerId",
        "sourceQueryKey",
        "recordLimit",
    }:
        raise ValueError("action budget reservation is incomplete")
    requests = value.get("requests")
    if requests not in {0, 1} or isinstance(requests, bool):
        raise ValueError("action budget reservation requests must be zero or one")
    provider = _safe_provider(value.get("providerId"))
    query_key = value.get("sourceQueryKey")
    if query_key is not None and (
        not isinstance(query_key, str) or not re.fullmatch(r"[0-9a-f]{64}", query_key)
    ):
        raise ValueError("action budget reservation source query key is invalid")
    if (requests == 0) != (provider is None):
        raise ValueError("action budget reservation provider does not match requests")
    record_limit = value.get("recordLimit")
    if (
        not isinstance(record_limit, int)
        or isinstance(record_limit, bool)
        or not 0 <= record_limit <= 100_000
        or (query_key is None and record_limit != 0)
    ):
        raise ValueError("action budget reservation record limit is invalid")
    return {
        "requests": requests,
        "providerId": provider,
        "sourceQueryKey": query_key,
        "recordLimit": record_limit,
    }


def reservation_problem(
    state: dict[str, Any],
    reservation: dict[str, Any],
) -> str | None:
    reservation = _validated_reservation(reservation)
    requests = reservation["requests"]
    usage = state["usage"]
    budgets = state["budgets"]
    if usage["requestsStarted"] + requests > budgets["maxRequests"]:
        return "budget-exhausted:max-requests"
    provider = reservation["providerId"]
    if provider is not None and (
        usage["requestsByProvider"].get(provider, 0) + requests
        > budgets["maxRequestsPerProvider"]
    ):
        return "budget-exhausted:max-requests-per-provider"
    return None


def action_stop_reason(
    plan: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
) -> str | None:
    reservation = reservation_for_action(plan, action, state)
    problem = reservation_problem(state, reservation)
    if problem:
        return problem
    if reservation["sourceQueryKey"] is not None:
        if reservation["recordLimit"] < 1:
            return "budget-exhausted:max-records"
        if reservation["sourceQueryKey"] in state["usage"]["exhaustedSourceQueries"]:
            return "source-exhausted:query"
    return None


def apply_start_reservation(
    state: dict[str, Any],
    plan: dict[str, Any],
    action: dict[str, Any],
    supplied: Any,
) -> None:
    reservation = _validated_reservation(supplied)
    if reservation != reservation_for_action(plan, action, state):
        raise ValueError("journal action budget reservation does not match the plan")
    if reservation["sourceQueryKey"] is not None and reservation["recordLimit"] < 1:
        raise ValueError("budget-exhausted:max-records")
    problem = reservation_problem(state, reservation)
    if problem:
        raise ValueError(problem)
    requests = reservation["requests"]
    state["usage"]["requestsStarted"] += requests
    provider = reservation["providerId"]
    if provider is not None:
        current = state["usage"]["requestsByProvider"].get(provider, 0)
        state["usage"]["requestsByProvider"][provider] = current + requests
    state["usage"]["recordsReserved"] += reservation["recordLimit"]


def global_stop_reason(state: dict[str, Any], now: float) -> str | None:
    usage = state["usage"]
    budgets = state["budgets"]
    for budget_key, usage_key, reason in GLOBAL_STOP_PRIORITY[:3]:
        if usage[usage_key] >= budgets[budget_key]:
            return reason
    if now - state["startedAt"] >= budgets["maxSeconds"]:
        return "budget-exhausted:max-seconds"
    for budget_key, usage_key, reason in GLOBAL_STOP_PRIORITY[3:]:
        if usage[usage_key] >= budgets[budget_key]:
            return reason
    return None


def _strings(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or len(value) > 100_000
        or any(
            not isinstance(item, str)
            or not item
            or len(item) > 512
            or any(ord(character) < 32 for character in item)
            for item in value
        )
    ):
        raise ValueError(f"{label} must be a bounded non-empty string array")
    return value


def _prefixed(values: list[str], prefix: str) -> set[str]:
    return {f"{prefix}:{value}" for value in values}


def agent_novelty_keys(metadata: dict[str, Any]) -> list[str]:
    keys = _prefixed(metadata.get("originFamilyIds", []), "origin")
    keys.update(_prefixed(metadata.get("claimIds", []), "claim"))
    keys.update(_prefixed(metadata.get("normalizedRecordIds", []), "object"))
    keys.update(_prefixed(metadata.get("objectIds", []), "object"))
    keys.update(_prefixed(metadata.get("contradictionIds", []), "contradiction"))
    return sorted(keys)


def _artifact_budget_usage(
    action: dict[str, Any],
    result_path: Path,
) -> tuple[int, list[str], bool | None]:
    try:
        artifact = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot account for deterministic result: {error}") from error
    if not isinstance(artifact, dict):
        raise ValueError("deterministic result must be an object for budget accounting")
    executor = action["execution"]["executor"]
    if executor == "ingest-source":
        records = artifact.get("records")
        query = artifact.get("queryArtifact")
        if not isinstance(records, list) or not isinstance(query, dict):
            raise ValueError("ingest result lacks records or query metadata")
        pagination = query.get("pagination")
        if not isinstance(pagination, dict) or not isinstance(
            pagination.get("sourceExhausted"), bool
        ):
            raise ValueError("ingest result lacks a source exhaustion decision")
        keys: set[str] = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("ingest result record must be an object")
            origin = record.get("originFamilyId")
            record_id = record.get("recordId")
            if not isinstance(origin, str) or not isinstance(record_id, str):
                raise ValueError("ingest result record lacks novelty lineage")
            keys.update((f"origin:{origin}", f"object:{record_id}"))
        return len(records), sorted(keys), pagination["sourceExhausted"]
    if executor == "reconcile-records":
        entities = artifact.get("entities")
        if not isinstance(entities, list):
            raise ValueError("reconciliation result lacks entities")
        keys = set()
        for entity in entities:
            if not isinstance(entity, dict) or not isinstance(entity.get("entityId"), str):
                raise ValueError("reconciliation entity lacks entityId")
            entity_id = entity["entityId"]
            keys.add(f"object:{entity_id}")
            for origin in entity.get("originFamilyIds", []):
                if not isinstance(origin, str):
                    raise ValueError("reconciliation origin family is invalid")
                keys.add(f"origin:{origin}")
            conflicts = entity.get("fieldConflicts", {})
            fields = conflicts if isinstance(conflicts, list) else conflicts.keys()
            for field in fields:
                if not isinstance(field, str):
                    raise ValueError("reconciliation conflict field is invalid")
                keys.add(f"contradiction:{entity_id}:{field}")
        return 0, sorted(keys), None
    raise ValueError("unsupported deterministic executor for budget accounting")


def completion_budget_usage(
    action: dict[str, Any],
    metadata: dict[str, Any],
    result_path: Path | None,
) -> dict[str, Any]:
    executor = action["execution"]["executor"]
    if executor == "codex-research":
        records = len(metadata.get("normalizedRecordIds", []))
        novelty = agent_novelty_keys(metadata)
        exhausted = None
    else:
        if result_path is None:
            raise ValueError("deterministic completion lacks its result artifact")
        records, novelty, exhausted = _artifact_budget_usage(action, result_path)
    return {
        "records": records,
        "noveltyKeys": novelty,
        "sourceQueryKey": source_query_key(action),
        "sourceExhausted": exhausted,
    }


def validate_completion_usage(
    action: dict[str, Any],
    value: Any,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "records",
        "noveltyKeys",
        "sourceQueryKey",
        "sourceExhausted",
    }:
        raise ValueError("result budget usage is incomplete")
    records = value.get("records")
    if (
        not isinstance(records, int)
        or isinstance(records, bool)
        or not 0 <= records <= LIMIT_MAXIMUMS["maxRecords"]
    ):
        raise ValueError("result budget record count is invalid")
    novelty = _strings(value.get("noveltyKeys"), "result noveltyKeys")
    if novelty != sorted(set(novelty)):
        raise ValueError("result noveltyKeys must be sorted and unique")
    query_key = value.get("sourceQueryKey")
    expected_query = source_query_key(action)
    if query_key != expected_query:
        raise ValueError("result source query key does not match the action")
    exhausted = value.get("sourceExhausted")
    if expected_query is None:
        if exhausted is not None:
            raise ValueError("non-ingest result cannot declare source exhaustion")
    elif not isinstance(exhausted, bool):
        raise ValueError("ingest result requires a source exhaustion decision")
    return {
        "records": records,
        "noveltyKeys": novelty,
        "sourceQueryKey": query_key,
        "sourceExhausted": exhausted,
    }


def completion_problem(
    state: dict[str, Any],
    action: dict[str, Any],
    value: Any,
    reservation: Any,
) -> str | None:
    usage = validate_completion_usage(action, value)
    reserved = _validated_reservation(reservation)
    if (
        reserved["sourceQueryKey"] is not None
        and usage["records"] > reserved["recordLimit"]
    ):
        return "budget-exhausted:max-records"
    if state["usage"]["recordsReturned"] + usage["records"] > state["budgets"][
        "maxRecords"
    ]:
        return "budget-exhausted:max-records"
    return None


def apply_completion_usage(
    state: dict[str, Any],
    action: dict[str, Any],
    value: Any,
    reservation: Any,
) -> None:
    usage = validate_completion_usage(action, value)
    reserved = _validated_reservation(reservation)
    problem = completion_problem(state, action, usage, reserved)
    if problem:
        raise ValueError(problem)
    release_record_reservation(state, reserved)
    state["usage"]["recordsReturned"] += usage["records"]
    seen = set(state["usage"]["noveltyKeysSeen"])
    novel = set(usage["noveltyKeys"]).difference(seen)
    seen.update(usage["noveltyKeys"])
    state["usage"]["noveltyKeysSeen"] = sorted(seen)
    state["usage"]["consecutiveNoNovelty"] = (
        0 if novel else state["usage"]["consecutiveNoNovelty"] + 1
    )
    if usage["sourceExhausted"]:
        exhausted = set(state["usage"]["exhaustedSourceQueries"])
        exhausted.add(usage["sourceQueryKey"])
        state["usage"]["exhaustedSourceQueries"] = sorted(exhausted)


def release_record_reservation(
    state: dict[str, Any],
    reservation: Any,
) -> None:
    reserved = _validated_reservation(reservation)["recordLimit"]
    if reserved > state["usage"]["recordsReserved"]:
        raise ValueError("journal releases more record budget than was reserved")
    state["usage"]["recordsReserved"] -= reserved
