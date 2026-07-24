from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
CLI_PATH = SCRIPT_DIR / "methodology.py"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_common import atomic_write_json
from methodology import add_decision, build_method_case, validate_method_case


class MethodologyTests(unittest.TestCase):
    def test_case_records_frame_and_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            case_path = Path(temporary_directory) / "case.json"
            case = build_method_case(
                "Framed case",
                "Which relief proxies repeat?",
                "Generalized study area",
                "restricted",
                [],
                "local relief contrast",
                ["ground classification retains low banks"],
                "40-160 m",
                ["modern drainage", "geological ridge"],
                "advance only if two visualization families agree",
                "candidate follows mapped modern drainage",
                "target labels withheld",
            )
            atomic_write_json(case_path, case)
            decision = add_decision(
                case_path,
                "visualization",
                "Compare hillshade and local relief",
                "Directional lighting alone can hide earthworks",
                ["single-azimuth hillshade"],
                "withheld",
                ["sha256:example"],
            )
            self.assertEqual("withheld", decision["targetLabelsState"])
            persisted = json.loads(case_path.read_text(encoding="utf-8"))
            self.assertEqual("1.1", persisted["schemaVersion"])
            self.assertEqual("local relief contrast", persisted["researchFrame"]["expectedProxy"])
            self.assertEqual(1, len(persisted["decisionLog"]))
            self.assertEqual([], validate_method_case(persisted))

    def test_cli_rejects_an_empty_visibility_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "new-case",
                    "--title",
                    "Incomplete case",
                    "--question",
                    "What is visible?",
                    "--study-area",
                    "Generalized area",
                    "--expected-proxy",
                    "local relief",
                    "--target-scale",
                    "40-160 m",
                    "--alternative-explanation",
                    "modern drainage",
                    "--decision-rule",
                    "two products agree",
                    "--falsifier",
                    "mapped drain",
                    "--interpretive-prior",
                    "target labels withheld",
                    "--out",
                    str(Path(temporary_directory) / "case.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("visibility condition", completed.stderr)


if __name__ == "__main__":
    unittest.main()
