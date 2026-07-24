#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Sequence

from ij_casebook import add_source, new_case, validate_case
from ij_common import atomic_write_json, load_json, sha256_file, utc_now
from ij_sources import (
    build_raster_sidecar,
    fetch_osm_context,
    resolve_spatial_reference,
    search_stac,
)


WCS_ENDPOINT = (
    "https://environment.data.gov.uk/geoservices/datasets/"
    "13787b9a-26a4-4775-8523-806d13af58fc/wcs"
)
WCS_COVERAGE = (
    "13787b9a-26a4-4775-8523-806d13af58fc__"
    "Lidar_Composite_Elevation_DTM_1m"
)
EA_DATASET_URL = (
    "https://www.data.gov.uk/dataset/01b3ee39-da3f-47b6-83da-dc98e73a461f/"
    "lidar-composite-digital-terrain-model-dtm-1m"
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def _float_list(value: str) -> List[float]:
    try:
        return [float(item) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected comma-separated numbers") from error


def command_new_case(args: argparse.Namespace) -> int:
    case = new_case(
        args.title,
        args.question,
        args.study_area,
        args.disclosure,
        args.authorize_platform,
    )
    atomic_write_json(args.out, case)
    print(json.dumps({"ok": True, "case": str(args.out), "caseId": case["caseId"]}))
    return 0


def command_add_source(args: argparse.Namespace) -> int:
    source = add_source(
        args.case,
        args.locator,
        args.kind,
        args.access_basis,
        args.license,
        args.notes,
        args.platform,
    )
    print(json.dumps({"ok": True, "source": source}, sort_keys=True))
    return 0


def command_validate_case(args: argparse.Namespace) -> int:
    errors = validate_case(load_json(args.case))
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


def _validate_ea_bbox(bbox: Sequence[float]) -> None:
    e_min, n_min, e_max, n_max = bbox
    if not (e_min < e_max and n_min < n_max):
        raise ValueError("bbox must be E_MIN N_MIN E_MAX N_MAX")
    if e_min < 80000 or e_max > 656000 or n_min < 4000 or n_max > 665000:
        raise ValueError("bbox falls outside the advertised EPSG:27700 coverage")
    width = e_max - e_min
    height = n_max - n_min
    if width * height > 25_000_000:
        raise ValueError("bbox exceeds the 25 km² safety limit")


def command_fetch_ea_dtm(args: argparse.Namespace) -> int:
    bbox = [float(value) for value in args.bbox]
    _validate_ea_bbox(bbox)
    e_min, n_min, e_max, n_max = bbox
    query = urllib.parse.urlencode(
        [
            ("service", "WCS"),
            ("request", "GetCoverage"),
            ("version", "2.0.1"),
            ("coverageId", WCS_COVERAGE),
            ("format", "image/tiff"),
            ("subset", f"E({e_min},{e_max})"),
            ("subset", f"N({n_min},{n_max})"),
        ]
    )
    url = f"{WCS_ENDPOINT}?{query}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{args.out.name}.",
        suffix=".part",
        dir=str(args.out.parent),
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Indiana-Jones-Codex-POC/0.1"},
        )
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            with temporary_path.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
        with temporary_path.open("rb") as handle:
            magic = handle.read(4)
        if magic not in {b"II*\x00", b"MM\x00*"}:
            preview = temporary_path.read_bytes()[:500].decode("utf-8", errors="replace")
            raise ValueError(f"WCS did not return a TIFF: {preview}")
        os.replace(temporary_path, args.out)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    sidecar_path = Path(f"{args.out}.source.json")
    sidecar = {
        "schemaVersion": "1.0",
        "sourceType": "WCS GetCoverage",
        "dataset": "Environment Agency LIDAR Composite DTM 1m",
        "datasetUrl": EA_DATASET_URL,
        "requestUrl": url,
        "retrievedAt": utc_now(),
        "license": "Open Government Licence; verify current dataset terms",
        "coverageId": WCS_COVERAGE,
        "modality": "terrain",
        "crs": "EPSG:27700",
        "coordinateUnit": "metre",
        "verticalDatum": "Ordnance Datum Newlyn, per dataset metadata",
        "pixelSizeM": 1.0,
        "bbox": bbox,
        "path": str(args.out),
        "sha256": sha256_file(args.out),
        "targetLabelsUsed": False,
    }
    atomic_write_json(sidecar_path, sidecar)
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(args.out),
                "sourceSidecar": str(sidecar_path),
                "sha256": sidecar["sha256"],
            }
        )
    )
    return 0


