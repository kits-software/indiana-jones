from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from ij_common import load_json, sha256_file, utc_now


OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
OSM_LABEL_TAGS = {
    "historic",
    "heritage",
    "heritage:operator",
    "site_type",
    "archaeological_site",
    "name",
    "alt_name",
    "old_name",
    "description",
    "wikidata",
    "wikipedia",
}
GEOGRAPHIC_CRS_NAMES = {
    "EPSG:4326",
    "OGC:CRS84",
    "CRS:84",
    "WGS84",
    "WGS 84",
}


def validate_projected_crs(crs: str, coordinate_unit: str) -> str:
    normalized = crs.strip().upper()
    if not normalized:
        raise ValueError("A projected metric CRS is required")
    if normalized in GEOGRAPHIC_CRS_NAMES:
        raise ValueError(
            "Geographic longitude/latitude is not metric; reproject the raster to a local "
            "projected CRS such as its UTM zone"
        )
    if not (
        re.fullmatch(r"EPSG:\d+", normalized)
        or normalized.startswith("PROJCRS[")
        or normalized.startswith("+PROJ=")
    ):
        raise ValueError("CRS must be an EPSG identifier, PROJCRS WKT, or PROJ string")
    if coordinate_unit.strip().lower() not in {"metre", "meter"}:
        raise ValueError(
            "Detector kernels are expressed in metres; reproject feet-based or other "
            "rasters before registration"
        )
    return crs.strip()


def validate_metric_bbox(
    bbox: Sequence[float],
    max_area_km2: float = 100.0,
) -> Tuple[float, float, float, float]:
    if len(bbox) != 4:
        raise ValueError("bbox must contain X_MIN Y_MIN X_MAX Y_MAX")
    x_min, y_min, x_max, y_max = [float(value) for value in bbox]
    if not all(math.isfinite(value) for value in (x_min, y_min, x_max, y_max)):
        raise ValueError("bbox values must be finite")
    if not (x_min < x_max and y_min < y_max):
        raise ValueError("bbox must be X_MIN Y_MIN X_MAX Y_MAX")
    area_km2 = (x_max - x_min) * (y_max - y_min) / 1_000_000.0
    if area_km2 > max_area_km2:
        raise ValueError(
            f"bbox area {area_km2:.2f} km² exceeds the {max_area_km2:.2f} km² "
            "analysis safety limit; tile the study area"
        )
    return x_min, y_min, x_max, y_max


def validate_wgs84_bbox(
    bbox: Sequence[float],
    max_area_km2: float = 100.0,
) -> Tuple[float, float, float, float]:
    if len(bbox) != 4:
        raise ValueError("bbox must contain SOUTH WEST NORTH EAST")
    south, west, north, east = [float(value) for value in bbox]
    if not (-90.0 <= south < north <= 90.0):
        raise ValueError("latitude bounds must satisfy -90 <= south < north <= 90")
    if not (-180.0 <= west < east <= 180.0):
        raise ValueError("longitude bounds must satisfy -180 <= west < east <= 180")
    center_latitude = math.radians((south + north) / 2.0)
    height_km = (north - south) * 111.32
    width_km = (east - west) * 111.32 * max(math.cos(center_latitude), 0.01)
    area_km2 = height_km * width_km
    if area_km2 > max_area_km2:
        raise ValueError(
            f"bbox area is approximately {area_km2:.2f} km², above the "
            f"{max_area_km2:.2f} km² context-query limit"
        )
    return south, west, north, east


def build_raster_sidecar(
    input_path: Path,
    bbox: Sequence[float],
    crs: str,
    coordinate_unit: str,
    source_url: str,
    license_name: str,
    modality: str,
    sensor: str,
    acquired_at: str,
    notes: str,
    contains_target_labels: bool,
) -> Dict[str, Any]:
    if not input_path.is_file():
        raise ValueError(f"Raster does not exist: {input_path}")
    resolved_bbox = validate_metric_bbox(bbox)
    resolved_crs = validate_projected_crs(crs, coordinate_unit)
    return {
        "schemaVersion": "1.0",
        "sourceType": "user-registered-raster",
        "sourceUrl": source_url or None,
        "retrievedAt": None,
        "registeredAt": utc_now(),
        "license": license_name or "unknown",
        "sensor": sensor or None,
        "acquiredAt": acquired_at or None,
        "modality": modality,
        "crs": resolved_crs,
        "coordinateUnit": "metre",
        "bbox": list(resolved_bbox),
        "path": str(input_path),
        "sha256": sha256_file(input_path),
        "targetLabelsUsed": bool(contains_target_labels),
        "notes": notes,
    }


def load_verified_sidecar(input_path: Path, sidecar_path: Path) -> Dict[str, Any]:
    sidecar = load_json(sidecar_path)
    recorded_hash = str(sidecar.get("sha256") or "")
    if not recorded_hash:
        raise ValueError(f"Source sidecar has no raster SHA-256: {sidecar_path}")
    actual_hash = sha256_file(input_path)
    if recorded_hash != actual_hash:
        raise ValueError(
            "Source sidecar SHA-256 does not match the input raster; register the "
            "raster again instead of reusing stale spatial metadata"
        )
    return sidecar


