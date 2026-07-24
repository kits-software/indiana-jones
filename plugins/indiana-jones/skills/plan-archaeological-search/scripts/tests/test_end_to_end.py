from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = SCRIPT_DIR.parent
LEGACY_TEMPLATE = SKILL_DIR / "assets" / "search-plan-template.json"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_frontier import build_frontier
from ij_materials import build_material_evidence_report
from ij_migrate import freeze_candidates, migrate_plan
from ij_plan import new_plan, validate_plan
from ij_probability import calibrated_probability_report
from ij_readiness import readiness_errors
from ij_reports import build_finds_report, lint_public_report
from ij_runtime import (
    complete_action,
    execute_deterministic_action,
    initialize_run,
    next_task_packet,
    resume_run,
    run_status,
    start_action,
)
from ij_journal import file_sha256
from ij_source_contract import acquisition_contract
from permission_fixture import calibration_fixture, complete_permission_fields


def _source(
    source_id: str,
    *,
    title: str,
    record_type: str,
    origin_family_id: str,
) -> dict:
    return {
        "sourceId": source_id,
        "title": title,
        "originFamilyId": origin_family_id,
        "workflowRole": "research-context",
        "targetLabelState": "none",
        "accessStage": "pre-detection",
        "accessBasis": "public",
        "sensitivity": "public",
        "recordType": record_type,
        "license": "Local public test fixture; redistribution permitted.",
    }


def _scores(*, coverage: float = 0.5, discrimination: float = 0.7) -> dict:
    return {
        "discrimination": discrimination,
        "falsification": 0.6,
        "independence": 0.8,
        "coverage": coverage,
        "compute": 0.1,
        "humanReview": 0.2,
        "delay": 0.1,
        "money": 0.0,
    }


def _execution(executor: str, inputs: dict) -> dict:
    execution = {
        "executor": executor,
        "inputs": inputs,
        "outputs": ["hash-bound evidence artifact"],
        "acceptanceCriteria": [
            "Preserve source and origin-family lineage.",
            "Record uncertainty and negative evidence.",
        ],
        "timeoutSeconds": 300,
        "maxAttempts": 2,
    }
    if executor == "ingest-source":
        execution["acceptanceChecks"] = [
            {"kind": "ingest-lineage"},
            {"kind": "ingest-bounds"},
        ]
    elif executor == "reconcile-records":
        execution["acceptanceChecks"] = [
            {"kind": "reconciliation-lineage"},
            {"kind": "reconciliation-conflicts"},
        ]
    return execution


def _action(
    action_id: str,
    *,
    label: str,
    lane: str,
    method: str,
    source_ids: list[str],
    execution: dict,
    prerequisites: list[str] | None = None,
    requires_candidates_frozen: bool = False,
    sensitive_subjects: list[str] | None = None,
) -> dict:
    return {
        "actionId": action_id,
        "actionClass": "public-desk",
        "method": method,
        "label": label,
        "lane": lane,
        "stage": "documentary-research",
        "status": "planned",
        "candidateFocused": False,
        "requiresCandidatesFrozen": requires_candidates_frozen,
        "cellIds": [],
        "hypothesisIds": ["hyp_documented_finds", "hyp_null"],
        "sourceIds": source_ids,
        "prerequisites": prerequisites or [],
        "authorization": {"required": "none", "state": "not-required"},
        "researchIntent": "known-record-research",
        "outputPrecision": "generalized",
        "sensitiveSubjects": sensitive_subjects or [],
        "scores": _scores(
            coverage=0.9 if lane == "coverage" else 0.5,
            discrimination=0.8 if lane == "discrimination" else 0.4,
        ),
        "execution": execution,
    }


