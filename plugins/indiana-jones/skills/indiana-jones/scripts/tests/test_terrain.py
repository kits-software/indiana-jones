from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from ij_terrain import (
    rank_candidates,
    scan_templates,
    score_against_ground_truth,
    terrain_features,
)


class TerrainDetectorTests(unittest.TestCase):
    def test_synthetic_diamond_enclosure_is_ranked_first(self) -> None:
        random = np.random.default_rng(7)
        height = 320
        width = 360
        pixel_size_m = 2.0
        target_row = 136
        target_column = 227
        yy, xx = np.mgrid[0:height, 0:width]
        local_x = xx - target_column
        local_y = yy - target_row
        angle = math.radians(30.0)
        xr = local_x * math.cos(angle) + local_y * math.sin(angle)
        yr = -local_x * math.sin(angle) + local_y * math.cos(angle)
        distance = np.abs(xr) / 30.0 + np.abs(yr) / 19.0
        outer_bank = 1.8 * np.exp(-((distance - 1.0) / 0.055) ** 2)
        inner_bank = 1.0 * np.exp(-((distance - 0.72) / 0.055) ** 2)
        broad_slope = 0.012 * xx + 0.006 * yy
        noise = random.normal(0.0, 0.08, size=(height, width))
        dtm = (300.0 + broad_slope + outer_bank + inner_bank + noise).astype(np.float32)

        feature, _ = terrain_features(dtm, pixel_size_m)
        score, template_index, definitions, _ = scan_templates(
            feature,
            pixel_size_m,
            [60.0],
            [1.6],
            [0.0, 30.0, 60.0, 90.0],
            ["diamond"],
        )
        candidates = rank_candidates(
            score,
            template_index,
            definitions,
            feature,
            [0.0, 0.0, width * pixel_size_m, height * pixel_size_m],
            "EPSG:32630",
            pixel_size_m,
            5,
            100.0,
        )
        first = candidates[0]
        predicted_row = first["row"]
        predicted_column = first["column"]
        error_px = math.hypot(predicted_row - target_row, predicted_column - target_column)
        self.assertLess(error_px, 8.0)
        self.assertEqual("diamond", first["template"]["family"])

    def test_ground_truth_is_scored_after_candidate_generation(self) -> None:
        candidate_result = {
            "input": {"crs": "EPSG:27700"},
            "candidates": [
                {"rank": 1, "candidateId": "cand_a", "x": 1000.0, "y": 1000.0},
                {"rank": 2, "candidateId": "cand_b", "x": 2000.0, "y": 2000.0},
            ],
        }
        ground_truth = {
            "siteId": "known",
            "name": "Known site",
            "crs": "EPSG:27700",
            "x": 2010.0,
            "y": 2000.0,
            "toleranceM": 25.0,
            "source": "https://example.test/record",
        }
        score = score_against_ground_truth(candidate_result, ground_truth)
        self.assertTrue(score["result"]["hit"])
        self.assertEqual(2, score["result"]["hitRank"])
        self.assertFalse(score["result"]["top1Hit"])

    def test_response_normalization_modes_are_distinct(self) -> None:
        feature = np.zeros((80, 80), dtype=np.float32)
        feature[25:55, 25:55] = 1.0
        raw_score, _, _, _ = scan_templates(
            feature,
            2.0,
            [20.0],
            [1.25],
            [0.0],
            ["diamond"],
            "raw",
        )
        normalized_score, _, _, _ = scan_templates(
            feature,
            2.0,
            [20.0],
            [1.25],
            [0.0],
            ["diamond"],
            "robust-per-template",
        )
        self.assertFalse(np.allclose(raw_score, normalized_score))
        with self.assertRaisesRegex(ValueError, "Unsupported response normalization"):
            scan_templates(
                feature,
                2.0,
                [20.0],
                [1.25],
                [0.0],
                ["diamond"],
                "unknown",
            )


if __name__ == "__main__":
    unittest.main()
