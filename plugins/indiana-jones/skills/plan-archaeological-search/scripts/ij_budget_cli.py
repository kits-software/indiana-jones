from __future__ import annotations

import argparse
from typing import Any


def add_budget_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-actions", type=int, default=100)
    parser.add_argument("--max-attempts", type=int, default=200)
    parser.add_argument("--max-result-bytes", type=int, default=100_000_000)
    parser.add_argument("--max-seconds", type=int, default=86_400)
    parser.add_argument("--max-requests", type=int, default=200)
    parser.add_argument("--max-requests-per-provider", type=int, default=200)
    parser.add_argument("--max-records", type=int, default=100_000)
    parser.add_argument("--max-consecutive-no-novelty", type=int, default=100)


def budget_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "max_actions": args.max_actions,
        "max_attempts": args.max_attempts,
        "max_result_bytes": args.max_result_bytes,
        "max_seconds": args.max_seconds,
        "max_requests": args.max_requests,
        "max_requests_per_provider": args.max_requests_per_provider,
        "max_records": args.max_records,
        "max_consecutive_no_novelty": args.max_consecutive_no_novelty,
    }
