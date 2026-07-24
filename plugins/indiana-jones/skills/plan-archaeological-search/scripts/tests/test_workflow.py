from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_claims import extract_claims
from ij_ingest import discover_source_candidates, normalize_record
from ij_orchestrator import run_until_handoff
from ij_runtime import initialize_run
from ij_source_contract import acquisition_contract
from ij_workflow import (
    discover_declared_sources,
    extract_record_claims,
)


def load_template() -> dict:
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


class WorkflowTests(unittest.TestCase):
    def test_source_discovery_separates_capability_from_permission(self) -> None:
        plan = load_template()
        plan["sources"][0]["acquisition"] = {
            "format": "oai-pmh",
            "locator": "https://example.org/oai",
            "automationAuthorized": True,
            "automationBasis": "Fixture public API policy permits this bounded read.",
            "automationCheckedAt": "2026-07-24T10:00:00Z",
            "adapterVersion": "1.0.0",
            "retentionPolicy": "retain-snapshot",
            "retentionBasis": "Fixture terms allow bounded local evidence snapshots.",
            "retentionDecision": "permitted",
            "retentionEvidenceLocator": "https://example.org/terms",
            "retentionCheckedAt": "2026-07-24T10:00:00Z",
            "rateLimit": {"requestsPerMinute": 30, "maxConcurrency": 1},
        }
        plan["sources"][0]["providerTerms"] = "Fixture OAI-PMH public API terms."
        discovered = discover_source_candidates(plan)
        first = next(
            item
            for item in discovered["candidates"]
            if item["sourceId"] == plan["sources"][0]["sourceId"]
        )
        self.assertTrue(first["executable"])
        self.assertFalse(discovered["implicitAuthorization"])

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
            origin_family_id="origin_catalogue",
        )
        extracted = extract_claims(
            {
                "queryArtifact": {
                    "sourceId": "src_museum",
                    "originFamilyId": "wrong-query-level-origin",
                },
                "records": [record],
            }
        )
        predicates = {claim["predicate"] for claim in extracted["claims"]}
        self.assertIn("made-of", predicates)
        self.assertIn("held-by", predicates)
        self.assertTrue(
            all(
                claim["sourceIds"] == ["src_museum"]
                for claim in extracted["claims"]
            )
        )
        self.assertTrue(
            all(
                claim["originFamilyId"] == "origin_catalogue"
                for claim in extracted["claims"]
            )
        )

    def test_compatibility_shim_delegates_to_production_functions(self) -> None:
        plan = load_template()
        self.assertEqual(
            discover_source_candidates(plan),
            discover_declared_sources(plan),
        )
        record = normalize_record(
            {"identifier": "A-2", "material": "iron"},
            source_id="src_museum",
            index=1,
            sensitivity="restricted",
            origin_family_id="origin_catalogue",
        )
        artifact = {
            "queryArtifact": {"sourceId": "src_museum"},
            "records": [record],
        }
        self.assertEqual(extract_claims(artifact), extract_record_claims(artifact))

    def test_claim_extraction_does_not_fall_back_to_query_origin_family(self) -> None:
        record = normalize_record(
            {"identifier": "A-3", "material": "iron"},
            source_id="src_museum",
            index=1,
            sensitivity="restricted",
        )
        del record["originFamilyId"]
        with self.assertRaisesRegex(ValueError, "origin-family"):
            extract_claims(
                {
                    "queryArtifact": {
                        "sourceId": "src_museum",
                        "originFamilyId": "query-origin-must-not-be-used",
                    },
                    "records": [record],
                }
            )

    def test_extract_claims_cli_uses_production_claim_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = normalize_record(
                {
                    "identifier": "A-4",
                    "material": "iron",
                    "repository": "Test Museum",
                },
                source_id="src_museum",
                index=1,
                sensitivity="restricted",
                origin_family_id="origin_catalogue",
            )
            source = root / "records.json"
            output = root / "claims.json"
            source.write_text(
                json.dumps(
                    {
                        "queryArtifact": {"sourceId": "src_museum"},
                        "records": [record],
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_DIR / "search_plan.py"),
                    "extract-claims",
                    "--input",
                    str(source),
                    "--out",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            claims = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("archaeological-claims-1.0", claims["schemaVersion"])
            self.assertTrue(
                all(
                    claim["originFamilyId"] == "origin_catalogue"
                    for claim in claims["claims"]
                )
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
                "acceptanceChecks": [{"kind": "ingest-lineage"}],
                "timeoutSeconds": 60,
                "maxAttempts": 1,
            }
            payload = '{"records":[{"identifier":"A-1","title":"Sword"}]}'
            plan["sources"][0]["acquisition"] = acquisition_contract(
                plan["sources"][0],
                locator="inputs/records.json",
                format_name="json",
                query={},
                snapshot_sha256=hashlib.sha256(payload.encode()).hexdigest(),
                retrieved_at="2026-07-24T10:00:00Z",
            )
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
                payload,
                encoding="utf-8",
            )
            result = run_until_handoff(
                run_dir,
                max_batches=10,
                batch_limit=4,
            )
            executed = [
                action_id
                for batch in result["batches"]
                for action_id in batch["executedActionIds"]
            ]
            handed_off = [
                action_id
                for batch in result["batches"]
                for action_id in batch["handoffActionIds"]
            ]
            self.assertEqual([action["actionId"]], executed)
            self.assertTrue(handed_off)
            self.assertTrue(result["next"]["recommendedBatch"])


if __name__ == "__main__":
    unittest.main()
