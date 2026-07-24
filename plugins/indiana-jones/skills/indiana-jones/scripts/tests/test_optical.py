from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parents[1]
CLI_PATH = SCRIPT_DIR / "satellite.py"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_common import atomic_write_json, load_json, sha256_file
from ij_optical import (
    build_features,
    load_optical_cube,
    rank_optical_candidates,
    score_optical_cube,
)
from ij_spatial import validate_projected_crs

import satellite as satellite_cli


def build_test_cube(directory: Path) -> Path:
    dates, rows, columns = 4, 40, 40
    row_grid, column_grid = np.mgrid[:rows, :columns]
    gradient = row_grid * 0.0002 + column_grid * 0.0001
    red = np.stack(
        [0.22 + gradient + date * 0.002 for date in range(dates)]
    )
    nir = np.stack(
        [0.43 + gradient + date * 0.004 for date in range(dates)]
    )
    green = np.stack(
        [0.30 + gradient + date * 0.001 for date in range(dates)]
    )
    blue = np.stack(
        [0.18 + gradient + date * 0.001 for date in range(dates)]
    )
    swir1 = np.stack(
        [0.28 + gradient + date * 0.002 for date in range(dates)]
    )
    for date in (1, 2):
        red[date, 17:20, 23:26] -= 0.08
        nir[date, 17:20, 23:26] += 0.12
        swir1[date, 17:20, 23:26] -= 0.07
    valid = np.ones((dates, rows, columns), dtype=bool)
    array_path = directory / "cube.npz"
    np.savez_compressed(
        array_path,
        blue=blue,
        green=green,
        red=red,
        nir=nir,
        swir1=swir1,
        valid=valid,
    )
    date_values = [
        "2025-03-15",
        "2025-04-20",
        "2025-05-25",
        "2025-06-30",
    ]
    manifest = {
        "schemaVersion": "1.0",
        "modality": "multispectral-optical",
        "arrayPath": array_path.name,
        "arraySha256": sha256_file(array_path),
        "bands": ["blue", "green", "red", "nir", "swir1"],
        "nativeGsdM": {
            "blue": 10.0,
            "green": 10.0,
            "red": 10.0,
            "nir": 10.0,
            "swir1": 20.0,
        },
        "dates": date_values,
        "crs": "EPSG:32632",
        "coordinateUnit": "metre",
        "bbox": [500000.0, 4100000.0, 500400.0, 4100400.0],
        "pixelSizeM": 10.0,
        "northUp": True,
        "unit": "surface-reflectance",
        "sensor": "synthetic multispectral test sensor",
        "processingLevel": "synthetic surface reflectance",
        "maskPolicy": "all synthetic observations valid",
        "resampling": "none",
        "disclosure": "restricted",
        "reflectanceScale": 1.0,
        "reflectanceOffset": 0.0,
        "targetLabelsUsed": False,
        "sourceAssets": [
            {
                "itemId": f"test-item-{index}",
                "itemUrl": f"https://example.test/items/{index}",
                "collection": "synthetic-test-collection",
                "processingVersion": "1.0",
                "acquiredAt": date,
                "accessedAt": "2026-07-24T12:00:00Z",
                "accessBasis": "public",
                "license": "test-only",
                "assets": {
                    band: {
                        "href": f"https://example.test/items/{index}/{band}.tif"
                    }
                    for band in ("blue", "green", "red", "nir", "swir1")
                },
            }
            for index, date in enumerate(date_values)
        ],
    }
    manifest_path = directory / "cube.json"
    atomic_write_json(manifest_path, manifest)
    return manifest_path


