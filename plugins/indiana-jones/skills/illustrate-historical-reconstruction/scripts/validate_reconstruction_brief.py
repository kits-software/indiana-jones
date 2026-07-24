from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


SUBJECT_KINDS = {
    "person",
    "object",
    "clothing",
    "building",
    "interior",
    "settlement",
    "city",
    "landscape",
    "scene",
}
SOURCE_AUTHORITIES = {
    "primary-direct",
    "primary-indirect",
    "secondary",
    "analogy",
    "living-tradition",
}
DECISION_STATUSES = {
    "documented",
    "strongly-constrained",
    "plausible",
    "illustrative",
    "contested",
}
IMPACTS = {"low", "medium", "high"}
DISCLOSURES = {"public", "restricted", "heritage-authority-only"}
VARIANT_POLICIES = {
    "alternative-variants",
    "single-main-with-disclosure",
    "defer-depiction",
}
REVIEW_POLICIES = VARIANT_POLICIES | {"decision-specific"}
UNCERTAIN_STATUSES = {"plausible", "illustrative", "contested"}


def issue(path: str, message: str) -> dict[str, str]:
    return {"path": path, "message": message}


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def require_text(
    container: Mapping[str, Any],
    key: str,
    path: str,
    issues: list[dict[str, str]],
) -> None:
    if not text(container.get(key)):
        issues.append(issue(f"{path}.{key}", "must be a non-empty string"))


def validate_source_links(
    value: Any,
    path: str,
    source_ids: set[str],
    issues: list[dict[str, str]],
) -> list[str]:
    if not isinstance(value, list):
        issues.append(issue(path, "must be an array"))
        return []
    linked_sources: list[str] = []
    for index, source_id in enumerate(value):
        if not text(source_id):
            issues.append(
                issue(f"{path}[{index}]", "must be a non-empty source ID")
            )
            continue
        linked_sources.append(source_id)
    unknown_sources = sorted(
        source_id
        for source_id in linked_sources
        if source_id not in source_ids
    )
    if unknown_sources:
        issues.append(
            issue(
                path,
                "contains unknown source IDs: " + ", ".join(unknown_sources),
            )
        )
    return linked_sources


def validate_subject(payload: Mapping[str, Any], issues: list[dict[str, str]]) -> None:
    subject = payload.get("subject")
    if not mapping(subject):
        issues.append(issue("$.subject", "must be an object"))
        return
    for key in (
        "name",
        "place",
        "timeSlice",
        "state",
        "viewpoint",
        "intendedUse",
    ):
        require_text(subject, key, "$.subject", issues)
    if subject.get("kind") not in SUBJECT_KINDS:
        issues.append(
            issue(
                "$.subject.kind",
                "must be one of " + ", ".join(sorted(SUBJECT_KINDS)),
            )
        )
    if subject.get("disclosure") not in DISCLOSURES:
        issues.append(
            issue(
                "$.subject.disclosure",
                "must be public, restricted, or heritage-authority-only",
            )
        )


def validate_sources(
    payload: Mapping[str, Any],
    issues: list[dict[str, str]],
) -> set[str]:
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append(issue("$.sources", "must contain at least one source"))
        return set()
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        path = f"$.sources[{index}]"
        if not mapping(source):
            issues.append(issue(path, "must be an object"))
            continue
        for key in ("id", "citation", "originFamilyId", "licenseOrUseBasis"):
            require_text(source, key, path, issues)
        source_id = source.get("id")
        if text(source_id):
            if source_id in source_ids:
                issues.append(issue(f"{path}.id", "must be unique"))
            source_ids.add(source_id)
        if source.get("authority") not in SOURCE_AUTHORITIES:
            issues.append(
                issue(
                    f"{path}.authority",
                    "must be one of " + ", ".join(sorted(SOURCE_AUTHORITIES)),
                )
            )
        roles = source.get("roles")
        if not isinstance(roles, list) or not any(text(role) for role in roles):
            issues.append(issue(f"{path}.roles", "must name at least one role"))
        if text(source.get("url")) and not text(source.get("accessedAt")):
            issues.append(
                issue(
                    f"{path}.accessedAt",
                    "is required when the source has a URL",
                )
            )
    return source_ids


