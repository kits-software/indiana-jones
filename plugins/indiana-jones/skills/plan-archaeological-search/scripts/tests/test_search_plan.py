from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
EVENT_TEMPLATE = SKILL_DIR / "assets" / "event-search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_artifacts import canonical_plan, plan_sha256, public_export
from ij_frontier import build_frontier
from ij_plan import new_plan, validate_plan
from ij_readiness import readiness_errors
from entity_fixture import entity_record


def load_template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


class PlanValidationTests(unittest.TestCase):
    def test_authored_skill_files_stay_below_700_lines(self) -> None:
        authored = [
            path
            for path in SKILL_DIR.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix in {".md", ".py", ".json", ".yaml"}
        ]
        oversized = [
            f"{path.relative_to(SKILL_DIR)}:{len(path.read_text(encoding='utf-8').splitlines())}"
            for path in authored
            if len(path.read_text(encoding="utf-8").splitlines()) >= 700
        ]
        self.assertEqual([], oversized)

    def test_template_is_valid(self) -> None:
        result = validate_plan(load_template())
        self.assertEqual([], result.errors)
        self.assertEqual([], readiness_errors(load_template()))

    def test_event_template_is_valid_and_ready(self) -> None:
        plan = json.loads(EVENT_TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual([], validate_plan(plan).errors)
        self.assertEqual([], readiness_errors(plan))

    def test_new_plan_is_valid(self) -> None:
        plan = new_plan(
            "Resolved place",
            "Which non-invasive task should run first?",
            [10.0, 50.0, 10.2, 50.2],
            2,
            2,
            "prospective-survey",
            "restricted",
            "gaz:123",
        )
        self.assertTrue(validate_plan(plan).valid)

    def test_hash_ignores_top_level_array_order(self) -> None:
        plan = load_template()
        shuffled = copy.deepcopy(plan)
        for key in ("sources", "nodes", "edges", "actions"):
            shuffled[key].reverse()
        shuffled["grid"]["cells"].reverse()
        self.assertEqual(plan_sha256(plan), plan_sha256(shuffled))
        self.assertEqual(canonical_plan(plan), canonical_plan(shuffled))

    def test_ambiguous_unselected_place_is_rejected(self) -> None:
        plan = load_template()
        plan["area"]["gazetteerCandidates"].append(
            {"id": "example:other", "label": "Other town", "selected": True}
        )
        result = validate_plan(plan)
        self.assertTrue(any("exactly one" in error for error in result.errors))

    def test_degree_crs_is_rejected_for_metric_planning(self) -> None:
        plan = load_template()
        plan["area"]["metricPlanning"] = True
        result = validate_plan(plan)
        self.assertTrue(any("projected CRS" in error for error in result.errors))

    def test_non_finite_bbox_is_rejected(self) -> None:
        plan = load_template()
        plan["area"]["restrictedGeometry"]["bbox"][0] = float("nan")
        result = validate_plan(plan)
        self.assertTrue(any("must be [west" in error for error in result.errors))

    def test_historical_cycle_has_witness(self) -> None:
        plan = load_template()
        plan["edges"].append(
            {
                "edgeId": "edge_reverse",
                "from": "phase_later_expansion",
                "to": "phase_early_routes",
                "relation": "historically-precedes",
                "authority": "reported",
                "sourceIds": ["src_map_series"],
                "rationale": "Deliberately contradictory test edge.",
            }
        )
        result = validate_plan(plan)
        self.assertTrue(any("historically-precedes cycle" in error for error in result.errors))

    def test_speculative_nodes_cannot_form_stratigraphy(self) -> None:
        plan = load_template()
        plan["edges"].append(
            {
                "edgeId": "edge_false_harris",
                "from": "phase_early_routes",
                "to": "phase_later_expansion",
                "relation": "stratigraphically-precedes",
                "authority": "hypothesis",
                "sourceIds": ["src_map_series"],
                "rationale": "Deliberately invalid speculative relation.",
            }
        )
        result = validate_plan(plan)
        self.assertTrue(any("excavation contexts" in error for error in result.errors))
        self.assertTrue(any("observed-stratigraphy" in error for error in result.errors))

    def test_documentary_nodes_cannot_masquerade_as_excavation_contexts(self) -> None:
        plan = load_template()
        for node_id in ("ctx_a", "ctx_b"):
            plan["nodes"].append(
                {
                    "nodeId": node_id,
                    "kind": "excavation-context",
                    "label": "Documentary guess relabelled as a context",
                    "authority": "hypothesis",
                    "sourceIds": ["src_map_series"],
                    "cellIds": [],
                    "sensitivity": "restricted",
                    "record": entity_record("excavation-context"),
                }
            )
        plan["edges"].append(
            {
                "edgeId": "edge_false_contexts",
                "from": "ctx_a",
                "to": "ctx_b",
                "relation": "stratigraphically-precedes",
                "authority": "observed-stratigraphy",
                "sourceIds": ["src_map_series"],
                "recordLocator": "map sheet 3",
                "rationale": "Deliberately invalid documentary relation.",
            }
        )
        result = validate_plan(plan)
        self.assertTrue(any("observed authority" in error for error in result.errors))
        self.assertTrue(any("excavation-record" in error for error in result.errors))

    def test_grid_parent_cycle_is_rejected(self) -> None:
        plan = load_template()
        plan["grid"]["cells"][0]["parentId"] = "cell_L0_R01C02"
        plan["grid"]["cells"][1]["parentId"] = "cell_L0_R01C01"
        result = validate_plan(plan)
        self.assertTrue(any("grid parent cycle" in error for error in result.errors))

    def test_action_prerequisite_cycle_is_rejected(self) -> None:
        plan = load_template()
        plan["actions"][0]["prerequisites"] = ["act_map_regression"]
        result = validate_plan(plan)
        self.assertTrue(any("prerequisite cycle" in error for error in result.errors))

    def test_secret_bearing_url_is_rejected(self) -> None:
        plan = load_template()
        plan["sources"][0]["url"] = "https://example.org/data?api_key=secret"
        result = validate_plan(plan)
        self.assertTrue(any("secret-bearing" in error for error in result.errors))

    def test_nested_and_provider_signature_urls_are_rejected(self) -> None:
        plan = load_template()
        plan["sources"][0]["url"] = (
            "https://example.org/redirect?"
            "next=https%253A%252F%252Ftiles.example%252F%253Faccess_token%253Dsecret"
        )
        result = validate_plan(plan)
        self.assertTrue(any("credential" in error for error in result.errors))
        plan["sources"][0]["url"] = "https://example.org/data?X-Amz-Signature=secret"
        result = validate_plan(plan)
        self.assertTrue(any("secret-bearing" in error for error in result.errors))

    def test_policy_weights_reject_booleans_and_bad_totals(self) -> None:
        plan = load_template()
        plan["policy"]["weights"]["discrimination"] = True
        result = validate_plan(plan)
        self.assertTrue(any("policy.weights" in error for error in result.errors))
        plan = load_template()
        plan["policy"]["weights"]["coverage"] = 0.2
        result = validate_plan(plan)
        self.assertTrue(any("sum to 1" in error for error in result.errors))

    def test_visible_benchmark_target_leakage_is_rejected(self) -> None:
        plan = load_template()
        plan["case"]["studyKind"] = "known-site-rediscovery"
        plan["sources"][2]["targetLabelState"] = "visible"
        result = validate_plan(plan)
        self.assertTrue(any("target-label provenance" in error for error in result.errors))

    def test_transitive_target_provenance_is_rejected(self) -> None:
        plan = load_template()
        heritage = next(
            source
            for source in plan["sources"]
            if source["sourceId"] == "src_heritage_inventory"
        )
        heritage["targetLabelState"] = "visible"
        hypothesis = next(
            node for node in plan["nodes"] if node["nodeId"] == "hyp_route_growth"
        )
        hypothesis["sourceIds"].append("src_heritage_inventory")
        result = validate_plan(plan)
        self.assertTrue(any("target-label provenance" in error for error in result.errors))

    def test_transitive_authority_source_requires_approval(self) -> None:
        plan = load_template()
        heritage = next(
            source
            for source in plan["sources"]
            if source["sourceId"] == "src_heritage_inventory"
        )
        heritage["accessStage"] = "pre-detection"
        heritage["targetLabelState"] = "none"
        hypothesis = next(
            node for node in plan["nodes"] if node["nodeId"] == "hyp_route_growth"
        )
        hypothesis["sourceIds"] = ["src_heritage_inventory"]
        result = validate_plan(plan)
        self.assertTrue(any("authority-controlled source" in error for error in result.errors))

    def test_candidate_action_cannot_self_pair(self) -> None:
        plan = load_template()
        action = next(
            item for item in plan["actions"] if item["actionId"] == "act_relief_control"
        )
        action["candidateFocused"] = True
        action["pairedControlActionId"] = action["actionId"]
        result = validate_plan(plan)
        self.assertTrue(any("cannot pair with itself" in error for error in result.errors))

    def test_intrusive_or_authority_bypassing_action_is_rejected(self) -> None:
        plan = load_template()
        action = plan["actions"][0]
        action["label"] = "Trespass at night and metal-detect a burial"
        result = validate_plan(plan)
        self.assertTrue(any("prohibited intrusive conduct" in error for error in result.errors))
        plan = load_template()
        action = next(
            item
            for item in plan["actions"]
            if item["actionId"] == "act_inventory_unblind"
        )
        action["authorization"] = {"required": "none", "state": "not-required"}
        result = validate_plan(plan)
        self.assertTrue(any("authority-controlled source" in error for error in result.errors))


class FrontierTests(unittest.TestCase):
    def test_initial_frontier_is_deterministic(self) -> None:
        plan = load_template()
        first = build_frontier(plan, 4)
        second = build_frontier(plan, 4)
        self.assertEqual(first, second)
        self.assertIn("not site probability", first["scoreMeaning"])
        self.assertEqual(
            ["act_name_concordance", "act_systematic_coverage"],
            [item["actionId"] for item in first["recommendedBatch"]],
        )

    def test_plan_with_every_action_blocked_is_not_ready(self) -> None:
        plan = load_template()
        for action in plan["actions"]:
            action["status"] = "blocked"
        self.assertTrue(validate_plan(plan).valid)
        self.assertTrue(
            any("executable action" in error for error in readiness_errors(plan))
        )

    def test_candidate_action_reserves_its_control(self) -> None:
        plan = load_template()
        for action in plan["actions"]:
            if action["actionId"] in {"act_name_concordance", "act_map_regression"}:
                action["status"] = "completed"
                action["resultRefs"] = [
                    {
                        "resultId": f"result_{action['actionId']}",
                        "sha256": "a" * 64,
                    }
                ]
                action["_runtimeEvidenceVerified"] = True
        frontier = build_frontier(plan, 4)
        selected = [item["actionId"] for item in frontier["recommendedBatch"]]
        self.assertIn("act_relief_candidate", selected)
        self.assertIn("act_relief_control", selected)

    def test_hand_edited_completion_cannot_unlock_a_dependency(self) -> None:
        plan = load_template()
        action = next(
            item for item in plan["actions"] if item["actionId"] == "act_name_concordance"
        )
        action["status"] = "completed"
        action["resultRefs"] = [{"path": "forged.json", "sha256": "a" * 64}]
        frontier = build_frontier(plan, 10)
        selected = {item["actionId"] for item in frontier["recommendedBatch"]}
        self.assertNotIn("act_map_regression", selected)

    def test_completed_control_unlocks_candidate_without_rescheduling_control(self) -> None:
        plan = load_template()
        for action in plan["actions"]:
            if action["actionId"] in {
                "act_name_concordance",
                "act_map_regression",
                "act_relief_control",
            }:
                action["status"] = "completed"
                action["resultRefs"] = [
                    {
                        "resultId": f"result_{action['actionId']}",
                        "sha256": "a" * 64,
                    }
                ]
                action["_runtimeEvidenceVerified"] = True
        frontier = build_frontier(plan, 2)
        selected = [item["actionId"] for item in frontier["recommendedBatch"]]
        self.assertIn("act_relief_candidate", selected)
        self.assertNotIn("act_relief_control", selected)

    def test_unauthorized_high_score_action_stays_blocked(self) -> None:
        plan = load_template()
        action = plan["actions"][0]
        action["authorization"] = {
            "required": "user-account",
            "state": "not-authorized",
        }
        for key in action["scores"]:
            action["scores"][key] = 1.0
        frontier = build_frontier(plan, 4)
        selected = {item["actionId"] for item in frontier["recommendedBatch"]}
        self.assertNotIn(action["actionId"], selected)

    def test_public_export_preserves_spatial_evidence_and_withholds_private_sources(
        self,
    ) -> None:
        plan = load_template()
        plan["nodes"][0]["coordinate"] = [10.15, 50.15]
        plan["nodes"][2]["restrictedGeometry"] = {
            "type": "Point",
            "coordinates": [10.123456, 50.123456],
        }
        plan["nodes"][2]["nested"] = {"bbox": [10.1, 50.1, 10.2, 50.2]}
        exported = public_export(plan)
        self.assertIn(
            [10.15, 50.15],
            [node.get("coordinate") for node in exported["nodes"]],
        )
        mapped_node = next(
            node
            for node in exported["nodes"]
            if node.get("coordinate") == [10.15, 50.15]
        )
        self.assertEqual(
            (
                "https://www.google.com/maps/search/?api=1&"
                "query=50.150000%2C10.150000"
            ),
            mapped_node["googleMapsLink"],
        )
        serialized = json.dumps(exported, sort_keys=True)
        self.assertNotIn("10.123456", serialized)
        self.assertNotIn("50.123456", serialized)
        withheld = [
            source
            for source in exported["sources"]
            if source["sensitivity"] == "withheld"
        ]
        self.assertTrue(withheld)
        self.assertTrue(all("url" not in source for source in withheld))
        self.assertEqual(plan_sha256(plan), exported["publicExport"]["exportedFromSha256"])


class CliTests(unittest.TestCase):
    def test_empty_skeleton_is_valid_but_not_research_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "skeleton.json"
            create = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "new",
                    "--place",
                    "Resolved place",
                    "--gazetteer-id",
                    "gaz:123",
                    "--question",
                    "Where should research begin?",
                    "--bbox",
                    "10",
                    "50",
                    "10.2",
                    "50.2",
                    "--out",
                    str(plan_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, create.returncode, create.stderr)
            validate = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "validate",
                    "--plan",
                    str(plan_path),
                    "--ready",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, validate.returncode)
            payload = json.loads(validate.stdout)
            self.assertTrue(payload["valid"])
            self.assertFalse(payload["ready"])
            self.assertTrue(payload["readinessErrors"])

    def test_validate_and_rank_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            frontier = Path(temp_dir) / "frontier.json"
            validate = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "validate",
                    "--plan",
                    str(TEMPLATE),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, validate.returncode, validate.stderr)
            rank = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "rank",
                    "--plan",
                    str(TEMPLATE),
                    "--limit",
                    "4",
                    "--out",
                    str(frontier),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, rank.returncode, rank.stderr)
            self.assertTrue(frontier.exists())

    def test_command_refuses_to_overwrite_plan_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "plan.json"
            plan_path.write_bytes(TEMPLATE.read_bytes())
            before = plan_path.read_bytes()
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "rank",
                    "--plan",
                    str(plan_path),
                    "--out",
                    str(plan_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(3, result.returncode)
            self.assertEqual(before, plan_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