def command_register_raster(args: argparse.Namespace) -> int:
    sidecar = build_raster_sidecar(
        args.input,
        args.bbox,
        args.crs,
        args.coordinate_unit,
        args.source_url,
        args.license,
        args.modality,
        args.sensor,
        args.acquired_at,
        args.notes,
        args.contains_target_labels,
    )
    output_path = args.out or Path(f"{args.input}.source.json")
    atomic_write_json(output_path, sidecar)
    print(
        json.dumps(
            {
                "ok": True,
                "sourceSidecar": str(output_path),
                "sha256": sidecar["sha256"],
                "crs": sidecar["crs"],
            }
        )
    )
    return 0


def command_fetch_osm_context(args: argparse.Namespace) -> int:
    record = fetch_osm_context(
        args.bbox,
        args.include_heritage,
        args.timeout,
    )
    atomic_write_json(args.out, record)
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(args.out),
                "elements": len(record["data"]["elements"]),
                "targetLabelsUsed": record["targetLabelsUsed"],
            }
        )
    )
    return 0


def command_search_stac(args: argparse.Namespace) -> int:
    record = search_stac(
        args.endpoint,
        args.bbox,
        args.collection,
        args.datetime,
        args.limit,
        args.timeout,
    )
    atomic_write_json(args.out, record)
    print(
        json.dumps(
            {
                "ok": True,
                "path": str(args.out),
                "itemsReturned": record["itemsReturned"],
            }
        )
    )
    return 0


