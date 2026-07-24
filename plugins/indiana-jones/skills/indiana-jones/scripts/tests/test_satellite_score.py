from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1]
CLI_PATH = SCRIPT_DIR / "satellite.py"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_common import atomic_write_json, load_json, sha256_file
from ij_optical_io import validate_safe_locator

import satellite as satellite_cli


def candidate_artifact(rank: object = 1) -> dict:
    return {
        "schemaVersion": "1.0",
        "method": {
            "name": "transparent-multitemporal-optical-proxy-baseline",
            "version": "1.2",
        },
        "input": {
            "crs": "EPSG:32630",
            "coordinateUnit": "metre",
            "bbox": [533000.0, 6076000.0, 534000.0, 6077000.0],
            "northUp": True,
            "manifestSha256": "a" * 64,
            "arraySha256": "b" * 64,
            "targetLabelsUsed": False,
        },
        "access": {"disclosure": "restricted"},
        "diagnostics": {
            "scoreArrays": {
                "path": "optical-scores.npz",
                "sha256": "c" * 64,
            }
        },
        "candidates": [
            {
                "rank": rank,
                "candidateId": "optical_test",
                "centroidProjected": [533630.0, 6076225.0],
            }
        ],
    }


def ground_truth(x: object = 533627.744, y: object = 6076224.617) -> dict:
    return {
        "siteId": "known-site",
        "name": "Public known site",
        "crs": "EPSG:32630",
        "x": x,
        "y": y,
        "toleranceM": 20.0,
        "source": "https://example.test/known-site",
        "sensitivity": "public-known",
    }