def validate_decisions(
    payload: Mapping[str, Any],
    source_ids: set[str],
    issues: list[dict[str, str]],
) -> set[str]:
    decisions = payload.get("visualDecisions")
    if not isinstance(decisions, list) or not decisions:
        issues.append(
            issue("$.visualDecisions", "must contain at least one visual decision")
        )
        return set()
    decision_ids: set[str] = set()
    uncertain_high_impact: set[str] = set()
    for index, decision in enumerate(decisions):
        path = f"$.visualDecisions[{index}]"
        if not mapping(decision):
            issues.append(issue(path, "must be an object"))
            continue
        for key in (
            "id",
            "element",
            "depiction",
            "rationale",
            "promptClause",
            "inspectionCheck",
        ):
            require_text(decision, key, path, issues)
        decision_id = decision.get("id")
        if text(decision_id):
            if decision_id in decision_ids:
                issues.append(issue(f"{path}.id", "must be unique"))
            decision_ids.add(decision_id)
        status = decision.get("status")
        if status not in DECISION_STATUSES:
            issues.append(
                issue(
                    f"{path}.status",
                    "must be one of " + ", ".join(sorted(DECISION_STATUSES)),
                )
            )
        impact = decision.get("impact")
        if impact not in IMPACTS:
            issues.append(
                issue(
                    f"{path}.impact",
                    "must be low, medium, or high",
                )
            )
        linked_sources = validate_source_links(
            decision.get("sourceIds"),
            f"{path}.sourceIds",
            source_ids,
            issues,
        )
        if status != "illustrative" and not linked_sources:
            issues.append(
                issue(
                    f"{path}.sourceIds",
                    f"{status or 'this'} decision requires a source",
                )
            )
        alternatives = decision.get("alternatives")
        if not isinstance(alternatives, list):
            issues.append(issue(f"{path}.alternatives", "must be an array"))
            alternatives = []
        if impact == "high" and status in UNCERTAIN_STATUSES:
            if text(decision_id):
                uncertain_high_impact.add(decision_id)
            if not any(text(alternative) for alternative in alternatives):
                issues.append(
                    issue(
                        f"{path}.alternatives",
                        "high-impact uncertainty requires an alternative",
                    )
                )
            if decision.get("uncertaintyTreatment") not in VARIANT_POLICIES:
                issues.append(
                    issue(
                        f"{path}.uncertaintyTreatment",
                        "must declare alternative-variants, "
                        "single-main-with-disclosure, or defer-depiction",
                    )
                )
    return uncertain_high_impact


def validate_negative_constraints(
    payload: Mapping[str, Any],
    source_ids: set[str],
    issues: list[dict[str, str]],
) -> None:
    constraints = payload.get("negativeConstraints")
    if not isinstance(constraints, list) or not constraints:
        issues.append(
            issue(
                "$.negativeConstraints",
                "must contain at least one anachronism or bias constraint",
            )
        )
        return
    for index, constraint in enumerate(constraints):
        path = f"$.negativeConstraints[{index}]"
        if not mapping(constraint):
            issues.append(issue(path, "must be an object"))
            continue
        require_text(constraint, "constraint", path, issues)
        require_text(constraint, "reason", path, issues)
        validate_source_links(
            constraint.get("sourceIds"),
            f"{path}.sourceIds",
            source_ids,
            issues,
        )


def validate_prompt(payload: Mapping[str, Any], issues: list[dict[str, str]]) -> None:
    prompt = payload.get("prompt")
    if not mapping(prompt):
        issues.append(issue("$.prompt", "must be an object"))
        return
    for key in (
        "assetType",
        "primaryRequest",
        "composition",
        "lightingAndMood",
        "finalPrompt",
    ):
        require_text(prompt, key, "$.prompt", issues)
    if prompt.get("useCase") != "historical-scene":
        issues.append(
            issue("$.prompt.useCase", "must be historical-scene")
        )
    for key in (
        "structuralAnchors",
        "culturalMaterialDetails",
        "sceneAndEnvironment",
        "constraints",
        "avoid",
    ):
        value = prompt.get(key)
        if not isinstance(value, list) or not any(text(item) for item in value):
            issues.append(
                issue(f"$.prompt.{key}", "must contain at least one item")
            )


