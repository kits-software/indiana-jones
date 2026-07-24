from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qsl, unquote, urlparse

from ij_permissions import permission_instrument_ids, restricted_permission_errors
from ij_targeting import (
    PROHIBITED_DIRECTIVE,
    SENSITIVE_SUBJECTS,
    object_risk_errors,
)

SOURCE_ROLES = {
    "analysis",
    "negative-control",
    "research-context",
    "corroboration",
    "ground-truth",
    "manual-reference",
}
ACCESS_BASES = {
    "public",
    "user-provided",
    "licensed",
    "authenticated",
    "authority-controlled",
    "community-controlled",
}
SENSITIVITIES = {
    "public",
    "restricted",
    "non-public",
    "vulnerable",
    "sacred",
    "burial",
}
RECORD_TYPES = {
    "measurement",
    "official-guidance",
    "official-inventory",
    "scholarly-publication",
    "historical-document",
    "historical-map",
    "modern-map",
    "community-knowledge",
    "lead",
    "excavation-record",
    "museum-catalogue",
    "finds-register",
    "accession-record",
    "laboratory-analysis",
    "custody-record",
    "historical-register",
    "collection-catalogue",
}
METHOD_CLASSES = {
    "name-resolution": {"public-desk", "authenticated-read"},
    "source-coverage": {"public-desk", "licensed-computation"},
    "archive-research": {"public-desk", "authenticated-read"},
    "map-regression": {"licensed-computation"},
    "historical-terrain-reconstruction": {"licensed-computation"},
    "terrain-analysis": {"licensed-computation"},
    "optical-analysis": {"licensed-computation"},
    "sar-analysis": {"licensed-computation"},
    "lidar-analysis": {"licensed-computation"},
    "photogrammetry-review": {"licensed-computation"},
    "modern-context-review": {"public-desk", "licensed-computation"},
    "negative-control": {"public-desk", "licensed-computation"},
    "heritage-inventory-corroboration": {"specialist-handoff"},
    "authenticated-source-review": {"authenticated-read"},
    "community-consultation": {"community-consultation"},
    "non-invasive-field-survey": {"field-non-invasive"},
    "specialist-review": {"specialist-handoff"},
    "museum-catalogue-research": {"public-desk", "authenticated-read"},
    "finds-register-research": {"public-desk", "authenticated-read"},
    "artifact-provenance-reconciliation": {"public-desk", "authenticated-read"},
    "laboratory-analysis-review": {
        "public-desk",
        "authenticated-read",
        "specialist-handoff",
    },
    "custody-history-research": {"public-desk", "authenticated-read"},
    "historical-synthesis": {"public-desk", "authenticated-read"},
    "excavation-assemblage-synthesis": {"public-desk", "authenticated-read"},
    "sensitive-findspot-assessment": {
        "public-desk",
        "licensed-computation",
        "specialist-handoff",
    },
}
ACTION_FIELDS = {
    "actionId",
    "actionClass",
    "method",
    "label",
    "instructions",
    "rationale",
    "lane",
    "stage",
    "status",
    "candidateFocused",
    "comparisonFamilyId",
    "pairedControlActionId",
    "requiresCandidatesFrozen",
    "cellIds",
    "hypothesisIds",
    "sourceIds",
    "prerequisites",
    "authorization",
    "platform",
    "possibleOutcomes",
    "predictions",
    "scores",
    "resultNodeIds",
    "resultRefs",
    "researchIntent",
    "outputPrecision",
    "sensitiveSubjects",
    "objectRiskClassification",
    "execution",
}
INBOUND_PROVENANCE_RELATIONS = {
    "reports",
    "measures",
    "derived-from",
    "supports",
    "corroborates",
    "motivates",
    "implies-process",
    "may-produce",
    "observable-as",
}
SECRET_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "credential",
    "key",
    "password",
    "secret",
    "signature",
    "sig",
    "token",
}
MAX_NESTING_DEPTH = 64
MAX_INSPECTED_VALUES = 100_000
RESEARCH_INTENTS = {
    "known-record-research",
    "prospective-landscape-research",
    "professional-custody-support",
    "treasure-research-public",
    "treasure-research-restricted",
}
OUTPUT_PRECISIONS = {
    "non-spatial",
    "generalized",
    "restricted-exact",
    "public-exact",
}


