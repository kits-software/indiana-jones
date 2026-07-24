from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_runtime import (
    complete_action,
    execute_deterministic_action,
    fail_action,
    initialize_run,
    next_task_packet,
    resume_run,
    run_status,
    start_action,
)
from ij_source_contract import acquisition_contract


def executable_plan() -> dict:
    plan = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    for action in plan["actions"]:
        action["execution"] = {
            "executor": "codex-research",
            "inputs": {"instruction": action["label"]},
            "outputs": ["evidence-bound research result"],
            "acceptanceCriteria": [
                "Cite every observation to a declared source.",
                "Record negative evidence and unresolved alternatives.",
            ],
            "timeoutSeconds": 3600,
            "maxAttempts": 2,
        }
    return plan


def agent_result(
    root: Path,
    action_id: str,
    source_id: str,
    *,
    normalized_ids: list[str] | None = None,
) -> Path:
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
                        "statement": "The same bounded observation was recovered.",
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
                "normalizedRecordIds": normalized_ids or [],
                "methodVersion": "fixture-method-1.0",
                "adapterVersion": "fixture-adapter-1.0",
                "resultSensitivity": "restricted",
                "disclosureDecision": "restricted",
                "acceptanceEvidence": [
                    "The observation cites the declared source.",
                    "The bounded result preserves unresolved alternatives.",
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def complete_fixture(
    root: Path,
    run_dir: Path,
    action_id: str,
    source_id: str,
) -> dict:
    started = start_action(run_dir, action_id)
    return complete_action(
        run_dir,
        action_id,
        started["attemptId"],
        result_path=agent_result(root, action_id, source_id),
        summary="Bounded fixture result.",
        source_ids=[source_id],
    )


def ingestion_plan(payload: str) -> dict:
    plan = executable_plan()
    action_ids = {
        "act_name_concordance",
        "act_systematic_coverage",
        "act_map_regression",
    }
    for action in plan["actions"]:
        if action["actionId"] not in action_ids:
            continue
        action["sourceIds"] = ["src_hul"]
        action["prerequisites"] = []
        action["execution"] = {
            "executor": "ingest-source",
            "inputs": {
                "sourceId": "src_hul",
                "locator": "inputs/records.json",
                "format": "json",
                "maxRecords": 5,
            },
            "outputs": ["normalized records"],
            "acceptanceCriteria": ["Preserve source and record lineage."],
            "acceptanceChecks": [{"kind": "ingest-lineage"}],
            "timeoutSeconds": 60,
            "maxAttempts": 1,
        }
    plan["sources"][0]["acquisition"] = acquisition_contract(
        plan["sources"][0],
        locator="inputs/records.json",
        format_name="json",
        query={},
        snapshot_sha256=hashlib.sha256(payload.encode()).hexdigest(),
        retrieved_at="2026-07-24T10:00:00Z",
    )
    return plan


class RuntimeBudgetTests(unittest.TestCase):
    def test_cli_persists_extended_budget_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "plan.json"
            run_dir = root / "run"
            plan_path.write_text(json.dumps(executable_plan()), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "init-run",
                    "--plan",
                    str(plan_path),
                    "--run-dir",
                    str(run_dir),
                    "--max-actions",
                    "20",
                    "--max-attempts",
                    "40",
                    "--max-result-bytes",
                    "1000000",
                    "--max-seconds",
                    "3600",
                    "--max-requests",
                    "12",
                    "--max-requests-per-provider",
                    "3",
                    "--max-records",
                    "44",
                    "--max-consecutive-no-novelty",
                    "5",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            budgets = json.loads(completed.stdout)["budgets"]
            self.assertEqual(12, budgets["maxRequests"])
            self.assertEqual(3, budgets["maxRequestsPerProvider"])
            self.assertEqual(44, budgets["maxRecords"])
            self.assertEqual(5, budgets["maxConsecutiveNoNovelty"])

    def test_invalid_extended_limits_fail_before_run_creation(self) -> None:
        cases = (
            {"max_requests": 0},
            {"max_requests_per_provider": True},
            {"max_records": -1},
            {"max_consecutive_no_novelty": 0},
        )
        for index, extra in enumerate(cases):
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temp_dir:
                run_dir = Path(temp_dir) / f"run-{index}"
                with self.assertRaisesRegex(ValueError, "must be an integer"):
                    initialize_run(
                        executable_plan(),
                        run_dir,
                        max_actions=20,
                        max_attempts=40,
                        max_result_bytes=1_000_000,
                        max_seconds=3600,
                        **extra,
                    )
                self.assertFalse(run_dir.exists())

    def test_request_budget_replays_and_resumes_at_exact_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                executable_plan(),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
                max_requests=2,
                max_requests_per_provider=2,
            )
            first = start_action(run_dir, "act_name_concordance", "request:one")
            replay = start_action(run_dir, "act_name_concordance", "request:one")
            self.assertTrue(replay["replayed"])
            self.assertEqual(1, run_status(run_dir)["usage"]["requestsStarted"])
            resume_run(run_dir, now=first["leaseExpiresAt"] + 1)
            second = start_action(run_dir, "act_name_concordance", "request:two")
            self.assertEqual(2, second["run"]["usage"]["requestsStarted"])
            status = run_status(run_dir)
            self.assertEqual("budget-exhausted:max-requests", status["budgetStopReason"])
            self.assertEqual(
                "budget-exhausted:max-requests",
                next_task_packet(run_dir, 4)["stopReason"],
            )

    def test_provider_limit_blocks_one_provider_without_blocking_another(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            plan = executable_plan()
            by_id = {action["actionId"]: action for action in plan["actions"]}
            by_id["act_name_concordance"]["execution"]["inputs"]["provider"] = "archive-a"
            by_id["act_map_regression"]["execution"]["inputs"]["provider"] = "archive-a"
            by_id["act_systematic_coverage"]["execution"]["inputs"][
                "provider"
            ] = "archive-b"
            complete_source = by_id["act_name_concordance"]["sourceIds"][0]
            initialize_run(
                plan,
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
                max_requests=10,
                max_requests_per_provider=1,
            )
            complete_fixture(
                root,
                run_dir,
                "act_name_concordance",
                complete_source,
            )
            packet = next_task_packet(run_dir, 10)
            ready = {item["actionId"] for item in packet["recommendedBatch"]}
            blocked = {
                item["actionId"]: item["reasons"] for item in packet["blockedActions"]
            }
            self.assertIn("act_systematic_coverage", ready)
            self.assertIn(
                "budget-exhausted:max-requests-per-provider",
                blocked["act_map_regression"],
            )
            with self.assertRaisesRegex(ValueError, "max-requests-per-provider"):
                start_action(run_dir, "act_map_regression")
            started = start_action(run_dir, "act_systematic_coverage")
            self.assertEqual(
                {"archive-a": 1, "archive-b": 1},
                started["run"]["usage"]["requestsByProvider"],
            )

    def test_no_novelty_stop_replays_at_configured_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            plan = executable_plan()
            by_id = {action["actionId"]: action for action in plan["actions"]}
            for action_id in (
                "act_name_concordance",
                "act_systematic_coverage",
                "act_map_regression",
            ):
                by_id[action_id]["sourceIds"] = ["src_hul"]
            initialize_run(
                plan,
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
                max_consecutive_no_novelty=2,
            )
            first = complete_fixture(root, run_dir, "act_name_concordance", "src_hul")
            self.assertEqual(0, first["run"]["usage"]["consecutiveNoNovelty"])
            second = complete_fixture(
                root,
                run_dir,
                "act_systematic_coverage",
                "src_hul",
            )
            self.assertEqual(1, second["run"]["usage"]["consecutiveNoNovelty"])
            third = complete_fixture(root, run_dir, "act_map_regression", "src_hul")
            self.assertEqual(2, third["run"]["usage"]["consecutiveNoNovelty"])
            self.assertEqual(
                "stop:no-novelty-threshold",
                run_status(run_dir)["budgetStopReason"],
            )
            self.assertEqual(
                "stop:no-novelty-threshold",
                next_task_packet(run_dir, 4)["stopReason"],
            )

    def test_record_capacity_is_reserved_released_and_never_overshot(self) -> None:
        payload = json.dumps(
            {
                "records": [
                    {"identifier": "A-1", "title": "Sword"},
                    {"identifier": "A-2", "title": "Scabbard"},
                ]
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            initialize_run(
                ingestion_plan(payload),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
                max_records=1,
            )
            (run_dir / "inputs").mkdir()
            (run_dir / "inputs" / "records.json").write_text(payload, encoding="utf-8")
            started = start_action(run_dir, "act_name_concordance")
            self.assertEqual(1, started["run"]["usage"]["recordsReserved"])
            blocked = {
                item["actionId"]: item["reasons"]
                for item in next_task_packet(run_dir, 10)["blockedActions"]
            }
            self.assertIn(
                "budget-exhausted:max-records",
                blocked["act_systematic_coverage"],
            )
            failed = fail_action(
                run_dir,
                "act_name_concordance",
                started["attemptId"],
                error="fixture interruption",
                retryable=False,
            )
            self.assertEqual(0, failed["run"]["usage"]["recordsReserved"])
            completed = execute_deterministic_action(
                run_dir,
                "act_systematic_coverage",
            )
            artifact = json.loads(
                (run_dir / completed["result"]["path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(1, artifact["queryArtifact"]["resultCount"])
            self.assertTrue(artifact["queryArtifact"]["truncated"])
            self.assertEqual(1, completed["run"]["usage"]["recordsReturned"])
            self.assertEqual(0, completed["run"]["usage"]["recordsReserved"])
            with self.assertRaisesRegex(ValueError, "max-records"):
                start_action(run_dir, "act_map_regression")

    def test_exhausted_query_cannot_be_read_again(self) -> None:
        payload = '{"records":[{"identifier":"A-1","title":"Sword"}]}'
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_run(
                ingestion_plan(payload),
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
                max_records=10,
            )
            (run_dir / "inputs").mkdir()
            (run_dir / "inputs" / "records.json").write_text(payload, encoding="utf-8")
            completed = execute_deterministic_action(run_dir, "act_name_concordance")
            self.assertEqual(
                1,
                len(completed["run"]["usage"]["exhaustedSourceQueries"]),
            )
            with self.assertRaisesRegex(ValueError, "source-exhausted:query"):
                start_action(run_dir, "act_systematic_coverage")

if __name__ == "__main__":
    unittest.main()