def command_detect_enclosures(args: argparse.Namespace) -> int:
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("NumPy is required; install scripts/requirements.txt") from error
    try:
        from ij_terrain import (
            block_reduce_mean,
            build_detection_result,
            rank_candidates,
            read_float_tiff,
            save_diagnostics,
            scan_templates,
            terrain_features,
        )
    except ImportError as error:
        raise RuntimeError("Pillow is required; install scripts/requirements.txt") from error

    source_sidecar = Path(f"{args.input}.source.json")
    bbox, crs, sidecar = resolve_spatial_reference(
        args.input,
        source_sidecar,
        args.bbox,
        args.crs,
        args.coordinate_unit,
    )
    if sidecar and sidecar.get("targetLabelsUsed") is not False:
        raise ValueError(
            "Candidate generation refuses rasters marked as containing target labels"
        )
    modality = str((sidecar or {}).get("modality") or args.modality or "")
    if modality != "terrain":
        raise ValueError(
            "The bundled enclosure detector currently supports terrain rasters only; "
            "use a modality-specific method for optical, SAR, or thermal inputs"
        )
    original = read_float_tiff(args.input)
    reduced = block_reduce_mean(original, args.downsample)
    e_min, n_min, e_max, n_max = bbox
    pixel_size_x = (e_max - e_min) / original.shape[1] * args.downsample
    pixel_size_y = (n_max - n_min) / original.shape[0] * args.downsample
    if abs(pixel_size_x - pixel_size_y) > max(pixel_size_x, pixel_size_y) * 0.01:
        raise ValueError("Detector requires approximately square pixels")
    pixel_size_m = float((pixel_size_x + pixel_size_y) / 2.0)

    feature, feature_metadata = terrain_features(reduced, pixel_size_m)
    score, template_index, definitions, _ = scan_templates(
        feature,
        pixel_size_m,
        args.major_radii,
        args.aspects,
        args.angles,
        args.families,
        args.response_normalization,
    )
    candidates = rank_candidates(
        score,
        template_index,
        definitions,
        feature,
        bbox,
        crs,
        pixel_size_m,
        args.top_k,
        args.minimum_distance,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    hillshade_path = args.out_dir / "hillshade.png"
    heatmap_path = args.out_dir / "template-score.png"
    candidate_image_path = args.out_dir / "candidates.png"
    save_diagnostics(
        reduced,
        score,
        candidates,
        pixel_size_m,
        hillshade_path,
        heatmap_path,
        candidate_image_path,
    )
    result = build_detection_result(
        args.input,
        source_sidecar,
        bbox,
        crs,
        modality,
        original.shape,
        reduced.shape,
        pixel_size_m,
        args.downsample,
        args.top_k,
        args.minimum_distance,
        feature_metadata,
        args.major_radii,
        args.aspects,
        args.angles,
        args.families,
        args.response_normalization,
        candidates,
        (hillshade_path, heatmap_path, candidate_image_path),
    )
    result_path = args.out_dir / "candidates.json"
    atomic_write_json(result_path, result)
    print(
        json.dumps(
            {
                "ok": True,
                "candidates": str(result_path),
                "count": len(candidates),
                "inputSha256": result["input"]["sha256"],
            }
        )
    )
    return 0


def command_score(args: argparse.Namespace) -> int:
    from ij_terrain import score_against_ground_truth

    candidates = load_json(args.candidates)
    ground_truth = load_json(args.ground_truth)
    score = score_against_ground_truth(candidates, ground_truth)
    score["candidateArtifactSha256"] = sha256_file(args.candidates)
    score["groundTruthArtifactSha256"] = sha256_file(args.ground_truth)
    atomic_write_json(args.out, score)
    print(json.dumps({"ok": True, "score": str(args.out), **score["result"]}))
    return 0 if score["result"]["hit"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evidence-led aerial archaeology case and terrain-analysis utilities."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_case_parser = subparsers.add_parser("new-case", help="Create a scoped case ledger")
    new_case_parser.add_argument("--title", required=True)
    new_case_parser.add_argument("--question", required=True)
    new_case_parser.add_argument("--study-area", required=True)
    new_case_parser.add_argument(
        "--disclosure",
        choices=("public", "restricted", "heritage-authority-only"),
        default="restricted",
    )
    new_case_parser.add_argument("--authorize-platform", action="append", default=[])
    new_case_parser.add_argument("--out", type=Path, required=True)
    new_case_parser.set_defaults(handler=command_new_case)

    source_parser = subparsers.add_parser("add-source", help="Add a source to a case ledger")
    source_parser.add_argument("--case", type=Path, required=True)
    source_parser.add_argument("--locator", required=True)
    source_parser.add_argument(
        "--kind",
        required=True,
        choices=(
            "primary-measurement",
            "authoritative-record",
            "contemporary-account",
            "secondary-summary",
            "lead-only",
        ),
    )
    source_parser.add_argument(
        "--access-basis",
        choices=("public", "local-user-provided", "user-authorized"),
        default="public",
    )
    source_parser.add_argument("--platform", default="")
    source_parser.add_argument("--license", default="unknown")
    source_parser.add_argument("--notes", default="")
    source_parser.set_defaults(handler=command_add_source)

    validate_parser = subparsers.add_parser("validate-case", help="Validate a case ledger")
    validate_parser.add_argument("--case", type=Path, required=True)
    validate_parser.set_defaults(handler=command_validate_case)

    fetch_parser = subparsers.add_parser(
        "fetch-ea-dtm",
        help="Fetch a bounded Environment Agency 1 m DTM subset",
    )
    fetch_parser.add_argument("--bbox", nargs=4, type=float, required=True)
    fetch_parser.add_argument("--out", type=Path, required=True)
    fetch_parser.add_argument("--timeout", type=_positive_int, default=120)
    fetch_parser.set_defaults(handler=command_fetch_ea_dtm)

    register_parser = subparsers.add_parser(
        "register-raster",
        help="Bind any worldwide projected raster to verified spatial provenance",
    )
    register_parser.add_argument("--input", type=Path, required=True)
    register_parser.add_argument("--bbox", nargs=4, type=float, required=True)
    register_parser.add_argument("--crs", required=True)
    register_parser.add_argument(
        "--coordinate-unit",
        choices=("metre",),
        default="metre",
    )
    register_parser.add_argument("--source-url", default="")
    register_parser.add_argument("--license", default="unknown")
    register_parser.add_argument(
        "--modality",
        choices=("terrain", "surface", "optical-index", "sar", "thermal", "other"),
        default="other",
    )
    register_parser.add_argument("--sensor", default="")
    register_parser.add_argument("--acquired-at", default="")
    register_parser.add_argument("--notes", default="")
    register_parser.add_argument("--contains-target-labels", action="store_true")
    register_parser.add_argument("--out", type=Path)
    register_parser.set_defaults(handler=command_register_raster)

    osm_parser = subparsers.add_parser(
        "fetch-osm-context",
        help="Fetch bounded OSM context for negative controls or later corroboration",
    )
    osm_parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("SOUTH", "WEST", "NORTH", "EAST"),
    )
    osm_parser.add_argument("--include-heritage", action="store_true")
    osm_parser.add_argument("--timeout", type=_positive_int, default=60)
    osm_parser.add_argument("--out", type=Path, required=True)
    osm_parser.set_defaults(handler=command_fetch_osm_context)

    stac_parser = subparsers.add_parser(
        "search-stac",
        help="Discover worldwide satellite or terrain items from a public STAC API",
    )
    stac_parser.add_argument("--endpoint", required=True)
    stac_parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    stac_parser.add_argument("--collection", action="append", required=True)
    stac_parser.add_argument("--datetime", required=True)
    stac_parser.add_argument("--limit", type=_positive_int, default=20)
    stac_parser.add_argument("--timeout", type=_positive_int, default=60)
    stac_parser.add_argument("--out", type=Path, required=True)
    stac_parser.set_defaults(handler=command_search_stac)

    detect_parser = subparsers.add_parser(
        "detect-enclosures",
        help="Rank enclosure-like anomalies in a projected metric raster",
    )
    detect_parser.add_argument("--input", type=Path, required=True)
    detect_parser.add_argument("--bbox", nargs=4, type=float)
    detect_parser.add_argument("--crs")
    detect_parser.add_argument("--coordinate-unit", choices=("metre",))
    detect_parser.add_argument("--modality", choices=("terrain",))
    detect_parser.add_argument("--out-dir", type=Path, required=True)
    detect_parser.add_argument("--downsample", type=_positive_int, default=4)
    detect_parser.add_argument("--top-k", type=_positive_int, default=20)
    detect_parser.add_argument("--minimum-distance", type=float, default=180.0)
    detect_parser.add_argument(
        "--major-radii",
        type=_float_list,
        default=[40.0, 60.0, 90.0, 120.0],
    )
    detect_parser.add_argument("--aspects", type=_float_list, default=[1.25, 1.65])
    detect_parser.add_argument(
        "--angles",
        type=_float_list,
        default=[0.0, 30.0, 60.0, 90.0, 120.0, 150.0],
    )
    detect_parser.add_argument(
        "--families",
        type=lambda value: [item.strip() for item in value.split(",") if item.strip()],
        default=["diamond", "ellipse"],
    )
    detect_parser.add_argument(
        "--response-normalization",
        choices=("raw", "robust-per-template"),
        default="robust-per-template",
        help="Use raw 1.0 responses or robust per-template 1.1 normalization",
    )
    detect_parser.set_defaults(handler=command_detect_enclosures)

    score_parser = subparsers.add_parser(
        "score",
        help="Score frozen candidates against separately supplied ground truth",
    )
    score_parser.add_argument("--candidates", type=Path, required=True)
    score_parser.add_argument("--ground-truth", type=Path, required=True)
    score_parser.add_argument("--out", type=Path, required=True)
    score_parser.set_defaults(handler=command_score)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
