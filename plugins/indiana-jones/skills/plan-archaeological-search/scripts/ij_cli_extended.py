from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ij_adapter_protocol import build_search_ladder, resume_acquisition
from ij_artifacts import plan_sha256, read_json, write_json
from ij_authoring import prepare_research_plan
from ij_execution_spec import execution_readiness_errors
from ij_plan import validate_plan
from ij_probability import heuristic_report_from_input
from ij_readiness import readiness_errors


def add_extended_commands(commands: argparse._SubParsersAction) -> None:
    prepare = commands.add_parser(
        "prepare",
        help="Apply a declarative research package and require a ready schema-2 plan.",
    )
    prepare.add_argument("--plan", type=Path, required=True)
    prepare.add_argument("--package", type=Path, required=True)
    prepare.add_argument("--out", type=Path, required=True)

    ladder = commands.add_parser(
        "search-ladder",
        help="Build bounded alias, object, and language query branches.",
    )
    ladder.add_argument("--place-alias", action="append", required=True)
    ladder.add_argument("--object-term", action="append", required=True)
    ladder.add_argument("--language-variant", action="append", default=[])
    ladder.add_argument("--broader-term", action="append", default=[])
    ladder.add_argument("--maximum", type=int, default=100)
    ladder.add_argument("--out", type=Path, required=True)

    resume = commands.add_parser(
        "resume-source",
        help="Consume a sealed adapter cursor through a declared continuation page.",
    )
    resume.add_argument("--plan", type=Path, required=True)
    resume.add_argument("--source-id", required=True)
    resume.add_argument("--previous", type=Path, required=True)
    resume.add_argument("--out", type=Path, required=True)
    resume.add_argument("--max-bytes", type=int, default=10_000_000)
    resume.add_argument("--max-records", type=int, default=5_000)

    heuristic = commands.add_parser(
        "assess-heuristic",
        help="Rank candidate evidence without presenting a calibrated probability.",
    )
    heuristic.add_argument(
        "--input",
        type=Path,
        required=True,
        help=(
            "Candidate/evidence JSON with method, score meaning, assumptions, "
            "uncertainty, limitations, and evidence references."
        ),
    )
    heuristic.add_argument(
        "--plan",
        type=Path,
        help="Optional validated plan whose case disclosure controls the output.",
    )
    heuristic.add_argument("--out", type=Path, required=True)


def handle_extended_command(args: Any) -> int | None:
    if args.command == "prepare":
        prepared = prepare_research_plan(
            read_json(args.plan),
            read_json(args.package),
        )
        write_json(args.out, prepared)
        print(json.dumps({"out": str(args.out), "planSha256": plan_sha256(prepared)}))
        return 0
    if args.command == "search-ladder":
        ladder = build_search_ladder(
            place_aliases=args.place_alias,
            object_terms=args.object_term,
            language_variants=args.language_variant,
            broader_terms=args.broader_term,
            maximum=args.maximum,
        )
        write_json(
            args.out,
            {
                "schemaVersion": "archaeological-search-ladder-1.0",
                "queryCount": len(ladder),
                "queries": ladder,
            },
        )
        print(json.dumps({"out": str(args.out), "queryCount": len(ladder)}))
        return 0
    if args.command == "resume-source":
        plan = read_json(args.plan)
        source = next(
            (
                value
                for value in plan.get("sources", [])
                if isinstance(value, dict) and value.get("sourceId") == args.source_id
            ),
            None,
        )
        if source is None:
            raise ValueError(f"unknown source: {args.source_id}")
        artifact = resume_acquisition(
            previous_artifact=args.previous,
            source=source,
            out=args.out,
            max_bytes=args.max_bytes,
            max_records=args.max_records,
        )
        print(
            json.dumps(
                {
                    "out": str(args.out),
                    "resultCount": artifact["queryArtifact"]["resultCount"],
                    "sourceExhausted": artifact["queryArtifact"]["checkpoint"][
                        "sourceExhausted"
                    ],
                }
            )
        )
        return 0
    if args.command == "assess-heuristic":
        case = None
        if args.plan:
            plan = read_json(args.plan)
            validation = validate_plan(plan)
            if not validation.valid:
                raise ValueError(
                    "heuristic assessment plan is invalid: "
                    + "; ".join(validation.errors)
                )
            case = plan.get("case", {})
        report = heuristic_report_from_input(
            read_json(args.input),
            case=case,
        )
        write_json(args.out, report)
        print(
            json.dumps(
                {
                    "out": str(args.out),
                    "assessmentType": report["assessmentType"],
                    "candidateCount": len(report["candidates"]),
                }
            )
        )
        return 0
    return None


def validate_command(plan: dict[str, Any], require_ready: bool) -> int:
    result = validate_plan(plan)
    readiness = (
        readiness_errors(plan) + execution_readiness_errors(plan)
        if result.valid
        else []
    )
    output: dict[str, Any] = {
        "ok": result.valid,
        "valid": result.valid,
        "ready": result.valid and not readiness,
        "planSha256": plan_sha256(plan),
        "errors": result.errors,
        "readinessErrors": readiness,
        "warnings": result.warnings,
    }
    if not result.valid:
        output["error"] = {
            "code": "IJ_SCHEMA_INVALID",
            "message": "Plan schema validation failed.",
            "path": "$",
            "hint": "Correct the listed schema errors and retry.",
        }
    print(json.dumps(output, indent=2, sort_keys=True))
    if not result.valid:
        return 3
    return 2 if require_ready and readiness else 0
