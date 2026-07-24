from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from ij_artifacts import plan_sha256, read_json
from ij_candidates import validate_candidate_artifact
from ij_journal import file_sha256, value_sha256
from ij_results import run_path


SHA256 = re.compile(r"[0-9a-f]{64}")
GROUND_TRUTH_KEY = re.compile(
    r"(ground.?truth|target.?coordinate|known.?site.?coordinate)",
    re.IGNORECASE,
)


def _contains_ground_truth(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (
                str(key) != "groundTruthState"
                and GROUND_TRUTH_KEY.search(str(key))
            )
            or (
                str(key) == "groundTruthState"
                and child != "withheld"
            )
            or _contains_ground_truth(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_ground_truth(child) for child in value)
    return False


def verify_candidate_freeze(
    plan: dict[str, Any],
    candidate_artifact: Path | None,
    candidate_seal: Path | None,
) -> dict[str, Any] | None:
    case = plan.get("case")
    case = case if isinstance(case, dict) else {}
    frozen = case.get("candidatesFrozen") is True
    if not frozen and candidate_artifact is None and candidate_seal is None:
        return None
    if not frozen:
        raise ValueError("candidate-dependent run requires a frozen candidate set")
    if candidate_artifact is None or candidate_seal is None:
        raise ValueError("candidate artifact and freeze seal are required")
    if not candidate_artifact.is_file() or not candidate_seal.is_file():
        raise ValueError("candidate artifact or freeze seal does not exist")
    try:
        candidates = json.loads(candidate_artifact.read_text(encoding="utf-8"))
        seal = json.loads(candidate_seal.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"candidate freeze input is invalid: {error}") from error
    if not isinstance(candidates, (dict, list)) or not isinstance(seal, dict):
        raise ValueError("candidate artifact and freeze seal have invalid roots")
    if _contains_ground_truth(candidates):
        raise ValueError("candidate artifact contains ground-truth-like fields")
    validate_candidate_artifact(plan, candidates)
    artifact_hash = file_sha256(candidate_artifact)
    expected = case.get("candidateArtifactSha256")
    if not isinstance(expected, str) or artifact_hash != expected:
        raise ValueError("candidate artifact does not match the frozen plan hash")
    if seal.get("schemaVersion") != "candidate-freeze-seal-1.0":
        raise ValueError("candidate freeze seal version is unsupported")
    if seal.get("candidateArtifactSha256") != artifact_hash:
        raise ValueError("candidate freeze seal has a stale artifact hash")
    if seal.get("candidateCanonicalSha256") != value_sha256(candidates):
        raise ValueError("candidate freeze seal has a stale canonical hash")
    if seal.get("groundTruthKeyScan") != "passed":
        raise ValueError("candidate freeze seal lacks a passed lineage scan")
    if seal.get("targetLabelsState") != case.get("targetLabelsState"):
        raise ValueError("candidate freeze seal target-label state is stale")
    if seal.get("frozenPlanSha256") != plan_sha256(plan):
        raise ValueError("candidate freeze seal does not match the frozen plan")
    source_plan = copy.deepcopy(plan)
    source_case = source_plan["case"]
    source_case["candidatesFrozen"] = False
    source_case.pop("candidateArtifactSha256", None)
    if seal.get("sourcePlanSha256") != plan_sha256(source_plan):
        raise ValueError("candidate freeze seal does not match the source plan")
    return {
        "artifactPath": candidate_artifact,
        "sealPath": candidate_seal,
        "artifactSha256": artifact_hash,
        "sealSha256": file_sha256(candidate_seal),
    }


def verify_run_candidate_freeze(
    plan: dict[str, Any],
    run_dir: Path,
    run_payload: dict[str, Any],
) -> None:
    freeze = run_payload.get("candidateFreeze")
    frozen = isinstance(plan.get("case"), dict) and plan["case"].get(
        "candidatesFrozen"
    ) is True
    if not frozen:
        if freeze is not None:
            raise ValueError("unfrozen run contains unexpected candidate evidence")
        return
    if not isinstance(freeze, dict):
        raise ValueError("frozen run lacks retained candidate evidence")
    artifact = run_path(run_dir, str(freeze.get("artifactPath", "")))
    seal = run_path(run_dir, str(freeze.get("sealPath", "")))
    verified = verify_candidate_freeze(plan, artifact, seal)
    if (
        verified is None
        or verified["artifactSha256"] != freeze.get("artifactSha256")
        or verified["sealSha256"] != freeze.get("sealSha256")
    ):
        raise ValueError("retained candidate evidence does not match the run journal")


def normalized_artifact_errors(
    artifact: dict[str, Any],
    known_sources: set[str],
    result_ref: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if artifact.get("schemaVersion") != "archaeological-find-records-1.0":
        errors.append("unsupported normalized artifact schema")
    query = artifact.get("queryArtifact")
    if not isinstance(query, dict):
        return errors + ["normalized artifact lacks queryArtifact"]
    source_id = query.get("sourceId")
    if source_id not in known_sources:
        errors.append("normalized artifact references an unknown source")
    raw_hash = query.get("rawArtifactSha256")
    if not isinstance(raw_hash, str) or not SHA256.fullmatch(raw_hash):
        errors.append("normalized artifact lacks a valid raw snapshot hash")
    attachment_hashes = {
        attachment.get("sha256")
        for attachment in result_ref.get("attachments", [])
        if isinstance(attachment, dict)
    }
    if raw_hash not in attachment_hashes:
        errors.append("raw snapshot is not a sealed result attachment")
    records = artifact.get("records")
    if not isinstance(records, list):
        return errors + ["normalized artifact records must be an array"]
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"normalized record {index} is not an object")
            continue
        record_id = record.get("recordId")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"normalized record {index} lacks recordId")
        elif record_id in seen:
            errors.append(f"normalized recordId is duplicated: {record_id}")
        else:
            seen.add(record_id)
        if record.get("sourceId") != source_id:
            errors.append(f"normalized record {index} has inconsistent sourceId")
        if not isinstance(record.get("originFamilyId"), str):
            errors.append(f"normalized record {index} lacks originFamilyId")
        record_hash = record.get("rawRecordSha256")
        if not isinstance(record_hash, str) or not SHA256.fullmatch(record_hash):
            errors.append(f"normalized record {index} lacks rawRecordSha256")
        if record.get("normalizationVersion") != query.get("normalizationVersion"):
            errors.append(f"normalized record {index} has a version mismatch")
    if query.get("resultCount") != len(records):
        errors.append("query resultCount does not match normalized records")
    return errors


