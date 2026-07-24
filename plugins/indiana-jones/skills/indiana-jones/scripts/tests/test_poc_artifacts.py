from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from ij_common import sha256_file


class PocArtifactTests(unittest.TestCase):
    def test_whitley_development_poc_is_hash_bound(self) -> None:
        poc_dir = SKILL_DIR / "assets" / "poc" / "whitley-castle"
        candidate_path = poc_dir / "run-03" / "candidates.json"
        score_path = poc_dir / "run-03" / "score.json"
        ground_truth_path = poc_dir / "ground-truth.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        score = json.loads(score_path.read_text(encoding="utf-8"))

        self.assertEqual(
            sha256_file(candidate_path),
            score["candidateArtifactSha256"],
        )
        self.assertEqual(
            sha256_file(ground_truth_path),
            score["groundTruthArtifactSha256"],
        )
        for implementation in candidate["implementation"]:
            path = SKILL_DIR / implementation["path"]
            self.assertEqual(sha256_file(path), implementation["sha256"])

        self.assertTrue(score["result"]["hit"])
        self.assertEqual(8, score["result"]["hitRank"])
        self.assertTrue(score["result"]["top10Hit"])
        nearest = min(score["distances"], key=lambda item: item["distanceM"])
        self.assertEqual(8, nearest["rank"])
        self.assertLess(nearest["distanceM"], 17.0)

    def test_failed_runs_remain_failed(self) -> None:
        poc_dir = SKILL_DIR / "assets" / "poc" / "whitley-castle"
        for run_name in ("run-01", "run-02"):
            score_path = poc_dir / run_name / "score.json"
            score = json.loads(score_path.read_text(encoding="utf-8"))
            self.assertFalse(score["result"]["hit"])

    def test_optical_poc_preserves_precommitted_miss_without_coordinates(
        self,
    ) -> None:
        summary_path = (
            SKILL_DIR
            / "assets"
            / "poc"
            / "whitley-castle-optical"
            / "result-summary.json"
        )
        raw = summary_path.read_text(encoding="utf-8")
        summary = json.loads(raw)
        benchmark = summary["benchmark"]
        self.assertTrue(benchmark["candidateArtifactsFrozenBeforeGroundTruth"])
        self.assertFalse(benchmark["targetLabelsUsedDuringCandidateGeneration"])
        self.assertEqual("miss", benchmark["outcome"])
        self.assertEqual(160.0, benchmark["acceptanceToleranceM"])
        self.assertEqual(3, len(summary["profiles"]))
        self.assertTrue(
            all(not profile["hit"] for profile in summary["profiles"])
        )
        self.assertEqual(
            191.15,
            min(profile["nearestDistanceM"] for profile in summary["profiles"]),
        )
        self.assertFalse(
            summary["site"]["coordinatesIncludedInThisPublicSummary"]
        )
        self.assertNotIn("centroid", raw.lower())
        self.assertNotIn("distancevector", raw.lower())


if __name__ == "__main__":
    unittest.main()
