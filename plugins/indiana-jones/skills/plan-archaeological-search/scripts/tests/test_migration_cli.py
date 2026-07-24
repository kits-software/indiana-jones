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
CLI = SCRIPT_DIR / "search_plan.py"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_migrate import freeze_candidates, migrate_plan, verify_candidate_freeze
from ij_runtime import execute_deterministic_action, initialize_run, run_status


def load_template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


class MigrationAndFreezeTests(unittest.TestCase):
    def test_legacy_completion_is_quarantined_and_migration_is_idempotent(self) -> None:
        original = load_template()
        original["schemaVersion"] = "1.0"
        original["nodes"].append(
            {
                "nodeId": "legacy_result",
                "kind": "result",
                "label": "Legacy manually asserted result",
                "authority": "reported",
                "sourceIds": ["src_hul"],
                "cellIds": [],
                "sensitivity": "restricted",
            }
        )
        original["actions"][0]["status"] = "completed"
        original["actions"][0]["resultNodeIds"] = ["legacy_result"]
        before = copy.deepcopy(original)
        migrated, manifest = migrate_plan(original)
        self.assertEqual(before, original)
        self.assertEqual("2.0", migrated["schemaVersion"])
        self.assertEqual("completed-unverified", migrated["actions"][0]["status"])
        self.assertNotIn("resultNodeIds", migrated["actions"][0])
        self.assertEqual(64, len(manifest["sourcePlanSha256"]))
        second, second_manifest = migrate_plan(migrated)
        self.assertEqual(migrated, second)
        self.assertEqual([], second_manifest["changes"])

    def test_unknown_legacy_sensitivity_migrates_restricted(self) -> None:
        plan = load_template()
        plan["schemaVersion"] = "1.0"
        plan["nodes"][0]["sensitivity"] = "publci"
        migrated, _ = migrate_plan(plan)
        self.assertEqual("restricted", migrated["nodes"][0]["sensitivity"])

    def test_candidate_freeze_rejects_embedded_ground_truth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "candidates.json"
            path.write_text('{"groundTruthCoordinates":[1,2]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ground-truth-like"):
                freeze_candidates(load_template(), json.loads(path.read_text()), path)

    def test_candidate_freeze_produces_hash_bound_plan_and_seal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "candidates.json"
            path.write_text('{"candidates":[{"candidateId":"c1","score":0.5}]}', encoding="utf-8")
            frozen, seal = freeze_candidates(
                load_template(), json.loads(path.read_text()), path
            )
            self.assertTrue(frozen["case"]["candidatesFrozen"])
            self.assertEqual(
                seal["candidateArtifactSha256"],
                frozen["case"]["candidateArtifactSha256"],
            )
            self.assertEqual("passed", seal["groundTruthKeyScan"])
            seal_path = Path(temp_dir) / "candidate-seal.json"
            seal_path.write_text(json.dumps(seal), encoding="utf-8")
            verify_candidate_freeze(frozen, path, seal_path)
            with self.assertRaisesRegex(ValueError, "require both"):
                verify_candidate_freeze(frozen, None, None)
            path.write_text('{"candidates":[]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "stale"):
                verify_candidate_freeze(frozen, path, seal_path)


class CliAndDeterministicRuntimeTests(unittest.TestCase):
    def test_cli_malformed_data_has_stable_diagnostic_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            plan = load_template()
            plan["nodes"] = ["not-an-object"]
            path.write_text(json.dumps(plan), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(CLI), "validate", "--plan", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, result.returncode)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["valid"])
            self.assertNotIn("Traceback", result.stderr)

    def test_cli_init_next_and_status_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "init-run",
                    "--plan",
                    str(TEMPLATE),
                    "--run-dir",
                    str(run_dir),
                    "--max-actions",
                    "10",
                    "--max-attempts",
                    "20",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            packet = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "next",
                    "--run-dir",
                    str(run_dir),
                    "--limit",
                    "2",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, packet.returncode, packet.stderr)
            self.assertTrue(json.loads(packet.stdout)["recommendedBatch"])
            status = subprocess.run(
                [sys.executable, str(CLI), "status", "--run-dir", str(run_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status.returncode, status.stderr)
            self.assertEqual("active", json.loads(status.stdout)["status"])

    def test_deterministic_ingestion_action_executes_and_seals_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = load_template()
            action = plan["actions"][0]
            action["execution"] = {
                "executor": "ingest-source",
                "inputs": {
                    "sourceId": "src_hul",
                    "locator": "inputs/finds.csv",
                    "format": "csv",
                    "maxBytes": 10000,
                    "maxRecords": 10,
                    "query": {"term": "sword"},
                },
                "outputs": ["normalized finds"],
                "acceptanceCriteria": ["Retain query and source hashes."],
                "timeoutSeconds": 60,
                "maxAttempts": 1,
            }
            plan["sources"][0]["acquisition"] = {
                "locator": "inputs/finds.csv",
                "format": "csv",
            }
            run_dir = root / "run"
            initialize_run(
                plan,
                run_dir,
                max_actions=10,
                max_attempts=20,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            input_dir = run_dir / "inputs"
            input_dir.mkdir()
            (input_dir / "finds.csv").write_text(
                "identifier,title,material\nA-1,Gold sword fitting,gold\n",
                encoding="utf-8",
            )
            result = execute_deterministic_action(run_dir, action["actionId"])
            self.assertEqual("completed", result["run"]["actions"][action["actionId"]]["status"])
            self.assertEqual(64, len(result["result"]["sha256"]))
            self.assertEqual(3, run_status(run_dir)["eventCount"])


if __name__ == "__main__":
    unittest.main()