def _fresh_v2_plan(museum_path: Path, register_path: Path) -> dict:
    plan = new_plan(
        "Fixture district",
        "Which swords and gold objects are documented, and what do they establish?",
        [19.0, 54.0, 19.2, 54.2],
        2,
        2,
        "historical-reconstruction",
        "public",
        "fixture-gazetteer:district",
    )
    plan["case"]["researchMode"] = "treasure-research-public"
    plan["area"]["publicDescription"] = (
        "Fixture district, generalized to the municipality level"
    )
    plan["sources"] = [
        _source(
            "src_names",
            title="Fixture place-name authority",
            record_type="official-guidance",
            origin_family_id="origin_names",
        ),
        _source(
            "src_museum",
            title="Fixture museum catalogue",
            record_type="museum-catalogue",
            origin_family_id="origin_museum",
        ),
        _source(
            "src_register",
            title="Fixture public finds register",
            record_type="finds-register",
            origin_family_id="origin_register",
        ),
    ]
    museum_locator = f"fixtures/{museum_path.name}"
    register_locator = f"fixtures/{register_path.name}"
    museum_query = {"terms": ["sword", "gold"], "scope": "fixture"}
    register_query = {"terms": ["sword"], "scope": "fixture"}
    plan["sources"][1]["acquisition"] = acquisition_contract(
        plan["sources"][1],
        locator=museum_locator,
        format_name="csv",
        query=museum_query,
        snapshot_sha256=file_sha256(museum_path),
        retrieved_at="2026-07-24T10:00:00Z",
    )
    plan["sources"][1]["spatialRestriction"] = "authority-only"
    plan["sources"][2]["acquisition"] = acquisition_contract(
        plan["sources"][2],
        locator=register_locator,
        format_name="json",
        query=register_query,
        snapshot_sha256=file_sha256(register_path),
        retrieved_at="2026-07-24T10:00:00Z",
    )
    plan["sources"][2]["spatialRestriction"] = "authority-only"
    plan["nodes"] = [
        {
            "nodeId": "hyp_documented_finds",
            "kind": "hypothesis",
            "hypothesisClass": "archaeological",
            "label": "Documented sword or gold-object records exist in the study area",
            "authority": "hypothesis",
            "sourceIds": [],
            "cellIds": [],
            "sensitivity": "restricted",
        },
        {
            "nodeId": "hyp_natural",
            "kind": "hypothesis",
            "hypothesisClass": "natural",
            "label": "Natural context or redeposition weakens the spatial association",
            "authority": "hypothesis",
            "sourceIds": [],
            "cellIds": [],
            "sensitivity": "restricted",
        },
        {
            "nodeId": "hyp_modern",
            "kind": "hypothesis",
            "hypothesisClass": "modern",
            "label": "Modern collection history explains the catalogue association",
            "authority": "hypothesis",
            "sourceIds": [],
            "cellIds": [],
            "sensitivity": "restricted",
        },
        {
            "nodeId": "hyp_processing",
            "kind": "hypothesis",
            "hypothesisClass": "processing",
            "label": "Duplicate catalogue descriptions inflate the apparent find count",
            "authority": "hypothesis",
            "sourceIds": [],
            "cellIds": [],
            "sensitivity": "restricted",
        },
        {
            "nodeId": "hyp_null",
            "kind": "hypothesis",
            "hypothesisClass": "null",
            "label": "No relevant record is present in the bounded sources",
            "authority": "hypothesis",
            "sourceIds": [],
            "cellIds": [],
            "sensitivity": "restricted",
        },
    ]
    plan["edges"] = [
        {
            "edgeId": "edge_catalogue_alternative",
            "from": "hyp_documented_finds",
            "to": "hyp_processing",
            "relation": "alternative-to",
            "authority": "hypothesis",
            "sourceIds": [],
            "rationale": "Repeated catalogue records may describe one object.",
        }
    ]
    plan["actions"] = [
        _action(
            "act_names",
            label="Resolve the fixture place and historical name variants",
            lane="discrimination",
            method="name-resolution",
            source_ids=["src_names"],
            execution=_execution(
                "codex-research",
                {"instruction": "Resolve the declared fixture place and aliases."},
            ),
        ),
        _action(
            "act_coverage",
            label="Record catalogue coverage and explicit source gaps",
            lane="coverage",
            method="source-coverage",
            source_ids=["src_museum", "src_register"],
            execution=_execution(
                "codex-research",
                {"instruction": "Record the bounded source coverage denominator."},
            ),
        ),
        _action(
            "act_ingest_museum",
            label="Ingest the bounded public sword and gold museum catalogue",
            lane="coverage",
            method="museum-catalogue-research",
            source_ids=["src_museum"],
            execution=_execution(
                "ingest-source",
                {
                    "sourceId": "src_museum",
                    "locator": museum_locator,
                    "format": "csv",
                    "maxBytes": 10_000,
                    "maxRecords": 10,
                    "query": museum_query,
                },
            ),
            sensitive_subjects=["weapon", "precious-metal"],
        ),
        _action(
            "act_ingest_register",
            label="Ingest the bounded public sword finds register",
            lane="coverage",
            method="finds-register-research",
            source_ids=["src_register"],
            execution=_execution(
                "ingest-source",
                {
                    "sourceId": "src_register",
                    "locator": register_locator,
                    "format": "json",
                    "maxBytes": 10_000,
                    "maxRecords": 10,
                    "query": register_query,
                },
            ),
            sensitive_subjects=["weapon"],
        ),
        _action(
            "act_reconcile",
            label="Reconcile sword and gold catalogue identities conservatively",
            lane="discrimination",
            method="artifact-provenance-reconciliation",
            source_ids=["src_museum", "src_register"],
            execution=_execution(
                "reconcile-records",
                {
                    "artifacts": [
                        "results/act_ingest_museum-001.json",
                        "results/act_ingest_register-001.json",
                    ]
                },
            ),
            prerequisites=["act_ingest_museum", "act_ingest_register"],
            sensitive_subjects=["weapon", "precious-metal"],
        ),
        _action(
            "act_material_review",
            label="Assess whether the finished gold object demonstrates local production",
            lane="discrimination",
            method="historical-synthesis",
            source_ids=["src_museum", "src_register"],
            execution=_execution(
                "codex-research",
                {
                    "instruction": (
                        "Separate gold-object presence from circulation, working, "
                        "and production."
                    )
                },
            ),
            prerequisites=["act_reconcile"],
            sensitive_subjects=["precious-metal"],
        ),
        _action(
            "act_public_report",
            label="Prepare an explicitly restricted sword and gold finds report",
            lane="coverage",
            method="source-coverage",
            source_ids=["src_museum", "src_register"],
            execution=_execution(
                "codex-research",
                {"instruction": "Publish only municipality-level find information."},
            ),
            prerequisites=["act_material_review"],
            requires_candidates_frozen=True,
            sensitive_subjects=["weapon", "precious-metal"],
        ),
    ]
    return plan


