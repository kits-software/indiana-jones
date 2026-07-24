#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Sequence

from ij_common import atomic_write_json, utc_now
from ij_optical import (
    _implementation_identity,
    build_features,
    build_optical_result,
    load_optical_cube,
    rank_optical_candidates,
    save_optical_diagnostics,
    score_optical_cube,
)
from ij_optical_io import validate_safe_locator
from ij_spatial import validate_projected_crs


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0.0:
        raise argparse.ArgumentTypeError("value must be positive and finite")
    return parsed


def _sha256_argument(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise argparse.ArgumentTypeError("value must be a 64-character SHA-256")
    return normalized


def _load_hashed_json(path: Path) -> tuple[Dict[str, Any], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON artifact: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value, digest


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be a finite number")
    return parsed


def _write_json_exclusive(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path, follow_symlinks=False)
        except FileExistsError as error:
            raise ValueError(f"Score output already exists: {path}") from error
        if os.name != "nt":
            directory_flags = os.O_RDONLY
            if hasattr(os, "O_DIRECTORY"):
                directory_flags |= os.O_DIRECTORY
            directory_descriptor = os.open(path.parent, directory_flags)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    finally:
        temporary_path.unlink(missing_ok=True)


def _validate_candidate_artifact(
    candidate_result: Dict[str, Any],
) -> tuple[
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    list[Dict[str, Any]],
    tuple[float, float, float, float],
]:
    if candidate_result.get("schemaVersion") != "1.0":
        raise ValueError("Candidate artifact schemaVersion must be 1.0")
    candidate_method = candidate_result.get("method")
    if not isinstance(candidate_method, dict) or candidate_method.get("name") != (
        "transparent-multitemporal-optical-proxy-baseline"
    ):
        raise ValueError("Candidate artifact is not a bundled optical-baseline result")
    _required_string(candidate_method.get("version"), "candidate method version")
    candidate_input = candidate_result.get("input")
    if not isinstance(candidate_input, dict):
        raise ValueError("Candidate artifact has no input provenance")
    if candidate_input.get("targetLabelsUsed") is not False:
        raise ValueError("Candidate artifact must state targetLabelsUsed: false")
    for hash_field in ("manifestSha256", "arraySha256"):
        if not re.fullmatch(
            r"[0-9a-f]{64}",
            str(candidate_input.get(hash_field) or "").lower(),
        ):
            raise ValueError(f"Candidate input {hash_field} is missing or invalid")
    candidate_crs = _required_string(
        candidate_input.get("crs"),
        "candidate input CRS",
    )
    if candidate_input.get("coordinateUnit") != "metre":
        raise ValueError("Candidate input coordinateUnit must be metre")
    validate_projected_crs(candidate_crs, "metre")
    if candidate_input.get("northUp") is not True:
        raise ValueError("Candidate input must state northUp: true")
    bbox_value = candidate_input.get("bbox")
    if not isinstance(bbox_value, list) or len(bbox_value) != 4:
        raise ValueError("Candidate input bbox must contain four coordinates")
    x_min, y_min, x_max, y_max = (
        _finite_number(value, f"candidate input bbox[{index}]")
        for index, value in enumerate(bbox_value)
    )
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("Candidate input bbox must have increasing bounds")

    candidate_access = candidate_result.get("access")
    if not isinstance(candidate_access, dict) or candidate_access.get(
        "disclosure"
    ) not in {"public", "restricted", "heritage-authority-only"}:
        raise ValueError("Candidate artifact has no valid disclosure class")
    diagnostics = candidate_result.get("diagnostics")
    if not isinstance(diagnostics, dict) or not diagnostics:
        raise ValueError("Candidate artifact has no hash-bound diagnostics")
    for name, diagnostic in diagnostics.items():
        if not isinstance(diagnostic, dict) or not re.fullmatch(
            r"[0-9a-f]{64}",
            str(diagnostic.get("sha256") or "").lower(),
        ):
            raise ValueError(f"Candidate diagnostic {name} has no valid SHA-256")

    candidate_values = candidate_result.get("candidates")
    if not isinstance(candidate_values, list):
        raise ValueError("Candidate artifact candidates must be an array")
    candidates = []
    seen_ranks = set()
    for candidate in candidate_values:
        if not isinstance(candidate, dict):
            raise ValueError("Every candidate must be an object")
        rank_value = candidate.get("rank")
        if isinstance(rank_value, bool) or not isinstance(rank_value, int):
            raise ValueError("Candidate ranks must be unique positive integers")
        if rank_value < 1 or rank_value in seen_ranks:
            raise ValueError("Candidate ranks must be unique positive integers")
        seen_ranks.add(rank_value)
        centroid = candidate.get("centroidProjected")
        if not isinstance(centroid, list) or len(centroid) != 2:
            raise ValueError("Every optical candidate must have a projected centroid")
        x = _finite_number(centroid[0], "candidate centroid x")
        y = _finite_number(centroid[1], "candidate centroid y")
        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            raise ValueError("Candidate centroid lies outside the analyzed bbox")
        candidates.append(
            {
                "rank": rank_value,
                "candidateId": _required_string(
                    candidate.get("candidateId"),
                    "candidateId",
                ),
                "x": x,
                "y": y,
            }
        )
    if seen_ranks != set(range(1, len(candidates) + 1)):
        raise ValueError("Candidate ranks must be contiguous from 1 through N")
    return (
        candidate_method,
        candidate_input,
        candidate_access,
        candidates,
        (x_min, y_min, x_max, y_max),
    )


def command_validate(args: argparse.Namespace) -> int:
    manifest, arrays, valid = load_optical_cube(args.manifest)
    print(
        json.dumps(
            {
                "ok": True,
                "array": manifest["arrayPath"],
                "bands": sorted(arrays),
                "dates": len(manifest["dates"]),
                "shape": list(valid.shape),
                "validObservations": int(valid.sum()),
                "targetLabelsUsed": False,
            },
            sort_keys=True,
        )
    )
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    manifest, bands, valid = load_optical_cube(args.manifest)
    if args.out_dir.is_symlink():
        raise ValueError(
            f"Output directory must not be a symbolic link: {args.out_dir}"
        )
    out_dir = args.out_dir.resolve()
    input_paths = {
        args.manifest.resolve(),
        Path(manifest["arrayPath"]).resolve(),
    }
    output_paths = {
        out_dir / "candidates.json",
        out_dir / "optical-scores.npz",
        out_dir / "optical-anomalies.png",
    }
    collisions = sorted(input_paths & output_paths)
    if collisions:
        raise ValueError(
            "Output paths would overwrite an input artifact: "
            + ", ".join(str(path) for path in collisions)
        )
    if out_dir.exists():
        raise ValueError(
            f"Output directory already exists; use a new output directory: {out_dir}"
        )
    radius = max(1, int(round(args.background_radius_m / manifest["pixelSizeM"])))
    if radius * 2 + 1 > min(valid.shape[1:]):
        raise ValueError("background radius is larger than the cube")
    features = build_features(bands, valid)
    scores = score_optical_cube(
        features,
        valid,
        radius,
        args.rx_shrinkage,
        args.rx_max_samples,
        args.threshold,
    )
    candidates = rank_optical_candidates(
        scores,
        manifest,
        args.threshold,
        args.min_pixels,
        args.min_dates,
        args.min_valid_dates,
        args.top_k,
    )
    parameters = {
        "backgroundRadiusM": args.background_radius_m,
        "backgroundRadiusPixels": radius,
        "threshold": args.threshold,
        "minimumComponentPixels": args.min_pixels,
        "minimumSupportDatesAtPeakPixel": args.min_dates,
        "minimumValidDatesAtPeakPixel": args.min_valid_dates,
        "topK": args.top_k,
        "rxShrinkage": args.rx_shrinkage,
        "rxMaximumBackgroundSamples": args.rx_max_samples,
        "rankingOrder": (
            "support fraction, support date count, peak standardized anomaly, "
            "single-date component area"
        ),
    }
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{out_dir.name}.",
            dir=str(out_dir.parent),
        )
    )
    try:
        diagnostics = save_optical_diagnostics(staging_dir, scores, candidates)
        result = build_optical_result(
            args.manifest,
            manifest,
            scores,
            candidates,
            parameters,
            diagnostics,
        )
        final_diagnostic_paths = {
            name: out_dir / path.name
            for name, path in diagnostics.items()
        }
        for name, path in final_diagnostic_paths.items():
            result["diagnostics"][name]["path"] = str(path)
        atomic_write_json(staging_dir / "candidates.json", result)
        os.replace(staging_dir, out_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    result_path = out_dir / "candidates.json"
    print(
        json.dumps(
            {
                "ok": True,
                "candidates": str(result_path),
                "count": len(candidates),
                "inputSha256": manifest["arraySha256"],
                "claimBoundary": result["method"]["claimBoundary"],
            },
            sort_keys=True,
        )
    )
    return 0


def command_score(args: argparse.Namespace) -> int:
    if args.out.is_symlink():
        raise ValueError(f"Score output must not be a symbolic link: {args.out}")
    candidate_path = args.candidates.resolve()
    ground_truth_path = args.ground_truth.resolve()
    output_path = Path(os.path.abspath(args.out))
    if candidate_path == ground_truth_path or os.path.samefile(
        candidate_path,
        ground_truth_path,
    ):
        raise ValueError("Candidates and ground truth must be distinct artifacts")
    if output_path in {candidate_path, ground_truth_path}:
        raise ValueError("Score output must not overwrite an input artifact")
    candidate_result, candidate_hash = _load_hashed_json(candidate_path)
    if candidate_hash != args.expected_candidate_sha256:
        raise ValueError(
            "Candidate artifact does not match --expected-candidate-sha256; "
            "freeze and hash it before opening ground truth"
        )
    (
        candidate_method,
        candidate_input,
        candidate_access,
        candidates,
        candidate_bbox,
    ) = _validate_candidate_artifact(candidate_result)
    ground_truth, ground_truth_hash = _load_hashed_json(ground_truth_path)
    crs = _required_string(candidate_input.get("crs"), "candidate input CRS")
    if _required_string(ground_truth.get("crs"), "ground-truth CRS") != crs:
        raise ValueError("Candidate and ground-truth CRS values do not match")
    sensitivity = _required_string(
        ground_truth.get("sensitivity"),
        "ground-truth sensitivity",
    )
    if not sensitivity.lower().startswith("public-known"):
        raise ValueError(
            "The bundled scorer emits exact distances and therefore accepts only "
            "explicitly public-known ground truth"
        )
    source = validate_safe_locator(
        ground_truth.get("source"),
        "groundTruth.source",
    )
    site_id = _required_string(ground_truth.get("siteId"), "groundTruth.siteId")
    site_name = _required_string(ground_truth.get("name"), "groundTruth.name")
    target_x = _finite_number(ground_truth.get("x"), "groundTruth.x")
    target_y = _finite_number(ground_truth.get("y"), "groundTruth.y")
    tolerance = _finite_number(
        ground_truth.get("toleranceM", 150.0),
        "groundTruth.toleranceM",
    )
    if tolerance <= 0.0:
        raise ValueError("Ground-truth tolerance must be positive")
    x_min, y_min, x_max, y_max = candidate_bbox
    if not (x_min <= target_x <= x_max and y_min <= target_y <= y_max):
        raise ValueError("Ground-truth target lies outside the analyzed bbox")

    distances = []
    hit_ranks = []
    for candidate in candidates:
        distance = math.hypot(
            candidate["x"] - target_x,
            candidate["y"] - target_y,
        )
        rank = candidate["rank"]
        within_tolerance = distance <= tolerance
        if within_tolerance:
            hit_ranks.append(rank)
        distances.append(
            {
                "rank": rank,
                "candidateId": candidate["candidateId"],
                "distanceM": round(distance, 3),
                "withinTolerance": within_tolerance,
            }
        )
    distances.sort(key=lambda item: item["rank"])
    hit_rank = min(hit_ranks, default=None)
    nearest = min(distances, key=lambda item: item["distanceM"], default=None)
    score = {
        "schemaVersion": "1.0",
        "generatedAt": utc_now(),
        "method": {
            "name": "known-site-optical-localization-scorer",
            "version": "1.0",
            "implementation": _implementation_identity(),
        },
        "input": {
            "candidatePath": str(args.candidates),
            "candidateArtifactSha256": candidate_hash,
            "expectedCandidateSha256": args.expected_candidate_sha256,
            "groundTruthPath": str(args.ground_truth),
            "groundTruthArtifactSha256": ground_truth_hash,
            "candidateMethod": {
                "name": candidate_method["name"],
                "version": candidate_method["version"],
            },
            "targetLabelsUsedDuringCandidateGeneration": False,
        },
        "access": {
            "disclosure": candidate_access["disclosure"],
            "spatiallyRedacted": False,
            "containsExactCandidateTargetDistances": True,
            "sharingWarning": (
                "This score inherits the candidate artifact disclosure class. Exact "
                "distances are not spatially redacted and must not be combined with "
                "candidate coordinates outside that boundary."
            ),
        },
        "groundTruth": {
            "siteId": site_id,
            "name": site_name,
            "crs": crs,
            "toleranceM": tolerance,
            "source": source,
            "sensitivity": sensitivity,
        },
        "result": {
            "hit": hit_rank is not None,
            "hitRank": hit_rank,
            "top1Hit": hit_rank == 1,
            "top5Hit": hit_rank is not None and hit_rank <= 5,
            "top10Hit": hit_rank is not None and hit_rank <= 10,
            "candidatesScored": len(distances),
            "nearestCandidate": nearest,
        },
        "distances": distances,
        "claimBoundary": (
            "Known-site optical rediscovery benchmark only; not evidence of a "
            "new site or a transferable detection rate."
        ),
    }
    _write_json_exclusive(output_path, score)
    print(
        json.dumps(
            {
                "ok": True,
                "score": str(output_path),
                "hit": score["result"]["hit"],
                "hitRank": hit_rank,
            },
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and rank proxy anomalies in registered multi-date optical cubes."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Verify cube geometry, mask, hash, bands, and source provenance",
    )
    validate_parser.add_argument("--manifest", type=Path, required=True)
    validate_parser.set_defaults(handler=command_validate)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run transparent local-contrast and regularized-RX candidate ranking",
    )
    analyze_parser.add_argument("--manifest", type=Path, required=True)
    analyze_parser.add_argument("--out-dir", type=Path, required=True)
    analyze_parser.add_argument(
        "--background-radius-m",
        type=_positive_float,
        default=120.0,
    )
    analyze_parser.add_argument("--threshold", type=_positive_float, default=3.5)
    analyze_parser.add_argument("--min-pixels", type=_positive_int, default=2)
    analyze_parser.add_argument("--min-dates", type=_positive_int, default=2)
    analyze_parser.add_argument("--min-valid-dates", type=_positive_int, default=2)
    analyze_parser.add_argument("--top-k", type=_positive_int, default=50)
    analyze_parser.add_argument("--rx-shrinkage", type=float, default=0.15)
    analyze_parser.add_argument(
        "--rx-max-samples",
        type=_positive_int,
        default=50_000,
    )
    analyze_parser.set_defaults(handler=command_analyze)

    score_parser = subparsers.add_parser(
        "score",
        help="Unblind frozen optical candidates against separate known-site ground truth",
    )
    score_parser.add_argument("--candidates", type=Path, required=True)
    score_parser.add_argument(
        "--expected-candidate-sha256",
        type=_sha256_argument,
        required=True,
        help="Precommitted SHA-256 recorded before ground truth is opened",
    )
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
