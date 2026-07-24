from __future__ import annotations

import math
from typing import Any


BENEFIT_KEYS = {"discrimination", "falsification", "independence", "coverage"}
BURDEN_KEYS = {"compute", "humanReview", "delay", "money"}
LANES = {"discrimination", "negative-control", "coverage", "corroboration"}


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def unit_score(value: Any) -> bool:
    return finite_number(value) and 0 <= float(value) <= 1


def validate_policy(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = plan.get("policy")
    if not isinstance(policy, dict):
        return ["policy must be an object"]
    if not isinstance(policy.get("scoreVersion"), str) or not policy.get("scoreVersion"):
        errors.append("policy.scoreVersion is required")
    pattern = policy.get("lanePattern")
    if not isinstance(pattern, list) or not pattern:
        errors.append("policy.lanePattern must be a non-empty array")
    elif any(lane not in LANES for lane in pattern):
        errors.append("policy.lanePattern contains an invalid lane")
    errors.extend(_validate_weights(policy.get("weights"), BENEFIT_KEYS, "policy.weights"))
    errors.extend(
        _validate_weights(policy.get("burdenWeights"), BURDEN_KEYS, "policy.burdenWeights")
    )
    stopping = policy.get("stoppingRules")
    if (
        not isinstance(stopping, list)
        or not stopping
        or any(not isinstance(rule, str) or not rule for rule in stopping)
    ):
        errors.append("policy.stoppingRules must be a non-empty string array")
    return errors


def _validate_weights(value: Any, keys: set[str], label: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    if set(value) != keys:
        errors.append(f"{label} must contain exactly: {', '.join(sorted(keys))}")
        return errors
    if any(not unit_score(weight) for weight in value.values()):
        errors.append(f"{label} values must be finite numbers between 0 and 1")
        return errors
    if not math.isclose(sum(float(weight) for weight in value.values()), 1.0, abs_tol=1e-9):
        errors.append(f"{label} values must sum to 1")
    return errors
