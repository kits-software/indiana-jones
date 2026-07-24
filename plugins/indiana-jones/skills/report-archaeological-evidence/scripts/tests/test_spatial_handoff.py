from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
HANDOFF = SCRIPT_DIR / "create_spatial_handoff.py"


class SpatialHandoffTests(unittest.TestCase):
    def run_handoff(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HANDOFF), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_possible_new_candidate_gets_exact_google_maps_point(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed = self.run_handoff(
                "--title",
                "Possible new candidate",
                "--out-dir",
                temporary_directory,
                "--geometry",
                "point",
                "--feature-role",
                "candidate-point",
                "--location-class",
                "possible-new",
                "--sensitivity",
                "public",
                "--disclosure",
                "public",
                "--latitude",
                "53.123456",
                "--longitude",
                "20.654321",
            )
            self.assertEqual(0, completed.returncode, completed.stdout)
            directory = Path(temporary_directory)
            manifest = json.loads(
                (directory / "map-handoff.manifest.json").read_text()
            )
            geojson = json.loads((directory / "map-handoff.geojson").read_text())
            kml = (directory / "map-handoff.kml").read_text()
            self.assertEqual("exact-point", manifest["precisionClass"])
            self.assertTrue(manifest["containsPreciseCoordinates"])
            self.assertIn("google.com/maps/search", manifest["googleMapsLink"])
            self.assertEqual(
                manifest["googleMapsLink"],
                geojson["features"][0]["properties"]["googleMapsLink"],
            )
            self.assertEqual(
                [20.654321, 53.123456],
                geojson["features"][0]["geometry"]["coordinates"],
            )
            self.assertIn("<Point>", kml)
            self.assertIn("<![CDATA[<a href=", kml)
            self.assertIn("Open in Google Maps</a>", kml)

    def test_candidate_aoi_preserves_exact_footprint_without_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed = self.run_handoff(
                "--title",
                "Candidate footprint",
                "--out-dir",
                temporary_directory,
                "--geometry",
                "aoi",
                "--feature-role",
                "candidate-footprint",
                "--location-class",
                "possible-new",
                "--sensitivity",
                "public",
                "--disclosure",
                "public",
                "--west",
                "20.51",
                "--south",
                "53.80",
                "--east",
                "20.55",
                "--north",
                "53.83",
            )
            self.assertEqual(0, completed.returncode, completed.stdout)
            directory = Path(temporary_directory)
            manifest = json.loads(
                (directory / "map-handoff.manifest.json").read_text()
            )
            geojson = json.loads((directory / "map-handoff.geojson").read_text())
            self.assertEqual("exact-aoi", manifest["precisionClass"])
            self.assertIn("google.com/maps/@", manifest["googleMapsLink"])
            self.assertEqual(
                "candidate-footprint",
                geojson["features"][0]["properties"]["featureRole"],
            )
            self.assertEqual(
                [20.51, 53.8],
                geojson["features"][0]["geometry"]["coordinates"][0][0],
            )

    def test_public_handoff_rejects_protected_location_and_signed_image(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            protected = self.run_handoff(
                "--title",
                "Protected location",
                "--out-dir",
                temporary_directory,
                "--geometry",
                "point",
                "--feature-role",
                "candidate-point",
                "--location-class",
                "burial",
                "--sensitivity",
                "public",
                "--disclosure",
                "public",
                "--latitude",
                "53.123456",
                "--longitude",
                "20.654321",
            )
            self.assertEqual(2, protected.returncode)
            self.assertIn("cannot use public disclosure", protected.stdout)

            directory = Path(temporary_directory)
            features_path = directory / "signed-image.json"
            features_path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {
                                    "name": "Candidate",
                                    "featureRole": "candidate-point",
                                    "locationClass": "possible-new",
                                    "sensitivity": "public",
                                    "imageUrl": "https://example.test/a.png?token=secret",
                                },
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [20.654321, 53.123456],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            signed = self.run_handoff(
                "--title",
                "Signed image",
                "--out-dir",
                str(directory / "signed-output"),
                "--features",
                str(features_path),
                "--disclosure",
                "public",
            )
            self.assertEqual(2, signed.returncode)
            self.assertIn("signed or credential", signed.stdout)

    def test_feature_collection_keeps_points_aois_and_image_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            features_path = directory / "features.json"
            features_path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "id": "candidate-a",
                                "properties": {
                                    "name": "Candidate A",
                                    "featureRole": "candidate-point",
                                    "locationClass": "possible-new",
                                    "sensitivity": "public",
                                    "observation": "Low-relief oval response",
                                },
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [20.52923, 53.81515],
                                },
                            },
                            {
                                "type": "Feature",
                                "id": "source-frame-01",
                                "properties": {
                                    "name": "Orthophoto source frame",
                                    "featureRole": "image-point",
                                    "sensitivity": "public",
                                    "imagePath": "source-orthophoto-plate.png",
                                    "imageSourceId": "src-gugik-2025",
                                    "imageCaption": "Source image centre",
                                },
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [20.53011, 53.81491],
                                },
                            },
                            {
                                "type": "Feature",
                                "id": "research-area",
                                "properties": {
                                    "name": "Research AOI",
                                    "featureRole": "research-aoi",
                                    "sensitivity": "public",
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [20.51, 53.80],
                                            [20.55, 53.80],
                                            [20.55, 53.83],
                                            [20.51, 53.83],
                                            [20.51, 53.80],
                                        ]
                                    ],
                                },
                            },
                            {
                                "type": "Feature",
                                "id": "source-frame-footprint-01",
                                "properties": {
                                    "name": "Orthophoto frame footprint",
                                    "featureRole": "image-footprint",
                                    "sensitivity": "public",
                                    "imageUrl": "https://example.test/frame/01",
                                    "imageSourceId": "src-gugik-2025",
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [20.50, 53.79],
                                            [20.56, 53.79],
                                            [20.56, 53.84],
                                            [20.50, 53.84],
                                            [20.50, 53.79],
                                        ]
                                    ],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = self.run_handoff(
                "--title",
                "Candidate A spatial evidence",
                "--out-dir",
                str(directory / "handoff"),
                "--features",
                str(features_path),
                "--disclosure",
                "public",
            )
            self.assertEqual(0, completed.returncode, completed.stdout)
            output = directory / "handoff"
            manifest = json.loads(
                (output / "map-handoff.manifest.json").read_text()
            )
            geojson = json.loads((output / "map-handoff.geojson").read_text())
            kml = (output / "map-handoff.kml").read_text()
            self.assertEqual("exact-feature-collection", manifest["precisionClass"])
            self.assertEqual(4, manifest["featureCount"])
            self.assertEqual(2, manifest["pointCount"])
            self.assertEqual(2, manifest["areaCount"])
            self.assertEqual(2, manifest["imageLinkedFeatureCount"])
            self.assertEqual(4, len(manifest["googleMapsLinks"]))
            self.assertTrue(
                all(
                    feature["properties"]["googleMapsLink"].startswith(
                        "https://www.google.com/maps/"
                    )
                    for feature in geojson["features"]
                )
            )
            self.assertEqual(4, kml.count("Open in Google Maps</a>"))
            self.assertEqual(
                [20.52923, 53.81515],
                manifest["features"][0]["geometry"]["coordinates"],
            )
            self.assertEqual(
                "Polygon",
                manifest["features"][3]["geometry"]["type"],
            )
            self.assertIn("source-orthophoto-plate.png", kml)
            self.assertIn("https://example.test/frame/01", kml)
            self.assertIn("Candidate A", kml)
            self.assertIn("<Polygon>", kml)

    def test_public_handoff_requires_explicit_public_spatial_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed = self.run_handoff(
                "--title",
                "Unclassified point",
                "--out-dir",
                temporary_directory,
                "--geometry",
                "point",
                "--feature-role",
                "candidate-point",
                "--location-class",
                "possible-new",
                "--disclosure",
                "public",
                "--latitude",
                "53.123456",
                "--longitude",
                "20.654321",
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("requires explicit sensitivity=public", completed.stdout)

    def test_feature_collection_rejects_unclosed_polygon(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            features_path = directory / "features.json"
            features_path.write_text(
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "properties": {
                                    "name": "Broken AOI",
                                    "featureRole": "research-aoi",
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [
                                            [20.51, 53.80],
                                            [20.55, 53.80],
                                            [20.55, 53.83],
                                            [20.51, 53.83],
                                        ]
                                    ],
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = self.run_handoff(
                "--title",
                "Broken",
                "--out-dir",
                str(directory / "handoff"),
                "--features",
                str(features_path),
                "--disclosure",
                "public",
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("must be closed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
