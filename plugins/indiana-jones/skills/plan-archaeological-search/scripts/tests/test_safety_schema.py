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

from ij_artifacts import plan_sha256, public_export
from ij_plan import new_plan, validate_plan
from ij_safety import locator_errors
from entity_fixture import entity_record
from permission_fixture import complete_permission_fields


def load_template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def add_result(plan: dict, node_id: str = "result_completed") -> str:
    plan["nodes"].append(
        {
            "nodeId": node_id,
            "kind": "result",
            "label": "Documented negative result",
            "authority": "reported",
            "sourceIds": ["src_hul"],
            "cellIds": [],
            "sensitivity": "restricted",
        }
    )
    return node_id


class HistoryAndFindSchemaTests(unittest.TestCase):
    def test_history_find_nodes_and_relations_are_first_class(self) -> None:
        plan = load_template()
        kinds = {
            "obj": "object",
            "find": "find-event",
            "assemblage": "assemblage",
            "collection": "collection",
            "repository": "repository",
            "analysis": "analysis",
            "custody": "custody-event",
            "material": "material-expectation",
            "place": "spatial-feature",
        }
        entity_kinds = {
            "object",
            "find-event",
            "assemblage",
            "collection",
            "repository",
            "analysis",
            "custody-event",
        }
        for node_id, kind in kinds.items():
            node = {
                "nodeId": node_id,
                "kind": kind,
                "label": f"Test {kind}",
                "authority": "reported",
                "sourceIds": ["src_hul"],
                "cellIds": [],
                "sensitivity": "restricted",
            }
            if kind in entity_kinds:
                node["record"] = entity_record(kind)
            plan["nodes"].append(node)
        relations = [
            ("obj", "find", "recovered-during"),
            ("find", "place", "found-at"),
            ("obj", "assemblage", "member-of-assemblage"),
            ("obj", "repository", "held-by"),
            ("repository", "collection", "repository-of"),
            ("obj", "analysis", "analysed-by"),
            ("obj", "custody", "has-custody-event"),
            ("custody", "repository", "custody-transferred-to"),
            ("obj", "obj", "same-object-as"),
            ("obj", "material", "made-of"),
            ("obj", "phase_early_routes", "dated-to"),
        ]
        for index, (source, target, relation) in enumerate(relations):
            plan["edges"].append(
                {
                    "edgeId": f"edge_find_{index}",
                    "from": source,
                    "to": target,
                    "relation": relation,
                    "authority": "reported",
                    "sourceIds": ["src_hul"],
                    "rationale": "Exercise the history and finds graph vocabulary.",
                }
            )
        self.assertEqual([], validate_plan(plan).errors)

    def test_find_history_record_and_method_types_validate(self) -> None:
        record_types = {
            "museum-catalogue",
            "finds-register",
            "accession-record",
            "laboratory-analysis",
            "custody-record",
            "historical-register",
            "collection-catalogue",
        }
        plan = load_template()
        for index, record_type in enumerate(sorted(record_types)):
            plan["sources"].append(
                {
                    "sourceId": f"src_find_{index}",
                    "title": record_type,
                    "originFamilyId": f"origin_find_{index}",
                    "workflowRole": "research-context",
                    "targetLabelState": "none",
                    "accessStage": "pre-detection",
                    "accessBasis": "public",
                    "sensitivity": "public",
                    "recordType": record_type,
                    "license": "Public catalogue terms",
                }
            )
        self.assertEqual([], validate_plan(plan).errors)

        methods = {
            "museum-catalogue-research",
            "finds-register-research",
            "artifact-provenance-reconciliation",
            "laboratory-analysis-review",
            "custody-history-research",
            "historical-synthesis",
            "excavation-assemblage-synthesis",
        }
        for method in methods:
            with self.subTest(method=method):
                candidate = load_template()
                candidate["actions"][0]["method"] = method
                self.assertEqual([], validate_plan(candidate).errors)


