from __future__ import annotations

import copy
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from ij_artifacts import plan_sha256


def _six(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _weighted_mean(values: dict[str, Any], weights: dict[str, Any]) -> float:
    numerator = 0.0
    denominator = 0.0
    for key, weight in weights.items():
        numerator += float(values.get(key, 0.0)) * float(weight)
        denominator += float(weight)
    return numerator / denominator if denominator else 0.0


def score_action(action: dict[str, Any], policy: dict[str, Any]) -> dict[str, float]:
    scores = action["scores"]
    weights = policy["weights"]
    benefit = (
        float(weights["discrimination"]) * float(scores["discrimination"])
        + float(weights["falsification"]) * float(scores["falsification"])
        + float(weights["independence"]) * float(scores["independence"])
        + float(weights["coverage"]) * float(scores["coverage"])
    )
    burden = _weighted_mean(scores, policy["burdenWeights"])
    priority = benefit / (1.0 + burden)
    return {
        "discrimination": _six(float(scores["discrimination"])),
        "falsification": _six(float(scores["falsification"])),
        "independence": _six(float(scores["independence"])),
        "coverage": _six(float(scores["coverage"])),
        "benefit": _six(benefit),
        "burden": _six(burden),
        "priority": _six(priority),
    }


def _gate_reasons(
    action: dict[str, Any],
    action_map: dict[str, dict[str, Any]],
    candidates_frozen: bool,
    candidate_artifact_sha256: Any,
) -> list[str]:
    reasons: list[str] = []
    if action.get("status") != "planned":
        reasons.append(f"status is {action.get('status')}")
    incomplete: list[str] = []
    for action_id in action.get("prerequisites", []):
        prerequisite = action_map[action_id]
        if prerequisite.get("status") != "completed" or not prerequisite.get(
            "resultRefs"
        ) or prerequisite.get("_runtimeEvidenceVerified") is not True:
            incomplete.append(action_id)
    if incomplete:
        reasons.append("incomplete prerequisites: " + ", ".join(sorted(incomplete)))
    authorization = action.get("authorization", {})
    required = authorization.get("required")
    state = authorization.get("state")
    if required == "none":
        if state not in {"not-required", "confirmed"}:
            reasons.append("public action is not authorized for execution")
    elif state != "confirmed":
        reasons.append(f"{required} authorization is {state}")
    if action.get("requiresCandidatesFrozen") is True:
        if not candidates_frozen:
            reasons.append("candidate list is not frozen")
        if not isinstance(candidate_artifact_sha256, str) or not re.fullmatch(
            r"[0-9a-f]{64}", candidate_artifact_sha256
        ):
            reasons.append("candidate freeze artifact is not hash-bound")
    return reasons


def _sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -float(item["score"]["priority"]),
        str(item.get("cellIds", [""])[0] if item.get("cellIds") else ""),
        str(item["actionId"]),
    )


def _schedule(
    ready: list[dict[str, Any]],
    lane_pattern: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    available = {item["actionId"]: item for item in ready}
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    pattern_index = 0

    def candidates(lane: str | None = None) -> list[dict[str, Any]]:
        values = [
            item
            for action_id, item in available.items()
            if action_id not in selected_ids and (lane is None or item["lane"] == lane)
        ]
        return sorted(values, key=_sort_key)

    while len(selected) < limit:
        lane = lane_pattern[pattern_index % len(lane_pattern)]
        pattern_index += 1
        options = candidates(lane)
        if not options:
            options = candidates()
        if not options:
            break
        choice = options[0]
        pair_id = choice.get("pairedControlActionId")
        if (
            choice.get("candidateFocused") is True
            and not choice.get("pairedControlCompleted")
            and pair_id not in selected_ids
        ):
            pair = available.get(pair_id)
            if pair is None or len(selected) + 2 > limit:
                selected_ids.add(choice["actionId"])
                continue
            selected.append(choice)
            selected_ids.add(choice["actionId"])
            selected.append(pair)
            selected_ids.add(pair_id)
            continue
        selected.append(choice)
        selected_ids.add(choice["actionId"])
    return selected


def build_frontier(plan: dict[str, Any], limit: int) -> dict[str, Any]:
    action_map = {action["actionId"]: action for action in plan["actions"]}
    ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    policy = plan["policy"]
    candidates_frozen = bool(plan["case"].get("candidatesFrozen"))
    candidate_artifact_sha256 = plan["case"].get("candidateArtifactSha256")

    preliminary_reasons = {
        action_id: _gate_reasons(
            action,
            action_map,
            candidates_frozen,
            candidate_artifact_sha256,
        )
        for action_id, action in action_map.items()
    }
    for action_id in sorted(action_map):
        action = action_map[action_id]
        reasons = list(preliminary_reasons[action_id])
        if action.get("candidateFocused") is True:
            pair_id = action.get("pairedControlActionId")
            pair = action_map.get(pair_id)
            pair_reasons = preliminary_reasons.get(pair_id, ["paired control is missing"])
            if pair is None or (pair.get("status") != "completed" and pair_reasons):
                reasons.append("paired control is not ready")
        if reasons:
            blocked.append({"actionId": action_id, "reasons": reasons})
            continue
        item = {
            "actionId": action_id,
            "label": action.get("label", action_id),
            "lane": action["lane"],
            "cellIds": sorted(action.get("cellIds", [])),
            "hypothesisIds": sorted(action.get("hypothesisIds", [])),
            "candidateFocused": bool(action.get("candidateFocused")),
            "pairedControlActionId": action.get("pairedControlActionId"),
            "pairedControlCompleted": bool(
                action_map.get(action.get("pairedControlActionId"), {}).get("status")
                == "completed"
                and action_map.get(action.get("pairedControlActionId"), {}).get(
                    "resultRefs"
                )
                and action_map.get(action.get("pairedControlActionId"), {}).get(
                    "_runtimeEvidenceVerified"
                )
                is True
            ),
            "method": action.get("method"),
            "actionClass": action.get("actionClass"),
            "stage": action.get("stage"),
            "sourceIds": sorted(action.get("sourceIds", [])),
            "authorization": copy.deepcopy(action.get("authorization", {})),
            "execution": copy.deepcopy(action.get("execution")),
            "score": score_action(action, policy),
        }
        ready.append(item)

    selected = _schedule(ready, policy["lanePattern"], limit)
    selected_ids = {item["actionId"] for item in selected}
    return {
        "schemaVersion": "1.0",
        "sourcePlanSha256": plan_sha256(plan),
        "scoreVersion": policy["scoreVersion"],
        "scoreMeaning": "deterministic task-scheduling priority, not site probability",
        "weights": policy["weights"],
        "burdenWeights": policy["burdenWeights"],
        "lanePattern": policy["lanePattern"],
        "recommendedBatch": selected,
        "readyUnscheduled": sorted(
            [item for item in ready if item["actionId"] not in selected_ids],
            key=_sort_key,
        ),
        "blockedActions": blocked,
    }
