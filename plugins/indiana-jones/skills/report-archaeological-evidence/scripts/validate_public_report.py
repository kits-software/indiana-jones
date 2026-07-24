from __future__ import annotations

import argparse
import ipaddress
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
from urllib.parse import parse_qsl, urlparse

from PIL import Image


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".html"}
PROTECTED_LOCATION_CLASSES = {"vulnerable", "sacred", "burial", "non-public"}
RESTRICTED_SPATIAL_VALUES = {
    "withhold",
    "authority-only",
    "restricted",
    "private",
    "non-public",
    "vulnerable",
    "sacred",
    "burial",
}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "auth",
    "credential",
    "expires",
    "key",
    "secret",
    "sig",
    "signature",
    "token",
    "x-amz-signature",
    "x-goog-signature",
}


def issue(path: Path, code: str, detail: str) -> Dict[str, str]:
    return {"path": str(path), "code": code, "detail": detail}


def _unsafe_public_reference(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme == "file":
        return True
    if parsed.scheme in {"http", "https"}:
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            return True
        if parsed.hostname.casefold() == "localhost":
            return True
        try:
            if ipaddress.ip_address(parsed.hostname).is_private:
                return True
        except ValueError:
            pass
        query_keys = {key.casefold() for key, _ in parse_qsl(parsed.query)}
        return bool(query_keys.intersection(SENSITIVE_QUERY_KEYS))
    candidate = Path(value)
    return candidate.is_absolute() or ".." in candidate.parts or value.startswith("~")


def _point_pair(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in value
        )
    )


def _clickable_google_maps_link(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname in {"google.com", "www.google.com", "maps.google.com"}
        and parsed.path.startswith("/maps")
    )


def _spatial_payload(current: Mapping[str, Any]) -> bool:
    if current.get("type") == "Feature":
        geometry = current.get("geometry")
        return isinstance(geometry, dict) and geometry.get("type") in {
            "Point",
            "Polygon",
        }
    if any(
        current.get(key) not in (None, "", [], {})
        for key in (
            "coordinate",
            "coordinates",
            "geometry",
            "bbox",
            "imagePoint",
            "imageFootprint",
        )
    ):
        return True
    return any(key in current for key in ("latitude", "longitude"))


def _public_spatial_classification(current: Mapping[str, Any]) -> tuple[Any, Any]:
    if current.get("type") == "Feature":
        properties = current.get("properties")
        if isinstance(properties, dict):
            return properties.get("sensitivity"), properties.get(
                "spatialRestriction"
            )
    return current.get("sensitivity"), current.get("spatialRestriction")


def _point_link_issue(
    path: Path,
    current: Mapping[str, Any],
    current_path: str,
) -> Optional[Dict[str, str]]:
    if current.get("type") == "Feature":
        geometry = current.get("geometry")
        if (
            isinstance(geometry, dict)
            and geometry.get("type") == "Point"
            and _point_pair(geometry.get("coordinates"))
        ):
            properties = current.get("properties")
            link = (
                properties.get("googleMapsLink")
                if isinstance(properties, dict)
                else None
            )
            if not _clickable_google_maps_link(link):
                return issue(
                    path,
                    "missing-google-maps-link",
                    f"{current_path} Point feature lacks a clickable Google Maps link",
                )
        return None

    direct_point = current.get("coordinate")
    if direct_point is None and current.get("type") not in {"Point", "Polygon"}:
        direct_point = current.get("coordinates")
    if _point_pair(direct_point) and not _clickable_google_maps_link(
        current.get("googleMapsLink")
    ):
        return issue(
            path,
            "missing-google-maps-link",
            f"{current_path} point lacks a clickable Google Maps link",
        )

    if _point_pair(current.get("imagePoint")) and not _clickable_google_maps_link(
        current.get("imagePointGoogleMapsLink")
    ):
        return issue(
            path,
            "missing-google-maps-link",
            f"{current_path}.imagePoint lacks a clickable Google Maps link",
        )
    return None


