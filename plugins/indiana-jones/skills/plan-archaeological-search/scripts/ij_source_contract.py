from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ij_ingest_guard import automation_access_problem
from ij_journal import file_sha256, value_sha256


SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_FIELDS = (
    "sourceId",
    "title",
    "workflowRole",
    "recordType",
    "originFamilyId",
    "accessBasis",
    "license",
    "url",
    "providerTerms",
)


def source_identity_sha256(source: dict[str, Any]) -> str:
    return value_sha256(
        {field: source.get(field) for field in IDENTITY_FIELDS if field in source}
    )


def acquisition_contract(
    source: dict[str, Any],
    *,
    locator: str,
    format_name: str,
    query: dict[str, Any],
    snapshot_sha256: str | None = None,
    retrieved_at: str | None = None,
) -> dict[str, Any]:
    contract = {
        "kind": "remote-public" if urlparse(locator).scheme else "local-snapshot",
        "locator": locator,
        "format": format_name,
        "sourceIdentitySha256": source_identity_sha256(source),
        "querySha256": value_sha256(query),
    }
    if snapshot_sha256 is not None:
        contract["snapshotSha256"] = snapshot_sha256
    if retrieved_at is not None:
        contract["retrievedAt"] = retrieved_at
    return contract


def acquisition_contract_errors(
    source: dict[str, Any],
    inputs: dict[str, Any],
) -> list[str]:
    source_id = source.get("sourceId", "<unknown>")
    prefix = f"source {source_id} acquisition"
    acquisition = source.get("acquisition")
    if not isinstance(acquisition, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    for field in ("locator", "format"):
        if acquisition.get(field) != inputs.get(field):
            errors.append(f"{prefix} {field} does not match action input")
    expected_identity = source_identity_sha256(source)
    if acquisition.get("sourceIdentitySha256") != expected_identity:
        errors.append(f"{prefix} sourceIdentitySha256 is missing or stale")
    query = inputs.get("query", {})
    if acquisition.get("querySha256") != value_sha256(query):
        errors.append(f"{prefix} querySha256 is missing or stale")
    locator = acquisition.get("locator")
    remote = isinstance(locator, str) and urlparse(locator).scheme in {"http", "https"}
    expected_kind = "remote-public" if remote else "local-snapshot"
    if acquisition.get("kind") != expected_kind:
        errors.append(f"{prefix} kind must be {expected_kind}")
    if remote:
        if source.get("accessBasis") != "public":
            errors.append(f"{prefix} remote automation requires public accessBasis")
        access_problem = automation_access_problem(source, str(locator))
        if access_problem:
            errors.append(f"{prefix} {access_problem}")
    else:
        digest = acquisition.get("snapshotSha256")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            errors.append(f"{prefix} snapshotSha256 must be a SHA-256 digest")
        retrieved = acquisition.get("retrievedAt")
        if not isinstance(retrieved, str) or not retrieved.strip():
            errors.append(f"{prefix} retrievedAt is required for a local snapshot")
    resume_pages = acquisition.get("resumePages")
    if resume_pages is not None:
        if not isinstance(resume_pages, list) or not resume_pages:
            errors.append(f"{prefix} resumePages must be a non-empty array")
        else:
            cursors: set[str] = set()
            for index, page in enumerate(resume_pages):
                if not isinstance(page, dict):
                    errors.append(f"{prefix} resumePages[{index}] must be an object")
                    continue
                cursor = page.get("cursor")
                if not isinstance(cursor, str) or not cursor or cursor in cursors:
                    errors.append(f"{prefix} resumePages[{index}] cursor is invalid")
                else:
                    cursors.add(cursor)
                if not isinstance(page.get("locator"), str) or not page["locator"]:
                    errors.append(f"{prefix} resumePages[{index}] locator is invalid")
                digest = page.get("snapshotSha256")
                if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                    errors.append(
                        f"{prefix} resumePages[{index}] snapshotSha256 is invalid"
                    )
                if not isinstance(page.get("retrievedAt"), str) or not page["retrievedAt"]:
                    errors.append(f"{prefix} resumePages[{index}] retrievedAt is required")
    return errors


def acquisition_binding_errors(plan: dict[str, Any]) -> list[str]:
    sources = {
        source.get("sourceId"): source
        for source in plan.get("sources", [])
        if isinstance(source, dict) and isinstance(source.get("sourceId"), str)
    }
    errors: list[str] = []
    for action in plan.get("actions", []):
        if not isinstance(action, dict) or action.get("status") != "planned":
            continue
        spec = action.get("execution")
        inputs = spec.get("inputs") if isinstance(spec, dict) else None
        if not isinstance(inputs, dict) or spec.get("executor") != "ingest-source":
            continue
        source = sources.get(inputs.get("sourceId"))
        if source is None:
            errors.append(
                f"action {action.get('actionId')} references an unknown ingest source"
            )
            continue
        errors.extend(acquisition_contract_errors(source, inputs))
    return errors


def verify_source_acquisition(
    source: dict[str, Any],
    *,
    actual_locator: str,
    inputs: dict[str, Any],
) -> None:
    errors = acquisition_contract_errors(source, inputs)
    acquisition = source.get("acquisition")
    if isinstance(acquisition, dict) and acquisition.get("kind") == "local-snapshot":
        path = Path(actual_locator)
        if not path.is_file():
            errors.append(f"declared local snapshot is not a file: {path}")
        elif file_sha256(path) != acquisition.get("snapshotSha256"):
            errors.append("local snapshot bytes do not match snapshotSha256")
    elif isinstance(acquisition, dict) and actual_locator != acquisition.get("locator"):
        errors.append("remote locator does not match the declared source endpoint")
    if errors:
        raise ValueError("; ".join(errors))