def sealed_reconciliation_artifacts(
    run_dir: Path,
    plan: dict[str, Any],
    state: dict[str, Any],
    action: dict[str, Any],
    paths: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prerequisite_ids = set(action.get("prerequisites", []))
    if not prerequisite_ids:
        raise ValueError("reconciliation requires completed ingestion prerequisites")
    eligible: dict[str, dict[str, Any]] = {}
    for prerequisite_id in prerequisite_ids:
        prerequisite = state["actions"].get(prerequisite_id)
        if not prerequisite or prerequisite.get("status") != "completed":
            raise ValueError(f"reconciliation prerequisite is not complete: {prerequisite_id}")
        for result_ref in prerequisite.get("resultRefs", []):
            if isinstance(result_ref, dict) and isinstance(result_ref.get("path"), str):
                eligible[result_ref["path"]] = result_ref
    if len(paths) != len(set(paths)):
        raise ValueError("reconciliation artifact paths must be unique")
    if any(path not in eligible for path in paths):
        raise ValueError("reconciliation inputs must be sealed prerequisite results")
    known_sources = {
        source.get("sourceId")
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    declared_sources = {
        source_id for source_id in action.get("sourceIds", []) if isinstance(source_id, str)
    }
    artifacts: list[dict[str, Any]] = []
    refs: list[dict[str, Any]] = []
    for relative in paths:
        ref = eligible[relative]
        artifact = read_json(run_path(run_dir, relative))
        errors = normalized_artifact_errors(artifact, known_sources, ref)
        source_id = artifact.get("queryArtifact", {}).get("sourceId")
        if source_id not in declared_sources:
            errors.append("normalized source is not declared by the reconciliation action")
        if errors:
            raise ValueError("; ".join(errors))
        artifacts.append(artifact)
        refs.append(ref)
    return artifacts, refs


def deterministic_acceptance_evidence(
    action: dict[str, Any],
    facts: list[str],
) -> list[str]:
    criteria = action.get("execution", {}).get("acceptanceCriteria", [])
    fact_text = "; ".join(facts)
    return [
        f"machine-check criterion {index}: {fact_text}"
        for index, _ in enumerate(criteria, 1)
    ]