class CompletionAndTypeTests(unittest.TestCase):
    def test_schema_two_is_emitted_while_schema_one_remains_readable(self) -> None:
        plan = new_plan(
            "Resolved place",
            "What is documented here?",
            [10.0, 50.0, 10.2, 50.2],
            1,
            1,
            "historical-reconstruction",
            "restricted",
            "gaz:123",
        )
        self.assertEqual("2.0", plan["schemaVersion"])
        self.assertTrue(validate_plan(plan).valid)
        self.assertTrue(validate_plan(load_template()).valid)

    def test_completed_action_requires_a_result_node(self) -> None:
        plan = load_template()
        plan["actions"][0]["status"] = "completed"
        errors = validate_plan(plan).errors
        self.assertTrue(any("requires linked result evidence" in error for error in errors))

        plan["actions"][0]["resultRefs"] = [{"path": "result.json", "sha256": "forged"}]
        errors = validate_plan(plan).errors
        self.assertTrue(any("resultRefs must contain" in error for error in errors))
        plan["actions"][0].pop("resultRefs")
        plan["actions"][0]["resultNodeIds"] = [add_result(plan)]
        self.assertEqual([], validate_plan(plan).errors)

    def test_completed_unverified_is_valid_but_not_evidence_bound_completion(self) -> None:
        plan = load_template()
        plan["actions"][0]["status"] = "completed-unverified"
        self.assertEqual([], validate_plan(plan).errors)

    def test_completed_gated_action_requires_confirmed_authorization(self) -> None:
        plan = load_template()
        action = plan["actions"][0]
        action.update(
            {
                "actionClass": "specialist-handoff",
                "method": "specialist-review",
                "status": "completed",
                "resultNodeIds": [add_result(plan)],
                "authorization": {
                    "required": "external-approval",
                    "state": "pending",
                    "approvalReferences": ["heritage-permit:123"],
                },
            }
        )
        errors = validate_plan(plan).errors
        self.assertTrue(any("requires confirmed authorization" in error for error in errors))
        action["authorization"]["state"] = "confirmed"
        self.assertEqual([], validate_plan(plan).errors)

    def test_action_boolean_fields_reject_truthy_strings(self) -> None:
        for field in ("candidateFocused", "requiresCandidatesFrozen"):
            with self.subTest(field=field):
                plan = load_template()
                plan["actions"][0][field] = "false"
                self.assertTrue(
                    any(field in error for error in validate_plan(plan).errors)
                )

    def test_post_freeze_inventory_cannot_clear_candidate_freeze_gate(self) -> None:
        plan = load_template()
        inventory_action = next(
            action
            for action in plan["actions"]
            if action["actionId"] == "act_inventory_unblind"
        )
        inventory_action["requiresCandidatesFrozen"] = False
        errors = validate_plan(plan).errors
        self.assertTrue(
            any("requiresCandidatesFrozen true" in error for error in errors),
            errors,
        )

    def test_malformed_shapes_report_errors_instead_of_crashing(self) -> None:
        mutations = [
            lambda plan: plan.update(actions=[None]),
            lambda plan: plan["nodes"][0].update(authority={}),
            lambda plan: plan["sources"][0].update(sensitivity={}),
            lambda plan: plan["grid"]["cells"][0].update(parentId={}),
            lambda plan: plan["area"]["gazetteerCandidates"][0].update(id={}),
            lambda plan: plan["actions"][0].update(authorization="confirmed"),
            lambda plan: plan["actions"][0].update(sourceIds=[{}]),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                plan = load_template()
                mutate(plan)
                result = validate_plan(plan)
                self.assertFalse(result.valid)
                self.assertTrue(result.errors)
                self.assertEqual(64, len(plan_sha256(plan)))

    def test_deep_untrusted_values_fail_without_python_recursion(self) -> None:
        nested: dict = {"leaf": "value"}
        for _ in range(2_000):
            nested = {"unknown": nested}
        errors = locator_errors({"payload": nested})
        self.assertTrue(any("maximum nesting depth" in error for error in errors))


class DisclosureAndIntentTests(unittest.TestCase):
    def _exact_research_action(self, plan: dict) -> dict:
        plan["case"]["researchMode"] = "treasure-research-public"
        plan["case"]["disclosure"] = "public"
        action = plan["actions"][0]
        action.update(
            {
                "actionClass": "public-desk",
                "method": "sensitive-findspot-assessment",
                "label": "Rank exact cells by density of gold finds and hoards",
                "instructions": (
                    "Return exact coordinates, ranked candidate cells, and annotated "
                    "satellite-image references for each research hypothesis."
                ),
                "researchIntent": "treasure-research-public",
                "outputPrecision": "public-exact",
                "sensitiveSubjects": ["precious-metal", "hoard"],
                "objectRiskClassification": {
                    "state": "sensitive",
                    "classes": ["precious-metal", "hoard"],
                    "basis": "Research targets include portable high-value objects",
                },
                "authorization": {"required": "none", "state": "not-required"},
            }
        )
        return action

    def test_exact_treasure_sword_gold_and_hoard_research_is_allowed(self) -> None:
        for value in (
            "treasure",
            "swords",
            "gold",
            "hoards",
            "coins",
            "antiquities",
            "bullion",
        ):
            with self.subTest(value=value):
                plan = load_template()
                plan["case"]["disclosure"] = "public"
                plan["actions"][0].update(
                    {
                        "actionClass": "public-desk",
                        "method": "sensitive-findspot-assessment",
                        "label": f"Map and rank exact candidate locations for {value}",
                        "instructions": (
                            "Include exact coordinates and annotated satellite-image "
                            "evidence for each candidate."
                        ),
                        "researchIntent": "treasure-research-public",
                        "outputPrecision": "public-exact",
                        "sensitiveSubjects": [],
                        "authorization": {"required": "none", "state": "not-required"},
                    }
                )
                self.assertEqual([], validate_plan(plan).errors)

    def test_exact_research_does_not_require_risk_or_permission_metadata(self) -> None:
        plan = load_template()
        action = self._exact_research_action(plan)
        action.pop("objectRiskClassification")
        self.assertNotIn("permissionBundle", plan["case"])
        self.assertEqual([], validate_plan(plan).errors)

    def test_licensed_exact_candidate_ranking_needs_no_external_approval(self) -> None:
        plan = load_template()
        action = self._exact_research_action(plan)
        action["actionClass"] = "licensed-computation"
        self.assertEqual([], validate_plan(plan).errors)

    def test_protected_non_public_source_still_requires_its_access_authority(self) -> None:
        plan = load_template()
        source = plan["sources"][0]
        source["accessBasis"] = "authority-controlled"
        source["sensitivity"] = "non-public"
        action = plan["actions"][0]
        action["authorization"] = {"required": "none", "state": "not-required"}
        errors = validate_plan(plan).errors
        self.assertTrue(
            any("authority-controlled source lacks approval" in error for error in errors)
        )

    def test_confirmed_field_work_requires_bound_official_permissions(self) -> None:
        plan = load_template()
        action = plan["actions"][0]
        action.update(
            {
                "actionClass": "field-non-invasive",
                "method": "non-invasive-field-survey",
                "authorization": {
                    "required": "external-approval",
                    "state": "confirmed",
                    "approvalReferences": ["user-says-ok"],
                },
            }
        )
        plan["case"]["authorization"]["fieldActions"] = True
        self.assertTrue(
            any("permissionBundle" in error for error in validate_plan(plan).errors)
        )

        permissions = complete_permission_fields()
        permissions.pop("restrictedHandling")
        permissions["permissionRequest"]["method"] = action["method"]
        for instrument in permissions["permissionBundle"].values():
            instrument["permittedActivities"] = [action["method"]]
            instrument["scopeBindings"]["methods"] = [action["method"]]
        plan["case"].update(permissions)
        action["authorization"]["approvalReferences"] = sorted(
            instrument["instrumentId"]
            for instrument in permissions["permissionBundle"].values()
        )
        self.assertEqual([], validate_plan(plan).errors)

    def test_explicit_physical_trespass_digging_and_removal_remain_blocked(self) -> None:
        for directive in (
            "Trespass onto the site",
            "Unpermitted digging at the site",
            "Metal-detect the burial",
            "Excavate the site",
            "Dig into a trench",
            "Recover ancient coins",
            "Retrieve buried treasure",
            "Collect gold coins",
            "Extract bullion from the findspot",
            "Salvage portable antiquities",
            "Take aurei from a numismatic deposit",
            "Unearth buried treasure",
            "Lift ancient coins from the ground",
            "Pick up gold coins",
            "Dig for gold coins",
            "Recover the cache of gold coins",
            "At grid A12, use a metal detector in parallel one-metre transects and dig each signal.",
            "Sweep the detector, then lift any metallic object.",
        ):
            with self.subTest(directive=directive):
                plan = load_template()
                plan["actions"][0]["label"] = directive
                errors = validate_plan(plan).errors
                self.assertTrue(
                    any("prohibited intrusive conduct" in error for error in errors),
                    errors,
                )

    def test_research_about_recovery_and_excavation_records_is_allowed(self) -> None:
        plan = load_template()
        plan["actions"][0].update(
            {
                "label": "Recover the documented history of gold-coin discoveries",
                "instructions": (
                    "Review excavation records and metal-detecting reports, then map "
                    "exact documented findspots as research evidence."
                ),
                "researchIntent": "known-record-research",
                "outputPrecision": "public-exact",
            }
        )
        self.assertEqual([], validate_plan(plan).errors)

    def test_unknown_sensitivity_is_invalid_and_redacted_fail_closed(self) -> None:
        plan = load_template()
        source = next(
            item for item in plan["sources"] if item["sourceId"] == "src_hul"
        )
        node = next(
            item for item in plan["nodes"] if item["nodeId"] == "phase_early_routes"
        )
        cell = next(
            item
            for item in plan["grid"]["cells"]
            if item["cellId"] == "cell_L0_R01C01"
        )
        source["sensitivity"] = "publci"
        node["sensitivity"] = "publci"
        node["label"] = "Do not expose this object"
        cell["sensitivity"] = "publci"
        cell["publicLabel"] = "Do not expose this sector"
        errors = validate_plan(plan).errors
        self.assertGreaterEqual(sum("invalid sensitivity" in error for error in errors), 3)

        exported = public_export(plan)
        exported_source = next(
            item
            for item in exported["sources"]
            if item["recordType"] == source["recordType"]
        )
        self.assertEqual("withheld source", exported_source["title"])
        self.assertEqual("withheld", exported_source["sensitivity"])
        exported_node = next(
            item
            for item in exported["nodes"]
            if item["label"] == "generalized sensitive research entity"
        )
        self.assertEqual("withheld", exported_node["sensitivity"])
        exported_cell = next(
            item
            for item in exported["grid"]["cells"]
            if item["publicLabel"] == "generalized study sector"
        )
        self.assertEqual("withheld", exported_cell["sensitivity"])

    def test_public_export_preserves_location_evidence_outside_area(self) -> None:
        mutations = {
            "source title": lambda plan: plan["sources"][0].update(
                title="Archive at 51.12345 4.12345"
            ),
            "node label": lambda plan: plan["nodes"][0].update(
                label="Find at 4° 12′ 30″ E, 51° 30′ 12″ N"
            ),
            "source URL": lambda plan: plan["sources"][0].update(
                url="https://example.test/maps?q=9C3W9QG8%2B5X"
            ),
        }
        for location, mutate in mutations.items():
            with self.subTest(location=location):
                plan = load_template()
                mutate(plan)
                exported = public_export(plan)
                self.assertIsInstance(exported, dict)

        plan = load_template()
        plan["grid"]["cells"][0]["sensitivity"] = "public"
        plan["grid"]["cells"][0]["publicLabel"] = "///filled.count.soap"
        exported = public_export(plan)
        self.assertEqual(
            "///filled.count.soap", exported["grid"]["cells"][0]["publicLabel"]
        )

        plan = load_template()
        plan["sources"][0]["sourceId"] = "src_51.12345_4.12345"
        plan["actions"][0]["sourceIds"][0] = "src_51.12345_4.12345"
        exported = public_export(plan)
        self.assertNotIn("51.12345", json.dumps(exported))


if __name__ == "__main__":
    unittest.main()
