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
from ij_calibration import evaluate_held_out_benchmark
from ij_material_classification import classify_reported_material
from ij_materials import build_material_evidence_report
from ij_probability import (
    calibrated_probability_report,
    heuristic_candidate_report,
    probability_gate_errors,
)
from ij_reports import build_finds_report, lint_public_report
from entity_fixture import entity_record
from permission_fixture import calibration_fixture


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
                    "record": entity_record("object"),
                },
                {
                    "nodeId": "repo_museum",
                    "kind": "repository",
                    "label": "Museum repository",
                    "authority": "reported",
                    "sourceIds": ["src_heritage_inventory"],
                    "cellIds": [],
                    "sensitivity": "public",
                    "record": entity_record("repository"),
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
                "materialAssessment": classify_reported_material("gold"),
            }
        ]
        report = build_material_evidence_report(records, "gold")
        self.assertEqual("material-presence-only", report["conclusion"])
        self.assertEqual("supported", report["conclusions"]["presence"]["status"])
        self.assertEqual(
            "not-demonstrated",
            report["conclusions"]["circulation"]["status"],
        )

    def test_secure_crucible_can_support_qualified_production(self) -> None:
        records = [
            {
                "recordId": "crucible-1",
                "sourceId": "excavation",
                "title": "Crucible with gold residue",
                "objectClass": "production debris",
                "material": "ceramic and gold",
                "materialAssessment": classify_reported_material("ceramic and gold"),
                "archaeologicalContext": "sealed workshop floor",
            }
        ]
        report = build_material_evidence_report(records, "gold")
        self.assertIn("production-supported", report["conclusion"])
        self.assertEqual(
            "supported-pending-specialist-review",
            report["conclusions"]["production"]["status"],
        )

    def test_descriptive_or_ambiguous_gold_does_not_support_presence(self) -> None:
        records = [
            {
                "recordId": "colour",
                "sourceId": "museum",
                "title": "Gold-coloured brooch",
                "material": "gold-coloured metal",
                "materialAssessment": classify_reported_material(
                    "gold-coloured metal"
                ),
            },
            {
                "recordId": "gilded",
                "sourceId": "museum",
                "title": "Gilded fitting",
                "material": "gilded copper alloy",
                "materialAssessment": classify_reported_material(
                    "gilded copper alloy"
                ),
            },
            {
                "recordId": "gold-tone",
                "sourceId": "museum",
                "title": "Gold-tone fitting",
                "material": "gold-tone base metal",
                "materialAssessment": classify_reported_material(
                    "gold-tone base metal"
                ),
            },
            {
                "recordId": "ambiguous",
                "sourceId": "museum",
                "title": "Uncertain ornament",
                "material": "possibly gold",
                "materialAssessment": classify_reported_material("possibly gold"),
            },
        ]
        report = build_material_evidence_report(records, "gold")
        self.assertEqual(
            "material-description-does-not-establish-material-presence",
            report["conclusion"],
        )
        self.assertEqual("not-supported", report["conclusions"]["presence"]["status"])
        self.assertTrue(
            all(
                not item["materialPresenceSupported"]
                for item in report["evidenceMatrix"]
            )
        )

    def test_record_material_assessment_overrides_optimistic_raw_text(self) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "ambiguous-assessment",
                    "sourceId": "museum",
                    "title": "Gold object?",
                    "material": "gold",
                    "materialAssessment": {
                        "reportedMaterial": "gold",
                        "materialClass": "ambiguous-material",
                        "basis": "catalogue-curator-note",
                        "certainty": "ambiguous",
                        "supportsPreciousMaterial": False,
                    },
                }
            ],
            "gold",
        )
        self.assertEqual("not-supported", report["conclusions"]["presence"]["status"])

    def test_missing_normalized_material_assessment_fails_closed(self) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "raw-gold-label",
                    "sourceId": "museum",
                    "title": "Gold object",
                    "material": "gold",
                }
            ],
            "gold",
        )
        self.assertEqual("not-supported", report["conclusions"]["presence"]["status"])
        self.assertEqual(
            "missing-normalized-material-assessment",
            report["evidenceMatrix"][0]["materialAssessment"]["basis"],
        )

    def test_contextless_crucible_does_not_support_local_working(self) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "loose-crucible",
                    "sourceId": "legacy-collection",
                    "title": "Crucible with gold residue",
                    "objectClass": "crucible",
                    "material": "ceramic and gold",
                    "materialAssessment": classify_reported_material(
                        "ceramic and gold"
                    ),
                }
            ],
            "gold",
        )
        self.assertEqual("not-demonstrated", report["conclusions"]["working"]["status"])
        self.assertEqual(
            "not-demonstrated",
            report["conclusions"]["production"]["status"],
        )

    def test_word_fragments_and_negated_context_do_not_create_working_claims(
        self,
    ) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "hammered-pendant",
                    "sourceId": "museum",
                    "title": "Hammered gold pendant",
                    "objectClass": "finished ornament",
                    "material": "gold",
                    "materialAssessment": classify_reported_material("gold"),
                    "archaeologicalContext": "unsealed and not in situ",
                }
            ],
            "gold",
        )
        evidence = report["evidenceMatrix"][0]
        self.assertEqual("finished-object-or-raw-material", evidence["evidenceClass"])
        self.assertFalse(evidence["secureContext"])
        self.assertEqual("not-demonstrated", report["conclusions"]["working"]["status"])

    def test_production_word_in_finished_object_title_is_not_a_proxy(self) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "crucible-pendant",
                    "sourceId": "museum",
                    "title": "Crucible-shaped gold pendant",
                    "objectClass": "finished ornament",
                    "material": "gold",
                    "materialAssessment": classify_reported_material("gold"),
                    "archaeologicalContext": "sealed stratified deposit",
                }
            ],
            "gold",
        )
        evidence = report["evidenceMatrix"][0]
        self.assertEqual("finished-object-or-raw-material", evidence["evidenceClass"])
        self.assertFalse(evidence["workingSupported"])

    def test_unresolved_production_link_fails_closed(self) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "linked-pendant",
                    "sourceId": "excavation",
                    "title": "Gold pendant",
                    "objectClass": "finished ornament",
                    "material": "gold",
                    "materialAssessment": classify_reported_material("gold"),
                    "archaeologicalContext": "sealed stratified deposit",
                    "productionEvidenceLinks": [
                        {
                            "kind": "production-debris",
                            "recordId": "missing-crucible",
                            "contextLink": "same-context",
                        }
                    ],
                }
            ],
            "gold",
        )
        evidence = report["evidenceMatrix"][0]
        self.assertEqual([], evidence["linkedProductionEvidence"])
        self.assertFalse(evidence["workingSupported"])
        self.assertFalse(evidence["productionSupported"])

    def test_xrf_pendant_only_supports_presence_and_circulation(self) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "xrf-pendant",
                    "sourceId": "excavation",
                    "title": "XRF-tested pendant",
                    "objectClass": "finished ornament",
                    "material": "gold",
                    "materialAssessment": classify_reported_material("gold"),
                    "archaeologicalContext": "sealed stratified deposit",
                    "laboratoryAssessment": {
                        "validated": True,
                        "method": "portable XRF",
                        "substance": "gold",
                        "result": "gold alloy detected",
                        "validator": "Accredited laboratory",
                        "reportId": "LAB-XRF-001",
                    },
                }
            ],
            "gold",
        )
        self.assertEqual("supported", report["conclusions"]["presence"]["status"])
        self.assertEqual("supported", report["conclusions"]["circulation"]["status"])
        self.assertEqual("not-demonstrated", report["conclusions"]["working"]["status"])
        self.assertEqual(
            "not-demonstrated",
            report["conclusions"]["production"]["status"],
        )

    def test_validated_residue_on_secure_tool_supports_working_not_production(
        self,
    ) -> None:
        report = build_material_evidence_report(
            [
                {
                    "recordId": "secure-hammer",
                    "sourceId": "excavation",
                    "title": "Goldsmith hammer with analysed residue",
                    "objectClass": "hammer",
                    "material": "iron with unidentified residue",
                    "materialAssessment": classify_reported_material(
                        "iron with unidentified residue"
                    ),
                    "archaeologicalContext": "in situ on a sealed floor",
                    "laboratoryAssessment": {
                        "validated": True,
                        "method": "SEM-EDS",
                        "substance": "gold",
                        "result": "gold-bearing residue on the working face",
                        "validator": "Accredited laboratory",
                        "reportId": "LAB-SEM-EDS-001",
                    },
                }
            ],
            "gold",
        )
        self.assertEqual("supported", report["conclusions"]["presence"]["status"])
        self.assertEqual("supported", report["conclusions"]["working"]["status"])
        self.assertEqual(
            "not-demonstrated",
            report["conclusions"]["production"]["status"],
        )

    def test_numeric_probability_is_blocked_without_calibration(self) -> None:
        calibration = calibration_fixture()
        del calibration["heldOutEvaluation"]
        with self.assertRaisesRegex(ValueError, "probability gate failed"):
            calibrated_probability_report(calibration)

    def test_frozen_hashes_datasets_bins_and_interval_are_mandatory(self) -> None:
        mutations = {
            "modelSha256": lambda value: value.pop("modelSha256"),
            "datasetReferences": lambda value: value.pop("datasetReferences"),
            "reliability-bin counts": lambda value: value["heldOutMetrics"][
                "reliabilityBins"
            ][0].update(count=1),
            "uncertaintyInterval": lambda value: value.update(
                estimatedProbability=0.9
            ),
        }
        for expected, mutate in mutations.items():
            with self.subTest(expected=expected):
                calibration = calibration_fixture()
                mutate(calibration)
                errors = probability_gate_errors(calibration)
                self.assertTrue(any(expected in error for error in errors), errors)
                with self.assertRaisesRegex(ValueError, "probability gate failed"):
                    calibrated_probability_report(calibration)

    def test_exact_gold_hoard_probability_can_be_public_research(self) -> None:
        calibration = calibration_fixture()
        calibration["eventDefinition"] = "A gold hoard in the exact target grid cell"
        benchmark = calibration["heldOutEvaluation"]["benchmark"]
        benchmark["eventDefinition"] = calibration["eventDefinition"]
        evaluation = evaluate_held_out_benchmark(
            benchmark,
            frozen_inputs=calibration["heldOutEvaluation"]["frozenInputs"],
        )
        calibration["heldOutEvaluation"] = evaluation
        calibration["heldOutMetrics"] = evaluation["heldOutMetrics"]
        calibration["datasetReferences"][-1] = evaluation["datasetReference"]
        case = {
            "researchMode": "treasure-research-public",
            "disclosure": "public",
        }
        self.assertEqual(
            [],
            probability_gate_errors(
                calibration,
                case=case,
                exact_high_risk_target=True,
            ),
        )
        report = calibrated_probability_report(
            calibration,
            case=case,
            exact_high_risk_target=True,
        )
        self.assertEqual("public", report["disclosure"])
        self.assertEqual("exact", report["targetPrecision"])
        self.assertEqual(0.31, report["estimatedProbability"])

    def test_probability_api_rejects_unknown_case_enums(self) -> None:
        for case, expected in (
            ({"disclosure": "publci"}, "case.disclosure is invalid"),
            (
                {"disclosure": "public", "researchMode": "treasur-ish"},
                "case.researchMode is invalid",
            ),
        ):
            with self.subTest(case=case):
                errors = probability_gate_errors(calibration_fixture(), case=case)
                self.assertIn(expected, errors)
                with self.assertRaisesRegex(ValueError, "probability gate failed"):
                    calibrated_probability_report(calibration_fixture(), case=case)

    def test_exact_treasure_probability_needs_no_permission_bundle(self) -> None:
        report = calibrated_probability_report(
            calibration_fixture(),
            case={
                "researchMode": "treasure-research-public",
                "disclosure": "public",
            },
            exact_high_risk_target=True,
        )
        self.assertEqual("public", report["disclosure"])
        self.assertNotIn("permissionBundle", report)

    def test_exact_heuristic_candidate_ranking_preserves_coordinates(self) -> None:
        report = heuristic_candidate_report(
            [
                {
                    "candidateId": "candidate-b",
                    "score": 4.2,
                    "hypothesis": "Sword-loss concentration near the former crossing",
                    "coordinates": [19.12345, 54.12345],
                    "imageryAnnotationRef": "plate-2:polygon-b",
                    "evidenceReferences": ["src:satellite:2026", "src:finds:7"],
                },
                {
                    "candidateId": "candidate-a",
                    "score": 8.4,
                    "hypothesis": "Hoard-deposition candidate at a boundary intersection",
                    "coordinates": [19.54321, 54.54321],
                    "imageryAnnotationRef": "plate-1:circle-a",
                    "evidenceReferences": ["src:satellite:2026", "src:map:1840"],
                },
            ],
            method="Weighted imagery, terrain, and documented-find agreement",
            score_meaning="Higher means more independent research signals agree",
            evidence_references=["src:satellite:2026", "src:map:1840", "src:finds:7"],
            limitations=["No representative held-out calibration set is available"],
            case={
                "researchMode": "treasure-research-public",
                "disclosure": "public",
            },
        )
        self.assertEqual(
            ["candidate-a", "candidate-b"],
            [candidate["candidateId"] for candidate in report["candidates"]],
        )
        self.assertEqual(
            [19.54321, 54.54321],
            report["candidates"][0]["coordinates"],
        )
        self.assertEqual(
            (
                "https://www.google.com/maps/search/?api=1&"
                "query=54.543210%2C19.543210"
            ),
            report["candidates"][0]["googleMapsLink"],
        )
        self.assertEqual("plate-1:circle-a", report["candidates"][0]["imageryAnnotationRef"])
        self.assertIn("not-probability", report["assessmentType"])

    def test_heuristic_report_withholds_only_explicitly_restricted_candidate(self) -> None:
        report = heuristic_candidate_report(
            [
                {
                    "candidateId": "ordinary",
                    "score": 2.0,
                    "hypothesis": "Public comparison point",
                    "coordinates": [19.54321, 54.54321],
                    "imageryAnnotationRef": "plate-public:a",
                    "evidenceReferences": ["src:public"],
                },
                {
                    "candidateId": "protected",
                    "score": 3.0,
                    "hypothesis": "Authority-controlled comparison point",
                    "coordinates": [18.11111, 53.22222],
                    "imageryAnnotationRef": "plate-private:b",
                    "spatialRestriction": "authority-only",
                    "evidenceReferences": ["src:authority"],
                },
            ],
            method="Evidence agreement",
            score_meaning="Higher means more signals agree",
            evidence_references=["src:public", "src:authority"],
            limitations=["Candidate sensitivities differ"],
            case={"disclosure": "public"},
        )
        protected, ordinary = report["candidates"]
        self.assertEqual("protected", protected["candidateId"])
        self.assertNotIn("coordinates", protected)
        self.assertNotIn("imageryAnnotationRef", protected)
        self.assertEqual(
            "withheld-by-explicit-restriction",
            protected["spatialEvidenceStatus"],
        )
        self.assertEqual([19.54321, 54.54321], ordinary["coordinates"])


