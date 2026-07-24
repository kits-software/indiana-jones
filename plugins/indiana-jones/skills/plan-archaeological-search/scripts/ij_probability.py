from __future__ import annotations

import math
import re
from typing import Any

from ij_calibration import FROZEN_INPUT_KEYS, held_out_evaluation_errors
from ij_spatial import add_google_maps_links

SHA256 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
DISCLOSURES = {"public", "restricted", "heritage-authority-only"}
RESEARCH_MODES = {
    "landscape-research",
    "treasure-research-public",
    "treasure-research-restricted",
    "authority-casework",
}
RESTRICTED_SPATIAL_VALUES = {
    "withhold",
    "authority-only",
    "restricted",
    "private",
    "non-public",
    "vulnerable",
    "sacred",
    "burial",
}
HEURISTIC_INPUT_SCHEMA = "heuristic-archaeological-assessment-input-1.0"
PROBABILITY_FIELDS = {
    "estimatedProbability",
    "probability",
    "probabilityPercent",
    "percentage",
}


def _finite_probability(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and 0 <= float(value) <= 1
    )


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _dataset_errors(calibration: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    references = calibration.get("datasetReferences")
    if not isinstance(references, list) or len(references) < 3:
        return [
            "calibration.datasetReferences requires training, calibration, "
            "and held-out dataset records"
        ]
    roles: set[str] = set()
    ids: set[str] = set()
    for index, reference in enumerate(references):
        prefix = f"calibration.datasetReferences[{index}]"
        if not isinstance(reference, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dataset_id = reference.get("datasetId")
        role = reference.get("role")
        if not _text(dataset_id):
            errors.append(f"{prefix}.datasetId is required")
        elif str(dataset_id) in ids:
            errors.append(f"{prefix}.datasetId must be unique")
        else:
            ids.add(str(dataset_id))
        if role not in {"training", "calibration", "held-out"}:
            errors.append(f"{prefix}.role is invalid")
        else:
            roles.add(str(role))
        if not isinstance(reference.get("recordCount"), int) or isinstance(
            reference.get("recordCount"), bool
        ) or reference.get("recordCount", 0) < 1:
            errors.append(f"{prefix}.recordCount must be a positive integer")
        if not isinstance(reference.get("sha256"), str) or not SHA256.fullmatch(
            reference["sha256"]
        ):
            errors.append(f"{prefix}.sha256 must be a 64-character SHA-256 digest")
    missing = {"training", "calibration", "held-out"} - roles
    if missing:
        errors.append(
            "calibration.datasetReferences is missing roles: "
            + ", ".join(sorted(missing))
        )
    return errors


def _reliability_bin_errors(bins: Any, held_out_count: int | None) -> list[str]:
    if not isinstance(bins, list) or len(bins) < 3:
        return [
            "calibration.heldOutMetrics.reliabilityBins requires at least three bins"
        ]
    errors: list[str] = []
    previous_upper = -1.0
    total = 0
    for index, item in enumerate(bins):
        prefix = f"calibration.heldOutMetrics.reliabilityBins[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        lower = item.get("lowerBound")
        upper = item.get("upperBound")
        predicted = item.get("predicted")
        observed = item.get("observed")
        count = item.get("count")
        if not all(_finite_probability(value) for value in (lower, upper)):
            errors.append(f"{prefix} bounds must be probabilities")
        elif float(lower) >= float(upper):
            errors.append(f"{prefix} must have lowerBound below upperBound")
        elif float(lower) < previous_upper:
            errors.append(f"{prefix} overlaps the preceding reliability bin")
        else:
            previous_upper = float(upper)
        if not _finite_probability(predicted) or not _finite_probability(observed):
            errors.append(f"{prefix} predicted and observed must be probabilities")
        elif _finite_probability(lower) and _finite_probability(upper) and not (
            float(lower) <= float(predicted) <= float(upper)
        ):
            errors.append(f"{prefix}.predicted must fall within its bin bounds")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            errors.append(f"{prefix}.count must be a positive integer")
        else:
            total += count
    if held_out_count is not None and total != held_out_count:
        errors.append(
            "calibration reliability-bin counts must equal calibration.sample.heldOut"
        )
    return errors


def probability_gate_errors(
    calibration: dict[str, Any],
    *,
    case: dict[str, Any] | None = None,
    exact_high_risk_target: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(exact_high_risk_target, bool):
        errors.append("exact_high_risk_target must be a boolean")
    supplied_case = case is not None
    case = case or {}
    if supplied_case and case.get("disclosure") not in DISCLOSURES:
        errors.append("case.disclosure is invalid")
    if "researchMode" in case and case.get("researchMode") not in RESEARCH_MODES:
        errors.append("case.researchMode is invalid")
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
    held_out_count: int | None = None
    if not isinstance(counts, dict):
        errors.append("calibration.sample must be an object")
    else:
        for key in ("positive", "negative", "heldOut"):
            value = counts.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                errors.append(f"calibration.sample.{key} must be a positive integer")
        held_out = counts.get("heldOut")
        if isinstance(held_out, int) and not isinstance(held_out, bool) and held_out > 0:
            held_out_count = held_out
    for key in (
        "geographicallySeparated",
        "modelFrozen",
        "featuresFrozen",
        "thresholdFrozen",
        "candidateSetFrozen",
    ):
        if calibration.get(key) is not True:
            errors.append(f"calibration.{key} must be true")
    for key in (
        "modelSha256",
        "featuresSha256",
        "thresholdSha256",
        "candidateSetSha256",
    ):
        value = calibration.get(key)
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            errors.append(f"calibration.{key} must be a 64-character SHA-256 digest")
    errors.extend(_dataset_errors(calibration))
    evaluation = calibration.get("heldOutEvaluation")
    evaluation_errors = held_out_evaluation_errors(evaluation)
    errors.extend(
        f"calibration.{error}" if error.startswith("heldOutEvaluation") else error
        for error in evaluation_errors
    )
    evaluated_metrics: dict[str, Any] | None = None
    if not evaluation_errors and isinstance(evaluation, dict):
        evaluated_metrics = evaluation["heldOutMetrics"]
        benchmark = evaluation["benchmark"]
        if benchmark.get("eventDefinition") != calibration.get("eventDefinition"):
            errors.append(
                "calibration.heldOutEvaluation eventDefinition does not match calibration"
            )
        if benchmark.get("denominator") != calibration.get("denominator"):
            errors.append(
                "calibration.heldOutEvaluation denominator does not match calibration"
            )
        for key in FROZEN_INPUT_KEYS:
            declared = calibration.get(key)
            evaluated = evaluation["frozenInputs"].get(key)
            if isinstance(declared, str) and declared.lower() != evaluated:
                errors.append(
                    f"calibration.heldOutEvaluation frozenInputs.{key} "
                    "does not match calibration"
                )
        evaluated_reference = evaluation["datasetReference"]
        references = calibration.get("datasetReferences")
        held_out_references = (
            [
                item
                for item in references
                if isinstance(item, dict) and item.get("role") == "held-out"
            ]
            if isinstance(references, list)
            else []
        )
        if not any(
            all(reference.get(key) == evaluated_reference.get(key) for key in (
                "datasetId",
                "role",
                "recordCount",
                "sha256",
            ))
            for reference in held_out_references
        ):
            errors.append(
                "calibration.datasetReferences held-out record must match "
                "calibration.heldOutEvaluation"
            )
    held_out = evaluated_metrics
    claimed_metrics = calibration.get("heldOutMetrics")
    if claimed_metrics is not None and claimed_metrics != evaluated_metrics:
        errors.append(
            "calibration.heldOutMetrics must match the local held-out recomputation"
        )
    if isinstance(claimed_metrics, dict):
        claimed_brier = claimed_metrics.get("brierScore")
        if not _finite_probability(claimed_brier):
            errors.append(
                "calibration.heldOutMetrics.brierScore must be between 0 and 1"
            )
        errors.extend(
            _reliability_bin_errors(
                claimed_metrics.get("reliabilityBins"),
                held_out_count,
            )
        )
    if isinstance(held_out, dict):
        brier = held_out.get("brierScore")
        if not _finite_probability(brier):
            errors.append("calibration.heldOutMetrics.brierScore must be between 0 and 1")
        errors.extend(
            _reliability_bin_errors(held_out.get("reliabilityBins"), held_out_count)
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
    elif (
        isinstance(interval, list)
        and len(interval) == 2
        and all(_finite_probability(value) for value in interval)
        and not float(interval[0]) <= float(estimate) <= float(interval[1])
    ):
        errors.append(
            "calibration.estimatedProbability must fall within uncertaintyInterval"
        )

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
    evaluation = calibration["heldOutEvaluation"]
    return {
        "schemaVersion": "calibrated-archaeological-probability-1.0",
        "assessmentType": "calibrated-probability",
        "eventDefinition": calibration["eventDefinition"],
        "denominator": calibration["denominator"],
        "estimatedProbability": float(calibration["estimatedProbability"]),
        "uncertaintyInterval": [
            float(calibration["uncertaintyInterval"][0]),
            float(calibration["uncertaintyInterval"][1]),
        ],
        "heldOutMetrics": evaluation["heldOutMetrics"],
        "calibrationEvidence": {
            "evaluationType": evaluation["evaluationType"],
            "artifactSha256": evaluation["artifactSha256"],
            "datasetReference": evaluation["datasetReference"],
            "evaluator": evaluation["evaluator"],
        },
        "datasetReferences": calibration["datasetReferences"],
        "frozenInputs": {
            "modelSha256": calibration["modelSha256"],
            "featuresSha256": calibration["featuresSha256"],
            "thresholdSha256": calibration["thresholdSha256"],
            "candidateSetSha256": calibration["candidateSetSha256"],
        },
        "validityDomain": calibration["validityDomain"],
        "biasTreatment": calibration["biasTreatment"],
        "disclosure": case.get("disclosure", "public") if case else "public",
        "targetPrecision": "exact" if exact_high_risk_target else "declared",
        "warning": (
            "This estimates the declared event under the stated validity domain; "
            "it is evidence for a research hypothesis, not permission for physical recovery."
        ),
    }


def heuristic_candidate_report(
    candidates: list[dict[str, Any]],
    *,
    method: str,
    score_meaning: str,
    evidence_references: list[str],
    limitations: list[str],
    assumptions: list[str] | None = None,
    uncertainty: list[str] | None = None,
    case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an auditable ranking without presenting scores as probabilities."""

    errors: list[str] = []
    assumptions = assumptions or [
        "No explicit assumptions were supplied; interpret the ranking only through "
        "the declared method and evidence."
    ]
    uncertainty = uncertainty or [
        "No representative held-out calibration supports a probability; score "
        "spacing and rank stability remain unvalidated."
    ]
    if case is not None and not isinstance(case, dict):
        errors.append("case must be an object")
        case = {}
    case = case or {}
    if case and case.get("disclosure", "public") not in DISCLOSURES:
        errors.append("case.disclosure is invalid")
    if not _text(method):
        errors.append("method is required")
    if not _text(score_meaning):
        errors.append("score_meaning is required")
    if (
        not isinstance(evidence_references, list)
        or not evidence_references
        or any(not _text(value) for value in evidence_references)
    ):
        errors.append("evidence_references must be a non-empty string array")
    declared_evidence = (
        set(evidence_references)
        if isinstance(evidence_references, list)
        and all(_text(value) for value in evidence_references)
        else set()
    )
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not _text(value) for value in limitations)
    ):
        errors.append("limitations must be a non-empty string array")
    if (
        not isinstance(assumptions, list)
        or not assumptions
        or any(not _text(value) for value in assumptions)
    ):
        errors.append("assumptions must be a non-empty string array")
    if (
        not isinstance(uncertainty, list)
        or not uncertainty
        or any(not _text(value) for value in uncertainty)
    ):
        errors.append("uncertainty must be a non-empty string array")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty array")

    ranked: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, candidate in enumerate(candidates if isinstance(candidates, list) else []):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidateId")
        score = candidate.get("score")
        if not _text(candidate_id):
            errors.append(f"{prefix}.candidateId is required")
        elif str(candidate_id) in seen_ids:
            errors.append(f"{prefix}.candidateId must be unique")
        else:
            seen_ids.add(str(candidate_id))
        if (
            not isinstance(score, (int, float))
            or isinstance(score, bool)
            or not math.isfinite(float(score))
        ):
            errors.append(f"{prefix}.score must be a finite number")
        if not _text(candidate.get("hypothesis")):
            errors.append(f"{prefix}.hypothesis is required")
        prohibited_fields = sorted(PROBABILITY_FIELDS.intersection(candidate))
        if prohibited_fields:
            errors.append(
                f"{prefix} cannot contain probability fields: "
                + ", ".join(prohibited_fields)
            )
        coordinates = candidate.get("coordinates")
        if coordinates is not None and (
            not isinstance(coordinates, list)
            or len(coordinates) != 2
            or any(
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(float(value))
                for value in coordinates
            )
            or not -180 <= float(coordinates[0]) <= 180
            or not -90 <= float(coordinates[1]) <= 90
        ):
            errors.append(f"{prefix}.coordinates must be [longitude, latitude]")
        imagery_ref = candidate.get("imageryAnnotationRef")
        if imagery_ref is not None and not _text(imagery_ref):
            errors.append(f"{prefix}.imageryAnnotationRef must be text")
        imagery_refs = candidate.get("imageryAnnotationRefs")
        if imagery_refs is not None and (
            not isinstance(imagery_refs, list)
            or not imagery_refs
            or any(not _text(value) for value in imagery_refs)
        ):
            errors.append(f"{prefix}.imageryAnnotationRefs must be a non-empty string array")
        sensitivity = candidate.get("sensitivity")
        if sensitivity is not None and sensitivity not in (
            RESTRICTED_SPATIAL_VALUES | {"public"}
        ):
            errors.append(f"{prefix}.sensitivity is invalid")
        spatial_restriction = candidate.get("spatialRestriction")
        if spatial_restriction is not None and spatial_restriction not in (
            RESTRICTED_SPATIAL_VALUES | {"none", "public"}
        ):
            errors.append(f"{prefix}.spatialRestriction is invalid")
        evidence = candidate.get("evidenceReferences")
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(not _text(value) for value in evidence)
        ):
            errors.append(f"{prefix}.evidenceReferences must be a non-empty string array")
        else:
            undeclared = sorted(set(evidence) - declared_evidence)
            if undeclared:
                errors.append(
                    f"{prefix}.evidenceReferences are not declared by the assessment: "
                    + ", ".join(undeclared)
                )
        prepared = dict(candidate)
        restricted = candidate.get("sensitivity") in RESTRICTED_SPATIAL_VALUES
        restricted = restricted or (
            candidate.get("spatialRestriction") in RESTRICTED_SPATIAL_VALUES
        )
        if case.get("disclosure", "public") == "public" and restricted:
            for field in (
                "coordinates",
                "geometry",
                "imageryAnnotationRef",
                "imageryAnnotationRefs",
                "imagePath",
                "imageUrl",
            ):
                prepared.pop(field, None)
            prepared["spatialEvidenceStatus"] = (
                "withheld-by-explicit-restriction"
            )
        ranked.append(prepared)
    if errors:
        raise ValueError("heuristic assessment failed: " + "; ".join(errors))

    ranked.sort(key=lambda item: (-float(item["score"]), str(item["candidateId"])))
    for rank, candidate in enumerate(ranked, 1):
        candidate["rank"] = rank
        add_google_maps_links(candidate)
    return {
        "schemaVersion": "heuristic-archaeological-assessment-1.0",
        "assessmentType": "heuristic-ranking-not-probability",
        "method": method,
        "scoreMeaning": score_meaning,
        "evidenceReferences": list(evidence_references),
        "assumptions": list(assumptions),
        "uncertainty": list(uncertainty),
        "limitations": list(limitations),
        "candidates": ranked,
        "disclosure": case.get("disclosure", "public"),
        "calibrationStatus": "not-calibrated",
        "warning": (
            "Scores rank the stated hypotheses; they are not calibrated probabilities "
            "and do not direct physical recovery."
        ),
    }


def heuristic_report_from_input(
    value: dict[str, Any],
    *,
    case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the versioned CLI input and build its heuristic report."""

    if not isinstance(value, dict):
        raise ValueError("heuristic assessment input must be an object")
    schema = value.get("schemaVersion")
    if schema is not None and schema != HEURISTIC_INPUT_SCHEMA:
        raise ValueError(
            f"heuristic assessment input must use {HEURISTIC_INPUT_SCHEMA}"
        )
    prohibited_fields = sorted(PROBABILITY_FIELDS.intersection(value))
    if prohibited_fields:
        raise ValueError(
            "heuristic assessment input cannot contain probability fields: "
            + ", ".join(prohibited_fields)
        )
    resolved_case = case if case is not None else value.get("case")
    return heuristic_candidate_report(
        value.get("candidates"),
        method=value.get("method"),
        score_meaning=value.get("scoreMeaning"),
        evidence_references=value.get("evidenceReferences"),
        assumptions=value.get("assumptions"),
        uncertainty=value.get("uncertainty"),
        limitations=value.get("limitations"),
        case=resolved_case,
    )
