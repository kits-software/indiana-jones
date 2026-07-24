from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from ij_calibration import (
    evaluate_held_out_benchmark,
    held_out_evaluation_errors,
)
from ij_probability import (
    calibrated_probability_report,
    heuristic_candidate_report,
    probability_gate_errors,
)
from permission_fixture import calibration_fixture


FROZEN_INPUTS = {
    "modelSha256": "1" * 64,
    "featuresSha256": "2" * 64,
    "thresholdSha256": "3" * 64,
    "candidateSetSha256": "4" * 64,
}


def benchmark_fixture() -> dict:
    buckets = (
        (0.1, [0, 0, 0, 0, 1]),
        (0.3, [0, 0, 0, 1, 1]),
        (0.6, [0, 0, 1, 1, 1]),
        (0.9, [0, 1, 1, 1, 1]),
    )
    rows = [
        (predicted, outcome)
        for predicted, outcomes in buckets
        for outcome in outcomes
    ]
    return {
        "schemaVersion": "archaeological-calibration-benchmark-1.0",
        "benchmarkId": "treasure-target-benchmark-v1",
        "datasetId": "held-out-targets-v1",
        "eventDefinition": "A documented gold hoard in the declared target cell",
        "denominator": "Comparable prospectively frozen target cells",
        "status": "resolved",
        "observations": [
            {
                "observationId": f"target-{index:02d}",
                "predictedProbability": predicted,
                "observedOutcome": outcome,
                "resolutionStatus": "resolved",
                "split": "held-out",
                "sourceSnapshotId": f"snapshot:{index:02d}",
                "geographyGroupId": f"area-{index % 4}",
            }
            for index, (predicted, outcome) in enumerate(rows, 1)
        ],
    }


class HeldOutEvaluationTests(unittest.TestCase):
    def test_recomputes_brier_and_reliability_deterministically(self) -> None:
        benchmark = benchmark_fixture()
        first = evaluate_held_out_benchmark(
            benchmark,
            frozen_inputs=FROZEN_INPUTS,
        )
        benchmark["observations"].reverse()
        second = evaluate_held_out_benchmark(
            benchmark,
            frozen_inputs=FROZEN_INPUTS,
        )

        self.assertEqual(first, second)
        self.assertEqual(0.2075, first["heldOutMetrics"]["brierScore"])
        self.assertEqual(
            [0.2, 0.4, 0.6, 0.8],
            [
                item["observed"]
                for item in first["heldOutMetrics"]["reliabilityBins"]
            ],
        )
        self.assertEqual(0.075, first["heldOutMetrics"]["expectedCalibrationError"])
        self.assertEqual([], held_out_evaluation_errors(first))
        self.assertEqual(64, len(first["artifactSha256"]))

    def test_rejects_undersized_or_unresolved_benchmark(self) -> None:
        undersized = benchmark_fixture()
        undersized["observations"] = undersized["observations"][:-1]
        with self.assertRaisesRegex(ValueError, "at least 20 records"):
            evaluate_held_out_benchmark(
                undersized,
                frozen_inputs=FROZEN_INPUTS,
            )

        unresolved = benchmark_fixture()
        unresolved["observations"][0]["resolutionStatus"] = "pending"
        unresolved["observations"][0]["observedOutcome"] = None
        with self.assertRaisesRegex(ValueError, "resolved label 0 or 1"):
            evaluate_held_out_benchmark(
                unresolved,
                frozen_inputs=FROZEN_INPUTS,
            )

    def test_rejects_self_reported_metrics_and_tampered_artifact(self) -> None:
        self_reported = benchmark_fixture()
        self_reported["brierScore"] = 0.01
        with self.assertRaisesRegex(ValueError, "self-reported metrics"):
            evaluate_held_out_benchmark(
                self_reported,
                frozen_inputs=FROZEN_INPUTS,
            )

        evaluation = evaluate_held_out_benchmark(
            benchmark_fixture(),
            frozen_inputs=FROZEN_INPUTS,
        )
        evaluation["heldOutMetrics"]["brierScore"] = 0.01
        self.assertTrue(
            any(
                "deterministic local recomputation" in error
                for error in held_out_evaluation_errors(evaluation)
            )
        )

    def test_probability_gate_requires_raw_recomputed_evaluation(self) -> None:
        calibration = calibration_fixture()
        calibration.pop("heldOutEvaluation")
        errors = probability_gate_errors(calibration)
        self.assertTrue(
            any("raw observations" in error for error in errors),
            errors,
        )

    def test_probability_report_references_verified_artifact(self) -> None:
        calibration = calibration_fixture()
        report = calibrated_probability_report(
            calibration,
            case={
                "researchMode": "treasure-research-public",
                "disclosure": "public",
            },
            exact_high_risk_target=True,
        )

        self.assertEqual("calibrated-probability", report["assessmentType"])
        self.assertEqual(
            calibration["heldOutEvaluation"]["artifactSha256"],
            report["calibrationEvidence"]["artifactSha256"],
        )
        self.assertEqual(
            calibration["heldOutEvaluation"]["heldOutMetrics"],
            report["heldOutMetrics"],
        )
        self.assertEqual("public", report["disclosure"])
        self.assertEqual("exact", report["targetPrecision"])

    def test_dataset_or_metric_claim_cannot_replace_evaluation(self) -> None:
        calibration = calibration_fixture()
        calibration["datasetReferences"][-1]["sha256"] = "f" * 64
        self.assertTrue(
            any(
                "held-out record must match" in error
                for error in probability_gate_errors(calibration)
            )
        )

        calibration = calibration_fixture()
        calibration["heldOutMetrics"] = copy.deepcopy(
            calibration["heldOutMetrics"]
        )
        calibration["heldOutMetrics"]["brierScore"] = 0.001
        self.assertTrue(
            any(
                "must match the local" in error
                for error in probability_gate_errors(calibration)
            )
        )

    def test_heuristic_schema_remains_explicitly_non_probability(self) -> None:
        report = heuristic_candidate_report(
            [
                {
                    "candidateId": "candidate-gold",
                    "score": 8.2,
                    "hypothesis": "Gold-hoard target at a mapped boundary",
                    "coordinates": [19.54321, 54.54321],
                    "evidenceReferences": ["snapshot:map", "snapshot:imagery"],
                }
            ],
            method="Weighted independent evidence agreement",
            score_meaning="Higher means more research signals agree",
            evidence_references=["snapshot:map", "snapshot:imagery"],
            limitations=["No representative local calibration for this ranking"],
            case={
                "researchMode": "treasure-research-public",
                "disclosure": "public",
            },
        )
        self.assertEqual(
            "heuristic-ranking-not-probability",
            report["assessmentType"],
        )
        self.assertNotIn("estimatedProbability", report)


if __name__ == "__main__":
    unittest.main()
