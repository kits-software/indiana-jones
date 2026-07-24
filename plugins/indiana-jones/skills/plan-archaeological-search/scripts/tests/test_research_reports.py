from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_history import build_history_report, build_object_biography
from ij_materials import build_material_evidence_report
from ij_probability import calibrated_probability_report, probability_gate_errors
from ij_reports import build_finds_report, lint_public_report


def calibration_fixture() -> dict:
    return {
        "eventDefinition": "A documented find in a declared survey unit",
        "denominator": "100 independently surveyed units",
        "detectionProcess": "Frozen systematic survey protocol",
        "reportingProcess": "Mandatory reporting with audited follow-up",
        "biasTreatment": "Inverse reporting weights and missingness sensitivity",
        "validityDomain": "Comparable arable survey units in the study region",
        "sample": {"positive": 20, "negative": 80, "heldOut": 20},
        "geographicallySeparated": True,
        "modelFrozen": True,
        "featuresFrozen": True,
        "heldOutMetrics": {
            "brierScore": 0.14,
            "reliabilityBins": [
                {"predicted": 0.1, "observed": 0.08},
                {"predicted": 0.3, "observed": 0.25},
                {"predicted": 0.6, "observed": 0.55},
            ],
        },
        "estimatedProbability": 0.31,
        "uncertaintyInterval": [0.2, 0.44],
    }


class HistoryTests(unittest.TestCase):
    def test_history_report_is_not_labelled_stratigraphy(self) -> None:
        plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        report = build_history_report(plan)
        self.assertIn("not a Harris", report["sequenceAuthority"])
        self.assertTrue(report["timeSlices"])
        self.assertGreaterEqual(report["sourceCoverage"]["historySourceCount"], 1)

    def test_object_biography_separates_provenance_authorities(self) -> None:
        plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        plan["nodes"].extend(
            [
                {
                    "nodeId": "obj_sword",
                    "kind": "object",
                    "label": "Catalogued sword",
                    "authority": "reported",
                    "sourceIds": ["src_heritage_inventory"],
                    "cellIds": [],
                    "sensitivity": "restricted",
                },
                {
                    "nodeId": "repo_museum",
                    "kind": "repository",
                    "label": "Museum repository",
                    "authority": "reported",
                    "sourceIds": ["src_heritage_inventory"],
                    "cellIds": [],
                    "sensitivity": "public",
                },
            ]
        )
        plan["edges"].append(
            {
                "edgeId": "edge_sword_repository",
                "from": "obj_sword",
                "to": "repo_museum",
                "relation": "held-by",
                "authority": "reported",
                "sourceIds": ["src_heritage_inventory"],
                "rationale": "Catalogue repository assertion.",
            }
        )
        biography = build_object_biography(plan, "obj_sword")
        self.assertEqual("obj_sword", biography["object"]["nodeId"])
        self.assertEqual("held-by", biography["relationships"][0]["relation"])
        self.assertIn("provenience", biography["provenanceWarning"])
        self.assertIn("custody", biography["provenanceWarning"])


class MaterialAndProbabilityTests(unittest.TestCase):
    def test_finished_gold_object_yields_presence_only(self) -> None:
        records = [
            {
                "recordId": "gold-1",
                "sourceId": "museum",
                "title": "Gold pendant",
                "objectClass": "ornament",
                "material": "gold",
            }
        ]
        report = build_material_evidence_report(records, "gold")
        self.assertEqual("material-presence-only", report["conclusion"])

    def test_secure_crucible_can_support_qualified_production(self) -> None:
        records = [
            {
                "recordId": "crucible-1",
                "sourceId": "excavation",
                "title": "Crucible with gold residue",
                "objectClass": "production debris",
                "material": "ceramic and gold",
                "archaeologicalContext": "sealed workshop floor",
            }
        ]
        report = build_material_evidence_report(records, "gold")
        self.assertIn("production-supported", report["conclusion"])

    def test_numeric_probability_is_blocked_without_calibration(self) -> None:
        calibration = calibration_fixture()
        del calibration["heldOutMetrics"]
        with self.assertRaisesRegex(ValueError, "probability gate failed"):
            calibrated_probability_report(calibration)

    def test_exact_treasure_probability_requires_permission_bundle(self) -> None:
        calibration = calibration_fixture()
        errors = probability_gate_errors(
            calibration,
            case={
                "researchMode": "treasure-research-restricted",
                "disclosure": "restricted",
            },
            exact_high_risk_target=True,
        )
        self.assertTrue(any("permission bundle" in error for error in errors))

    def test_permission_complete_restricted_probability_remains_restricted(self) -> None:
        permissions = {
            key: {
                "state": "confirmed",
                "basis": "fixture approval",
                "scope": "declared test area and method",
            }
            for key in (
                "jurisdiction",
                "landAccess",
                "detecting",
                "excavation",
                "heritage",
                "findsReporting",
                "communityAuthority",
            )
        }
        report = calibrated_probability_report(
            calibration_fixture(),
            case={
                "researchMode": "treasure-research-restricted",
                "disclosure": "restricted",
                "permissionBundle": permissions,
            },
            exact_high_risk_target=True,
        )
        self.assertEqual("restricted", report["disclosure"])
        self.assertEqual(0.31, report["estimatedProbability"])


class PublicReportTests(unittest.TestCase):
    def test_public_finds_report_omits_exact_findspot(self) -> None:
        reconciliation = {
            "entities": [
                {
                    "entityId": "find_1",
                    "identityBasis": "accession",
                    "canonicalRecord": {
                        "recordId": "museum:A-1",
                        "sourceId": "museum",
                        "title": "Gold sword fitting",
                        "objectClass": "weapon fitting",
                        "material": "gold",
                        "findspot": {
                            "description": "Exact field",
                            "coordinates": [19.12345, 54.12345],
                        },
                        "riskClasses": ["portable-high-value", "weapon"],
                    },
                    "recordIds": ["museum:A-1"],
                    "sourceIds": ["museum"],
                    "duplicateCount": 1,
                    "independentSourceCount": 1,
                    "reconciliationStatus": "strong-identifier-match",
                }
            ]
        }
        report = build_finds_report(
            reconciliation,
            area_description="Generalized district",
            public=True,
        )
        serialized = json.dumps(report)
        self.assertNotIn("Exact field", serialized)
        self.assertNotIn("19.12345", serialized)
        self.assertNotIn('"findspot":', serialized)

    def test_public_lint_rejects_nested_coordinates_and_coordinate_prose(self) -> None:
        with self.assertRaisesRegex(ValueError, "restricted key"):
            lint_public_report({"nested": {"coordinates": [19.12345, 54.12345]}})
        with self.assertRaisesRegex(ValueError, "coordinate-like prose"):
            lint_public_report({"note": "Inspect 19.12345, 54.12345"})


if __name__ == "__main__":
    unittest.main()
