from __future__ import annotations

import re
from typing import Any

from ij_frontier import build_frontier


def readiness_errors(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["research-ready plan must be an object"]
    raw_sources = plan.get("sources")
    raw_nodes = plan.get("nodes")
    raw_actions = plan.get("actions")
    sources = raw_sources if isinstance(raw_sources, list) else []
    nodes = raw_nodes if isinstance(raw_nodes, list) else []
    actions = raw_actions if isinstance(raw_actions, list) else []
    if not sources:
        errors.append("research-ready plan requires at least one source")
    if not nodes:
        errors.append("research-ready plan requires evidence and hypothesis nodes")
    if not actions:
        errors.append("research-ready plan requires at least one action")

    hypotheses = [
        node for node in nodes if isinstance(node, dict) and node.get("kind") == "hypothesis"
    ]
    classes = {node.get("hypothesisClass") for node in hypotheses}
    if "archaeological" not in classes:
        errors.append("research-ready plan requires an archaeological hypothesis")
    if not classes.intersection({"natural", "modern"}):
        errors.append("research-ready plan requires a natural or modern alternative")
    if "processing" not in classes:
        errors.append("research-ready plan requires a processing alternative")
    if "null" not in classes:
        errors.append("research-ready plan requires a null hypothesis")

    lanes = {
        action.get("lane")
        for action in actions
        if isinstance(action, dict) and action.get("status") != "rejected"
    }
    for lane in ("discrimination", "coverage"):
        if lane not in lanes:
            errors.append(f"research-ready plan requires a {lane} action")
    if any(
        isinstance(action, dict) and action.get("candidateFocused") is True
        for action in actions
    ):
        if "negative-control" not in lanes:
            errors.append("candidate-focused plan requires a negative-control action")
    methods = {action.get("method") for action in actions if isinstance(action, dict)}
    if "name-resolution" not in methods:
        errors.append("research-ready place plan requires a name-resolution action")
    if "source-coverage" not in methods:
        errors.append("research-ready place plan requires a source-coverage action")

    case = plan.get("case")
    case = case if isinstance(case, dict) else {}
    if case.get("candidatesFrozen") is True:
        digest = case.get("candidateArtifactSha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append("frozen candidates require candidateArtifactSha256")
    area = plan.get("area")
    if not isinstance(area, dict) or not area.get("publicDescription"):
        errors.append("research-ready plan requires a safe public area description")
    structurally_rankable = (
        isinstance(raw_actions, list)
        and all(isinstance(action, dict) for action in raw_actions)
        and isinstance(plan.get("policy"), dict)
        and isinstance(plan.get("case"), dict)
    )
    if actions and structurally_rankable and not build_frontier(plan, 1).get(
        "recommendedBatch"
    ):
        errors.append("research-ready plan requires at least one executable action")
    return errors
