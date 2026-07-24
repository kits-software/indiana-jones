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
        for node_id, kind in kinds.items():
            plan["nodes"].append(
                {
                    "nodeId": node_id,
                    "kind": kind,
                    "label": f"Test {kind}",
                    "authority": "reported",
                    "sourceIds": ["src_hul"],
                    "cellIds": [],
                    "sensitivity": "restricted",
                }
            )
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


class DisclosureAndIntentTests(unittest.TestCase):
    def _sensitive_action(self, plan: dict) -> dict:
        plan["case"]["researchMode"] = "treasure-research-restricted"
        plan["case"]["permissionBundle"] = {
            key: {
                "state": "confirmed",
                "basis": "test authority record",
                "scope": "declared research area and method",
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
        action = plan["actions"][0]
        action.update(
            {
                "actionClass": "specialist-handoff",
                "method": "sensitive-findspot-assessment",
                "label": "Rank exact cells by density of gold finds and hoards",
                "researchIntent": "known-record-research",
                "outputPrecision": "restricted-exact",
                "sensitiveSubjects": ["precious-metal", "hoard"],
                "authorization": {
                    "required": "external-approval",
                    "state": "confirmed",
                    "approvalReferences": ["heritage-authority:case-123"],
                },
            }
        )
        return action

    def test_generalized_public_catalogue_research_is_allowed(self) -> None:
        plan = load_template()
        plan["case"]["disclosure"] = "public"
        plan["actions"][0].update(
            {
                "actionClass": "public-desk",
                "method": "museum-catalogue-research",
                "label": "Catalogue documented sword finds using generalized regional counts",
                "researchIntent": "known-record-research",
                "outputPrecision": "generalized",
                "sensitiveSubjects": ["weapon"],
                "authorization": {"required": "none", "state": "not-required"},
            }
        )
        self.assertEqual([], validate_plan(plan).errors)

    def test_public_exact_sensitive_targeting_is_blocked(self) -> None:
        plan = load_template()
        plan["case"]["disclosure"] = "public"
        self._sensitive_action(plan)
        plan["actions"][0]["outputPrecision"] = "public-exact"
        errors = validate_plan(plan).errors
        self.assertTrue(any("exact sensitive findspot" in error for error in errors))

    def test_restricted_exact_work_requires_and_accepts_heritage_authority(self) -> None:
        plan = load_template()
        action = self._sensitive_action(plan)
        self.assertEqual([], validate_plan(plan).errors)

        action["authorization"]["state"] = "pending"
        errors = validate_plan(plan).errors
        self.assertTrue(any("exact sensitive findspot" in error for error in errors))

        action["authorization"]["state"] = "confirmed"
        del plan["case"]["permissionBundle"]["heritage"]
        errors = validate_plan(plan).errors
        self.assertTrue(any("permissionBundle.heritage" in error for error in errors))

    def test_unpermitted_recovery_conduct_remains_blocked(self) -> None:
        plan = load_template()
        plan["actions"][0]["label"] = "Recover gold and swords from the field"
        errors = validate_plan(plan).errors
        self.assertTrue(any("prohibited intrusive conduct" in error for error in errors))

    def test_unknown_sensitivity_is_invalid_and_redacted_fail_closed(self) -> None:
        plan = load_template()
        source = plan["sources"][0]
        node = plan["nodes"][0]
        cell = plan["grid"]["cells"][0]
        source["sensitivity"] = "publci"
        node["sensitivity"] = "publci"
        node["label"] = "Do not expose this object"
        cell["sensitivity"] = "publci"
        cell["publicLabel"] = "Do not expose this sector"
        errors = validate_plan(plan).errors
        self.assertGreaterEqual(sum("invalid sensitivity" in error for error in errors), 3)

        exported = public_export(plan)
        self.assertEqual("withheld source", exported["sources"][0]["title"])
        self.assertEqual(
            "generalized sensitive research entity", exported["nodes"][0]["label"]
        )
        self.assertEqual(
            "generalized study sector", exported["grid"]["cells"][0]["publicLabel"]
        )


if __name__ == "__main__":
    unittest.main()