def _choice(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def safe_url_problem(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "must use an absolute http(s) URL"
    if parsed.username or parsed.password:
        return "must not contain URL credentials"
    for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
        lowered_key = key.lower()
        if lowered_key in SECRET_KEYS or re.search(
            r"(?:^|[-_])(api[-_]?key|access[-_]?token|authorization|credential|"
            r"password|secret|signature|sig|token|key)$",
            lowered_key,
        ):
            return f"must not include secret-bearing query key {key!r}"
    lowered = url.lower()
    for _ in range(3):
        if re.search(
            r"(bearer|password|credential|secret|signature|api[_-]?key|"
            r"access[_-]?token|authorization)\s*[:=]",
            lowered,
        ):
            return "appears to contain a credential"
        decoded = unquote(lowered)
        if decoded == lowered:
            break
        lowered = decoded
    return None


def safe_locator_problem(locator: Any) -> str | None:
    if not isinstance(locator, str) or not locator:
        return "must be a non-empty string"
    if locator.startswith(("http://", "https://")):
        return safe_url_problem(locator)
    lowered = locator.lower()
    for _ in range(3):
        if re.search(
            r"(password|credential|secret|signature|api[_-]?key|access[_-]?token|"
            r"authorization|bearer)\s*[:=]",
            lowered,
        ):
            return "appears to contain a credential"
        decoded = unquote(lowered)
        if decoded == lowered:
            break
        lowered = decoded
    return None


def locator_errors(value: Any, path: str = "plan") -> list[str]:
    errors: list[str] = []
    stack: list[tuple[Any, str, int]] = [(value, path, 0)]
    inspected = 0
    while stack:
        current, current_path, depth = stack.pop()
        inspected += 1
        if inspected > MAX_INSPECTED_VALUES:
            errors.append(
                f"{path} exceeds the maximum inspected value count "
                f"{MAX_INSPECTED_VALUES}"
            )
            break
        if depth > MAX_NESTING_DEPTH:
            errors.append(
                f"{current_path} exceeds maximum nesting depth "
                f"{MAX_NESTING_DEPTH}"
            )
            continue
        if isinstance(current, dict):
            for key, child in reversed(list(current.items())):
                child_path = f"{current_path}.{key}"
                lowered_key = str(key).lower()
                if isinstance(child, str) and (
                    lowered_key.endswith("url") or "locator" in lowered_key
                ):
                    problem = safe_locator_problem(child)
                    if problem:
                        errors.append(f"{child_path} {problem}")
                else:
                    stack.append((child, child_path, depth + 1))
        elif isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append(
                    (current[index], f"{current_path}[{index}]", depth + 1)
                )
    return errors


def validate_source_safety(source: dict[str, Any]) -> list[str]:
    source_id = source.get("sourceId", "<unknown>")
    errors: list[str] = []
    if not _choice(source.get("workflowRole"), SOURCE_ROLES):
        errors.append(f"{source_id}: invalid workflowRole")
    if not _choice(source.get("targetLabelState"), {"none", "withheld", "visible"}):
        errors.append(f"{source_id}: invalid targetLabelState")
    if not _choice(
        source.get("accessStage"),
        {"pre-detection", "post-freeze", "post-unblinding"},
    ):
        errors.append(f"{source_id}: invalid accessStage")
    if not _choice(source.get("accessBasis"), ACCESS_BASES):
        errors.append(f"{source_id}: invalid accessBasis")
    if not _choice(source.get("sensitivity"), SENSITIVITIES):
        errors.append(f"{source_id}: invalid sensitivity")
    if not _choice(source.get("recordType"), RECORD_TYPES):
        errors.append(f"{source_id}: invalid recordType")
    if not isinstance(source.get("license"), str) or not source.get("license"):
        errors.append(f"{source_id}: license or rights statement is required")
    url = source.get("url")
    if url is not None:
        if not isinstance(url, str):
            errors.append(f"{source_id}: url must be a string")
        else:
            problem = safe_url_problem(url)
            if problem:
                errors.append(f"{source_id}: url {problem}")
    return errors


def _provenance_sources(plan: dict[str, Any], action: dict[str, Any]) -> set[str]:
    action_sources = action.get("sourceIds")
    sources = {
        source_id
        for source_id in (action_sources if isinstance(action_sources, list) else [])
        if isinstance(source_id, str)
    }
    raw_nodes = plan.get("nodes")
    nodes = {
        node.get("nodeId"): node
        for node in (raw_nodes if isinstance(raw_nodes, list) else [])
        if isinstance(node, dict) and node.get("nodeId")
    }
    hypotheses = action.get("hypothesisIds")
    queue = [
        node_id
        for node_id in (hypotheses if isinstance(hypotheses, list) else [])
        if isinstance(node_id, str)
    ]
    raw_edges = plan.get("edges")
    edges = [
        edge
        for edge in (raw_edges if isinstance(raw_edges, list) else [])
        if isinstance(edge, dict)
    ]
    seen: set[str] = set()
    while queue:
        node_id = queue.pop()
        if node_id in seen or node_id not in nodes:
            continue
        seen.add(node_id)
        linked_sources = nodes[node_id].get("sourceIds")
        if isinstance(linked_sources, list):
            sources.update(
                source_id for source_id in linked_sources if isinstance(source_id, str)
            )
        for edge in edges:
            if (
                edge.get("to") == node_id
                and edge.get("relation") in INBOUND_PROVENANCE_RELATIONS
            ):
                edge_sources = edge.get("sourceIds")
                if isinstance(edge_sources, list):
                    sources.update(
                        source_id
                        for source_id in edge_sources
                        if isinstance(source_id, str)
                    )
                if isinstance(edge.get("from"), str):
                    queue.append(edge["from"])
    return sources


def _action_text(action: dict[str, Any]) -> str:
    def strings(value: Any) -> list[str]:
        result: list[str] = []
        stack: list[tuple[Any, int]] = [(value, 0)]
        inspected = 0
        while stack and inspected < MAX_INSPECTED_VALUES:
            current, depth = stack.pop()
            inspected += 1
            if depth > MAX_NESTING_DEPTH:
                continue
            if isinstance(current, str):
                result.append(current)
            elif isinstance(current, list):
                stack.extend((item, depth + 1) for item in reversed(current))
            elif isinstance(current, dict):
                stack.extend(
                    (item, depth + 1) for item in reversed(list(current.values()))
                )
        return result

    return " ".join(
        text
        for field in (
            "label",
            "instructions",
            "rationale",
            "possibleOutcomes",
            "predictions",
            "execution",
        )
        for text in strings(action.get(field))
    )


def _targeting_metadata_errors(action: dict[str, Any]) -> list[str]:
    action_id = action.get("actionId", "<unknown>")
    errors: list[str] = []
    intent = action.get("researchIntent")
    precision = action.get("outputPrecision")
    subjects = action.get("sensitiveSubjects", [])
    if intent is not None and not _choice(intent, RESEARCH_INTENTS):
        errors.append(f"{action_id}: invalid researchIntent")
    if precision is not None and not _choice(precision, OUTPUT_PRECISIONS):
        errors.append(f"{action_id}: invalid outputPrecision")
    if not isinstance(subjects, list) or any(
        not isinstance(subject, str) or subject not in SENSITIVE_SUBJECTS
        for subject in subjects
    ):
        errors.append(f"{action_id}: sensitiveSubjects contains an invalid value")
        subjects = []
    errors.extend(
        f"{action_id}: {error}" for error in object_risk_errors(action)
    )
    return errors


def validate_action_safety(
    plan: dict[str, Any],
    action: dict[str, Any],
    action_map: dict[str, dict[str, Any]],
    source_map: dict[str, dict[str, Any]],
) -> list[str]:
    action_id = action.get("actionId", "<unknown>")
    errors: list[str] = []
    action_class = action.get("actionClass")
    method = action.get("method")
    unknown_fields = sorted(str(field) for field in set(action) - ACTION_FIELDS)
    if unknown_fields:
        errors.append(f"{action_id}: unsupported action fields: {', '.join(unknown_fields)}")
    if not isinstance(method, str) or method not in METHOD_CLASSES:
        errors.append(f"{action_id}: invalid or intrusive method")
    elif not _choice(action_class, METHOD_CLASSES[method]):
        errors.append(f"{action_id}: method {method} is incompatible with {action_class}")
    text = _action_text(action)
    if PROHIBITED_DIRECTIVE.search(text):
        errors.append(f"{action_id}: action text requests prohibited intrusive conduct")
    if action.get("instructions") is not None and not isinstance(
        action.get("instructions"), str
    ):
        errors.append(f"{action_id}: instructions must be a string")

    authorization = action.get("authorization", {})
    if not isinstance(authorization, dict):
        authorization = {}
    required = authorization.get("required")
    state = authorization.get("state")
    case = plan.get("case")
    case_auth = case.get("authorization", {}) if isinstance(case, dict) else {}
    if not isinstance(case_auth, dict):
        case_auth = {}
    approval_refs = authorization.get("approvalReferences", [])
    if (
        not isinstance(approval_refs, list)
        or any(not isinstance(reference, str) or not reference for reference in approval_refs)
    ):
        errors.append(f"{action_id}: approvalReferences must be a string array")
        approval_refs = []
    if action_class == "public-desk" and required != "none":
        errors.append(f"{action_id}: public-desk requires authorization.required none")
    elif action_class == "licensed-computation" and required not in (
        "none",
        "external-approval",
    ):
        errors.append(f"{action_id}: licensed-computation has incompatible authorization")
    elif action_class == "authenticated-read":
        platform = action.get("platform")
        allowed_platforms = case_auth.get("authenticatedPlatforms")
        if not isinstance(allowed_platforms, list):
            allowed_platforms = []
        if required != "user-account":
            errors.append(f"{action_id}: authenticated-read requires user-account")
        if not isinstance(platform, str) or not platform:
            errors.append(f"{action_id}: authenticated-read requires a named platform")
        elif state == "confirmed" and platform not in allowed_platforms:
            errors.append(f"{action_id}: platform is not authorized in the case")
    elif action_class == "community-consultation":
        if required != "community-governance":
            errors.append(f"{action_id}: community consultation requires governance")
        elif state == "confirmed" and (
            case_auth.get("communityConsultation") is not True or not approval_refs
        ):
            errors.append(f"{action_id}: community consultation lacks governed approval")
    elif action_class == "field-non-invasive":
        if required != "external-approval":
            errors.append(f"{action_id}: field action requires external approval")
        elif state == "confirmed" and (
            case_auth.get("fieldActions") is not True or not approval_refs
        ):
            errors.append(f"{action_id}: field action lacks case and external approval")
        elif state == "confirmed":
            area = plan.get("area")
            permission_case = case if isinstance(case, dict) else {}
            area_id = (
                area.get("selectedGazetteerId")
                if isinstance(area, dict)
                else None
            )
            field_errors = restricted_permission_errors(
                permission_case,
                method=method,
                area_id=area_id,
                require_restricted_handling=False,
            )
            errors.extend(f"{action_id}: {error}" for error in field_errors)
            missing_refs = permission_instrument_ids(permission_case) - set(approval_refs)
            if missing_refs:
                errors.append(
                    f"{action_id}: approvalReferences omit confirmed instruments: "
                    + ", ".join(sorted(missing_refs))
                )
    elif action_class == "specialist-handoff":
        if required not in ("external-approval", "community-governance"):
            errors.append(f"{action_id}: specialist handoff requires authority")
        elif state == "confirmed" and not approval_refs:
            errors.append(f"{action_id}: confirmed specialist handoff lacks approval reference")

    errors.extend(_targeting_metadata_errors(action))

    used_sources = [
        source_map[source_id]
        for source_id in _provenance_sources(plan, action)
        if source_id in source_map
    ]
    stage = action.get("stage")
    post_freeze_stage = isinstance(stage, str) and (
        stage.startswith("post-freeze") or stage.startswith("post-unblinding")
    )
    deferred_or_visible_source = any(
        source.get("accessStage") in {"post-freeze", "post-unblinding"}
        or source.get("targetLabelState") == "visible"
        for source in used_sources
    )
    if (
        post_freeze_stage or deferred_or_visible_source
    ) and action.get("requiresCandidatesFrozen") is not True:
        errors.append(
            f"{action_id}: post-freeze, post-unblinding, or visible-label work "
            "requires requiresCandidatesFrozen true"
        )
    if any(source.get("accessBasis") == "authenticated" for source in used_sources):
        if action_class != "authenticated-read":
            errors.append(f"{action_id}: authenticated source requires authenticated-read")
    if any(source.get("accessBasis") == "authority-controlled" for source in used_sources):
        if required != "external-approval":
            errors.append(f"{action_id}: authority-controlled source lacks approval")
        elif state == "confirmed" and not approval_refs:
            errors.append(f"{action_id}: confirmed authority access lacks approval reference")
    if any(source.get("accessBasis") == "community-controlled" for source in used_sources):
        if required != "community-governance":
            errors.append(f"{action_id}: community-controlled source lacks governance")
        elif state == "confirmed" and not approval_refs:
            errors.append(f"{action_id}: confirmed community access lacks approval reference")

    pair_id = action.get("pairedControlActionId")
    if action.get("candidateFocused") is True:
        pair = action_map.get(pair_id) if isinstance(pair_id, str) else None
        if pair_id == action_id:
            errors.append(f"{action_id}: candidate action cannot pair with itself")
        if pair is not None:
            if pair.get("candidateFocused") is True:
                errors.append(f"{action_id}: paired control cannot be candidate-focused")
            family = action.get("comparisonFamilyId")
            if not family or pair.get("comparisonFamilyId") != family:
                errors.append(f"{action_id}: paired control must share comparisonFamilyId")
            origins = {
                str(source_map[source_id].get("originFamilyId"))
                for source_id in (
                    action.get("sourceIds")
                    if isinstance(action.get("sourceIds"), list)
                    else []
                )
                if isinstance(source_id, str) and source_id in source_map
            }
            pair_origins = {
                str(source_map[source_id].get("originFamilyId"))
                for source_id in (
                    pair.get("sourceIds")
                    if isinstance(pair.get("sourceIds"), list)
                    else []
                )
                if isinstance(source_id, str) and source_id in source_map
            }
            if not origins.intersection(pair_origins):
                errors.append(f"{action_id}: paired control lacks a shared measurement family")

    if (
        action.get("stage") == "candidate-generation"
        and not (case.get("candidatesFrozen") if isinstance(case, dict) else False)
    ):
        leaked = [
            source_id
            for source_id in _provenance_sources(plan, action)
            if source_id in source_map
            and (
                source_map[source_id].get("accessStage") != "pre-detection"
                or
                source_map[source_id].get("targetLabelState") == "visible"
                or (
                    source_map[source_id].get("workflowRole")
                    in ("ground-truth", "corroboration")
                    and source_map[source_id].get("targetLabelState") != "none"
                )
            )
        ]
        if leaked:
            errors.append(
                f"{action_id}: target-label provenance used before candidate freeze: "
                + ", ".join(sorted(leaked))
            )
    return errors
