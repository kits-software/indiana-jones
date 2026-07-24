from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from ij_artifacts import plan_sha256
from ij_candidates import validate_candidate_artifact
from ij_journal import file_sha256, value_sha256
from ij_safety import SENSITIVITIES


GROUND_TRUTH_KEY = re.compile(
    r"(ground.?truth|target.?coordinate|known.?site.?coordinate)",
    re.IGNORECASE,
)


def _has_ground_truth_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (
                str(key) != "groundTruthState"
                and GROUND_TRUTH_KEY.search(str(key))
            )
            or (
                str(key) == "groundTruthState"
                and nested != "withheld"
            )
            or _has_ground_truth_key(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_has_ground_truth_key(item) for item in value)
    return False


def _execution_default(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "executor": "codex-research",
        "inputs": {
            "instruction": action.get("label", action.get("actionId", "research action")),
            "sourceIds": copy.deepcopy(action.get("sourceIds", [])),
        },
        "outputs": ["evidence-bound research result"],
        "acceptanceCriteria": [
            "Cite observations to declared sources and origin families.",
            "Record negative evidence, alternatives, and unresolved uncertainty.",
        ],
        "timeoutSeconds": 3600,
        "maxAttempts": 2,
    }


def migrate_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source_hash = plan_sha256(plan)
    if plan.get("schemaVersion") == "2.0":
        migrated = copy.deepcopy(plan)
        return migrated, {
            "schemaVersion": "archaeological-plan-migration-1.0",
            "sourcePlanSha256": source_hash,
            "migratedPlanSha256": source_hash,
            "changes": [],
            "warnings": ["Plan was already schema 2.0; migration was idempotent."],
        }
    if plan.get("schemaVersion") != "1.0":
        raise ValueError("only schema 1.0 or 2.0 plans can be migrated")
    migrated = copy.deepcopy(plan)
    changes: list[str] = ["schemaVersion: 1.0 -> 2.0"]
    warnings: list[str] = []
    migrated["schemaVersion"] = "2.0"
    case = migrated.setdefault("case", {})
    case.setdefault("researchMode", "landscape-research")
    changes.append("case.researchMode defaulted to landscape-research")
    case.setdefault("permissionBundle", {})
    changes.append("case.permissionBundle initialized empty")
    for collection_name, collection in (
        ("sources", migrated.get("sources", [])),
        ("nodes", migrated.get("nodes", [])),
        ("grid.cells", migrated.get("grid", {}).get("cells", [])),
    ):
        if not isinstance(collection, list):
            continue
        for index, item in enumerate(collection):
            if not isinstance(item, dict):
                continue
            sensitivity = item.get("sensitivity")
            if sensitivity not in SENSITIVITIES:
                item["sensitivity"] = "restricted"
                changes.append(
                    f"{collection_name}[{index}].sensitivity defaulted to restricted"
                )
    for action in migrated.get("actions", []):
        if not isinstance(action, dict):
            continue
        if action.get("status") == "completed":
            action["status"] = "completed-unverified"
            action.pop("resultNodeIds", None)
            action.pop("resultRefs", None)
            warnings.append(
                f"{action.get('actionId')}: legacy completion quarantined until resealed"
            )
        if not isinstance(action.get("execution"), dict):
            action["execution"] = _execution_default(action)
            changes.append(f"{action.get('actionId')}: execution contract added")
    manifest = {
        "schemaVersion": "archaeological-plan-migration-1.0",
        "sourcePlanSha256": source_hash,
        "migratedPlanSha256": plan_sha256(migrated),
        "changes": changes,
        "warnings": warnings,
    }
    return migrated, manifest


def freeze_candidates(
    plan: dict[str, Any],
    candidates: Any,
    candidate_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(candidates, (dict, list)):
        raise ValueError("candidate artifact must contain a JSON object or array")
    if _has_ground_truth_key(candidates):
        raise ValueError("candidate artifact contains ground-truth-like fields")
    validate_candidate_artifact(plan, candidates)
    try:
        persisted = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"candidate artifact file is invalid: {error}") from error
    if persisted != candidates:
        raise ValueError("candidate artifact value does not match its persisted file")
    frozen = copy.deepcopy(plan)
    case = frozen.get("case")
    if not isinstance(case, dict):
        raise ValueError("plan.case must be an object")
    artifact_hash = file_sha256(candidate_path)
    case["candidatesFrozen"] = True
    case["candidateArtifactSha256"] = artifact_hash
    seal = {
        "schemaVersion": "candidate-freeze-seal-1.0",
        "sourcePlanSha256": plan_sha256(plan),
        "frozenPlanSha256": plan_sha256(frozen),
        "candidateArtifactSha256": artifact_hash,
        "candidateCanonicalSha256": value_sha256(candidates),
        "targetLabelsState": case.get("targetLabelsState"),
        "groundTruthKeyScan": "passed",
    }
    return frozen, seal


def verify_candidate_freeze(
    plan: dict[str, Any],
    candidate_artifact: Path | None,
    candidate_seal: Path | None,
) -> None:
    case = plan.get("case", {})
    frozen = isinstance(case, dict) and case.get("candidatesFrozen") is True
    if not frozen:
        if candidate_artifact is not None or candidate_seal is not None:
            raise ValueError("candidate evidence was supplied for an unfrozen plan")
        return
    if candidate_artifact is None or candidate_seal is None:
        raise ValueError("frozen candidates require both artifact and freeze seal")
    candidates = json.loads(candidate_artifact.read_text(encoding="utf-8"))
    seal = json.loads(candidate_seal.read_text(encoding="utf-8"))
    if not isinstance(candidates, (dict, list)) or _has_ground_truth_key(candidates):
        raise ValueError("candidate artifact failed the ground-truth safety scan")
    if not isinstance(seal, dict) or seal.get("schemaVersion") != "candidate-freeze-seal-1.0":
        raise ValueError("candidate freeze seal is invalid")
    artifact_hash = file_sha256(candidate_artifact)
    expected = case.get("candidateArtifactSha256")
    if (
        artifact_hash != expected
        or seal.get("frozenPlanSha256") != plan_sha256(plan)
        or seal.get("candidateArtifactSha256") != expected
        or seal.get("candidateCanonicalSha256") != value_sha256(candidates)
        or seal.get("groundTruthKeyScan") != "passed"
        or seal.get("targetLabelsState") != case.get("targetLabelsState")
    ):
        raise ValueError("candidate artifact or freeze seal is stale")
