from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from PIL import Image


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".html"}
FORBIDDEN_KEYS = {
    "accessroute",
    "bbox",
    "boundingbox",
    "cadastralreference",
    "coordinates",
    "easting",
    "latitude",
    "longitude",
    "northing",
    "precisecoordinates",
    "quadkey",
    "restrictedlocation",
    "tileid",
    "xmax",
    "xmin",
    "ymax",
    "ymin",
}
COORDINATE_PAIR = re.compile(
    r"(?<![\d.])[-+]?\d{1,2}\.\d{4,}\s*[,/]\s*"
    r"[-+]?\d{1,3}\.\d{4,}(?![\d.])"
)
LOCATION_PARAMETER = re.compile(
    r"(?i)(?:[?&](?:lat|latitude|lon|lng|longitude|bbox|tile|quadkey)=)"
)
FILENAME_LOCATION = re.compile(
    r"(?i)(?:^|[-_.])(?:lat|latitude|lon|lng|longitude|bbox|tile|quadkey)"
)
FILENAME_COORDINATES = re.compile(
    r"(?i)(?:^|[-_.])(?:[NS])?\d{1,2}\.\d{3,}[-_]"
    r"(?:[EW])?\d{1,3}\.\d{3,}(?:[-_.]|$)"
)


def issue(path: Path, code: str, detail: str) -> Dict[str, str]:
    return {"path": str(path), "code": code, "detail": detail}


def scan_string(path: Path, value: str, field: str) -> List[Dict[str, str]]:
    issues = []
    if COORDINATE_PAIR.search(value):
        issues.append(
            issue(path, "coordinate-pair", f"High-precision coordinate-like pair in {field}")
        )
    if LOCATION_PARAMETER.search(value):
        issues.append(
            issue(path, "location-url-parameter", f"Location parameter in {field}")
        )
    return issues


def scan_json_value(
    path: Path,
    value: Any,
    field: str = "$",
) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
            child_field = f"{field}.{key}"
            if normalized == "containsprecisecoordinates":
                if child is not False:
                    issues.append(
                        issue(
                            path,
                            "precise-coordinate-flag",
                            f"{child_field} must be false in a public artifact",
                        )
                    )
            elif normalized in FORBIDDEN_KEYS:
                issues.append(
                    issue(
                        path,
                        "forbidden-location-field",
                        f"Public artifact contains {child_field}",
                    )
                )
            if (
                isinstance(child, str)
                and normalized.endswith("filename")
                and (
                    FILENAME_LOCATION.search(child)
                    or FILENAME_COORDINATES.search(child)
                )
            ):
                issues.append(
                    issue(
                        path,
                        "location-bearing-filename",
                        f"{child_field} contains a location-bearing filename",
                    )
                )
            issues.extend(scan_json_value(path, child, child_field))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(scan_json_value(path, child, f"{field}[{index}]"))
    elif isinstance(value, str):
        issues.extend(scan_string(path, value, field))
    return issues


def scan_json(path: Path) -> List[Dict[str, str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [issue(path, "invalid-json", str(error))]
    issues = scan_json_value(path, payload)
    if isinstance(payload, dict) and "disclosure" in payload:
        if payload["disclosure"] != "public":
            issues.append(
                issue(
                    path,
                    "non-public-disclosure",
                    "Artifact passed to public validation is not marked public",
                )
            )
    return issues


def scan_text(path: Path) -> List[Dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return [issue(path, "unreadable-text", str(error))]
    return scan_string(path, text, "text")


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
                        "Potentially sensitive metadata fields: " + ", ".join(suspicious),
                    )
                )
    except (OSError, ValueError) as error:
        issues.append(issue(path, "unreadable-image", str(error)))
    return issues


def scan_path(path: Path) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if not path.is_file():
        return [issue(path, "missing-file", "Artifact does not exist")]
    if FILENAME_LOCATION.search(path.name) or FILENAME_COORDINATES.search(path.name):
        issues.append(
            issue(
                path,
                "location-bearing-filename",
                "Public filename contains a location-bearing token",
            )
        )
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        issues.extend(scan_image(path))
    elif suffix == ".json":
        issues.extend(scan_json(path))
    elif suffix in TEXT_SUFFIXES:
        issues.extend(scan_text(path))
    else:
        issues.append(
            issue(
                path,
                "unsupported-artifact",
                f"Cannot validate public artifact type {suffix or '<none>'}",
            )
        )
    return issues


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
        description="Check public archaeology reports for obvious location leakage"
    )
    parser.add_argument("artifacts", type=Path, nargs="+")
    parser.add_argument("--out", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    all_issues = [
        current
        for artifact in args.artifacts
        for current in scan_path(artifact)
    ]
    result = {
        "schemaVersion": "1.0",
        "artifactCount": len(args.artifacts),
        "status": "pass" if not all_issues else "fail",
        "issues": all_issues,
        "claimBoundary": (
            "This bounded check cannot prove that a public report is safe; "
            "manual disclosure review remains required."
        ),
    }
    if args.out:
        atomic_write_json(result, args.out)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not all_issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