class SatelliteScoreTests(unittest.TestCase):
    def test_cli_scores_only_frozen_hash_bound_optical_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            candidate_path = directory / "candidates.json"
            ground_truth_path = directory / "ground-truth.json"
            score_path = directory / "score.json"
            atomic_write_json(
                candidate_path,
                candidate_artifact(),
            )
            atomic_write_json(ground_truth_path, ground_truth())
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "score",
                    "--candidates",
                    str(candidate_path),
                    "--expected-candidate-sha256",
                    sha256_file(candidate_path),
                    "--ground-truth",
                    str(ground_truth_path),
                    "--out",
                    str(score_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            score = load_json(score_path)
            self.assertTrue(score["result"]["hit"])
            self.assertEqual(1, score["result"]["hitRank"])
            self.assertEqual(
                sha256_file(candidate_path),
                score["input"]["candidateArtifactSha256"],
            )
            self.assertEqual(
                sha256_file(ground_truth_path),
                score["input"]["groundTruthArtifactSha256"],
            )
            self.assertEqual(
                "known-site-optical-localization-scorer",
                score["method"]["name"],
            )
            self.assertFalse(score["access"]["spatiallyRedacted"])
            self.assertNotIn("x", score["groundTruth"])
            self.assertNotIn("y", score["groundTruth"])

            restricted = load_json(ground_truth_path)
            restricted["sensitivity"] = "restricted"
            atomic_write_json(ground_truth_path, restricted)
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "score",
                    "--candidates",
                    str(candidate_path),
                    "--expected-candidate-sha256",
                    sha256_file(candidate_path),
                    "--ground-truth",
                    str(ground_truth_path),
                    "--out",
                    str(directory / "restricted-score.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, rejected.returncode)
            self.assertIn("public-known", rejected.stderr)

            restricted["sensitivity"] = "public-known"
            restricted["source"] = "https://example.test/site?access_token=secret"
            atomic_write_json(ground_truth_path, restricted)
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "score",
                    "--candidates",
                    str(candidate_path),
                    "--expected-candidate-sha256",
                    sha256_file(candidate_path),
                    "--ground-truth",
                    str(ground_truth_path),
                    "--out",
                    str(directory / "credential-score.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, rejected.returncode)
            self.assertIn("credential-bearing", rejected.stderr)

    def test_candidate_is_fully_validated_before_ground_truth_is_opened(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            candidate_path = directory / "candidates.json"
            ground_truth_path = directory / "ground-truth.json"
            atomic_write_json(candidate_path, {"schemaVersion": "invalid"})
            ground_truth_path.write_text("{malformed", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "score",
                    "--candidates",
                    str(candidate_path),
                    "--expected-candidate-sha256",
                    sha256_file(candidate_path),
                    "--ground-truth",
                    str(ground_truth_path),
                    "--out",
                    str(directory / "score.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("Candidate artifact schemaVersion", completed.stderr)
            self.assertNotIn("Invalid JSON artifact", completed.stderr)

    def test_score_rejects_target_outside_analyzed_bbox(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            candidate_path = directory / "candidates.json"
            ground_truth_path = directory / "ground-truth.json"
            atomic_write_json(candidate_path, candidate_artifact())
            atomic_write_json(ground_truth_path, ground_truth(1_000_000, 1_000_000))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "score",
                    "--candidates",
                    str(candidate_path),
                    "--expected-candidate-sha256",
                    sha256_file(candidate_path),
                    "--ground-truth",
                    str(ground_truth_path),
                    "--out",
                    str(directory / "score.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("outside the analyzed bbox", completed.stderr)

    def test_score_rejects_geographic_candidate_crs_before_unblinding(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            candidate_path = directory / "candidates.json"
            ground_truth_path = directory / "ground-truth.json"
            candidate = candidate_artifact()
            candidate["input"]["crs"] = "EPSG:4326"
            atomic_write_json(candidate_path, candidate)
            ground_truth_path.write_text("{malformed", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "score",
                    "--candidates",
                    str(candidate_path),
                    "--expected-candidate-sha256",
                    sha256_file(candidate_path),
                    "--ground-truth",
                    str(ground_truth_path),
                    "--out",
                    str(directory / "score.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("Geographic longitude/latitude", completed.stderr)
            self.assertNotIn("Invalid JSON artifact", completed.stderr)

    def test_score_rejects_fractional_and_boolean_ranks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            ground_truth_path = directory / "ground-truth.json"
            atomic_write_json(ground_truth_path, ground_truth())
            for index, rank in enumerate((1.9, True)):
                candidate_path = directory / f"candidates-{index}.json"
                atomic_write_json(candidate_path, candidate_artifact(rank))
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(CLI_PATH),
                        "score",
                        "--candidates",
                        str(candidate_path),
                        "--expected-candidate-sha256",
                        sha256_file(candidate_path),
                        "--ground-truth",
                        str(ground_truth_path),
                        "--out",
                        str(directory / f"score-{index}.json"),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(2, completed.returncode)
                self.assertIn("positive integers", completed.stderr)

    def test_locator_rejects_nested_delimited_and_bearer_secrets(self) -> None:
        for locator in (
            "https://example.test/item?foo=1;access_token=SECRET",
            "https://example.test/item?foo[access_token]=SECRET",
            "Bearer TOP-SECRET",
        ):
            with self.subTest(locator=locator):
                with self.assertRaises(ValueError):
                    validate_safe_locator(locator, "source")
        self.assertEqual(
            "https://example.test/item?collection=sentinel-2",
            validate_safe_locator(
                "https://example.test/item?collection=sentinel-2",
                "source",
            ),
        )

    def test_exclusive_score_write_never_publishes_partial_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            output = directory / "score.json"

            def interrupted_dump(value, handle, **kwargs):
                handle.write('{"partial":')
                handle.flush()
                raise RuntimeError("injected interruption")

            with patch.object(
                satellite_cli.json,
                "dump",
                side_effect=interrupted_dump,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "injected interruption",
                ):
                    satellite_cli._write_json_exclusive(output, {"ok": True})
            self.assertFalse(output.exists())
            self.assertFalse(list(directory.glob(".score.json.*.tmp")))

            satellite_cli._write_json_exclusive(output, {"ok": True})
            before = output.read_bytes()
            with self.assertRaisesRegex(ValueError, "already exists"):
                satellite_cli._write_json_exclusive(output, {"ok": False})
            self.assertEqual(before, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