def _nested_public_issues(path: Path, payload: Mapping[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    stack: List[tuple[Any, str, int, bool]] = [(payload, "$", 0, False)]
    inspected = 0
    while stack:
        current, current_path, depth, inherited_public = stack.pop()
        inspected += 1
        if inspected > 100_000 or depth > 64:
            issues.append(
                issue(path, "public-structure-limit", f"Unsafe nesting at {current_path}")
            )
            break
        if isinstance(current, dict):
            point_issue = _point_link_issue(path, current, current_path)
            if point_issue:
                issues.append(point_issue)
            if current.get("locationClass") in PROTECTED_LOCATION_CLASSES:
                issues.append(
                    issue(
                        path,
                        "protected-public-location",
                        f"{current_path}.locationClass cannot be public",
                    )
                )
            if current.get("spatialRestriction") in RESTRICTED_SPATIAL_VALUES:
                issues.append(
                    issue(
                        path,
                        "restricted-spatial-evidence",
                        f"{current_path} carries a non-public spatial restriction",
                    )
                )
            if (
                current.get("sensitivity") in RESTRICTED_SPATIAL_VALUES
                and any(
                    key in current
                    for key in (
                        "coordinate",
                        "coordinates",
                        "geometry",
                        "findspot",
                        "location",
                    )
                )
            ):
                issues.append(
                    issue(
                        path,
                        "restricted-spatial-evidence",
                        f"{current_path} combines non-public sensitivity with spatial data",
                    )
                )
            sensitivity, spatial_restriction = _public_spatial_classification(
                current
            )
            declared_classification = (
                sensitivity is not None or spatial_restriction is not None
            )
            explicitly_public = (
                sensitivity == "public"
                or spatial_restriction == "public"
                or (inherited_public and not declared_classification)
            )
            if (
                _spatial_payload(current)
                and not explicitly_public
            ):
                issues.append(
                    issue(
                        path,
                        "unclassified-spatial-evidence",
                        f"{current_path} spatial evidence is not explicitly public",
                    )
                )
            for key, nested in current.items():
                key_folded = str(key).casefold().replace("_", "").replace("-", "")
                if (
                    ("restricted" in key_folded or "private" in key_folded)
                    and any(
                        token in key_folded
                        for token in (
                            "location",
                            "geometry",
                            "coordinate",
                            "findspot",
                            "url",
                            "locator",
                            "path",
                        )
                    )
                    and nested not in (None, "", [], {})
                ):
                    issues.append(
                        issue(
                            path,
                            "forbidden-location-field",
                            f"{current_path}.{key} is explicitly non-public",
                        )
                    )
                if (
                    isinstance(nested, str)
                    and any(
                        token in key_folded for token in ("url", "locator", "path")
                    )
                    and _unsafe_public_reference(nested)
                ):
                    issues.append(
                        issue(
                            path,
                            "unsafe-public-reference",
                            f"{current_path}.{key} contains a private or signed reference",
                        )
                    )
                stack.append(
                    (
                        nested,
                        f"{current_path}.{key}",
                        depth + 1,
                        explicitly_public,
                    )
                )
        elif isinstance(current, list):
            for index, nested in enumerate(current):
                stack.append(
                    (
                        nested,
                        f"{current_path}[{index}]",
                        depth + 1,
                        inherited_public,
                    )
                )
    return issues


def scan_json(path: Path) -> List[Dict[str, str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [issue(path, "invalid-json", str(error))]
    if not isinstance(payload, dict):
        return [issue(path, "invalid-json-root", "JSON artifact must be an object")]
    issues: List[Dict[str, str]] = []
    if "disclosure" in payload and payload["disclosure"] != "public":
        issues.append(
            issue(
                path,
                "non-public-disclosure",
                "Artifact passed to public validation is not marked public",
            )
        )
    issues.extend(_nested_public_issues(path, payload))
    return issues


def scan_text(path: Path) -> List[Dict[str, str]]:
    try:
        path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [issue(path, "unreadable-text", str(error))]
    return []


def scan_image(path: Path) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            if exif:
                issues.append(
                    issue(path, "embedded-exif", "Public image retains EXIF metadata")
                )
            suspicious = [
                key
                for key in image.info
                if any(
                    token in str(key).lower()
                    for token in ("exif", "gps", "location", "comment", "description", "xml")
                )
            ]
            if suspicious:
                issues.append(
                    issue(
                        path,
                        "embedded-image-metadata",
                        "Unreviewed embedded metadata fields: "
                        + ", ".join(suspicious),
                    )
                )
    except (OSError, ValueError) as error:
        issues.append(issue(path, "unreadable-image", str(error)))
    return issues


def scan_path(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        return [issue(path, "missing-file", "Artifact does not exist")]
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return scan_image(path)
    if suffix == ".json":
        return scan_json(path)
    if suffix in TEXT_SUFFIXES:
        return scan_text(path)
    return [
        issue(
            path,
            "unsupported-artifact",
            f"Cannot validate public artifact type {suffix or '<none>'}",
        )
    ]


def atomic_write_json(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".json",
        dir=str(path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check public archaeology artifacts for readability, disclosure "
            "mismatches, missing Google Maps point links, and unreviewed "
            "embedded image metadata"
        )
    )
    parser.add_argument("artifacts", type=Path, nargs="+")
    parser.add_argument("--out", type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    all_issues = [
        current
        for artifact in args.artifacts
        for current in scan_path(artifact)
    ]
    result = {
        "schemaVersion": "2.0",
        "artifactCount": len(args.artifacts),
        "status": "pass" if not all_issues else "fail",
        "issues": all_issues,
        "spatialEvidencePolicy": (
            "Declared coordinates, map links, points, AOIs, and image footprints "
            "are intentional report evidence and are not treated as leaks. Every "
            "declared point must expose a clickable Google Maps link."
        ),
        "claimBoundary": (
            "This bounded check validates artifact handling only. It does not "
            "replace review of applicable law, source terms, community protocols, "
            "personal privacy, or field-access permissions."
        ),
    }
    if args.out:
        atomic_write_json(result, args.out)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not all_issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
