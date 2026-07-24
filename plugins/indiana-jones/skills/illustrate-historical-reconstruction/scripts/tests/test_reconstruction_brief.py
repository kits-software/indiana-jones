from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = SKILL_DIR.parents[1]
SCRIPT = SKILL_DIR / "scripts" / "validate_reconstruction_brief.py"
TEMPLATE = SKILL_DIR / "assets" / "reconstruction-brief-template.json"


def valid_brief() -> dict:
    payload = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    payload["title"] = "Harbour worker reconstruction"
    payload["researchQuestion"] = (
        "How could a harbour worker and working quay have appeared in 120 CE?"
    )
    payload["subject"].update(
        {
            "kind": "scene",
            "name": "Harbour worker and quay",
            "place": "Generalized Roman Mediterranean harbour",
            "timeSlice": "circa 120 CE",
            "state": "ordinary working day",
            "viewpoint": "street-level three-quarter view",
            "intendedUse": "public educational illustration",
        }
    )
    payload["sources"][0].update(
        {
            "citation": "Synthetic excavation report for validator testing",
            "url": "https://example.test/report",
            "accessedAt": "2026-07-24",
            "originFamilyId": "excavation-01",
            "roles": ["quay geometry", "material"],
            "licenseOrUseBasis": "Synthetic test source",
        }
    )
    payload["visualDecisions"][0].update(
        {
            "element": "Quay edge",
            "depiction": "Worn stone blocks at human scale",
            "rationale": "The source directly records the stone dimensions.",
            "promptClause": "worn stone quay blocks approximately waist high",
            "inspectionCheck": "Quay blocks retain irregular measured proportions.",
        }
    )
    payload["negativeConstraints"][0].update(
        {
            "constraint": "No modern dock hardware",
            "reason": "Modern steel bollards would be anachronistic.",
            "sourceIds": ["S1"],
        }
    )
    payload["prompt"].update(
        {
            "assetType": "museum interpretation image",
            "primaryRequest": "Illustrate a working harbour scene.",
            "structuralAnchors": ["waist-high irregular stone quay"],
            "culturalMaterialDetails": ["worn local stone", "period rope"],
            "sceneAndEnvironment": ["working waterfront", "salt weathering"],
            "composition": "street-level three-quarter view",
            "lightingAndMood": "natural morning light, active but ordinary",
            "constraints": ["keep the quay geometry legible"],
            "avoid": ["modern dock hardware", "pristine fantasy surfaces"],
            "finalPrompt": (
                "Historical-scene illustration of a working quay circa 120 CE; "
                "use a waist-high irregular stone quay, period rope, salt "
                "weathering, and no modern dock hardware."
            ),
        }
    )
    payload["review"].update(
        {
            "anachronismChecks": ["No modern dock fittings"],
            "geometryChecks": ["Quay height and block irregularity"],
            "culturalChecks": ["Ordinary labour is not idealized"],
            "remainingIssues": [],
        }
    )
    payload["caption"].update(
        {
            "summary": "A working quay reconstructed from excavated dimensions.",
            "uncertaintyStatement": (
                "The worker's individual appearance and exact activity are illustrative."
            ),
        }
    )
    return payload


def run_validator(payload: dict, stage: str = "preflight") -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as temporary_directory:
        brief_path = Path(temporary_directory) / "brief.json"
        brief_path.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(brief_path),
                "--stage",
                stage,
            ],
            check=False,
            capture_output=True,
            text=True,
        )


class ReconstructionBriefTests(unittest.TestCase):
    def test_authored_files_stay_below_700_lines(self) -> None:
        oversized = []
        for path in SKILL_DIR.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md"}:
                continue
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count >= 700:
                oversized.append(f"{path.relative_to(SKILL_DIR)}: {line_count}")
        self.assertEqual([], oversized, "Oversized authored files: " + ", ".join(oversized))

    def test_preflight_accepts_complete_evidence_led_brief(self) -> None:
        completed = run_validator(valid_brief())
        self.assertEqual(0, completed.returncode, completed.stdout)
        self.assertTrue(json.loads(completed.stdout)["valid"])

    def test_plugin_routes_and_surfaces_historical_illustration(self) -> None:
        manifest = json.loads(
            (PLUGIN_DIR / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        core_skill = (
            PLUGIN_DIR / "skills" / "indiana-jones" / "SKILL.md"
        ).read_text(encoding="utf-8")
        readme = (PLUGIN_DIR / "README.md").read_text(encoding="utf-8")
        interface = manifest["interface"]
        self.assertIn(
            "illustrate-historical-reconstruction",
            core_skill,
        )
        self.assertIn(
            "Evidence-Based Illustration",
            interface["capabilities"],
        )
        self.assertIn("historical illustration", manifest["keywords"])
        self.assertTrue(
            any("could have looked" in prompt for prompt in interface["defaultPrompt"])
        )
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        self.assertIn(
            "skills/illustrate-historical-reconstruction/SKILL.md",
            readme,
        )

    def test_high_impact_uncertainty_requires_alternative_and_policy_record(self) -> None:
        payload = valid_brief()
        decision = payload["visualDecisions"][0]
        decision["status"] = "plausible"
        decision["alternatives"] = []
        completed = run_validator(payload)
        self.assertEqual(1, completed.returncode)
        result = json.loads(completed.stdout)
        paths = {item["path"] for item in result["issues"]}
        self.assertIn("$.visualDecisions[0].alternatives", paths)
        self.assertIn("$.review.unresolvedHighImpact", paths)

    def test_unknown_source_reference_is_rejected(self) -> None:
        payload = valid_brief()
        payload["visualDecisions"][0]["sourceIds"] = ["S404"]
        completed = run_validator(payload)
        self.assertEqual(1, completed.returncode)
        result = json.loads(completed.stdout)
        self.assertTrue(
            any(
                "unknown source IDs" in item["message"]
                for item in result["issues"]
            )
        )

    def test_malformed_source_links_report_issues_without_crashing(self) -> None:
        payload = valid_brief()
        payload["visualDecisions"][0]["sourceIds"] = [42, {"id": "S1"}]
        completed = run_validator(payload)
        self.assertEqual(1, completed.returncode)
        result = json.loads(completed.stdout)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any(
                item["path"].startswith("$.visualDecisions[0].sourceIds[")
                for item in result["issues"]
            )
        )

    def test_final_stage_requires_generation_and_pixel_review(self) -> None:
        payload = valid_brief()
        completed = run_validator(payload, stage="final")
        self.assertEqual(1, completed.returncode)
        result = json.loads(completed.stdout)
        paths = {item["path"] for item in result["issues"]}
        self.assertIn("$.generation.outputPath", paths)
        self.assertIn("$.review.outputChecked", paths)

        payload["generation"].update(
            {
                "tool": "built-in image_gen",
                "generatedAt": "2026-07-24",
                "outputPath": "/workspace/harbour-reconstruction.png",
            }
        )
        payload["review"]["outputChecked"] = True
        completed = run_validator(payload, stage="final")
        self.assertEqual(0, completed.returncode, completed.stdout)


if __name__ == "__main__":
    unittest.main()
