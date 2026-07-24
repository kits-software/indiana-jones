from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from typing import Any


BENCHMARK_SCHEMA = "archaeological-calibration-benchmark-1.0"
EVALUATION_SCHEMA = "archaeological-held-out-evaluation-1.0"
EVALUATOR_VERSION = "1.0.0"
MINIMUM_RECORDS = 20
MINIMUM_CLASS_RECORDS = 5
BIN_EDGES = (0.0, 0.2, 0.5, 0.8, 1.0)
SHA256 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
SELF_REPORTED_FIELDS = {
    "artifactSha256",
    "brierScore",
    "expectedCalibrationError",
    "heldOutMetrics",
    "metrics",
    "reliabilityBins",
}
FROZEN_INPUT_KEYS = (
    "modelSha256",
    "featuresSha256",
    "thresholdSha256",
    "candidateSetSha256",
)


def _canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonical JSON: {exc}") from exc
    return text.encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _probability(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and 0 <= float(value) <= 1
    )


def _frozen_input_errors(frozen_inputs: Any) -> list[str]:
    if not isinstance(frozen_inputs, dict):
        return ["frozenInputs must be an object"]
    errors: list[str] = []
    for key in FROZEN_INPUT_KEYS:
        value = frozen_inputs.get(key)
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            errors.append(f"frozenInputs.{key} must be a 64-character SHA-256 digest")
    return errors


def _benchmark_errors(benchmark: Any) -> list[str]:
    if not isinstance(benchmark, dict):
        return ["benchmark must be an object"]
    errors: list[str] = []
    if benchmark.get("schemaVersion") != BENCHMARK_SCHEMA:
        errors.append(f"benchmark.schemaVersion must be {BENCHMARK_SCHEMA}")
    for key in ("benchmarkId", "datasetId", "eventDefinition", "denominator"):
        if not _text(benchmark.get(key)):
            errors.append(f"benchmark.{key} is required")
    if benchmark.get("status") != "resolved":
        errors.append("benchmark.status must be resolved")
    reported = sorted(SELF_REPORTED_FIELDS.intersection(benchmark))
    if reported:
        errors.append(
            "benchmark must contain observations, not self-reported metrics: "
            + ", ".join(reported)
        )
    observations = benchmark.get("observations")
    if not isinstance(observations, list):
        errors.append("benchmark.observations must be an array")
        return errors
    if len(observations) < MINIMUM_RECORDS:
        errors.append(
            f"benchmark.observations requires at least {MINIMUM_RECORDS} records"
        )
    seen_ids: set[str] = set()
    geography_groups: set[str] = set()
    positive_count = 0
    negative_count = 0
    populated_bins: set[int] = set()
    for index, observation in enumerate(observations):
        prefix = f"benchmark.observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        reported_observation = sorted(SELF_REPORTED_FIELDS.intersection(observation))
        if reported_observation:
            errors.append(
                f"{prefix} contains self-reported metrics: "
                + ", ".join(reported_observation)
            )
        observation_id = observation.get("observationId")
        if not _text(observation_id):
            errors.append(f"{prefix}.observationId is required")
        elif str(observation_id) in seen_ids:
            errors.append(f"{prefix}.observationId must be unique")
        else:
            seen_ids.add(str(observation_id))
        predicted = observation.get("predictedProbability")
        if not _probability(predicted):
            errors.append(f"{prefix}.predictedProbability must be between 0 and 1")
        else:
            populated_bins.add(_bin_index(float(predicted)))
        outcome = observation.get("observedOutcome")
        if not isinstance(outcome, int) or isinstance(outcome, bool) or outcome not in {
            0,
            1,
        }:
            errors.append(f"{prefix}.observedOutcome must be the resolved label 0 or 1")
        elif outcome == 1:
            positive_count += 1
        else:
            negative_count += 1
        if observation.get("resolutionStatus") != "resolved":
            errors.append(f"{prefix}.resolutionStatus must be resolved")
        if observation.get("split") != "held-out":
            errors.append(f"{prefix}.split must be held-out")
        for key in ("sourceSnapshotId", "geographyGroupId"):
            if not _text(observation.get(key)):
                errors.append(f"{prefix}.{key} is required")
        if _text(observation.get("geographyGroupId")):
            geography_groups.add(str(observation["geographyGroupId"]))
    if positive_count < MINIMUM_CLASS_RECORDS:
        errors.append(
            f"benchmark requires at least {MINIMUM_CLASS_RECORDS} positive outcomes"
        )
    if negative_count < MINIMUM_CLASS_RECORDS:
        errors.append(
            f"benchmark requires at least {MINIMUM_CLASS_RECORDS} negative outcomes"
        )
    if len(geography_groups) < 2:
        errors.append("benchmark requires at least two separated geography groups")
    if len(populated_bins) < 3:
        errors.append("benchmark predictions must populate at least three reliability bins")
    try:
        _canonical_bytes(benchmark)
    except ValueError as exc:
        errors.append(f"benchmark {exc}")
    return errors