class AutonomousResearchEndToEndTests(unittest.TestCase):
    def test_catalogues_resume_sealed_result_and_safe_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            museum_path = root / "museum.csv"
            museum_path.write_text(
                "accessionNumber,title,objectClass,material,period,repository,"
                "findspot,context\n"
                "A-1,Medieval iron sword,Sword,iron,medieval,Fixture Museum,"
                "Exact east field,contested legacy context\n"
                "G-9,Gold pendant,Pendant,gold,medieval,Fixture Museum,"
                "Exact orchard,reported stray find\n",
                encoding="utf-8",
            )
            register_path = root / "register.json"
            register_path.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "accessionNumber": "A-1",
                                "title": "Sword",
                                "objectClass": "weapon",
                                "material": "iron",
                                "repository": "Fixture Museum",
                                "findspot": "Exact east field",
                            },
                            {
                                "title": "Iron sword",
                                "objectClass": "weapon",
                                "material": "iron",
                                "repository": "Fixture Museum",
                                "findspot": "Exact western plot",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            candidate_path = root / "candidates.json"
            candidates = {
                "schemaVersion": "candidate-set-1.0",
                "lineage": {
                    "sourceIds": ["src_names"],
                    "generationActionIds": [],
                    "groundTruthState": "withheld",
                },
                "candidates": [
                    {
                        "candidateId": "candidate_1",
                        "publicArea": "Fixture district",
                        "evidenceGrade": "hypothesis",
                    }
                ],
            }
            candidate_path.write_text(json.dumps(candidates), encoding="utf-8")

            draft = _fresh_v2_plan(museum_path, register_path)
            self.assertEqual("2.0", draft["schemaVersion"])
            self.assertTrue(validate_plan(draft).valid, validate_plan(draft).errors)
            blocked = {
                item["actionId"]: item["reasons"]
                for item in build_frontier(draft, 20)["blockedActions"]
            }
            self.assertIn("candidate list is not frozen", blocked["act_public_report"])

            plan, freeze_seal = freeze_candidates(draft, candidates, candidate_path)
            freeze_seal_path = root / "candidate-freeze-seal.json"
            freeze_seal_path.write_text(json.dumps(freeze_seal), encoding="utf-8")
            self.assertTrue(plan["case"]["candidatesFrozen"])
            self.assertEqual(
                freeze_seal["candidateArtifactSha256"],
                plan["case"]["candidateArtifactSha256"],
            )
            self.assertTrue(validate_plan(plan).valid, validate_plan(plan).errors)
            self.assertEqual([], readiness_errors(plan))

            run_dir = root / "run"
            initialize_run(
                plan,
                run_dir,
                max_actions=20,
                max_attempts=30,
                max_result_bytes=1_000_000,
                max_seconds=3600,
                candidate_artifact=candidate_path,
                candidate_seal=freeze_seal_path,
            )
            run_fixtures = run_dir / "fixtures"
            run_fixtures.mkdir()
            (run_fixtures / "museum.csv").write_text(
                museum_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            (run_fixtures / "register.json").write_text(
                register_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            museum_result = execute_deterministic_action(
                run_dir, "act_ingest_museum"
            )
            register_result = execute_deterministic_action(
                run_dir, "act_ingest_register"
            )
            museum_artifact = json.loads(
                (run_dir / museum_result["result"]["path"]).read_text(encoding="utf-8")
            )
            register_artifact = json.loads(
                (run_dir / register_result["result"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(2, museum_artifact["queryArtifact"]["resultCount"])
            self.assertEqual(10, museum_artifact["queryArtifact"]["maxRecords"])
            self.assertFalse(museum_artifact["queryArtifact"]["truncated"])
            self.assertEqual(2, register_artifact["queryArtifact"]["resultCount"])

            reconcile_result = execute_deterministic_action(
                run_dir, "act_reconcile"
            )
            reconciliation = json.loads(
                (run_dir / reconcile_result["result"]["path"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(4, reconciliation["recordCount"])
            self.assertEqual(3, reconciliation["entityCount"])
            accession_entity = next(
                entity
                for entity in reconciliation["entities"]
                if entity["identityBasis"] == "accession"
                and entity["canonicalRecord"].get("accessionNumber") == "A-1"
            )
            self.assertEqual(2, accession_entity["duplicateCount"])
            self.assertEqual(2, accession_entity["independentSourceCount"])
            similar_swords = [
                entity
                for entity in reconciliation["entities"]
                if any(
                    "sword" in title.casefold()
                    for title in (
                        [entity["canonicalRecord"].get("title", "")]
                        + entity["fieldConflicts"].get("title", [])
                    )
                )
            ]
            self.assertEqual(2, len(similar_swords))

            before_review = next_task_packet(run_dir, 20)
            self.assertNotIn(
                "act_public_report",
                {item["actionId"] for item in before_review["recommendedBatch"]},
            )
            first_attempt = start_action(run_dir, "act_material_review")
            resumed = resume_run(
                run_dir, now=first_attempt["leaseExpiresAt"] + 1
            )
            material_state = resumed["actions"]["act_material_review"]
            self.assertEqual("planned", material_state["status"])
            self.assertEqual("interrupted", material_state["attempts"][0]["status"])

            second_attempt = start_action(run_dir, "act_material_review")
            self.assertNotEqual(
                first_attempt["attemptId"], second_attempt["attemptId"]
            )
            agent_result_path = root / "agent-material-result.json"
            agent_result_path.write_text(
                json.dumps(
                    {
                        "schemaVersion": "research-result-2.0",
                        "actionId": "act_material_review",
                        "judgment": "material-presence-only",
                        "observations": [
                            {
                                "statement": (
                                    "The bounded catalogue contains a finished gold "
                                    "object, not production debris."
                                ),
                                "sourceIds": ["src_museum"],
                                "originFamilyIds": ["origin_museum"],
                            }
                        ],
                        "negativeResults": [
                            "No secure workshop, crucible, mould, or slag record was ingested."
                        ],
                        "warnings": [],
                        "errors": [],
                        "sourceSnapshotIds": [
                            "snapshot:src_museum:"
                            + museum_artifact["queryArtifact"]["rawArtifactSha256"]
                        ],
                        "normalizedRecordIds": ["src_museum:G-9"],
                        "methodVersion": "historical-synthesis-1.0",
                        "adapterVersion": "codex-research-1.0",
                        "resultSensitivity": "restricted",
                        "disclosureDecision": "public",
                        "acceptanceEvidence": [
                            "The sealed result preserves declared source lineage.",
                            "The sealed result records the missing production evidence.",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = complete_action(
                run_dir,
                "act_material_review",
                second_attempt["attemptId"],
                result_path=agent_result_path,
                summary="Finished gold object supports presence, not local production.",
                source_ids=["src_museum"],
                acceptance_evidence=[
                    "The sealed result preserves declared source lineage.",
                    "The sealed result records the missing production evidence.",
                ],
            )
            self.assertEqual(
                "completed",
                completed["run"]["actions"]["act_material_review"]["status"],
            )
            self.assertEqual(64, len(completed["result"]["sha256"]))
            self.assertEqual(
                completed["result"],
                completed["run"]["actions"]["act_material_review"]["resultRefs"][0],
            )
            after_review = next_task_packet(run_dir, 20)
            self.assertIn(
                "act_public_report",
                {item["actionId"] for item in after_review["recommendedBatch"]},
            )
            audited = run_status(run_dir)
            self.assertEqual(
                "completed", audited["actions"]["act_material_review"]["status"]
            )
            self.assertGreaterEqual(audited["eventCount"], 8)

            gold_record = next(
                record
                for record in museum_artifact["records"]
                if "gold" in record.get("material", "").casefold()
            )
            material_report = build_material_evidence_report([gold_record], "gold")
            self.assertEqual("material-presence-only", material_report["conclusion"])
            self.assertNotIn("production-supported", material_report["conclusion"])

            public_report = build_finds_report(
                reconciliation,
                area_description=plan["area"]["publicDescription"],
                public=True,
            )
            serialized_public = json.dumps(public_report, sort_keys=True)
            self.assertEqual("public", public_report["disclosure"])
            self.assertEqual(3, len(public_report["finds"]))
            for sensitive_text in ("Exact east field", "Exact orchard", "Exact western plot"):
                self.assertNotIn(sensitive_text, serialized_public)
            for item in public_report["finds"]:
                self.assertNotIn("findspot", item["record"])
                self.assertEqual(
                    "withheld-by-explicit-restriction",
                    item["record"].get("spatialEvidenceStatus"),
                )
            lint_public_report(public_report)

    def test_restricted_exact_probability_and_public_spatial_evidence(self) -> None:
        permission_fields = complete_permission_fields()
        result = calibrated_probability_report(
            calibration_fixture(),
            case={
                "researchMode": "treasure-research-restricted",
                "disclosure": "restricted",
                **permission_fields,
            },
            exact_high_risk_target=True,
        )
        self.assertEqual("restricted", result["disclosure"])
        self.assertEqual(0.31, result["estimatedProbability"])
        self.assertIn("not permission for physical recovery", result["warning"])

        spatial_cases = [
            {"attachment": {"coordinates": [19.12345, 54.12345]}},
            {"caption": "Exact candidate is at 19.12345, 54.12345"},
            {"finds": [{"findspot": {"description": "Exact east field"}}]},
        ]
        for spatial_evidence in spatial_cases:
            with self.subTest(spatial_evidence=spatial_evidence):
                lint_public_report(spatial_evidence)

    def test_legacy_completion_is_quarantined_and_freeze_rejects_ground_truth(
        self,
    ) -> None:
        legacy = json.loads(LEGACY_TEMPLATE.read_text(encoding="utf-8"))
        legacy["schemaVersion"] = "1.0"
        legacy["actions"][0]["status"] = "completed"
        legacy["actions"][0]["resultRefs"] = [
            {"path": "legacy-result.json", "sha256": "a" * 64}
        ]
        original = copy.deepcopy(legacy)
        migrated, manifest = migrate_plan(legacy)
        self.assertEqual(original, legacy)
        self.assertEqual("2.0", migrated["schemaVersion"])
        self.assertEqual(
            "completed-unverified", migrated["actions"][0]["status"]
        )
        self.assertNotIn("resultRefs", migrated["actions"][0])
        self.assertTrue(any("legacy completion quarantined" in warning for warning in manifest["warnings"]))
        blocked = {
            item["actionId"]: item["reasons"]
            for item in build_frontier(migrated, 20)["blockedActions"]
        }
        self.assertTrue(
            any(
                "act_name_concordance" in reason
                for reason in blocked["act_map_regression"]
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            candidate_path = Path(temp_dir) / "unsafe-candidates.json"
            unsafe_candidates = {
                "candidates": [
                    {
                        "candidateId": "candidate_1",
                        "knownSiteCoordinate": [19.12345, 54.12345],
                    }
                ]
            }
            candidate_path.write_text(json.dumps(unsafe_candidates), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ground-truth-like"):
                freeze_candidates(migrated, unsafe_candidates, candidate_path)

if __name__ == "__main__":
    unittest.main()
