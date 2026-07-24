from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
CLI = SCRIPT_DIR / "search_plan.py"
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
GOLDEN = Path(__file__).parent / "goldens" / "public-export-hashes.json"
sys.path.insert(0, str(SCRIPT_DIR))

from entity_fixture import entity_record
from ij_artifacts import public_export


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


class ExtendedCliTests(unittest.TestCase):
    def test_new_prepare_and_ready_validation_are_documented_commands(self) -> None:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skeleton = root / "skeleton.json"
            package = root / "package.json"
            prepared = root / "prepared.json"
            area = template["area"]["restrictedGeometry"]["bbox"]
            created = _run(
                "new",
                "--place",
                template["area"]["namedPlace"],
                "--question",
                template["case"]["question"],
                "--gazetteer-id",
                template["area"]["selectedGazetteerId"],
                "--bbox",
                *(str(value) for value in area),
                "--rows",
                str(template["grid"]["rows"]),
                "--columns",
                str(template["grid"]["columns"]),
                "--study-kind",
                template["case"]["studyKind"],
                "--disclosure",
                template["case"]["disclosure"],
                "--out",
                str(skeleton),
            )
            self.assertEqual(0, created.returncode, created.stderr)
            package.write_text(
                json.dumps(
                    {
                        "schemaVersion": "archaeological-research-package-1.0",
                        "case": {
                            "intendedDecision": template["case"]["intendedDecision"],
                            "targetLabelsState": template["case"]["targetLabelsState"],
                        },
                        "area": {
                            "publicDescription": template["area"]["publicDescription"]
                        },
                        "sources": template["sources"],
                        "nodes": template["nodes"],
                        "edges": template["edges"],
                        "actions": template["actions"],
                    }
                ),
                encoding="utf-8",
            )
            result = _run(
                "prepare",
                "--plan",
                str(skeleton),
                "--package",
                str(package),
                "--out",
                str(prepared),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            validated = _run("validate", "--plan", str(prepared), "--ready")
            self.assertEqual(0, validated.returncode, validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["ready"])

    def test_search_ladder_cli_is_bounded_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.json"
            second = Path(temp_dir) / "second.json"
            arguments = (
                "search-ladder",
                "--place-alias",
                "Eboracum",
                "--place-alias",
                "York",
                "--object-term",
                "sword",
                "--language-variant",
                "gladius",
                "--maximum",
                "4",
            )
            result = _run(*arguments, "--out", str(first))
            self.assertEqual(0, result.returncode, result.stderr)
            repeated = _run(*arguments, "--out", str(second))
            self.assertEqual(0, repeated.returncode, repeated.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(4, json.loads(first.read_text())["queryCount"])

    def test_both_public_export_contracts_match_golden_hashes(self) -> None:
        plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        plan["nodes"][0]["sensitivity"] = "public"
        plan["nodes"][0]["kind"] = "object"
        plan["nodes"][0]["record"] = entity_record("object")
        expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
        exports = {
            version: public_export(plan, version)
            for version in ("1.0-public", "2.0-public")
        }
        for version, export in exports.items():
            self.assertEqual(
                expected[version],
                export["publicExport"]["publicContentSha256"],
            )
        self.assertFalse(any("record" in node for node in exports["1.0-public"]["nodes"]))
        self.assertTrue(any("record" in node for node in exports["2.0-public"]["nodes"]))

    def test_export_public_cli_selects_contract_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "public.json"
            result = _run(
                "export-public",
                "--plan",
                str(TEMPLATE),
                "--schema",
                "2.0-public",
                "--out",
                str(output),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            exported = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("2.0-public", exported["schemaVersion"])
            self.assertEqual(
                "2.0-public",
                exported["publicExport"]["contractVersion"],
            )

    def test_heuristic_cli_preserves_public_evidence_and_withholds_explicit_restriction(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "heuristic-input.json"
            output_path = root / "heuristic-report.json"
            input_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": (
                            "heuristic-archaeological-assessment-input-1.0"
                        ),
                        "method": "Weighted map, imagery, and find-record agreement",
                        "scoreMeaning": (
                            "Higher scores mean more independent research signals agree"
                        ),
                        "evidenceReferences": [
                            "snapshot:map:1840",
                            "snapshot:imagery:2026",
                            "snapshot:authority:1",
                        ],
                        "assumptions": [
                            "The historic map registration is accurate within 20 metres"
                        ],
                        "uncertainty": [
                            "Seasonal visibility may change the imagery signal"
                        ],
                        "limitations": [
                            "No representative held-out calibration set is available"
                        ],
                        "case": {
                            "researchMode": "treasure-research-public",
                            "disclosure": "public",
                        },
                        "candidates": [
                            {
                                "candidateId": "public-gold-candidate",
                                "score": 8.2,
                                "hypothesis": (
                                    "Hoard deposition near a mapped boundary junction"
                                ),
                                "coordinates": [19.54321, 54.54321],
                                "imageryAnnotationRefs": [
                                    "plate-1:boundary-junction"
                                ],
                                "evidenceReferences": [
                                    "snapshot:map:1840",
                                    "snapshot:imagery:2026",
                                ],
                            },
                            {
                                "candidateId": "protected-comparison",
                                "score": 9.1,
                                "hypothesis": "Explicitly protected comparison location",
                                "coordinates": [18.11111, 53.22222],
                                "imageryAnnotationRef": "plate-2:protected",
                                "spatialRestriction": "authority-only",
                                "evidenceReferences": ["snapshot:authority:1"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = _run(
                "assess-heuristic",
                "--input",
                str(input_path),
                "--out",
                str(output_path),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                "heuristic-ranking-not-probability",
                report["assessmentType"],
            )
            self.assertEqual("not-calibrated", report["calibrationStatus"])
            self.assertEqual(1, len(report["assumptions"]))
            self.assertEqual(1, len(report["uncertainty"]))
            protected, public = report["candidates"]
            self.assertNotIn("coordinates", protected)
            self.assertNotIn("imageryAnnotationRef", protected)
            self.assertEqual(
                [19.54321, 54.54321],
                public["coordinates"],
            )
            self.assertEqual(
                ["plate-1:boundary-junction"],
                public["imageryAnnotationRefs"],
            )
            self.assertIn("google.com/maps", public["googleMapsLink"])
            self.assertNotIn("estimatedProbability", report)

    def test_heuristic_cli_rejects_probability_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "invalid-heuristic-input.json"
            output_path = root / "heuristic-report.json"
            input_path.write_text(
                json.dumps(
                    {
                        "method": "Evidence agreement",
                        "scoreMeaning": "Higher means more signals agree",
                        "evidenceReferences": ["snapshot:map:1840"],
                        "assumptions": ["The map registration is usable"],
                        "uncertainty": ["The rank has not been independently validated"],
                        "limitations": ["Only one map edition is available"],
                        "estimatedProbability": 0.75,
                        "candidates": [
                            {
                                "candidateId": "candidate-a",
                                "score": 7.5,
                                "hypothesis": "Mapped-boundary comparison point",
                                "evidenceReferences": ["snapshot:map:1840"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = _run(
                "assess-heuristic",
                "--input",
                str(input_path),
                "--out",
                str(output_path),
            )
            self.assertEqual(3, result.returncode)
            diagnostic = json.loads(result.stderr)
            self.assertEqual("IJ_DATA_INVALID", diagnostic["error"]["code"])
            self.assertIn("probability fields", diagnostic["error"]["message"])
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