def _bin_index(predicted: float) -> int:
    for index in range(len(BIN_EDGES) - 1):
        upper = BIN_EDGES[index + 1]
        if predicted < upper or index == len(BIN_EDGES) - 2:
            return index
    raise AssertionError("fixed reliability-bin edges must cover every probability")


def _canonical_benchmark(benchmark: dict[str, Any]) -> dict[str, Any]:
    canonical = deepcopy(benchmark)
    canonical["observations"] = sorted(
        canonical["observations"], key=lambda item: str(item["observationId"])
    )
    for observation in canonical["observations"]:
        observation["predictedProbability"] = float(
            observation["predictedProbability"]
        )
    return canonical


def _held_out_metrics(observations: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[list[dict[str, Any]]] = [
        [] for _ in range(len(BIN_EDGES) - 1)
    ]
    squared_errors: list[float] = []
    positive_count = 0
    for observation in observations:
        predicted = float(observation["predictedProbability"])
        outcome = int(observation["observedOutcome"])
        rows[_bin_index(predicted)].append(observation)
        squared_errors.append((predicted - outcome) ** 2)
        positive_count += outcome
    reliability_bins: list[dict[str, Any]] = []
    absolute_error_total = 0.0
    for index, items in enumerate(rows):
        if not items:
            continue
        predicted = sum(
            float(item["predictedProbability"]) for item in items
        ) / len(items)
        observed = sum(int(item["observedOutcome"]) for item in items) / len(items)
        absolute_error_total += abs(predicted - observed) * len(items)
        reliability_bins.append(
            {
                "lowerBound": BIN_EDGES[index],
                "upperBound": BIN_EDGES[index + 1],
                "predicted": round(predicted, 12),
                "observed": round(observed, 12),
                "count": len(items),
            }
        )
    return {
        "recordCount": len(observations),
        "positiveCount": positive_count,
        "negativeCount": len(observations) - positive_count,
        "brierScore": round(sum(squared_errors) / len(observations), 12),
        "expectedCalibrationError": round(
            absolute_error_total / len(observations), 12
        ),
        "reliabilityBins": reliability_bins,
    }


def evaluate_held_out_benchmark(
    benchmark: dict[str, Any],
    *,
    frozen_inputs: dict[str, Any],
) -> dict[str, Any]:
    errors = _benchmark_errors(benchmark)
    errors.extend(_frozen_input_errors(frozen_inputs))
    if errors:
        raise ValueError("held-out benchmark invalid: " + "; ".join(errors))
    canonical_benchmark = _canonical_benchmark(benchmark)
    dataset_sha256 = _digest(canonical_benchmark)
    evaluation: dict[str, Any] = {
        "schemaVersion": EVALUATION_SCHEMA,
        "evaluationType": "local-held-out-recompute",
        "assessmentType": "calibration-evidence-not-target-probability",
        "evaluator": {
            "name": "ij_calibration",
            "version": EVALUATOR_VERSION,
        },
        "evaluationPolicy": {
            "minimumRecords": MINIMUM_RECORDS,
            "minimumClassRecords": MINIMUM_CLASS_RECORDS,
            "binEdges": list(BIN_EDGES),
        },
        "benchmark": canonical_benchmark,
        "datasetReference": {
            "datasetId": canonical_benchmark["datasetId"],
            "role": "held-out",
            "recordCount": len(canonical_benchmark["observations"]),
            "sha256": dataset_sha256,
        },
        "frozenInputs": {
            key: str(frozen_inputs[key]).lower() for key in FROZEN_INPUT_KEYS
        },
        "heldOutMetrics": _held_out_metrics(canonical_benchmark["observations"]),
    }
    evaluation["artifactSha256"] = _digest(evaluation)
    return evaluation


def held_out_evaluation_errors(evaluation: Any) -> list[str]:
    if not isinstance(evaluation, dict):
        return [
            "heldOutEvaluation must be a locally recomputed artifact with raw observations"
        ]
    if evaluation.get("schemaVersion") != EVALUATION_SCHEMA:
        return [f"heldOutEvaluation.schemaVersion must be {EVALUATION_SCHEMA}"]
    benchmark = evaluation.get("benchmark")
    frozen_inputs = evaluation.get("frozenInputs")
    try:
        recomputed = evaluate_held_out_benchmark(
            benchmark,
            frozen_inputs=frozen_inputs,
        )
    except ValueError as exc:
        return [str(exc)]
    if _canonical_bytes(evaluation) != _canonical_bytes(recomputed):
        return [
            "heldOutEvaluation does not match the deterministic local recomputation"
        ]
    return []