def resolve_spatial_reference(
    input_path: Path,
    sidecar_path: Path,
    explicit_bbox: Sequence[float] | None,
    explicit_crs: str | None,
    explicit_coordinate_unit: str | None,
) -> Tuple[Sequence[float], str, Dict[str, Any] | None]:
    sidecar = load_verified_sidecar(input_path, sidecar_path) if sidecar_path.is_file() else None
    sidecar_bbox = sidecar.get("bbox") if sidecar else None
    sidecar_crs = sidecar.get("crs") if sidecar else None
    sidecar_unit = sidecar.get("coordinateUnit") if sidecar else None

    if explicit_bbox and sidecar_bbox:
        requested = [float(value) for value in explicit_bbox]
        recorded = [float(value) for value in sidecar_bbox]
        if requested != recorded:
            raise ValueError("Explicit bbox conflicts with the verified source sidecar")
    if explicit_crs and sidecar_crs:
        if explicit_crs.strip().upper() != str(sidecar_crs).strip().upper():
            raise ValueError("Explicit CRS conflicts with the verified source sidecar")
    if explicit_coordinate_unit and sidecar_unit:
        if explicit_coordinate_unit.strip().lower() != str(sidecar_unit).strip().lower():
            raise ValueError("Explicit coordinate unit conflicts with the verified source sidecar")

    bbox = explicit_bbox or sidecar_bbox
    crs = explicit_crs or sidecar_crs
    coordinate_unit = explicit_coordinate_unit or sidecar_unit
    if bbox is None or crs is None or coordinate_unit is None:
        raise ValueError(
            "Provide --bbox, --crs, and --coordinate-unit, or register a verified "
            "<input>.source.json sidecar"
        )
    return (
        validate_metric_bbox(bbox),
        validate_projected_crs(str(crs), str(coordinate_unit)),
        sidecar,
    )


def build_overpass_query(
    bbox: Sequence[float],
    include_heritage: bool,
) -> str:
    south, west, north, east = validate_wgs84_bbox(bbox)
    bounds = f"{south},{west},{north},{east}"
    tags = [
        "building",
        "highway",
        "railway",
        "waterway",
        "landuse",
        "man_made",
        "power",
        "aeroway",
        "barrier",
        "natural",
    ]
    if include_heritage:
        tags.extend(("historic", "heritage"))
    selectors = "\n".join(f'  nwr["{tag}"]({bounds});' for tag in tags)
    return f"[out:json][timeout:25];\n(\n{selectors}\n);\nout tags center qt;"


def _strip_osm_labels(payload: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = json.loads(json.dumps(payload))
    for element in sanitized.get("elements", []):
        tags = element.get("tags")
        if isinstance(tags, dict):
            element["tags"] = {
                key: value
                for key, value in tags.items()
                if key not in OSM_LABEL_TAGS and not key.startswith("heritage:")
            }
    return sanitized


def fetch_osm_context(
    bbox: Sequence[float],
    include_heritage: bool,
    timeout: int,
) -> Dict[str, Any]:
    resolved_bbox = validate_wgs84_bbox(bbox)
    query = build_overpass_query(resolved_bbox, include_heritage)
    body = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        OVERPASS_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Indiana-Jones-Codex/0.1 (bounded research query)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
        raise ValueError("Overpass did not return the expected OSM JSON object")
    if not include_heritage:
        payload = _strip_osm_labels(payload)
    return {
        "schemaVersion": "1.0",
        "sourceType": "OpenStreetMap via Overpass API",
        "sourceUrl": OVERPASS_ENDPOINT,
        "retrievedAt": utc_now(),
        "bboxWgs84": list(resolved_bbox),
        "purpose": (
            "post-detection heritage corroboration"
            if include_heritage
            else "modern and natural negative-control context"
        ),
        "targetLabelsUsed": include_heritage,
        "redactedTags": [] if include_heritage else sorted(OSM_LABEL_TAGS),
        "license": "Open Database License 1.0 (ODbL)",
        "attribution": "© OpenStreetMap contributors",
        "copyrightUrl": "https://www.openstreetmap.org/copyright",
        "query": query,
        "data": payload,
    }


def _stac_search_url(endpoint: str) -> str:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("STAC endpoint must be an HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError("Do not place credentials in a STAC endpoint URL")
    return endpoint.rstrip("/") if parsed.path.rstrip("/").endswith("/search") else (
        f"{endpoint.rstrip('/')}/search"
    )


def _normalize_stac_datetime(value: str) -> str:
    def normalize_part(part: str, end: bool) -> str:
        if part == "..":
            return part
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", part):
            suffix = "T23:59:59Z" if end else "T00:00:00Z"
            return f"{part}{suffix}"
        return part

    if "/" in value:
        start, end = value.split("/", 1)
        return f"{normalize_part(start, False)}/{normalize_part(end, True)}"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value}T00:00:00Z/{value}T23:59:59Z"
    return value


def search_stac(
    endpoint: str,
    bbox: Sequence[float],
    collections: Sequence[str],
    datetime_range: str,
    limit: int,
    timeout: int,
) -> Dict[str, Any]:
    west, south, east, north = [float(value) for value in bbox]
    resolved = validate_wgs84_bbox(
        (south, west, north, east),
        max_area_km2=10_000.0,
    )
    if not collections:
        raise ValueError("At least one STAC collection is required")
    if limit < 1 or limit > 100:
        raise ValueError("STAC result limit must be between 1 and 100")
    search_url = _stac_search_url(endpoint)
    payload = {
        "bbox": [resolved[1], resolved[0], resolved[3], resolved[2]],
        "collections": list(collections),
        "datetime": _normalize_stac_datetime(datetime_range),
        "limit": limit,
    }
    request = urllib.request.Request(
        search_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/geo+json, application/json",
            "User-Agent": "Indiana-Jones-Codex/0.1 (bounded STAC search)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    if not isinstance(result, dict) or not isinstance(result.get("features"), list):
        raise ValueError("STAC endpoint did not return a FeatureCollection")
    return {
        "schemaVersion": "1.0",
        "sourceType": "STAC item search",
        "endpoint": endpoint,
        "searchUrl": search_url,
        "searchedAt": utc_now(),
        "request": payload,
        "itemsReturned": len(result["features"]),
        "targetLabelsUsed": False,
        "data": result,
    }
