#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ij_artifacts import plan_sha256, public_export, read_json, write_json
from ij_budget_cli import add_budget_arguments, budget_kwargs
from ij_errors import InvocationError, diagnostic_json, error_code
from ij_frontier import build_frontier
from ij_claims import extract_claims
from ij_cli_extended import add_extended_commands, handle_extended_command, validate_command
from ij_ingest import (
    SUPPORTED_FORMATS,
    acquire_and_normalize,
    assessment_summary,
    discover_source_candidates,
    reconcile_artifacts,
)
from ij_history import build_history_report, build_object_biography
from ij_materials import build_material_evidence_report
from ij_migrate import freeze_candidates, migrate_plan
from ij_orchestrator import advance_run, audit_run, run_until_handoff
from ij_plan import new_plan, validate_plan
from ij_probability import calibrated_probability_report
from ij_readiness import readiness_errors
from ij_report_inputs import read_sealed_report_input, read_sealed_report_inputs
from ij_reports import (
    build_finds_report,
    build_object_report,
    build_source_gap_report,
)
from ij_runtime import (
    complete_action,
    execution_readiness_errors,
    execute_deterministic_action,
    fail_action,
    initialize_run,
    next_task_packet,
    resume_run,
    run_status,
    start_action,
    stop_run,
)
from ij_source_contract import verify_source_acquisition


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InvocationError(f"invalid command arguments: {message}")