class PublicReportTests(unittest.TestCase):
    def test_public_finds_report_preserves_exact_findspot(self) -> None:
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
                            "sensitivity": "public",
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
        self.assertIn("Exact field", serialized)
        self.assertIn("19.12345", serialized)
        self.assertIn('"findspot":', serialized)
        self.assertEqual(
            (
                "https://www.google.com/maps/search/?api=1&"
                "query=54.123450%2C19.123450"
            ),
            report["finds"][0]["record"]["findspot"]["googleMapsLink"],
        )
        self.assertIn("points and AOIs retained", report["locationPolicy"])

    def test_public_finds_report_honors_explicit_spatial_restriction(self) -> None:
        reconciliation = {
            "entities": [
                {
                    "entityId": "find_1",
                    "canonicalRecord": {
                        "recordId": "authority:A-1",
                        "sourceId": "authority",
                        "title": "Restricted record",
                        "findspot": {"coordinates": [19.12345, 54.12345]},
                        "spatialRestriction": "authority-only",
                    },
                    "recordIds": ["authority:A-1"],
                    "sourceIds": ["authority"],
                    "duplicateCount": 1,
                    "independentSourceCount": 1,
                }
            ]
        }
        report = build_finds_report(
            reconciliation,
            area_description="Study area",
            public=True,
        )
        record = report["finds"][0]["record"]
        self.assertNotIn("findspot", record)
        self.assertEqual(
            "withheld-by-explicit-restriction",
            record["spatialEvidenceStatus"],
        )

    def test_public_finds_report_preserves_unrestricted_spatial_evidence(self) -> None:
        for sensitivity in (None, "unknown"):
            with self.subTest(sensitivity=sensitivity):
                findspot = {"coordinates": [19.12345, 54.12345]}
                if sensitivity is not None:
                    findspot["sensitivity"] = sensitivity
                reconciliation = {
                    "entities": [
                        {
                            "entityId": "find_unclassified",
                            "canonicalRecord": {
                                "recordId": "catalogue:A-1",
                                "sourceId": "catalogue",
                                "title": "Unclassified spatial record",
                                "findspot": findspot,
                            },
                            "recordIds": ["catalogue:A-1"],
                            "sourceIds": ["catalogue"],
                            "duplicateCount": 1,
                            "independentSourceCount": 1,
                        }
                    ]
                }
                report = build_finds_report(
                    reconciliation,
                    area_description="Study area",
                    public=True,
                )
                record = report["finds"][0]["record"]
                self.assertEqual(
                    [19.12345, 54.12345],
                    record["findspot"]["coordinates"],
                )
                self.assertIn("google.com/maps", record["findspot"]["googleMapsLink"])
                self.assertNotIn("spatialEvidenceStatus", record)

    def test_public_lint_preserves_declared_spatial_evidence(self) -> None:
        lint_public_report({"nested": {"coordinates": [19.12345, 54.12345]}})
        lint_public_report({"note": "Inspect 19.12345, 54.12345"})
        for text in (
            "Inspect 51.123456 4.123456",
            "51° 30′ 12″ N, 4° 12′ 30″ E",
            "4° 12′ 30″ E, 51° 30′ 12″ N",
            "51.123456 N, 4.123456 E",
            "4.123456 E, 51.123456 N",
            "N 54.12345 E 19.12345",
            "54.12345° N, 19.12345° E",
            "UTM zone 31U 448251 5411932",
            "31U DQ 48251 11932",
            "grid reference TQ 12345 67890",
            "EPSG:27700 530000 180000",
            "9C3W9QG8+5X",
            "///filled.count.soap",
            "filled.count.soap",
            "wypełniony.liczenie.mydło",
            "https://example.test/map?lat=51.12345&lon=4.12345",
            "https://example.test/map?q=9C3W9QG8%2B5X",
            "https://example.test/lat/54.12345/lon/19.12345",
            "https://w3w.co/filled.count.soap",
        ):
            with self.subTest(text=text):
                lint_public_report({"note": text})
        lint_public_report({"position": {"x": 19.12345, "y": 54.12345}})
        lint_public_report({"parts": ["54.12345", "19.12345"]})

    def test_public_lint_rejects_excessive_depth_without_recursion_error(self) -> None:
        value: dict = {"note": "generalized"}
        for _ in range(2_000):
            value = {"nested": value}
        with self.assertRaisesRegex(ValueError, "maximum nesting depth"):
            lint_public_report(value)


if __name__ == "__main__":
    unittest.main()