def validate_review(
    payload: Mapping[str, Any],
    uncertain_high_impact: set[str],
    stage: str,
    issues: list[dict[str, str]],
) -> None:
    review = payload.get("review")
    if not mapping(review):
        issues.append(issue("$.review", "must be an object"))
        return
    for key in ("anachronismChecks", "culturalChecks"):
        value = review.get(key)
        if not isinstance(value, list) or not any(text(item) for item in value):
            issues.append(issue(f"$.review.{key}", "must contain at least one check"))
    geometry_checks = review.get("geometryChecks")
    if not isinstance(geometry_checks, list):
        issues.append(issue("$.review.geometryChecks", "must be an array"))
    unresolved = review.get("unresolvedHighImpact")
    if not isinstance(unresolved, list):
        issues.append(issue("$.review.unresolvedHighImpact", "must be an array"))
        unresolved_ids: set[str] = set()
    else:
        unresolved_ids = {item for item in unresolved if text(item)}
    missing = sorted(uncertain_high_impact - unresolved_ids)
    if missing:
        issues.append(
            issue(
                "$.review.unresolvedHighImpact",
                "must name uncertain high-impact decisions: " + ", ".join(missing),
            )
        )
    if uncertain_high_impact and review.get("variantPolicy") not in REVIEW_POLICIES:
        issues.append(
            issue(
                "$.review.variantPolicy",
                "must declare how high-impact uncertainty is shown",
            )
        )
    if stage == "final" and review.get("outputChecked") is not True:
        issues.append(issue("$.review.outputChecked", "must be true at final stage"))
    if not isinstance(review.get("remainingIssues"), list):
        issues.append(issue("$.review.remainingIssues", "must be an array"))


def validate_caption(
    payload: Mapping[str, Any],
    source_ids: set[str],
    issues: list[dict[str, str]],
) -> None:
    caption = payload.get("caption")
    if not mapping(caption):
        issues.append(issue("$.caption", "must be an object"))
        return
    for key in ("label", "summary", "uncertaintyStatement"):
        require_text(caption, key, "$.caption", issues)
    linked_sources = validate_source_links(
        caption.get("sourceIds"),
        "$.caption.sourceIds",
        source_ids,
        issues,
    )
    if not linked_sources:
        issues.append(issue("$.caption.sourceIds", "must cite at least one source"))


def validate_generation(
    payload: Mapping[str, Any],
    stage: str,
    issues: list[dict[str, str]],
) -> None:
    generation = payload.get("generation")
    if not mapping(generation):
        issues.append(issue("$.generation", "must be an object"))
        return
    references = generation.get("referenceImages")
    if not isinstance(references, list):
        issues.append(issue("$.generation.referenceImages", "must be an array"))
    else:
        for index, reference in enumerate(references):
            path = f"$.generation.referenceImages[{index}]"
            if not mapping(reference):
                issues.append(issue(path, "must be an object"))
                continue
            for key in ("pathOrUrl", "role", "licenseOrUseBasis"):
                require_text(reference, key, path, issues)
    if stage == "final":
        for key in ("tool", "generatedAt", "outputPath", "promptVersion"):
            require_text(generation, key, "$.generation", issues)


def validate(payload: Any, stage: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not mapping(payload):
        return [issue("$", "brief must be a JSON object")]
    if payload.get("schemaVersion") != "1.0":
        issues.append(issue("$.schemaVersion", "must be 1.0"))
    for key in ("title", "researchQuestion"):
        require_text(payload, key, "$", issues)
    validate_subject(payload, issues)
    source_ids = validate_sources(payload, issues)
    uncertain = validate_decisions(payload, source_ids, issues)
    validate_negative_constraints(payload, source_ids, issues)
    validate_prompt(payload, issues)
    validate_review(payload, uncertain, stage, issues)
    validate_generation(payload, stage, issues)
    validate_caption(payload, source_ids, issues)
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate an evidence-led historical reconstruction brief"
    )
    parser.add_argument("brief", type=Path)
    parser.add_argument(
        "--stage",
        choices=("preflight", "final"),
        default="preflight",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        result = {
            "valid": False,
            "stage": args.stage,
            "issues": [issue("$", str(error))],
        }
        print(json.dumps(result, indent=2))
        return 2
    issues = validate(payload, args.stage)
    result = {
        "valid": not issues,
        "stage": args.stage,
        "issues": issues,
    }
    print(json.dumps(result, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
