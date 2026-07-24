#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from ij_casebook import new_case, validate_case
from ij_common import atomic_write_json, load_json, stable_id, utc_now


DECISION_STAGES = {
    "acquisition",
    "documentation",
    "preprocessing",
    "analysis",
    "visualization",
    "interpretation",
    "reporting",
}
TARGET_LABEL_STATES = {"unknown", "visible", "withheld"}
RESEARCH_FRAME_KEYS = (
    "expectedProxy",
    "visibilityConditions",
    "targetScale",
    "alternativeExplanations",
    "decisionRule",
    "falsifier",
    "interpretivePrior",
)


def _unique_text(items: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def build_method_case(
    title: str,
    question: str,
    study_area: str,
    disclosure: str,
    authorized_platforms: Iterable[str],
    expected_proxy: str,
    visibility_conditions: Iterable[str],
    target_scale: str,
    alternative_explanations: Iterable[str],
    decision_rule: str,
    falsifier: str,
    interpretive_prior: str,
) -> Dict[str, Any]:
    visibility = _unique_text(visibility_conditions)
    alternatives = _unique_text(alternative_explanations)
    scalar_fields = {
        "expectedProxy": expected_proxy.strip(),
        "targetScale": target_scale.strip(),
        "decisionRule": decision_rule.strip(),
        "falsifier": falsifier.strip(),
        "interpretivePrior": interpretive_prior.strip(),
    }
    if any(not value for value in scalar_fields.values()):
        raise ValueError("All scalar research-frame fields are required")
    if not visibility or not alternatives:
        raise ValueError(
            "At least one visibility condition and alternative explanation are required"
        )

    case = new_case(
        title,
        question,
        study_area,
        disclosure,
        authorized_platforms,
    )
    case["schemaVersion"] = "1.1"
    case["researchFrame"] = {
        **scalar_fields,
        "visibilityConditions": visibility,
        "alternativeExplanations": alternatives,
    }
    case["decisionLog"] = []
    return case


def add_decision(
    case_path: Path,
    stage: str,
    choice: str,
    rationale: str,
    alternatives: Iterable[str],
    target_labels_state: str,
    affected_artifacts: Iterable[str],
) -> Dict[str, Any]:
    if stage not in DECISION_STAGES:
        raise ValueError(f"Unsupported decision stage: {stage}")
    if target_labels_state not in TARGET_LABEL_STATES:
        raise ValueError(f"Unsupported target-label state: {target_labels_state}")
    if not choice.strip() or not rationale.strip():
        raise ValueError("Decision choice and rationale are required")

    case = load_json(case_path)
    if case.get("schemaVersion") != "1.1":
        raise ValueError("Decision logging requires a methodology schema 1.1 case")
    created_at = utc_now()
    decision = {
        "decisionId": stable_id(
            "dec",
            f"{case.get('caseId', '')}|{stage}|{choice}|{created_at}",
        ),
        "stage": stage,
        "choice": choice.strip(),
        "rationale": rationale.strip(),
        "alternativesConsidered": _unique_text(alternatives),
        "targetLabelsState": target_labels_state,
        "affectedArtifacts": _unique_text(affected_artifacts),
        "createdAt": created_at,
    }
    decision_log: List[Dict[str, Any]] = list(case.get("decisionLog", []))
    decision_log.append(decision)
    case["decisionLog"] = decision_log
    atomic_write_json(case_path, case)
    return decision


def validate_method_case(case: Dict[str, Any]) -> List[str]:
    errors = validate_case(case)
    if case.get("schemaVersion") != "1.1":
        errors.append("schemaVersion must be 1.1 for a methodology case")

    frame = case.get("researchFrame")
    if not isinstance(frame, dict):
        errors.append("researchFrame is required")
    else:
        for key in RESEARCH_FRAME_KEYS:
            if key not in frame:
                errors.append(f"researchFrame.{key} is required")
        for key in (
            "expectedProxy",
            "targetScale",
            "decisionRule",
            "falsifier",
            "interpretivePrior",
        ):
            if not str(frame.get(key) or "").strip():
                errors.append(f"researchFrame.{key} cannot be empty")
        for key in ("visibilityConditions", "alternativeExplanations"):
            values = frame.get(key)
            if not isinstance(values, list) or not values:
                errors.append(f"researchFrame.{key} must be a non-empty list")

    decision_log = case.get("decisionLog")
    if not isinstance(decision_log, list):
        errors.append("decisionLog is required")
        return errors
    for index, decision in enumerate(decision_log):
        if decision.get("stage") not in DECISION_STAGES:
            errors.append(f"decisionLog[{index}].stage is invalid")
        if decision.get("targetLabelsState") not in TARGET_LABEL_STATES:
            errors.append(f"decisionLog[{index}].targetLabelsState is invalid")
        if not str(decision.get("choice") or "").strip():
            errors.append(f"decisionLog[{index}].choice is required")
        if not str(decision.get("rationale") or "").strip():
            errors.append(f"decisionLog[{index}].rationale is required")
    return errors


def command_new_case(args: argparse.Namespace) -> int:
    case = build_method_case(
        args.title,
        args.question,
        args.study_area,
        args.disclosure,
        args.authorize_platform,
        args.expected_proxy,
        args.visibility_condition,
        args.target_scale,
        args.alternative_explanation,
        args.decision_rule,
        args.falsifier,
        args.interpretive_prior,
    )
    atomic_write_json(args.out, case)
    print(json.dumps({"ok": True, "case": str(args.out), "caseId": case["caseId"]}))
    return 0


def command_add_decision(args: argparse.Namespace) -> int:
    decision = add_decision(
        args.case,
        args.stage,
        args.choice,
        args.rationale,
        args.alternative,
        args.target_labels_state,
        args.artifact,
    )
    print(json.dumps({"ok": True, "decision": decision}, sort_keys=True))
    return 0


def command_validate(args: argparse.Namespace) -> int:
    errors = validate_method_case(load_json(args.case))
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and audit theory-aware archaeological case ledgers."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_case_parser = subparsers.add_parser("new-case")
    new_case_parser.add_argument("--title", required=True)
    new_case_parser.add_argument("--question", required=True)
    new_case_parser.add_argument("--study-area", required=True)
    new_case_parser.add_argument(
        "--disclosure",
        choices=("public", "restricted", "heritage-authority-only"),
        default="public",
    )
    new_case_parser.add_argument("--authorize-platform", action="append", default=[])
    new_case_parser.add_argument("--expected-proxy", required=True)
    new_case_parser.add_argument("--visibility-condition", action="append", default=[])
    new_case_parser.add_argument("--target-scale", required=True)
    new_case_parser.add_argument("--alternative-explanation", action="append", default=[])
    new_case_parser.add_argument("--decision-rule", required=True)
    new_case_parser.add_argument("--falsifier", required=True)
    new_case_parser.add_argument("--interpretive-prior", required=True)
    new_case_parser.add_argument("--out", type=Path, required=True)
    new_case_parser.set_defaults(handler=command_new_case)

    decision_parser = subparsers.add_parser("add-decision")
    decision_parser.add_argument("--case", type=Path, required=True)
    decision_parser.add_argument("--stage", choices=sorted(DECISION_STAGES), required=True)
    decision_parser.add_argument("--choice", required=True)
    decision_parser.add_argument("--rationale", required=True)
    decision_parser.add_argument("--alternative", action="append", default=[])
    decision_parser.add_argument(
        "--target-labels-state",
        choices=sorted(TARGET_LABEL_STATES),
        default="unknown",
    )
    decision_parser.add_argument("--artifact", action="append", default=[])
    decision_parser.set_defaults(handler=command_add_decision)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--case", type=Path, required=True)
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
