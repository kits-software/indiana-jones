from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_authoring import prepare_research_plan
from ij_plan import new_plan, validate_plan
from ij_readiness import readiness_errors


class ResearchPackageAuthoringTests(unittest.TestCase):
    def test_fresh_skeleton_can_be_made_ready_from_a_declarative_package(self) -> None:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        area = template["area"]["restrictedGeometry"]["bbox"]
        skeleton = new_plan(
            template["area"]["namedPlace"],
            template["case"]["question"],
            area,
            template["grid"]["rows"],
            template["grid"]["columns"],
            template["case"]["studyKind"],
            template["case"]["disclosure"],
            template["area"]["selectedGazetteerId"],
        )
        package = {
            "schemaVersion": "archaeological-research-package-1.0",
            "case": {
                "intendedDecision": template["case"]["intendedDecision"],
                "targetLabelsState": template["case"]["targetLabelsState"],
            },
            "area": {"publicDescription": template["area"]["publicDescription"]},
            "sources": template["sources"],
            "nodes": template["nodes"],
            "edges": template["edges"],
            "actions": template["actions"],
        }
        prepared = prepare_research_plan(skeleton, package)
        self.assertTrue(validate_plan(prepared).valid)
        self.assertEqual([], readiness_errors(prepared))
        self.assertEqual(template["sources"], prepared["sources"])
        self.assertEqual(template["actions"], prepared["actions"])

    def test_package_cannot_smuggle_unknown_top_level_fields(self) -> None:
        skeleton = new_plan(
            "York",
            "Where are sword records concentrated?",
            [-1.2, 53.8, -0.9, 54.1],
            3,
            3,
            "prospective-survey",
            "public",
            "gaz:york",
        )
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            prepare_research_plan(
                skeleton,
                {
                    "schemaVersion": "archaeological-research-package-1.0",
                    "sources": [],
                    "nodes": [],
                    "edges": [],
                    "actions": [],
                    "runThisShellCommand": "ignored",
                },
            )


if __name__ == "__main__":
    unittest.main()
