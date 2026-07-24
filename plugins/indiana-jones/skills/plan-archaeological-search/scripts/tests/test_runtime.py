from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_journal import read_events
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


class RuntimeTests(unittest.TestCase):
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
                result_path=None,
                summary="Resolved the declared aliases from the cited public source.",
                source_ids=["src_hul"],
                acceptance_evidence=[
                    "The sealed result cites the declared source.",
                    "The sealed result records uncertainty and alternatives.",
                ],
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
                result_path=None,
                summary="Evidence result.",
                source_ids=["src_hul"],
                acceptance_evidence=[
                    "The sealed result cites the declared source.",
                    "The sealed result records uncertainty and alternatives.",
                ],
            )
            result_path = run_dir / completed["result"]["path"]
            result_path.write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing or changed"):
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
            resumed = resume_run(run_dir)
            action = resumed["actions"]["act_name_concordance"]
            self.assertEqual("planned", action["status"])
            self.assertEqual("interrupted", action["attempts"][0]["status"])
            second = start_action(run_dir, "act_name_concordance")
            self.assertNotEqual(first["attemptId"], second["attemptId"])

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
                result_path=None,
                summary="Evidence result.",
                source_ids=["src_hul"],
                acceptance_evidence=[
                    "The sealed result cites the declared source.",
                    "The sealed result records uncertainty and alternatives.",
                ],
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
