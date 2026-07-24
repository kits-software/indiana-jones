from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, PngImagePlugin


SCRIPT_DIR = Path(__file__).resolve().parents[1]
ANNOTATE = SCRIPT_DIR / "annotate_evidence.py"
VALIDATE = SCRIPT_DIR / "validate_public_report.py"


def annotation_payload(disclosure: str = "public") -> dict:
    return {
        "schemaVersion": "1.0",
        "title": "Candidate C-01 — source frame",
        "disclosure": disclosure,
        "coordinateSpace": "normalized",
        "source": {
            "sourceId": "src_test",
            "provider": "Open Imagery Test",
            "product": "Synthetic orthophoto",
            "sensor": "Synthetic RGB",
            "acquiredAt": "2026-07-24",
            "resolution": "1 m",
            "license": "Test licence",
            "attribution": "Synthetic test source",
            "locator": "https://example.test/item/restricted",
            "publicLocator": "https://example.test/collection",
            "sourceRole": "analysis",
            "derivativeUseAuthorized": True,
        },
        "frame": {
            "viewType": "source-measurement",
            "orientation": "north-up",
            "locationLabel": "Generalized test area",
            "processing": ["Synthetic source; no geometric processing"],
        },
        "annotations": [
            {
                "id": "A",
                "kind": "ellipse",
                "points": [[0.2, 0.25], [0.7, 0.75]],
                "label": "Repeated tonal arc",
                "observation": "Synthetic observation for renderer validation.",
                "status": "observed",
                "sensitivity": disclosure,
                "color": "#ff5a47",
            }
        ],
    }


class ReportingTests(unittest.TestCase):
    def test_authored_reporting_files_stay_below_700_lines(self) -> None:
        skill_directory = Path(__file__).resolve().parents[2]
        oversized = []
        for path in skill_directory.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md"}:
                continue
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count >= 700:
                oversized.append(f"{path.relative_to(skill_directory)}: {line_count}")
        self.assertEqual([], oversized, "Oversized authored files: " + ", ".join(oversized))

    def test_renderer_writes_paired_hash_bound_public_plate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            image_path = directory / "source.png"
            annotation_path = directory / "annotation.json"
            output_path = directory / "candidate-plate.png"
            manifest_path = directory / "candidate-plate.manifest.json"
            Image.new("RGB", (160, 120), color=(90, 120, 70)).save(image_path)
            annotation_path.write_text(
                json.dumps(annotation_payload()),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ANNOTATE),
                    "--image",
                    str(image_path),
                    "--annotations",
                    str(annotation_path),
                    "--out",
                    str(output_path),
                    "--manifest-out",
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertFalse(manifest["containsPreciseCoordinates"])
            self.assertTrue(
                manifest["renderedOutput"]["pairedSourceAndAnnotatedViews"]
            )
            self.assertEqual(
                "source-measurement",
                manifest["renderedOutput"]["leftViewType"],
            )
            self.assertEqual(
                "https://example.test/collection",
                manifest["source"]["locator"],
            )
            self.assertTrue(output_path.is_file())
            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATE),
                    str(output_path),
                    str(manifest_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, validation.returncode, validation.stdout)

    def test_renderer_rejects_google_and_unlicensed_derivatives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            image_path = directory / "source.png"
            Image.new("RGB", (100, 80), color=(0, 0, 0)).save(image_path)
            cases = [
                ("google", {"provider": "Google Earth"}),
                ("unlicensed", {"derivativeUseAuthorized": False}),
            ]
            for name, override in cases:
                payload = annotation_payload()
                payload["source"].update(override)
                annotation_path = directory / f"{name}.json"
                annotation_path.write_text(json.dumps(payload), encoding="utf-8")
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ANNOTATE),
                        "--image",
                        str(image_path),
                        "--annotations",
                        str(annotation_path),
                        "--out",
                        str(directory / f"{name}.png"),
                        "--manifest-out",
                        str(directory / f"{name}.manifest.json"),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(2, completed.returncode)

    def test_public_validator_detects_coordinates_and_image_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            report_path = directory / "report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "disclosure": "public",
                        "restrictedLocation": {"latitude": 51.12345},
                        "sourceImageFileName": "frame-51.12345_16.12345.png",
                    }
                ),
                encoding="utf-8",
            )
            image_path = directory / "evidence.png"
            info = PngImagePlugin.PngInfo()
            info.add_text("Description", "location metadata")
            Image.new("RGB", (16, 16)).save(image_path, pnginfo=info)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATE),
                    str(report_path),
                    str(image_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, completed.returncode)
            result = json.loads(completed.stdout)
            codes = {item["code"] for item in result["issues"]}
            self.assertIn("forbidden-location-field", codes)
            self.assertIn("embedded-image-metadata", codes)
            self.assertIn("location-bearing-filename", codes)


if __name__ == "__main__":
    unittest.main()
