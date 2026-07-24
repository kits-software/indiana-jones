from __future__ import annotations

import re
from typing import Any

from ij_acceptance import acceptance_check_errors
from ij_ingest import SUPPORTED_FORMATS, validate_query_artifact
from ij_source_contract import acquisition_binding_errors


EXECUTORS = {"codex-research", "ingest-source", "reconcile-records"}


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
        try:
            validate_query_artifact(inputs.get("query", {}))
        except ValueError as error:
            errors.append(f"action {action_id} {error}")
    elif isinstance(inputs, dict) and executor == "reconcile-records":
        artifacts = inputs.get("artifacts")
        if (
            not isinstance(artifacts, list)
            or not artifacts
            or len(artifacts) > 100
            or any(not isinstance(path, str) or not path for path in artifacts)
        ):
            errors.append(f"action {action_id} reconcile-records requires 1-100 artifact paths")
    errors.extend(acceptance_check_errors(action))
    return errors


def execution_readiness_errors(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for action in plan.get("actions", []):
        if isinstance(action, dict) and action.get("status") == "planned":
            errors.extend(validate_execution_spec(action))
    errors.extend(acquisition_binding_errors(plan))
    return errors