class OpticalCubeTests(unittest.TestCase):
    def test_satellite_crs_requires_projected_metre_axes(self) -> None:
        self.assertEqual(
            "EPSG:32718",
            validate_projected_crs("EPSG:32718", "metre"),
        )
        for crs in ("EPSG:4258", "EPSG:4269", "EPSG:2227", "EPSG:3857"):
            with self.subTest(crs=crs):
                with self.assertRaises(ValueError):
                    validate_projected_crs(crs, "metre")
        try:
            from pyproj import CRS
        except ImportError:
            mercator_wkt = None
        else:
            mercator_wkt = CRS.from_epsg(3857).to_wkt()
        if mercator_wkt is not None:
            with self.assertRaisesRegex(ValueError, "Global Mercator"):
                validate_projected_crs(mercator_wkt, "metre")
        for crs in (
            'PROJCRS[LENGTHUNIT["metre",1]]',
            "+proj=definitely_not_a_projection +units=m",
        ):
            with self.subTest(crs=crs):
                with self.assertRaises(ValueError):
                    validate_projected_crs(crs, "metre")
        with self.assertRaisesRegex(ValueError, "coordinateUnit"):
            validate_projected_crs("EPSG:32718", "foot")

    def test_cube_hash_geometry_mask_and_provenance_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest, arrays, valid = load_optical_cube(manifest_path)
            self.assertEqual((4, 40, 40), valid.shape)
            self.assertEqual({"blue", "green", "red", "nir", "swir1"}, set(arrays))
            self.assertFalse(manifest["targetLabelsUsed"])

            tampered = load_json(manifest_path)
            tampered["targetLabelsUsed"] = True
            atomic_write_json(manifest_path, tampered)
            with self.assertRaisesRegex(ValueError, "targetLabelsUsed"):
                load_optical_cube(manifest_path)

    def test_cube_rejects_changed_array(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            array_path = directory / "cube.npz"
            array_path.write_bytes(array_path.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "arraySha256"):
                load_optical_cube(manifest_path)

    def test_cube_rejects_nonfinite_values_marked_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            array_path = directory / manifest["arrayPath"]
            with np.load(array_path, allow_pickle=False) as archive:
                values = {name: archive[name] for name in archive.files}
            values["red"][0, 0, 0] = np.nan
            np.savez_compressed(array_path, **values)
            manifest["arraySha256"] = sha256_file(array_path)
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "non-finite"):
                load_optical_cube(manifest_path)

    def test_cube_rejects_credential_bearing_source_locators(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["sourceAssets"][0]["assets"]["red"]["href"] += (
                "?X-Amz-Credential=temporary&X-Amz-Signature=secret"
            )
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "credential-bearing"):
                load_optical_cube(manifest_path)

            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["sourceAssets"][0]["assets"]["red"]["href"] += (
                "#access_token=secret"
            )
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "fragment"):
                load_optical_cube(manifest_path)

            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["sourceAssets"][0]["authorization"] = "secret"
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                load_optical_cube(manifest_path)

            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["sourceAssets"][0]["assets"]["red"]["token"] = "secret"
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                load_optical_cube(manifest_path)

            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["sourceAssets"][0]["assets"]["red"]["href"] = {
                "authorization": "Bearer secret"
            }
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "must be a string"):
                load_optical_cube(manifest_path)

    def test_cube_rejects_complex_reflectance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            array_path = directory / manifest["arrayPath"]
            with np.load(array_path, allow_pickle=False) as archive:
                values = {name: archive[name] for name in archive.files}
            values["red"] = values["red"].astype(np.complex64) + 1j
            np.savez_compressed(array_path, **values)
            manifest["arraySha256"] = sha256_file(array_path)
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "complex"):
                load_optical_cube(manifest_path)

            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["sourceAssets"][0]["itemUrl"] += "?client_secret=secret"
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "credential-bearing"):
                load_optical_cube(manifest_path)

    def test_manifest_rejects_boolean_numeric_metadata(self) -> None:
        mutations = {
            "pixelSizeM": lambda manifest: manifest.__setitem__(
                "pixelSizeM",
                True,
            ),
            "bbox": lambda manifest: manifest["bbox"].__setitem__(0, False),
            "nativeGsdM": lambda manifest: manifest["nativeGsdM"].__setitem__(
                "red",
                True,
            ),
            "reflectanceScale": lambda manifest: manifest.__setitem__(
                "reflectanceScale",
                True,
            ),
            "reflectanceOffset": lambda manifest: manifest.__setitem__(
                "reflectanceOffset",
                False,
            ),
        }
        for field, mutate in mutations.items():
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    directory = Path(temporary_directory)
                    manifest_path = build_test_cube(directory)
                    manifest = load_json(manifest_path)
                    mutate(manifest)
                    atomic_write_json(manifest_path, manifest)
                    with self.assertRaisesRegex(ValueError, "number"):
                        load_optical_cube(manifest_path)

    def test_default_reflectance_transform_is_materialized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            del manifest["reflectanceScale"]
            del manifest["reflectanceOffset"]
            atomic_write_json(manifest_path, manifest)
            resolved, _, _ = load_optical_cube(manifest_path)
            self.assertEqual(1.0, resolved["reflectanceScale"])
            self.assertEqual(0.0, resolved["reflectanceOffset"])

    def test_multitemporal_proxy_is_ranked_without_target_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest_path = build_test_cube(Path(temporary_directory))
            manifest, bands, valid = load_optical_cube(manifest_path)
            valid[0, 17:20, 23:26] = False
            features = build_features(bands, valid)
            scores = score_optical_cube(
                features,
                valid,
                radius=5,
                shrinkage=0.15,
                max_samples=2_000,
                threshold=3.0,
            )
            candidates = rank_optical_candidates(
                scores,
                manifest,
                threshold=3.0,
                min_pixels=2,
                min_dates=2,
                min_valid_dates=2,
                top_k=10,
            )
            self.assertTrue(candidates)
            first = candidates[0]
            self.assertIn(first["peak"]["date"], manifest["dates"][1:3])
            self.assertGreaterEqual(first["supportDateCountAtPeakPixel"], 2)
            self.assertEqual(3, first["validDateCountAtPeakPixel"])
            self.assertAlmostEqual(2.0 / 3.0, first["supportFractionAtPeakPixel"])
            self.assertLessEqual(abs(first["peak"]["row"] - 18), 1)
            self.assertLessEqual(abs(first["peak"]["column"] - 24), 1)
            self.assertEqual(
                "standardized anomaly score; not probability",
                first["scoreType"],
            )

    def test_per_date_components_do_not_merge_moving_one_date_anomalies(self) -> None:
        dates, rows, columns = 2, 4, 4
        per_date = np.zeros((dates, rows, columns), dtype=float)
        per_date[0, 1, 1] = 5.0
        per_date[1, 1, 2] = 5.0
        local = per_date[np.newaxis, ...]
        scores = {
            "featureNames": ["red"],
            "local": local,
            "localFeatureIndex": np.zeros_like(per_date, dtype=np.int16),
            "useRx": np.zeros_like(per_date, dtype=bool),
            "perDate": per_date,
            "valid": np.ones_like(per_date, dtype=bool),
        }
        manifest = {
            "arraySha256": "a" * 64,
            "bbox": [500000.0, 4100000.0, 500040.0, 4100040.0],
            "pixelSizeM": 10.0,
            "dates": ["2025-04-01", "2025-05-01"],
            "nativeGsdM": {"red": 10.0},
        }
        one_date = rank_optical_candidates(
            scores,
            manifest,
            threshold=3.0,
            min_pixels=1,
            min_dates=1,
            min_valid_dates=2,
            top_k=10,
        )
        repeated = rank_optical_candidates(
            scores,
            manifest,
            threshold=3.0,
            min_pixels=1,
            min_dates=2,
            min_valid_dates=2,
            top_k=10,
        )
        self.assertEqual(2, len(one_date))
        self.assertEqual(0, len(repeated))

    def test_candidate_resolution_covers_every_component_signal(self) -> None:
        dates, rows, columns = 2, 3, 3
        local = np.zeros((2, dates, rows, columns), dtype=float)
        local[0, 0, 1, 1] = 6.0
        local[1, 0, 1, 2] = 5.0
        local[0, 1, 1, 1] = 4.0
        local_feature_index = np.argmax(np.abs(local), axis=0)
        per_date = np.max(np.abs(local), axis=0)
        scores = {
            "featureNames": ["red", "swir1"],
            "local": local,
            "localFeatureIndex": local_feature_index,
            "useRx": np.zeros_like(per_date, dtype=bool),
            "perDate": per_date,
            "valid": np.ones_like(per_date, dtype=bool),
        }
        manifest = {
            "arraySha256": "b" * 64,
            "bbox": [500000.0, 4100000.0, 500030.0, 4100030.0],
            "pixelSizeM": 10.0,
            "dates": ["2025-04-01", "2025-05-01"],
            "nativeGsdM": {"red": 10.0, "swir1": 20.0},
        }
        candidates = rank_optical_candidates(
            scores,
            manifest,
            threshold=3.0,
            min_pixels=1,
            min_dates=2,
            min_valid_dates=2,
            top_k=10,
        )
        self.assertEqual(1, len(candidates))
        self.assertEqual(2, candidates[0]["pixelCount"])
        self.assertEqual(20.0, candidates[0]["observableResolutionM"])

    def test_candidate_resolution_covers_cross_date_support(self) -> None:
        dates, rows, columns = 2, 3, 3
        local = np.zeros((2, dates, rows, columns), dtype=float)
        local[0, 0, 1, 1] = 6.0
        local[1, 1, 1, 1] = 5.0
        local_feature_index = np.argmax(np.abs(local), axis=0)
        per_date = np.max(np.abs(local), axis=0)
        scores = {
            "featureNames": ["red", "swir1"],
            "local": local,
            "localFeatureIndex": local_feature_index,
            "useRx": np.zeros_like(per_date, dtype=bool),
            "perDate": per_date,
            "valid": np.ones_like(per_date, dtype=bool),
        }
        manifest = {
            "arraySha256": "c" * 64,
            "bbox": [500000.0, 4100000.0, 500030.0, 4100030.0],
            "pixelSizeM": 10.0,
            "dates": ["2025-04-01", "2025-05-01"],
            "nativeGsdM": {"red": 10.0, "swir1": 20.0},
        }
        candidates = rank_optical_candidates(
            scores,
            manifest,
            threshold=3.0,
            min_pixels=1,
            min_dates=2,
            min_valid_dates=2,
            top_k=10,
        )
        self.assertEqual(1, len(candidates))
        self.assertEqual(
            [10.0, 20.0],
            [
                signal["observableResolutionM"]
                for signal in candidates[0]["supportSignals"]
            ],
        )
        self.assertEqual(20.0, candidates[0]["observableResolutionM"])

    def test_manifest_rejects_malformed_dates_and_archive_extras(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["dates"][0] = "not-a-date"
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "ISO-8601"):
                load_optical_cube(manifest_path)

            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            array_path = directory / "cube.npz"
            with np.load(array_path, allow_pickle=False) as archive:
                values = {name: archive[name] for name in archive.files}
            np.savez_compressed(array_path, **values, unexpected=np.zeros((1,)))
            manifest["arraySha256"] = sha256_file(array_path)
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "members"):
                load_optical_cube(manifest_path)

    def test_manifest_rejects_equivalent_timestamp_spellings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            manifest["dates"][0] = "2025-03-15T00:00:00Z"
            manifest["dates"][1] = "2025-03-15T01:00:00+01:00"
            atomic_write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "unique"):
                load_optical_cube(manifest_path)

    def test_cli_writes_hash_bound_candidate_and_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            out_dir = directory / "run"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "analyze",
                    "--manifest",
                    str(manifest_path),
                    "--out-dir",
                    str(out_dir),
                    "--background-radius-m",
                    "50",
                    "--threshold",
                    "3",
                    "--min-pixels",
                    "2",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            result = load_json(out_dir / "candidates.json")
            self.assertFalse(result["input"]["targetLabelsUsed"])
            self.assertTrue(result["candidates"])
            self.assertIn("not calibrated probabilities", result["method"]["claimBoundary"])
            self.assertEqual("1.2", result["method"]["version"])
            self.assertEqual(
                {
                    "ij_common.py",
                    "ij_optical.py",
                    "ij_optical_io.py",
                    "ij_sources.py",
                    "ij_spatial.py",
                    "satellite.py",
                },
                set(result["method"]["implementation"]["artifacts"]),
            )
            self.assertIn("python", result["method"]["implementation"]["runtime"])
            self.assertIn("pyproj", result["method"]["implementation"]["runtime"])
            self.assertEqual("surface-reflectance", result["input"]["unit"])
            self.assertTrue(result["input"]["northUp"])
            self.assertEqual(1.0, result["input"]["reflectanceScale"])
            self.assertEqual(0.0, result["input"]["reflectanceOffset"])
            self.assertEqual("restricted", result["access"]["disclosure"])
            self.assertTrue(result["access"]["containsPreciseCoordinates"])
            for diagnostic in result["diagnostics"].values():
                path = Path(diagnostic["path"])
                self.assertTrue(path.is_file())
                self.assertEqual(diagnostic["sha256"], sha256_file(path))

            before = {
                path.name: sha256_file(path)
                for path in out_dir.iterdir()
                if path.is_file()
            }
            repeated = subprocess.run(
                completed.args,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, repeated.returncode)
            self.assertIn("already exist", repeated.stderr)
            self.assertEqual(
                before,
                {
                    path.name: sha256_file(path)
                    for path in out_dir.iterdir()
                    if path.is_file()
                },
            )

    def test_failed_bundle_build_leaves_no_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            out_dir = directory / "run"
            args = satellite_cli.build_parser().parse_args(
                [
                    "analyze",
                    "--manifest",
                    str(manifest_path),
                    "--out-dir",
                    str(out_dir),
                    "--background-radius-m",
                    "50",
                    "--threshold",
                    "3",
                    "--min-pixels",
                    "2",
                ]
            )
            with patch.object(
                satellite_cli,
                "build_optical_result",
                side_effect=RuntimeError("injected late failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "injected late failure"):
                    satellite_cli.command_analyze(args)
            self.assertFalse(out_dir.exists())
            self.assertFalse(list(directory.glob(".run.*")))

    def test_cli_refuses_to_overwrite_an_input_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            manifest = load_json(manifest_path)
            out_dir = directory / "run"
            out_dir.mkdir()
            collision = out_dir / "optical-scores.npz"
            (directory / manifest["arrayPath"]).replace(collision)
            manifest["arrayPath"] = str(collision.relative_to(directory))
            manifest["arraySha256"] = sha256_file(collision)
            atomic_write_json(manifest_path, manifest)
            before = collision.read_bytes()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "analyze",
                    "--manifest",
                    str(manifest_path),
                    "--out-dir",
                    str(out_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("overwrite an input artifact", completed.stderr)
            self.assertEqual(before, collision.read_bytes())

    def test_cli_rejects_dangling_output_directory_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            out_dir = directory / "run"
            outside = directory / "outside"
            out_dir.symlink_to(outside, target_is_directory=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "analyze",
                    "--manifest",
                    str(manifest_path),
                    "--out-dir",
                    str(out_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("symbolic link", completed.stderr)
            self.assertFalse(outside.exists())

    def test_cli_rejects_non_finite_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            manifest_path = build_test_cube(directory)
            for threshold in ("nan", "inf", "-inf"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(CLI_PATH),
                        "analyze",
                        "--manifest",
                        str(manifest_path),
                        "--out-dir",
                        str(directory / threshold.replace("-", "negative-")),
                        f"--threshold={threshold}",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(0, completed.returncode)
                self.assertIn("positive and finite", completed.stderr)


if __name__ == "__main__":
    unittest.main()
