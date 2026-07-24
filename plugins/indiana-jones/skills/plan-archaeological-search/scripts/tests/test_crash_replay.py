from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

import ij_executors
import ij_results
import ij_runtime
from ij_artifacts import read_json
from ij_journal import file_sha256, read_events
from ij_runtime import (
    complete_action,
    execute_deterministic_action,
    initialize_run,
    load_run,
    replay_state,
    start_action,
)
from ij_source_contract import acquisition_contract


ACTION_ID = "act_name_concordance"
SOURCE_ID = "src_hul"
COMMAND_KEY = "fault-fixture:start:0001"


class InjectedCrash(RuntimeError):
    pass


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


def ingestion_plan(payload: str) -> dict:
    plan = executable_plan()
    action = next(item for item in plan["actions"] if item["actionId"] == ACTION_ID)
    action["sourceIds"] = [SOURCE_ID]
    action["prerequisites"] = []
    action["execution"] = {
        "executor": "ingest-source",
        "inputs": {
            "sourceId": SOURCE_ID,
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
    source = next(item for item in plan["sources"] if item["sourceId"] == SOURCE_ID)
    source["acquisition"] = acquisition_contract(
        source,
        locator="inputs/records.json",
        format_name="json",
        query={},
        snapshot_sha256=hashlib.sha256(payload.encode()).hexdigest(),
        retrieved_at="2026-07-24T10:00:00Z",
    )
    return plan


def write_agent_result(root: Path) -> Path:
    path = root / "agent-result.json"
    content = "Bounded public fixture source snapshot."
    content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    snapshot_id = f"snapshot:{SOURCE_ID}:{content_sha256}"
    path.write_text(
        json.dumps(
            {
                "schemaVersion": "research-result-2.0",
                "actionId": ACTION_ID,
                "observations": [
                    {
                        "statement": "The bounded source supports the fixture result.",
                        "sourceIds": [SOURCE_ID],
                        "originFamilyIds": ["unesco-hul-2011"],
                    }
                ],
                "negativeResults": [],
                "warnings": [],
                "errors": [],
                "sourceSnapshots": [
                    {
                        "snapshotId": snapshot_id,
                        "sourceId": SOURCE_ID,
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
                    "The result records bounded alternatives.",
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def initialize_fixture(plan: dict, run_dir: Path) -> dict:
    return initialize_run(
        plan,
        run_dir,
        max_actions=20,
        max_attempts=40,
        max_result_bytes=1_000_000,
        max_seconds=3600,
    )


def append_then_crash(event_type: str):
    original = ij_runtime.append_event
    crashed = False

    def fault(path, run_id, candidate_type, payload, **kwargs):
        nonlocal crashed
        event = original(path, run_id, candidate_type, payload, **kwargs)
        if candidate_type == event_type and not crashed:
            crashed = True
            raise InjectedCrash(f"crash after durable {event_type}")
        return event

    return fault


@contextmanager
def deterministic_mutations(timestamp: float):
    fixed_uuid = uuid.UUID("00000000-0000-0000-0000-000000000042")
    with (
        mock.patch.object(ij_runtime.time, "time", return_value=timestamp),
        mock.patch.object(ij_results.uuid, "uuid4", return_value=fixed_uuid),
    ):
        yield


class CrashReplayTests(unittest.TestCase):
    def assert_replay_equivalent(self, run_dir: Path) -> None:
        plan, events, state = load_run(run_dir)
        self.assertEqual(replay_state(plan, events), state)
        self.assertEqual(state, read_json(run_dir / "state.json"))

    def assert_same_run_outputs(self, baseline: Path, recovered: Path) -> None:
        self.assertEqual(
            (baseline / "events.jsonl").read_bytes(),
            (recovered / "events.jsonl").read_bytes(),
        )
        _, _, baseline_state = load_run(baseline)
        _, _, recovered_state = load_run(recovered)
        baseline_result = baseline_state["actions"][ACTION_ID]["resultRefs"][-1]
        recovered_result = recovered_state["actions"][ACTION_ID]["resultRefs"][-1]
        self.assertEqual(baseline_result, recovered_result)
        self.assertEqual(
            file_sha256(baseline / baseline_result["path"]),
            file_sha256(recovered / recovered_result["path"]),
        )

    def test_start_append_crash_matches_uninterrupted_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            seed = root / "seed"
            started_at = initialize_fixture(executable_plan(), seed)["startedAt"]
            baseline = root / "baseline"
            recovered = root / "recovered"
            shutil.copytree(seed, baseline)
            shutil.copytree(seed, recovered)
            result_path = write_agent_result(root)
            execution_count = 0

            with deterministic_mutations(started_at + 1):
                baseline_start = start_action(baseline, ACTION_ID, COMMAND_KEY)
                complete_action(
                    baseline,
                    ACTION_ID,
                    baseline_start["attemptId"],
                    result_path=result_path,
                    summary="Evidence result.",
                    source_ids=[SOURCE_ID],
                )
                with mock.patch.object(
                    ij_runtime,
                    "append_event",
                    side_effect=append_then_crash("action-started"),
                ):
                    with self.assertRaises(InjectedCrash):
                        start_action(recovered, ACTION_ID, COMMAND_KEY)
                durable_events = read_events(recovered / "events.jsonl")
                self.assertEqual(2, len(durable_events))
                replay = start_action(recovered, ACTION_ID, COMMAND_KEY)
                self.assertTrue(replay["replayed"])
                self.assertEqual(
                    durable_events[-1]["eventHash"], replay["journalEventSha256"]
                )
                self.assertEqual(2, len(read_events(recovered / "events.jsonl")))
                execution_count += 1
                complete_action(
                    recovered,
                    ACTION_ID,
                    replay["attemptId"],
                    result_path=result_path,
                    summary="Evidence result.",
                    source_ids=[SOURCE_ID],
                )

            self.assertEqual(1, execution_count)
            self.assert_same_run_outputs(baseline, recovered)
            self.assert_replay_equivalent(recovered)

    def test_completion_append_crash_reuses_one_sealed_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            seed = root / "seed"
            started_at = initialize_fixture(executable_plan(), seed)["startedAt"]
            baseline = root / "baseline"
            recovered = root / "recovered"
            shutil.copytree(seed, baseline)
            shutil.copytree(seed, recovered)
            result_path = write_agent_result(root)
            stored = 0
            original_store = ij_runtime.store_result

            def counted_store(*args, **kwargs):
                nonlocal stored
                stored += 1
                return original_store(*args, **kwargs)

            with deterministic_mutations(started_at + 1):
                baseline_start = start_action(baseline, ACTION_ID, COMMAND_KEY)
                baseline_complete = complete_action(
                    baseline,
                    ACTION_ID,
                    baseline_start["attemptId"],
                    result_path=result_path,
                    summary="Evidence result.",
                    source_ids=[SOURCE_ID],
                )
                recovered_start = start_action(recovered, ACTION_ID, COMMAND_KEY)
                with mock.patch.object(
                    ij_runtime,
                    "store_result",
                    side_effect=counted_store,
                ):
                    with mock.patch.object(
                        ij_runtime,
                        "append_event",
                        side_effect=append_then_crash("action-completed"),
                    ):
                        with self.assertRaises(InjectedCrash):
                            complete_action(
                                recovered,
                                ACTION_ID,
                                recovered_start["attemptId"],
                                result_path=result_path,
                                summary="Evidence result.",
                                source_ids=[SOURCE_ID],
                            )
                    journal_after_crash = (recovered / "events.jsonl").read_bytes()
                    replay = complete_action(
                        recovered,
                        ACTION_ID,
                        recovered_start["attemptId"],
                        result_path=result_path,
                        summary="Evidence result.",
                        source_ids=[SOURCE_ID],
                    )

            self.assertEqual(1, stored)
            self.assertTrue(replay["replayed"])
            self.assertEqual(baseline_complete["result"], replay["result"])
            self.assertEqual(
                journal_after_crash,
                (recovered / "events.jsonl").read_bytes(),
            )
            self.assert_same_run_outputs(baseline, recovered)
            self.assert_replay_equivalent(recovered)

    def test_executor_recovers_start_boundary_without_duplicate_acquisition(
        self,
    ) -> None:
        payload = json.dumps({"records": [{"identifier": "A-1", "title": "Sword"}]})
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_fixture(ingestion_plan(payload), run_dir)
            (run_dir / "inputs").mkdir()
            (run_dir / "inputs" / "records.json").write_text(payload, encoding="utf-8")

            with mock.patch.object(
                ij_executors,
                "acquire_and_normalize",
                wraps=ij_executors.acquire_and_normalize,
            ) as acquire:
                with mock.patch.object(
                    ij_runtime,
                    "append_event",
                    side_effect=append_then_crash("action-started"),
                ):
                    with self.assertRaises(InjectedCrash):
                        execute_deterministic_action(run_dir, ACTION_ID)
                self.assertEqual(0, acquire.call_count)
                recovered = execute_deterministic_action(run_dir, ACTION_ID)
                self.assertEqual(1, acquire.call_count)
                journal = (run_dir / "events.jsonl").read_bytes()
                result_hash = recovered["result"]["sha256"]
                replay = execute_deterministic_action(run_dir, ACTION_ID)

            self.assertTrue(replay["replayed"])
            self.assertEqual(1, acquire.call_count)
            self.assertEqual(result_hash, replay["result"]["sha256"])
            self.assertEqual(journal, (run_dir / "events.jsonl").read_bytes())
            self.assert_replay_equivalent(run_dir)

    def test_executor_recovers_completion_boundary_without_duplicate_acquisition(
        self,
    ) -> None:
        payload = json.dumps({"records": [{"identifier": "A-1", "title": "Sword"}]})
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialize_fixture(ingestion_plan(payload), run_dir)
            (run_dir / "inputs").mkdir()
            (run_dir / "inputs" / "records.json").write_text(payload, encoding="utf-8")

            with mock.patch.object(
                ij_executors,
                "acquire_and_normalize",
                wraps=ij_executors.acquire_and_normalize,
            ) as acquire:
                with mock.patch.object(
                    ij_runtime,
                    "append_event",
                    side_effect=append_then_crash("action-completed"),
                ):
                    with self.assertRaises(InjectedCrash):
                        execute_deterministic_action(run_dir, ACTION_ID)
                self.assertEqual(1, acquire.call_count)
                journal = (run_dir / "events.jsonl").read_bytes()
                _, _, after_crash = load_run(run_dir)
                result = after_crash["actions"][ACTION_ID]["resultRefs"][-1]
                result_hash = file_sha256(run_dir / result["path"])
                replay = execute_deterministic_action(run_dir, ACTION_ID)

            self.assertTrue(replay["replayed"])
            self.assertEqual(1, acquire.call_count)
            self.assertEqual(
                result_hash, file_sha256(run_dir / replay["result"]["path"])
            )
            self.assertEqual(journal, (run_dir / "events.jsonl").read_bytes())
            self.assert_replay_equivalent(run_dir)


if __name__ == "__main__":
    unittest.main()
