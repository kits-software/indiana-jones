from __future__ import annotations

from pathlib import Path
from typing import Any

from ij_claims import extract_claims
from ij_ingest import discover_source_candidates
from ij_orchestrator import (
    advance_run,
    audit_run,
    run_until_handoff,
)


def discover_declared_sources(plan: dict[str, Any]) -> dict[str, Any]:
    return discover_source_candidates(plan)


def extract_record_claims(artifact: dict[str, Any]) -> dict[str, Any]:
    return extract_claims(artifact)


def run_until_pause(
    run_dir: Path,
    max_steps: int = 100,
    limit: int = 4,
) -> dict[str, Any]:
    return run_until_handoff(
        run_dir,
        batch_limit=limit,
        max_batches=max_steps,
    )


__all__ = [
    "advance_run",
    "audit_run",
    "discover_declared_sources",
    "extract_record_claims",
    "run_until_handoff",
    "run_until_pause",
]
