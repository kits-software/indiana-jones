from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_journal import read_events
from ij_result_validation import (
    deterministic_result_metadata,
    validate_agent_result,
)
from ij_runtime import (
    complete_action,
    initialize_run,
    next_task_packet,
    resume_run,
    run_status,
    start_action,
)


def executable_plan() -> dict:
    plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    for action in plan["actions"]:
        action["execution"] = {
            "executor": "codex-research",
            "inputs": {
                "instruction": action["label"],
                "sourceIds": action["sourceIds"],
            },
            "outputs": ["evidence-bound research result"],
            "acceptanceCriteria": [
                "Cite every observation to a declared source.",
                "Record negative evidence and unresolved alternatives.",
            ],
            "timeoutSeconds": 3600,
            "maxAttempts": 2,
        }
    return plan


def write_agent_result(root: Path, action_id: str, source_id: str) -> Path:
    path = root / f"{action_id}-result.json"
    content = "Bounded public fixture source snapshot."
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    snapshot_id = f"snapshot:{source_id}:{content_sha256}"
    path.write_text(
        json.dumps(
            {
                "schemaVersion": "research-result-2.0",
                "actionId": action_id,
                "observations": [
                    {
                        "statement": "The bounded source supports this result.",
                        "sourceIds": [source_id],
                        "originFamilyIds": ["unesco-hul-2011"],
                    }
                ],
                "negativeResults": [],
                "warnings": [],
                "errors": [],
                "sourceSnapshots": [
                    {
                        "snapshotId": snapshot_id,
                        "sourceId": source_id,
                        "originFamilyId": "unesco-hul-2011",
                        "content": content,
                        "contentSha256": content_sha256,
                        "retrievedAt": "2026-07-24T10:00:00Z",
                        "accessBasis": "public",
                    }
                ],
                "sourceSnapshotIds": [snapshot_id],
                "normalizedRecordIds": [],
                "methodVersion": "fixture-method-1.0",
                "adapterVersion": "fixture-adapter-1.0",
                "resultSensitivity": "restricted",
                "disclosureDecision": "restricted",
                "acceptanceEvidence": [
                    "The result cites the declared source.",
                    "The result records bounded uncertainty and alternatives.",
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


class RuntimeTests(unittest.TestCase):
    def test_result_sensitivity_cannot_downgrade_a_protected_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = executable_plan()
            plan["case"]["disclosure"] = "public"
            plan["sources"][0]["sensitivity"] = "non-public"
            action = next(
                item
                for item in plan["actions"]
                if item["actionId"] == "act_name_concordance"
            )
            result_path = write_agent_result(
                root,
                "act_name_concordance",
                "src_hul",
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))
            result["resultSensitivity"] = "public"
            result["disclosureDecision"] = "public"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-public source"):
                validate_agent_result(result_path, action, plan)

            metadata = deterministic_result_metadata(plan, action, ["src_hul"])
            self.assertEqual("non-public", metadata["resultSensitivity"])
            self.assertEqual(
                "heritage-authority-only",
                metadata["disclosureDecision"],
            )

            plan["sources"][0]["sensitivity"] = "burial"
            result["resultSensitivity"] = "restricted"
            result["disclosureDecision"] = "restricted"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "downgrades source sensitivity"):
                validate_agent_result(result_path, action, plan)

    def test_execution_rejects_legacy_schema_before_creating_a_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            plan = executable_plan()
            plan["schemaVersion"] = "1.0"
            with self.assertRaisesRegex(ValueError, "schema 2.0"):
                initialize_run(
                    plan,
                    run_dir,
                    max_actions=20,
                    max_attempts=40,
                    max_result_bytes=1_000_000,
                    max_seconds=3600,
                )
            self.assertFalse(run_dir.exists())

    def test_agent_completion_requires_a_structured_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            started = start_action(run_dir, "act_name_concordance")
            with self.assertRaisesRegex(ValueError, "structured result"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=None,
                    summary="Unsupported assertion.",
                    source_ids=["src_hul"],
                )
            malformed = root / "malformed.json"
            malformed.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schemaVersion|research-result"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=malformed,
                    summary="Unsupported assertion.",
                    source_ids=["src_hul"],
                )
            forged = json.loads(
                write_agent_result(
                    root,
                    "act_name_concordance",
                    "src_hul",
                ).read_text(encoding="utf-8")
            )
            forged["observations"][0]["originFamilyIds"] = ["invented-origin"]
            forged["normalizedRecordIds"] = ["invented:record"]
            forged_path = root / "forged-lineage.json"
            forged_path.write_text(json.dumps(forged), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "originFamilyIds"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=forged_path,
                    summary="Unsupported assertion.",
                    source_ids=["src_hul"],
                )
            forged["observations"][0]["originFamilyIds"] = ["unesco-hul-2011"]
            unsealed = json.loads(json.dumps(forged))
            unsealed.pop("sourceSnapshots")
            unsealed["sourceSnapshotIds"] = ["snapshot:src_hul"]
            forged_path.write_text(json.dumps(unsealed), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unresolved or unsealed"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=forged_path,
                    summary="Unsupported assertion.",
                    source_ids=["src_hul"],
                )
            mismatched_content = json.loads(json.dumps(forged))
            mismatched_content["sourceSnapshots"][0]["content"] = "Substituted text."
            forged_path.write_text(
                json.dumps(mismatched_content),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "does not match content"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=forged_path,
                    summary="Unsupported assertion.",
                    source_ids=["src_hul"],
                )
            forged_path.write_text(json.dumps(forged), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "normalizedRecordIds"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=forged_path,
                    summary="Unsupported assertion.",
                    source_ids=["src_hul"],
                )
            self.assertEqual(
                "running",
                run_status(run_dir)["actions"]["act_name_concordance"]["status"],
            )

    def test_result_seal_unlocks_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            initial = next_task_packet(run_dir, 6)
            self.assertNotIn(
                "act_map_regression",
                {item["actionId"] for item in initial["recommendedBatch"]},
            )
            started = start_action(run_dir, "act_name_concordance")
            completed = complete_action(
                run_dir,
                "act_name_concordance",
                started["attemptId"],
                result_path=write_agent_result(
                    Path(temp_dir), "act_name_concordance", "src_hul"
                ),
                summary="Resolved the declared aliases from the cited public source.",
                source_ids=["src_hul"],
            )
            self.assertEqual(
                "completed",
                completed["run"]["actions"]["act_name_concordance"]["status"],
            )
            advanced = next_task_packet(run_dir, 6)
            self.assertIn(
                "act_map_regression",
                {item["actionId"] for item in advanced["recommendedBatch"]},
            )

    def test_result_artifact_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            started = start_action(run_dir, "act_name_concordance")
            completed = complete_action(
                run_dir,
                "act_name_concordance",
                started["attemptId"],
                result_path=write_agent_result(
                    Path(temp_dir), "act_name_concordance", "src_hul"
                ),
                summary="Evidence result.",
                source_ids=["src_hul"],
            )
            result_path = run_dir / completed["result"]["path"]
            result_path.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing or changed"):
                run_status(run_dir)

    def test_completed_result_replay_is_idempotent_and_payload_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            started = start_action(run_dir, "act_name_concordance")
            result_path = write_agent_result(
                root,
                "act_name_concordance",
                "src_hul",
            )
            first = complete_action(
                run_dir,
                "act_name_concordance",
                started["attemptId"],
                result_path=result_path,
                summary="Evidence result.",
                source_ids=["src_hul"],
            )
            replay = complete_action(
                run_dir,
                "act_name_concordance",
                started["attemptId"],
                result_path=result_path,
                summary="Evidence result.",
                source_ids=["src_hul"],
            )
            self.assertTrue(replay["replayed"])
            self.assertEqual(first["result"], replay["result"])
            self.assertEqual(3, run_status(run_dir)["eventCount"])
            with self.assertRaisesRegex(ValueError, "different payload"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=result_path,
                    summary="Changed summary.",
                    source_ids=["src_hul"],
                )

    def test_result_budget_preflight_leaves_no_partial_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1,
                max_seconds=3600,
            )
            started = start_action(run_dir, "act_name_concordance")
            with self.assertRaisesRegex(ValueError, "max_result_bytes"):
                complete_action(
                    run_dir,
                    "act_name_concordance",
                    started["attemptId"],
                    result_path=write_agent_result(
                        root,
                        "act_name_concordance",
                        "src_hul",
                    ),
                    summary="Evidence result.",
                    source_ids=["src_hul"],
                )
            result_dir = run_dir / "results" / "act_name_concordance"
            self.assertFalse(result_dir.exists())
            state = run_status(run_dir)
            self.assertEqual(0, state["usage"]["resultBytes"])
            self.assertEqual("running", state["actions"]["act_name_concordance"]["status"])

    def test_plan_snapshot_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            path = run_dir / "plan.json"
            plan = json.loads(path.read_text(encoding="utf-8"))
            plan["case"]["researchQuestion"] = "Substituted after initialization"
            path.write_text(json.dumps(plan), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match the plan snapshot"):
                run_status(run_dir)

    def test_hash_chain_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            lines = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            event = json.loads(lines[0])
            event["payload"]["budgets"]["maxActions"] = 999
            (run_dir / "events.jsonl").write_text(
                json.dumps(event, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "invalid event hash"):
                read_events(run_dir / "events.jsonl")

    def test_resume_recovers_interrupted_action_for_bounded_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            first = start_action(run_dir, "act_name_concordance")
            resumed = resume_run(run_dir, now=first["leaseExpiresAt"] + 1)
            action = resumed["actions"]["act_name_concordance"]
            self.assertEqual("planned", action["status"])
            self.assertEqual("interrupted", action["attempts"][0]["status"])
            second = start_action(run_dir, "act_name_concordance")
            self.assertNotEqual(first["attemptId"], second["attemptId"])

    def test_live_lease_cannot_be_stolen_and_start_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            key = "fixture:start:0001"
            first = start_action(run_dir, "act_name_concordance", key)
            replay = start_action(run_dir, "act_name_concordance", key)
            self.assertTrue(replay["replayed"])
            self.assertEqual(first["attemptId"], replay["attemptId"])
            self.assertEqual(2, run_status(run_dir)["eventCount"])
            with self.assertRaisesRegex(ValueError, "another action"):
                start_action(run_dir, "act_systematic_coverage", key)
            with self.assertRaisesRegex(ValueError, "leases are active"):
                resume_run(run_dir, now=first["leaseExpiresAt"] - 1)

    def test_action_budget_stops_a_second_unique_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=1,
                max_attempts=10,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            started = start_action(run_dir, "act_name_concordance")
            complete_action(
                run_dir,
                "act_name_concordance",
                started["attemptId"],
                result_path=write_agent_result(
                    Path(temp_dir), "act_name_concordance", "src_hul"
                ),
                summary="Evidence result.",
                source_ids=["src_hul"],
            )
            packet = next_task_packet(run_dir, 4)
            self.assertEqual("budget-exhausted:max-actions", packet["stopReason"])
            self.assertEqual([], packet["recommendedBatch"])

    def test_task_packet_carries_executable_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            action = next_task_packet(run_dir, 1)["recommendedBatch"][0]
            self.assertEqual("codex-research", action["execution"]["executor"])
            self.assertTrue(action["execution"]["acceptanceCriteria"])
            self.assertTrue(action["sourceIds"])


if __name__ == "__main__":
    unittest.main()
