from __future__ import annotations

import math
from typing import Any


REQUIRED_PERMISSION_KEYS = {
    "jurisdiction",
    "landAccess",
    "detecting",
    "excavation",
    "heritage",
    "findsReporting",
    "communityAuthority",
}


def _finite_probability(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and 0 <= float(value) <= 1
    )


def _confirmed_permission(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("state") in {"confirmed", "not-required"}
        and isinstance(value.get("basis"), str)
        and bool(value["basis"].strip())
        and isinstance(value.get("scope"), str)
        and bool(value["scope"].strip())
    )


def probability_gate_errors(
    calibration: dict[str, Any],
    *,
    case: dict[str, Any] | None = None,
    exact_high_risk_target: bool = False,
) -> list[str]:
    errors: list[str] = []
    required_strings = (
        "eventDefinition",
        "denominator",
        "detectionProcess",
        "reportingProcess",
        "biasTreatment",
        "validityDomain",
    )
    for key in required_strings:
        value = calibration.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"calibration.{key} is required")
    counts = calibration.get("sample")
    if not isinstance(counts, dict):
        errors.append("calibration.sample must be an object")
    else:
        for key in ("positive", "negative", "heldOut"):
            value = counts.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                errors.append(f"calibration.sample.{key} must be a positive integer")
    for key in ("geographicallySeparated", "modelFrozen", "featuresFrozen"):
        if calibration.get(key) is not True:
            errors.append(f"calibration.{key} must be true")
    held_out = calibration.get("heldOutMetrics")
    if not isinstance(held_out, dict):
        errors.append("calibration.heldOutMetrics must be an object")
    else:
        brier = held_out.get("brierScore")
        if not _finite_probability(brier):
            errors.append("calibration.heldOutMetrics.brierScore must be between 0 and 1")
        bins = held_out.get("reliabilityBins")
        if not isinstance(bins, list) or len(bins) < 3:
            errors.append(
                "calibration.heldOutMetrics.reliabilityBins requires at least three bins"
            )
    interval = calibration.get("uncertaintyInterval")
    if (
        not isinstance(interval, list)
        or len(interval) != 2
        or not all(_finite_probability(value) for value in interval)
        or float(interval[0]) > float(interval[1])
    ):
        errors.append("calibration.uncertaintyInterval must be an ordered probability pair")
    estimate = calibration.get("estimatedProbability")
    if not _finite_probability(estimate):
        errors.append("calibration.estimatedProbability must be between 0 and 1")

    if exact_high_risk_target:
        case = case or {}
        if case.get("researchMode") not in {
            "treasure-research-restricted",
            "authority-casework",
        }:
            errors.append("exact high-risk probability requires restricted research mode")
        if case.get("disclosure") not in {"restricted", "heritage-authority-only"}:
            errors.append("exact high-risk probability requires restricted disclosure")
        permissions = case.get("permissionBundle")
        if not isinstance(permissions, dict):
            errors.append("exact high-risk probability requires a permission bundle")
        else:
            for key in sorted(REQUIRED_PERMISSION_KEYS):
                if not _confirmed_permission(permissions.get(key)):
                    errors.append(f"permissionBundle.{key} is not confirmed")
    return errors


def calibrated_probability_report(
    calibration: dict[str, Any],
    *,
    case: dict[str, Any] | None = None,
    exact_high_risk_target: bool = False,
) -> dict[str, Any]:
    errors = probability_gate_errors(
        calibration,
        case=case,
        exact_high_risk_target=exact_high_risk_target,
    )
    if errors:
        raise ValueError("numeric probability gate failed: " + "; ".join(errors))
    return {
        "schemaVersion": "calibrated-archaeological-probability-1.0",
        "eventDefinition": calibration["eventDefinition"],
        "denominator": calibration["denominator"],
        "estimatedProbability": float(calibration["estimatedProbability"]),
        "uncertaintyInterval": [
            float(calibration["uncertaintyInterval"][0]),
            float(calibration["uncertaintyInterval"][1]),
        ],
        "heldOutMetrics": calibration["heldOutMetrics"],
        "validityDomain": calibration["validityDomain"],
        "biasTreatment": calibration["biasTreatment"],
        "disclosure": (
            "restricted" if exact_high_risk_target else case.get("disclosure", "public")
            if case
            else "public"
        ),
        "warning": (
            "This estimates the declared event under the stated validity domain; "
            "it is not permission for physical recovery."
        ),
    }
