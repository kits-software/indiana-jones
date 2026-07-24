from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_artifacts import public_export
from ij_authoring import prepare_research_plan
from ij_plan import new_plan, validate_plan
from ij_result_validation import deterministic_result_metadata
from search_plan import _parser


def _plan(disclosure: str) -> dict:
    return new_plan(
        "Exact public district",
        "Where do the documented candidates cluster?",
        [19.0, 54.0, 19.2, 54.2],
        2,
        2,
        "historical-reconstruction",
        disclosure,
        "gazetteer:exact-public",
    )


class PublicExactDefaultsTests(unittest.TestCase):
    def test_planner_cli_defaults_new_cases_to_public(self) -> None:
        args = _parser().parse_args(
            [
                "new",
                "--place",
                "Public district",
                "--question",
                "Where are the candidates?",
                "--gazetteer-id",
                "gazetteer:public",
                "--bbox",
                "19.0",
                "54.0",
                "19.2",
                "54.2",
                "--out",
                "case.json",
            ]
        )
        self.assertEqual("public", args.disclosure)

    def test_public_plan_uses_exportable_exact_area_and_grid_geometry(self) -> None:
        plan = _plan("public")
        self.assertEqual([], validate_plan(plan).errors)
        self.assertIn("geometry", plan["area"])
        self.assertNotIn("restrictedGeometry", plan["area"])
        self.assertEqual("public", plan["area"]["sensitivity"])
        self.assertTrue(
            all(
                cell["sensitivity"] == "public"
                and "geometry" in cell
                and "restrictedGeometry" not in cell
                for cell in plan["grid"]["cells"]
            )
        )
        exported = public_export(plan, "2.0-public")
        self.assertEqual(plan["area"]["geometry"], exported["area"]["geometry"])
        self.assertEqual(
            plan["grid"]["cells"][0]["geometry"],
            exported["grid"]["cells"][0]["geometry"],
        )

    def test_restricted_plan_keeps_area_and_grid_geometry_restricted(self) -> None:
        plan = _plan("restricted")
        self.assertEqual([], validate_plan(plan).errors)
        self.assertIn("restrictedGeometry", plan["area"])
        self.assertNotIn("geometry", plan["area"])
        self.assertEqual("restricted", plan["area"]["sensitivity"])
        self.assertTrue(
            all(
                cell["sensitivity"] == "restricted"
                and "restrictedGeometry" in cell
                and "geometry" not in cell
                for cell in plan["grid"]["cells"]
            )
        )
        exported = public_export(plan)
        self.assertNotIn("geometry", exported["area"])
        self.assertTrue(
            all("geometry" not in cell for cell in exported["grid"]["cells"])
        )

    def test_public_export_withholds_geometry_without_explicit_public_class(self) -> None:
        plan = _plan("public")
        plan["area"].pop("sensitivity")
        plan["grid"]["cells"][0]["sensitivity"] = "unknown"
        exported = public_export(plan, "2.0-public")
        self.assertNotIn("geometry", exported["area"])
        self.assertNotIn("geometry", exported["grid"]["cells"][0])

    def test_package_can_repair_restricted_skeleton_to_public_exact(self) -> None:
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        bbox = template["area"]["restrictedGeometry"]["bbox"]
        skeleton = new_plan(
            template["area"]["namedPlace"],
            template["case"]["question"],
            bbox,
            template["grid"]["rows"],
            template["grid"]["columns"],
            template["case"]["studyKind"],
            "restricted",
            template["area"]["selectedGazetteerId"],
        )
        public_layout = new_plan(
            template["area"]["namedPlace"],
            template["case"]["question"],
            bbox,
            template["grid"]["rows"],
            template["grid"]["columns"],
            template["case"]["studyKind"],
            "public",
            template["area"]["selectedGazetteerId"],
        )
        package = {
            "schemaVersion": "archaeological-research-package-1.0",
            "case": {
                "intendedDecision": template["case"]["intendedDecision"],
                "targetLabelsState": template["case"]["targetLabelsState"],
                "disclosure": "public",
            },
            "area": {
                "publicDescription": template["area"]["publicDescription"],
                "geometry": copy.deepcopy(public_layout["area"]["geometry"]),
                "sensitivity": "public",
            },
            "grid": copy.deepcopy(public_layout["grid"]),
            "sources": template["sources"],
            "nodes": template["nodes"],
            "edges": template["edges"],
            "actions": template["actions"],
        }
        prepared = prepare_research_plan(skeleton, package)
        self.assertEqual("public", prepared["case"]["disclosure"])
        self.assertIn("geometry", prepared["area"])
        self.assertNotIn("restrictedGeometry", prepared["area"])
        self.assertTrue(
            all(cell["sensitivity"] == "public" for cell in prepared["grid"]["cells"])
        )

    def test_package_grid_rejects_unknown_cell_fields(self) -> None:
        skeleton = _plan("public")
        grid = copy.deepcopy(skeleton["grid"])
        grid["cells"][0]["shellCommand"] = "ignored"
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            prepare_research_plan(
                skeleton,
                {
                    "schemaVersion": "archaeological-research-package-1.0",
                    "grid": grid,
                    "sources": [],
                    "nodes": [],
                    "edges": [],
                    "actions": [],
                },
            )

    def test_deterministic_results_propagate_declared_disclosure(self) -> None:
        action = {"method": "public-desk", "execution": {"executor": "test"}}
        public = deterministic_result_metadata(_plan("public"), action, [])
        restricted = deterministic_result_metadata(_plan("restricted"), action, [])
        self.assertEqual(("public", "public"), (
            public["resultSensitivity"],
            public["disclosureDecision"],
        ))
        self.assertEqual(("restricted", "restricted"), (
            restricted["resultSensitivity"],
            restricted["disclosureDecision"],
        ))

    def test_non_public_source_still_restricts_public_case_result(self) -> None:
        plan = _plan("public")
        plan["sources"] = [{"sourceId": "private", "sensitivity": "non-public"}]
        action = {"method": "catalogue", "execution": {"executor": "test"}}
        metadata = deterministic_result_metadata(plan, action, ["private"])
        self.assertEqual("non-public", metadata["resultSensitivity"])
        self.assertEqual(
            "heritage-authority-only",
            metadata["disclosureDecision"],
        )


if __name__ == "__main__":
    unittest.main()
