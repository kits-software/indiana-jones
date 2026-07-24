from __future__ import annotations

from pathlib import Path
from typing import Any

from ij_artifacts import read_json
from ij_results import run_path
from ij_runtime import load_run


def read_sealed_report_input(
    run_dir: Path,
    input_path: Path,
    allowed_schemas: set[str],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    plan, _, state = load_run(run_dir)
    resolved = input_path.resolve() if input_path.is_absolute() else run_path(
        run_dir, str(input_path)
    )
    try:
        relative = str(resolved.relative_to(run_dir.resolve()))
    except ValueError as error:
        raise ValueError("report input must be retained inside the run directory") from error
    result_ref = next(
        (
            result
            for action in state["actions"].values()
            if action.get("status") == "completed"
            for result in action.get("resultRefs", [])
            if isinstance(result, dict) and result.get("path") == relative
        ),
        None,
    )
    if result_ref is None:
        raise ValueError("report input is not a sealed completed-action result")
    artifact = read_json(resolved)
    if artifact.get("schemaVersion") not in allowed_schemas:
        raise ValueError("sealed report input has an unsupported schema")
    return artifact, result_ref, plan


def read_sealed_report_inputs(
    run_dir: Path,
    input_paths: list[Path],
    allowed_schemas: set[str],
) -> list[dict[str, Any]]:
    if not input_paths or len(input_paths) > 100:
        raise ValueError("report requires 1-100 sealed input artifacts")
    return [
        read_sealed_report_input(run_dir, path, allowed_schemas)[0]
        for path in input_paths
    ]
