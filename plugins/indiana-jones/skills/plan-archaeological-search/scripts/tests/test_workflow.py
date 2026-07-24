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

from ij_ingest import normalize_record
from ij_runtime import initialize_run
from ij_workflow import (
    discover_declared_sources,
    extract_record_claims,
    run_until_pause,
)


def load_template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


class WorkflowTests(unittest.TestCase):
    def test_source_discovery_separates_capability_from_permission(self) -> None:
        plan = load_template()
        plan["sources"][0]["acquisition"] = {
            "format": "oai-pmh",
            "locator": "https://example.org/oai",
        }
        discovered = discover_declared_sources(plan)
        first = next(
            item
            for item in discovered["candidates"]
            if item["sourceId"] == plan["sources"][0]["sourceId"]
        )
        self.assertTrue(first["ingestionEligible"])
        self.assertIn("does not grant", discovered["warning"])

    def test_claim_extraction_preserves_record_and_source_lineage(self) -> None:
        record = normalize_record(
            {
                "identifier": "A-1",
                "title": "Iron sword",
                "material": "iron",
                "repository": "Test Museum",
            },
            source_id="src_museum",
            index=1,
            sensitivity="restricted",
        )
        extracted = extract_record_claims({"records": [record]})
        predicates = {claim["predicate"] for claim in extracted["claims"]}
        self.assertIn("made-of", predicates)
        self.assertIn("held-by", predicates)
        self.assertTrue(
            all(claim["sourceId"] == "src_museum" for claim in extracted["claims"])
        )

    def test_run_executes_deterministic_work_then_pauses_for_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = load_template()
            action = plan["actions"][0]
            action["execution"] = {
                "executor": "ingest-source",
                "inputs": {
                    "sourceId": "src_hul",
                    "locator": "inputs/records.json",
                    "format": "json",
                },
                "outputs": ["normalized records"],
                "acceptanceCriteria": ["Preserve hashes."],
                "timeoutSeconds": 60,
                "maxAttempts": 1,
            }
            plan["sources"][0]["acquisition"] = {
                "locator": "inputs/records.json",
                "format": "json",
            }
            run_dir = root / "run"
            initialize_run(
                plan,
                run_dir,
                max_actions=20,
                max_attempts=40,
                max_result_bytes=1_000_000,
                max_seconds=3600,
            )
            (run_dir / "inputs").mkdir()
            (run_dir / "inputs" / "records.json").write_text(
                '{"records":[{"identifier":"A-1","title":"Sword"}]}',
                encoding="utf-8",
            )
            result = run_until_pause(run_dir, max_steps=10, limit=4)
            self.assertEqual(1, len(result["executed"]))
            self.assertEqual("agent-action-required", result["pauseReason"])
            self.assertTrue(result["taskPacket"]["recommendedBatch"])


if __name__ == "__main__":
    unittest.main()