def _parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description=(
            "Build, validate, execute, resume, ingest, and publish archaeological "
            "research while withholding only explicitly protected spatial or source material."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    add_extended_commands(commands)

    create = commands.add_parser("new", help="Create a coarse reconnaissance plan.")
    create.add_argument("--place", required=True)
    create.add_argument("--question", required=True)
    create.add_argument("--gazetteer-id", required=True)
    create.add_argument(
        "--bbox",
        required=True,
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    create.add_argument("--rows", type=int, default=3)
    create.add_argument("--columns", type=int, default=3)
    create.add_argument(
        "--study-kind",
        choices=[
            "prospective-survey",
            "known-site-rediscovery",
            "historical-reconstruction",
        ],
        default="prospective-survey",
    )
    create.add_argument(
        "--disclosure",
        choices=["public", "restricted", "heritage-authority-only"],
        default="public",
    )
    create.add_argument("--out", type=Path, required=True)

    validate = commands.add_parser("validate", help="Validate a search plan.")
    validate.add_argument("--plan", type=Path, required=True)
    validate.add_argument(
        "--ready",
        action="store_true",
        help="Also require enough sources, hypotheses, controls, and actions to begin research.",
    )

    rank = commands.add_parser("rank", help="Build the next ready action batch.")
    rank.add_argument("--plan", type=Path, required=True)
    rank.add_argument("--limit", type=int, default=4)
    rank.add_argument("--allow-draft", action="store_true",
        help="Write a non-executable preview even when research readiness is incomplete.",
    )
    rank.add_argument("--out", type=Path, required=True)

    export = commands.add_parser(
        "export-public",
        help="Create a public copy with explicitly protected material withheld.",
    )
    export.add_argument("--plan", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    export.add_argument("--schema", choices=["1.0-public", "2.0-public"], default="1.0-public")

    initialize = commands.add_parser(
        "init-run", help="Create an evidence-bound resumable research run."
    )
    initialize.add_argument("--plan", type=Path, required=True)
    initialize.add_argument("--run-dir", type=Path, required=True)
    add_budget_arguments(initialize)
    initialize.add_argument("--candidate-artifact", type=Path)
    initialize.add_argument("--candidate-seal", type=Path)

    next_action = commands.add_parser("next", help="Materialize the next task packet.")
    next_action.add_argument("--run-dir", type=Path, required=True)
    next_action.add_argument("--limit", type=int, default=4)
    next_action.add_argument("--out", type=Path)

    start = commands.add_parser("start-action", help="Lease and start one ready action.")
    start.add_argument("--run-dir", type=Path, required=True)
    start.add_argument("--action-id", required=True)
    start.add_argument("--idempotency-key")

    complete = commands.add_parser(
        "complete-action",
        aliases=["record-result"],
        help="Seal evidence and complete a running action.",
    )
    complete.add_argument("--run-dir", type=Path, required=True)
    complete.add_argument("--action-id", required=True)
    complete.add_argument("--attempt-id", required=True)
    complete.add_argument("--result", type=Path, required=True)
    complete.add_argument("--summary", required=True)
    complete.add_argument("--source-id", action="append", default=[])
    complete.add_argument("--acceptance-evidence", action="append", default=[])

    fail = commands.add_parser("fail-action", help="Record a bounded action failure.")
    fail.add_argument("--run-dir", type=Path, required=True)
    fail.add_argument("--action-id", required=True)
    fail.add_argument("--attempt-id", required=True)
    fail.add_argument("--error", required=True)
    fail.add_argument("--retryable", action="store_true")

    execute = commands.add_parser(
        "run-action", help="Execute one deterministic source or reconciliation action."
    )
    execute.add_argument("--run-dir", type=Path, required=True)
    execute.add_argument("--action-id", required=True)

    resume = commands.add_parser("resume", help="Recover interrupted action leases.")
    resume.add_argument("--run-dir", type=Path, required=True)
    resume.add_argument("--override-stop", action="store_true")

    stop = commands.add_parser("stop", help="Append an explicit run stop.")
    stop.add_argument("--run-dir", type=Path, required=True)
    stop.add_argument("--reason", required=True)

    status = commands.add_parser("status", help="Audit and show replayed run state.")
    status.add_argument("--run-dir", type=Path, required=True)

    ingest = commands.add_parser(
        "ingest-source",
        aliases=["source-ingest"],
        help="Boundedly ingest and normalize a public source.",
    )
    ingest.add_argument("--plan", type=Path, required=True)
    ingest.add_argument("--source-id", required=True)
    ingest.add_argument("--input", required=True)
    ingest.add_argument("--format", choices=sorted(SUPPORTED_FORMATS), required=True)
    ingest.add_argument("--max-bytes", type=int, default=10_000_000)
    ingest.add_argument("--max-records", type=int, default=5_000)
    ingest.add_argument("--query-json", default="{}")
    ingest.add_argument("--out", type=Path, required=True)

    reconcile = commands.add_parser(
        "reconcile-finds",
        help="Conservatively reconcile normalized find records.",
    )
    reconcile.add_argument("--input", type=Path, nargs="+", required=True)
    reconcile.add_argument("--out", type=Path, required=True)
    reconcile_run = commands.add_parser(
        "reconcile-entities",
        help="Reconcile only the sealed results declared by a ready run action.",
    )
    reconcile_run.add_argument("--run-dir", type=Path, required=True)
    reconcile_run.add_argument("--action-id", required=True)

    migrate = commands.add_parser("migrate", help="Migrate a v1 plan non-destructively.")
    migrate.add_argument("--plan", type=Path, required=True)
    migrate.add_argument("--out-dir", type=Path, required=True)

    freeze = commands.add_parser(
        "freeze-candidates", help="Hash-bind candidates before ground-truth access."
    )
    freeze.add_argument("--plan", type=Path, required=True)
    freeze.add_argument("--candidates", type=Path, required=True)
    freeze.add_argument("--out-plan", type=Path, required=True)
    freeze.add_argument("--out-seal", type=Path, required=True)

    history = commands.add_parser("report-history", help="Build a sourced history report.")
    history.add_argument("--plan", type=Path, required=True)
    history.add_argument("--out", type=Path, required=True)

    graph_object = commands.add_parser(
        "report-object-graph", help="Build a graph-backed object biography."
    )
    graph_object.add_argument("--plan", type=Path, required=True)
    graph_object.add_argument("--object-node-id", required=True)
    graph_object.add_argument("--out", type=Path, required=True)

    finds = commands.add_parser("report-finds", help="Build a known-finds report.")
    finds.add_argument("--run-dir", type=Path, required=True)
    finds.add_argument("--reconciliation", type=Path, required=True)
    finds.add_argument("--area", required=True)
    finds.add_argument("--public", action="store_true")
    finds.add_argument("--out", type=Path, required=True)

    object_report = commands.add_parser(
        "report-object", help="Build a reconciled object record report."
    )
    object_report.add_argument("--run-dir", type=Path, required=True)
    object_report.add_argument("--reconciliation", type=Path, required=True)
    object_report.add_argument("--entity-id", required=True)
    object_report.add_argument("--public", action="store_true")
    object_report.add_argument("--out", type=Path, required=True)

    material = commands.add_parser(
        "report-material", help="Distinguish material presence from production."
    )
    material.add_argument("--run-dir", type=Path, required=True)
    material.add_argument("--records", type=Path, required=True)
    material.add_argument("--material", required=True)
    material.add_argument("--out", type=Path, required=True)

    gaps = commands.add_parser("report-gaps", help="Report bounded source coverage gaps.")
    gaps.add_argument("--run-dir", type=Path, required=True)
    gaps.add_argument("--input", type=Path, nargs="+", required=True)
    gaps.add_argument("--question", required=True)
    gaps.add_argument("--alias", action="append", default=[])
    gaps.add_argument("--language", action="append", default=[])
    gaps.add_argument("--out", type=Path, required=True)

    probability = commands.add_parser(
        "assess-probability", help="Emit a probability only after calibration gates."
    )
    probability.add_argument("--calibration", type=Path, required=True)
    probability.add_argument("--plan", type=Path)
    probability.add_argument("--exact-high-risk-target", action="store_true")
    probability.add_argument("--out", type=Path, required=True)

    discover = commands.add_parser(
        "source-discover", help="List bounded declared source candidates."
    )
    discover.add_argument("--plan", type=Path, required=True)
    discover.add_argument("--record-type", action="append", default=[])
    discover.add_argument("--out", type=Path, required=True)

    claims = commands.add_parser(
        "extract-claims", help="Extract reviewable claims from normalized records."
    )
    claims.add_argument("--input", type=Path, required=True)
    claims.add_argument("--out", type=Path, required=True)

    advance = commands.add_parser(
        "advance", help="Execute one bounded deterministic batch or emit agent handoff."
    )
    advance.add_argument("--run-dir", type=Path, required=True)
    advance.add_argument("--limit", type=int, default=4)

    run = commands.add_parser(
        "run", help="Repeat bounded deterministic batches until stop or agent handoff."
    )
    run.add_argument("--run-dir", type=Path, required=True)
    run.add_argument("--batch-limit", type=int, default=4)
    run.add_argument("--max-batches", type=int, default=100)

    audit = commands.add_parser("audit", help="Replay and verify a research run.")
    audit.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        extended = handle_extended_command(args)
        if extended is not None:
            return extended
        if args.command == "new":
            if args.rows < 1 or args.columns < 1:
                raise ValueError("rows and columns must be positive")
            if args.rows * args.columns > 10000:
                raise ValueError("coarse initializer is limited to 10,000 cells")
            west, south, east, north = args.bbox
            if west >= east or south >= north:
                raise ValueError("bbox must have west < east and south < north")
            plan = new_plan(
                args.place,
                args.question,
                list(args.bbox),
                args.rows,
                args.columns,
                args.study_kind,
                args.disclosure,
                args.gazetteer_id,
            )
            write_json(args.out, plan)
            print(json.dumps({"out": str(args.out), "planSha256": plan_sha256(plan)}))
            return 0

        if args.command == "init-run":
            state = initialize_run(
                read_json(args.plan),
                args.run_dir,
                **budget_kwargs(args),
                candidate_artifact=args.candidate_artifact,
                candidate_seal=args.candidate_seal,
            )
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0
        if args.command == "next":
            packet = next_task_packet(args.run_dir, args.limit)
            if args.out:
                write_json(args.out, packet)
                print(json.dumps({"out": str(args.out), "runId": packet["runId"]}))
            else:
                print(json.dumps(packet, indent=2, sort_keys=True))
            return 0
        if args.command == "start-action":
            print(
                json.dumps(
                    start_action(
                        args.run_dir,
                        args.action_id,
                        idempotency_key=args.idempotency_key,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command in {"complete-action", "record-result"}:
            print(
                json.dumps(
                    complete_action(
                        args.run_dir,
                        args.action_id,
                        args.attempt_id,
                        result_path=args.result,
                        summary=args.summary,
                        source_ids=args.source_id,
                        acceptance_evidence=args.acceptance_evidence,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "fail-action":
            print(
                json.dumps(
                    fail_action(
                        args.run_dir,
                        args.action_id,
                        args.attempt_id,
                        error=args.error,
                        retryable=args.retryable,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "run-action":
            print(
                json.dumps(
                    execute_deterministic_action(args.run_dir, args.action_id),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "resume":
            print(
                json.dumps(
                    resume_run(args.run_dir, override_stop=args.override_stop),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "stop":
            print(
                json.dumps(
                    stop_run(args.run_dir, args.reason),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "status":
            print(json.dumps(run_status(args.run_dir), indent=2, sort_keys=True))
            return 0
        if args.command == "advance":
            print(
                json.dumps(
                    advance_run(args.run_dir, args.limit),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "run":
            print(
                json.dumps(
                    run_until_handoff(
                        args.run_dir,
                        batch_limit=args.batch_limit,
                        max_batches=args.max_batches,
                    ),
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "audit":
            print(json.dumps(audit_run(args.run_dir), indent=2, sort_keys=True))
            return 0
        if args.command == "reconcile-entities":
            result = execute_deterministic_action(args.run_dir, args.action_id)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.command == "reconcile-finds":
            reconciled = reconcile_artifacts([read_json(path) for path in args.input])
            reconciled["assessment"] = assessment_summary(reconciled)
            write_json(args.out, reconciled)
            print(json.dumps({"out": str(args.out), "entityCount": reconciled["entityCount"]}))
            return 0
        if args.command == "extract-claims":
            extracted = extract_claims(read_json(args.input))
            write_json(args.out, extracted)
            print(
                json.dumps(
                    {"out": str(args.out), "claimCount": extracted["claimCount"]}
                )
            )
            return 0
        if args.command == "migrate":
            migrated, manifest = migrate_plan(read_json(args.plan))
            args.out_dir.mkdir(parents=True, exist_ok=False)
            write_json(args.out_dir / "plan.json", migrated)
            write_json(args.out_dir / "migration.json", manifest)
            print(
                json.dumps(
                    {
                        "outDir": str(args.out_dir),
                        "migratedPlanSha256": manifest["migratedPlanSha256"],
                    }
                )
            )
            return 0
        if args.command == "freeze-candidates":
            plan = read_json(args.plan)
            candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
            frozen, seal = freeze_candidates(plan, candidates, args.candidates)
            write_json(args.out_plan, frozen)
            write_json(args.out_seal, seal)
            print(
                json.dumps(
                    {
                        "outPlan": str(args.out_plan),
                        "outSeal": str(args.out_seal),
                        "candidateArtifactSha256": seal["candidateArtifactSha256"],
                    }
                )
            )
            return 0
        if args.command == "report-finds":
            reconciliation, _, _ = read_sealed_report_input(
                args.run_dir,
                args.reconciliation,
                {"archaeological-find-reconciliation-1.0"},
            )
            report = build_finds_report(
                reconciliation,
                area_description=args.area,
                public=args.public,
            )
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "findCount": len(report["finds"])}))
            return 0
        if args.command == "report-object":
            reconciliation, _, _ = read_sealed_report_input(
                args.run_dir,
                args.reconciliation,
                {"archaeological-find-reconciliation-1.0"},
            )
            report = build_object_report(
                reconciliation,
                args.entity_id,
                public=args.public,
            )
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "entityId": args.entity_id}))
            return 0
        if args.command == "report-material":
            artifact, _, _ = read_sealed_report_input(
                args.run_dir,
                args.records,
                {"archaeological-find-records-1.0"},
            )
            records = artifact.get("records")
            if not isinstance(records, list):
                raise ValueError("records artifact must contain a records array")
            report = build_material_evidence_report(records, args.material)
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "conclusion": report["conclusion"]}))
            return 0
        if args.command == "report-gaps":
            inputs = read_sealed_report_inputs(
                args.run_dir,
                args.input,
                {
                    "archaeological-find-records-1.0",
                    "archaeological-find-reconciliation-1.0",
                },
            )
            report = build_source_gap_report(
                inputs,
                question=args.question,
                aliases=args.alias,
                languages=args.language,
            )
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "judgment": report["judgment"]}))
            return 0
        if args.command == "assess-probability":
            calibration = read_json(args.calibration)
            case = None
            if args.plan:
                probability_plan = read_json(args.plan)
                validation = validate_plan(probability_plan)
                if not validation.valid:
                    raise ValueError(
                        "probability plan is invalid: " + "; ".join(validation.errors)
                    )
                case = probability_plan.get("case", {})
            report = calibrated_probability_report(
                calibration,
                case=case,
                exact_high_risk_target=args.exact_high_risk_target,
            )
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "disclosure": report["disclosure"]}))
            return 0

        plan = read_json(args.plan)
        if args.command == "validate":
            return validate_command(plan, args.ready)

        result = validate_plan(plan)
        if not result.valid:
            for error in result.errors:
                print(f"error: {error}", file=sys.stderr)
            return 2
        if args.command == "rank":
            if args.limit < 1:
                raise ValueError("limit must be positive")
            research_errors = readiness_errors(plan) + execution_readiness_errors(plan)
            if research_errors and not args.allow_draft:
                for error in research_errors:
                    print(f"error: {error}", file=sys.stderr)
                return 2
            frontier = build_frontier(plan, args.limit)
            frontier["planningPreviewOnly"] = bool(research_errors)
            frontier["readinessErrors"] = research_errors
            write_json(args.out, frontier)
            print(json.dumps({"out": str(args.out), "sourcePlanSha256": plan_sha256(plan)}))
            return 0
        if args.command == "export-public":
            write_json(args.out, public_export(plan, args.schema))
            print(json.dumps({"out": str(args.out), "sourcePlanSha256": plan_sha256(plan)}))
            return 0
        if args.command == "report-history":
            report = build_history_report(plan)
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "timeSlices": len(report["timeSlices"])}))
            return 0
        if args.command == "report-object-graph":
            report = build_object_biography(plan, args.object_node_id)
            write_json(args.out, report)
            print(json.dumps({"out": str(args.out), "objectNodeId": args.object_node_id}))
            return 0
        if args.command == "source-discover":
            discovery = discover_source_candidates(
                plan,
                record_types=set(args.record_type) if args.record_type else None,
            )
            write_json(args.out, discovery)
            print(
                json.dumps(
                    {
                        "out": str(args.out),
                        "candidateCount": discovery["candidateCount"],
                    }
                )
            )
            return 0
        if args.command in {"ingest-source", "source-ingest"}:
            source = next(
                (
                    item
                    for item in plan.get("sources", [])
                    if isinstance(item, dict) and item.get("sourceId") == args.source_id
                ),
                None,
            )
            if source is None:
                raise ValueError(f"unknown source: {args.source_id}")
            acquisition = source.get("acquisition")
            if (
                not isinstance(acquisition, dict)
                or acquisition.get("locator") != args.input
                or acquisition.get("format") != args.format
            ):
                raise ValueError("ingestion input does not match the declared source contract")
            query = json.loads(args.query_json)
            if not isinstance(query, dict):
                raise ValueError("query-json must decode to an object")
            verify_source_acquisition(
                source,
                actual_locator=args.input,
                inputs={
                    "sourceId": args.source_id,
                    "locator": args.input,
                    "format": args.format,
                    "query": query,
                },
            )
            artifact = acquire_and_normalize(
                source=source,
                locator=args.input,
                format_name=args.format,
                out=args.out,
                max_bytes=args.max_bytes,
                max_records=args.max_records,
                query=query,
            )
            print(
                json.dumps(
                    {
                        "out": str(args.out),
                        "resultCount": artifact["queryArtifact"]["resultCount"],
                    }
                )
            )
            return 0
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RecursionError,
        json.JSONDecodeError,
    ) as error:
        print(diagnostic_json(error), file=sys.stderr)
        return error_code(error)[1]
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
