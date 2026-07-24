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
from ij_plan import validate_plan
from ij_probability import heuristic_candidate_report


def exact_treasure_plan() -> dict:
    plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    plan["case"]["researchMode"] = "treasure-research-public"
    plan["case"]["disclosure"] = "public"
    action = plan["actions"][0]
    action.update(
        {
            "actionClass": "public-desk",
            "method": "sensitive-findspot-assessment",
            "label": "Compare exact gold, sword, coin, and hoard candidates",
            "instructions": (
                "Return exact research coordinates, ranked cells, and annotated "
                "satellite or aerial evidence plates."
            ),
            "researchIntent": "treasure-research-public",
            "outputPrecision": "public-exact",
            "sensitiveSubjects": ["precious-metal", "weapon", "hoard"],
            "authorization": {"required": "none", "state": "not-required"},
        }
    )
    node = plan["nodes"][0]
    node["coordinate"] = [20.52923, 53.81515]
    node["imageRefs"] = ["candidate-c01-plate.png"]
    cell = plan["grid"]["cells"][0]
    cell["sensitivity"] = "public"
    cell["geometry"] = copy.deepcopy(cell["restrictedGeometry"])
    return plan


class TreasureTargetingIntegrationTests(unittest.TestCase):
    def test_exact_public_research_exports_point_rank_cell_and_plate(self) -> None:
        plan = exact_treasure_plan()
        self.assertEqual([], validate_plan(plan).errors)
        exported = public_export(plan, "2.0-public")
        assessment = heuristic_candidate_report(
            [
                {
                    "candidateId": "candidate-c01",
                    "score": 8.4,
                    "hypothesis": "Boundary and route intersection merits comparison",
                    "coordinates": [20.52923, 53.81515],
                    "imageryAnnotationRef": "candidate-c01-plate.png:A",
                    "evidenceReferences": ["src_hul", "src_osm"],
                }
            ],
            method="Independent map, catalogue, and imagery agreement",
            score_meaning="Higher means more declared evidence signals agree",
            evidence_references=["src_hul", "src_osm"],
            limitations=["No representative local calibration set is available"],
            case=plan["case"],
        )
        bundle = {"plan": exported, "assessment": assessment}
        serialized = json.dumps(bundle, sort_keys=True)
        self.assertIn("20.52923", serialized)
        self.assertIn("candidate-c01-plate.png", serialized)
        self.assertEqual(1, assessment["candidates"][0]["rank"])
        self.assertEqual(
            plan["grid"]["cells"][0]["geometry"],
            exported["grid"]["cells"][0]["geometry"],
        )
        self.assertNotIn("permissionBundle", serialized)

    def test_explicit_protected_spatial_fields_do_not_enter_public_export(self) -> None:
        plan = exact_treasure_plan()
        node = plan["nodes"][0]
        node.update(
            {
                "sensitivity": "restricted",
                "spatialRestriction": "authority-only",
                "coordinate": [18.11111, 53.22222],
                "imageRefs": ["authority-only-secret-plate.png"],
            }
        )
        cell = plan["grid"]["cells"][0]
        cell.update(
            {
                "sensitivity": "restricted",
                "spatialRestriction": "authority-only",
                "geometry": {
                    "type": "Point",
                    "coordinates": [18.11111, 53.22222],
                },
            }
        )
        serialized = json.dumps(public_export(plan), sort_keys=True)
        self.assertNotIn("18.11111", serialized)
        self.assertNotIn("53.22222", serialized)
        self.assertNotIn("authority-only-secret-plate.png", serialized)
        self.assertIn("withheld-by-explicit-restriction", serialized)


if __name__ == "__main__":
    unittest.main()
