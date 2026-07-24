from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlparse

from ij_common import atomic_write_json, load_json, sha256_file, stable_id, utc_now


SOURCE_KINDS = {
    "primary-measurement",
    "authoritative-record",
    "contemporary-account",
    "secondary-summary",
    "lead-only",
}
ACCESS_BASES = {"public", "local-user-provided", "user-authorized"}
DISCLOSURE_CLASSES = {"public", "restricted", "heritage-authority-only"}


def new_case(
    title: str,
    question: str,
    study_area: str,
    disclosure: str,
    authorized_platforms: Iterable[str],
) -> Dict[str, Any]:
    if disclosure not in DISCLOSURE_CLASSES:
        raise ValueError(f"Unsupported disclosure class: {disclosure}")
    created_at = utc_now()
    platforms = sorted({item.strip().lower() for item in authorized_platforms if item.strip()})
    return {
        "schemaVersion": "1.0",
        "caseId": stable_id("ij", f"{title}|{question}|{created_at}"),
        "title": title,
        "question": question,
        "createdAt": created_at,
        "status": "intake",
        "scope": {
            "studyArea": study_area,
            "intent": "candidate survey",
            "disclosure": disclosure,
            "publicPrecision": "region-only" if disclosure != "public" else "case-defined",
        },
        "authorization": {
            "publicWeb": True,
            "authenticatedPlatforms": platforms,
            "writeActions": False,
            "fieldActions": False,
        },
        "sources": [],
        "derivedArtifacts": [],
        "claims": [],
        "candidates": [],
        "rejectedExplanations": [],
        "missingEvidence": [],
    }


def _is_url(locator: str) -> bool:
    parsed = urlparse(locator)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _platform_from_url(locator: str) -> str:
    host = (urlparse(locator).hostname or "").lower()
    if "facebook.com" in host or host == "fb.com":
        return "facebook"
    return host


def add_source(
    case_path: Path,
    locator: str,
    kind: str,
    access_basis: str,
    license_name: str,
    notes: str,
    platform: str,
) -> Dict[str, Any]:
    if kind not in SOURCE_KINDS:
        raise ValueError(f"Unsupported source kind: {kind}")
    if access_basis not in ACCESS_BASES:
        raise ValueError(f"Unsupported access basis: {access_basis}")

    case = load_json(case_path)
    authorization = case.get("authorization", {})
    normalized_platform = platform.strip().lower()
    if _is_url(locator):
        inferred_platform = _platform_from_url(locator)
        normalized_platform = normalized_platform or inferred_platform
        content_hash = None
    else:
        local_path = Path(locator).expanduser().resolve()
        if not local_path.is_file():
            raise ValueError(f"Local source does not exist: {local_path}")
        locator = str(local_path)
        content_hash = sha256_file(local_path)

    if access_basis == "user-authorized":
        allowed = {str(item).lower() for item in authorization.get("authenticatedPlatforms", [])}
        if not normalized_platform or normalized_platform not in allowed:
            raise ValueError(
                f"Platform '{normalized_platform or 'unknown'}' is not authorized in this case"
            )
    elif normalized_platform in {"facebook", "instagram", "linkedin"}:
        raise ValueError(
            f"Use access basis user-authorized and record explicit {normalized_platform} authorization"
        )

    source = {
        "sourceId": stable_id("src", f"{locator}|{content_hash or ''}"),
        "kind": kind,
        "locator": locator,
        "accessBasis": access_basis,
        "platform": normalized_platform or None,
        "accessedAt": utc_now(),
        "sha256": content_hash,
        "license": license_name or "unknown",
        "sensor": None,
        "acquiredAt": None,
        "crs": None,
        "resolution": None,
        "notes": notes,
    }
    sources: List[Dict[str, Any]] = list(case.get("sources", []))
    if any(item.get("sourceId") == source["sourceId"] for item in sources):
        raise ValueError(f"Source is already recorded: {source['sourceId']}")
    sources.append(source)
    case["sources"] = sources
    atomic_write_json(case_path, case)
    return source


def validate_case(case: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in ("schemaVersion", "caseId", "title", "question", "scope", "authorization"):
        if key not in case:
            errors.append(f"Missing required key: {key}")
    scope = case.get("scope", {})
    if scope.get("disclosure") not in DISCLOSURE_CLASSES:
        errors.append("scope.disclosure is invalid")
    authorization = case.get("authorization", {})
    authorized_platforms = {
        str(item).strip().lower()
        for item in authorization.get("authenticatedPlatforms", [])
        if str(item).strip()
    }
    if authorization.get("writeActions") is not False:
        errors.append("writeActions must remain false in the case ledger")
    if authorization.get("fieldActions") is not False:
        errors.append("fieldActions must remain false in the case ledger")
    seen = set()
    for index, source in enumerate(case.get("sources", [])):
        source_id = source.get("sourceId")
        if not source_id:
            errors.append(f"sources[{index}] has no sourceId")
        elif source_id in seen:
            errors.append(f"Duplicate sourceId: {source_id}")
        seen.add(source_id)
        if source.get("kind") not in SOURCE_KINDS:
            errors.append(f"sources[{index}].kind is invalid")
        if source.get("accessBasis") not in ACCESS_BASES:
            errors.append(f"sources[{index}].accessBasis is invalid")
        normalized_platform = str(source.get("platform") or "").strip().lower()
        if source.get("accessBasis") == "user-authorized":
            if not normalized_platform or normalized_platform not in authorized_platforms:
                errors.append(
                    f"sources[{index}].platform is not authorized for this case"
                )
        elif normalized_platform in {"facebook", "instagram", "linkedin"}:
            errors.append(
                f"sources[{index}] requires user-authorized access for {normalized_platform}"
            )
    return errors
