from __future__ import annotations

import math
import platform
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, __version__ as pillow_version

from ij_common import sha256_file, stable_id, utc_now


ALGORITHM_VERSIONS = {
    "raw": "diamond-ring-baseline-1.0",
    "robust-per-template": "diamond-ring-baseline-1.1",
}


def read_float_tiff(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        array = np.asarray(image, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError(f"Expected a single-band terrain raster, got shape {array.shape}")
    finite = np.isfinite(array)
    if not finite.any():
        raise ValueError("Terrain raster contains no finite elevations")
    if not finite.all():
        array = array.copy()
        array[~finite] = float(np.median(array[finite]))
    return array


def block_reduce_mean(array: np.ndarray, factor: int) -> np.ndarray:
    if factor < 1:
        raise ValueError("Downsample factor must be at least 1")
    if factor == 1:
        return array.astype(np.float32, copy=True)
    height = (array.shape[0] // factor) * factor
    width = (array.shape[1] // factor) * factor
    if height == 0 or width == 0:
        raise ValueError("Downsample factor is larger than the raster")
    reduced = array[:height, :width].reshape(
        height // factor,
        factor,
        width // factor,
        factor,
    )
    return reduced.mean(axis=(1, 3), dtype=np.float32)


def box_mean(array: np.ndarray, radius: int) -> np.ndarray:
    radius = max(1, int(radius))
    kernel = 2 * radius + 1
    padded = np.pad(array, ((radius, radius), (radius, radius)), mode="reflect")
    integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant")
    integral = integral.cumsum(axis=0, dtype=np.float64).cumsum(axis=1, dtype=np.float64)
    summed = (
        integral[kernel:, kernel:]
        - integral[:-kernel, kernel:]
        - integral[kernel:, :-kernel]
        + integral[:-kernel, :-kernel]
    )
    return (summed / float(kernel * kernel)).astype(np.float32)


def robust_z(array: np.ndarray) -> np.ndarray:
    median = float(np.median(array))
    mad = float(np.median(np.abs(array - median)))
    scale = max(1.4826 * mad, 1e-6)
    return ((array - median) / scale).astype(np.float32)


def terrain_features(dtm: np.ndarray, pixel_size_m: float) -> Tuple[np.ndarray, Dict[str, Any]]:
    radii_m = (12.0, 35.0, 90.0)
    residuals = []
    for radius_m in radii_m:
        local_mean = box_mean(dtm, max(1, round(radius_m / pixel_size_m)))
        residuals.append(dtm - local_mean)

    slope_y, slope_x = np.gradient(dtm, pixel_size_m)
    local_y, local_x = np.gradient(residuals[1], pixel_size_m)
    slope = np.hypot(slope_x, slope_y)
    local_gradient = np.hypot(local_x, local_y)

    feature = (
        np.clip(robust_z(np.abs(residuals[0])), 0.0, 8.0)
        + 0.8 * np.clip(robust_z(np.abs(residuals[1])), 0.0, 8.0)
        + 1.2 * np.clip(robust_z(local_gradient), 0.0, 8.0)
        + 0.25 * np.clip(robust_z(slope), 0.0, 8.0)
    )
    feature = np.sqrt(np.maximum(feature, 0.0)).astype(np.float32)
    return feature, {
        "localReliefRadiiM": list(radii_m),
        "featureTerms": [
            "absolute-small-scale-local-relief",
            "absolute-medium-scale-local-relief",
            "medium-local-relief-gradient",
            "terrain-slope",
        ],
    }


def _template_kernel(
    canvas_radius: int,
    major_radius_px: float,
    aspect: float,
    angle_deg: float,
    family: str,
) -> np.ndarray:
    coordinates = np.arange(-canvas_radius, canvas_radius + 1, dtype=np.float32)
    yy, xx = np.meshgrid(coordinates, coordinates, indexing="ij")
    angle = math.radians(angle_deg)
    xr = xx * math.cos(angle) + yy * math.sin(angle)
    yr = -xx * math.sin(angle) + yy * math.cos(angle)
    minor_radius_px = major_radius_px / aspect
    if family == "diamond":
        distance = np.abs(xr) / major_radius_px + np.abs(yr) / minor_radius_px
    elif family == "ellipse":
        distance = np.sqrt((xr / major_radius_px) ** 2 + (yr / minor_radius_px) ** 2)
    else:
        raise ValueError(f"Unsupported template family: {family}")

    thickness = max(0.08, 1.25 / max(minor_radius_px, 1.0))
    outer = np.abs(distance - 1.0) <= thickness
    inner = np.abs(distance - 0.72) <= thickness
    positive = outer | inner
    negative = (distance <= 0.48) | ((distance >= 1.18) & (distance <= 1.45))
    kernel = np.zeros_like(distance, dtype=np.float32)
    positive_count = int(positive.sum())
    negative_count = int(negative.sum())
    if positive_count < 8 or negative_count < 8:
        raise ValueError("Template is too small for the analysis resolution")
    kernel[positive] = 1.0 / positive_count
    kernel[negative] = -1.0 / negative_count
    norm = float(np.sqrt(np.sum(kernel * kernel)))
    return kernel / max(norm, 1e-8)


def _template_definitions(
    pixel_size_m: float,
    major_radii_m: Sequence[float],
    aspects: Sequence[float],
    angles_deg: Sequence[float],
    families: Sequence[str],
) -> Tuple[List[Dict[str, Any]], int]:
    max_radius_m = max(major_radii_m)
    canvas_radius = int(math.ceil(max_radius_m / pixel_size_m * 1.5))
    definitions: List[Dict[str, Any]] = []
    for family in families:
        for major_radius_m in major_radii_m:
            for aspect in aspects:
                for angle_deg in angles_deg:
                    definitions.append(
                        {
                            "family": family,
                            "majorRadiusM": float(major_radius_m),
                            "aspect": float(aspect),
                            "angleDeg": float(angle_deg),
                        }
                    )
    return definitions, canvas_radius


def scan_templates(
    feature: np.ndarray,
    pixel_size_m: float,
    major_radii_m: Sequence[float],
    aspects: Sequence[float],
    angles_deg: Sequence[float],
    families: Sequence[str],
    response_normalization: str = "robust-per-template",
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]], int]:
    if response_normalization not in ALGORITHM_VERSIONS:
        raise ValueError(f"Unsupported response normalization: {response_normalization}")
    definitions, canvas_radius = _template_definitions(
        pixel_size_m,
        major_radii_m,
        aspects,
        angles_deg,
        families,
    )
    kernel_size = 2 * canvas_radius + 1
    full_shape = (
        feature.shape[0] + kernel_size - 1,
        feature.shape[1] + kernel_size - 1,
    )
    image_fft = np.fft.rfft2(feature, full_shape)
    best_score = np.full(feature.shape, -np.inf, dtype=np.float32)
    best_template = np.full(feature.shape, -1, dtype=np.int16)
    crop_y = (kernel_size - 1) // 2
    crop_x = (kernel_size - 1) // 2

    for index, definition in enumerate(definitions):
        kernel = _template_kernel(
            canvas_radius,
            definition["majorRadiusM"] / pixel_size_m,
            definition["aspect"],
            definition["angleDeg"],
            definition["family"],
        )
        kernel_fft = np.fft.rfft2(kernel[::-1, ::-1], full_shape)
        full_response = np.fft.irfft2(image_fft * kernel_fft, full_shape)
        response = full_response[
            crop_y : crop_y + feature.shape[0],
            crop_x : crop_x + feature.shape[1],
        ]
        if response_normalization == "robust-per-template":
            valid = response[
                canvas_radius : response.shape[0] - canvas_radius,
                canvas_radius : response.shape[1] - canvas_radius,
            ]
            response_median = float(np.median(valid))
            response_mad = float(np.median(np.abs(valid - response_median)))
            response_scale = max(1.4826 * response_mad, 1e-6)
            normalized_response = (response - response_median) / response_scale
        else:
            normalized_response = response
        improved = normalized_response > best_score
        best_score[improved] = normalized_response[improved].astype(np.float32)
        best_template[improved] = index

    margin = canvas_radius + 2
    best_score[:margin, :] = -np.inf
    best_score[-margin:, :] = -np.inf
    best_score[:, :margin] = -np.inf
    best_score[:, -margin:] = -np.inf
    return best_score, best_template, definitions, canvas_radius


def _boundary_samples(
    row: int,
    column: int,
    definition: Dict[str, Any],
    pixel_size_m: float,
    feature: np.ndarray,
    scale: float,
    count: int = 96,
) -> np.ndarray:
    angles = np.linspace(0.0, 2.0 * math.pi, count, endpoint=False)
    major = definition["majorRadiusM"] / pixel_size_m * scale
    minor = major / definition["aspect"]
    cosines = np.cos(angles)
    sines = np.sin(angles)
    if definition["family"] == "diamond":
        radial = 1.0 / (np.abs(cosines) / major + np.abs(sines) / minor)
        local_x = radial * cosines
        local_y = radial * sines
    else:
        local_x = major * cosines
        local_y = minor * sines
    rotation = math.radians(definition["angleDeg"])
    xx = local_x * math.cos(rotation) - local_y * math.sin(rotation)
    yy = local_x * math.sin(rotation) + local_y * math.cos(rotation)
    rows = np.clip(np.rint(row + yy).astype(int), 0, feature.shape[0] - 1)
    columns = np.clip(np.rint(column + xx).astype(int), 0, feature.shape[1] - 1)
    return feature[rows, columns]


def _candidate_metrics(
    row: int,
    column: int,
    definition: Dict[str, Any],
    feature: np.ndarray,
    pixel_size_m: float,
) -> Dict[str, float]:
    threshold = float(np.percentile(feature, 65.0))
    outer = _boundary_samples(row, column, definition, pixel_size_m, feature, 1.0)
    inner = _boundary_samples(row, column, definition, pixel_size_m, feature, 0.72)
    combined = 0.6 * outer + 0.4 * inner
    sectors = combined.reshape(16, -1).mean(axis=1)
    return {
        "boundaryMean": float(combined.mean()),
        "boundaryCoverage": float(np.mean(combined >= threshold)),
        "sectorCoverage": float(np.mean(sectors >= threshold)),
    }


def _raw_peaks(
    score: np.ndarray,
    count: int,
    suppression_px: int,
) -> List[Tuple[int, int, float]]:
    work = score.copy()
    peaks: List[Tuple[int, int, float]] = []
    for _ in range(count):
        flat_index = int(np.argmax(work))
        value = float(work.flat[flat_index])
        if not math.isfinite(value):
            break
        row, column = np.unravel_index(flat_index, work.shape)
        peaks.append((int(row), int(column), value))
        y0 = max(0, row - suppression_px)
        y1 = min(work.shape[0], row + suppression_px + 1)
        x0 = max(0, column - suppression_px)
        x1 = min(work.shape[1], column + suppression_px + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]
        mask = (yy - row) ** 2 + (xx - column) ** 2 <= suppression_px**2
        region = work[y0:y1, x0:x1]
        region[mask] = -np.inf
    return peaks


def rank_candidates(
    score: np.ndarray,
    template_index: np.ndarray,
    definitions: List[Dict[str, Any]],
    feature: np.ndarray,
    bbox: Sequence[float],
    crs: str,
    pixel_size_m: float,
    top_k: int,
    minimum_distance_m: float,
) -> List[Dict[str, Any]]:
    e_min, n_min, e_max, n_max = [float(value) for value in bbox]
    finite_scores = score[np.isfinite(score)]
    median = float(np.median(finite_scores))
    mad = float(np.median(np.abs(finite_scores - median)))
    scale = max(1.4826 * mad, 1e-6)
    raw = _raw_peaks(
        score,
        max(top_k * 8, 40),
        max(1, round(minimum_distance_m / pixel_size_m / 2.0)),
    )
    proposals: List[Dict[str, Any]] = []
    for row, column, raw_score in raw:
        definition = definitions[int(template_index[row, column])]
        metrics = _candidate_metrics(row, column, definition, feature, pixel_size_m)
        score_z = (raw_score - median) / scale
        combined = score_z + 1.25 * metrics["boundaryCoverage"] + metrics["sectorCoverage"]
        x = e_min + (column + 0.5) * pixel_size_m
        y = n_max - (row + 0.5) * pixel_size_m
        proposals.append(
            {
                "candidateId": stable_id(
                    "cand",
                    f"{crs}|{x:.2f}|{y:.2f}|{definition}",
                ),
                "row": row,
                "column": column,
                "crs": crs,
                "x": round(x, 3),
                "y": round(y, 3),
                "score": round(float(combined), 6),
                "templateScoreRobustZ": round(float(score_z), 6),
                "templateScoreRaw": round(raw_score, 6),
                "boundaryCoverage": round(metrics["boundaryCoverage"], 6),
                "sectorCoverage": round(metrics["sectorCoverage"], 6),
                "template": definition,
                "interpretation": "geometric terrain anomaly; archaeological status unverified",
            }
        )

    proposals.sort(key=lambda item: item["score"], reverse=True)
    accepted: List[Dict[str, Any]] = []
    for proposal in proposals:
        if any(
            math.hypot(proposal["x"] - item["x"], proposal["y"] - item["y"])
            < minimum_distance_m
            for item in accepted
        ):
            continue
        accepted.append(proposal)
        if len(accepted) >= top_k:
            break
    for rank, candidate in enumerate(accepted, start=1):
        candidate["rank"] = rank
    return accepted


def _normalize_image(array: np.ndarray, lower: float = 2.0, upper: float = 98.0) -> np.ndarray:
    finite = array[np.isfinite(array)]
    low, high = np.percentile(finite, [lower, upper])
    normalized = np.clip((array - low) / max(float(high - low), 1e-8), 0.0, 1.0)
    return np.rint(normalized * 255.0).astype(np.uint8)


def multi_hillshade(dtm: np.ndarray, pixel_size_m: float) -> np.ndarray:
    grad_y, grad_x = np.gradient(dtm, pixel_size_m)
    slope = np.arctan(np.hypot(grad_x, grad_y))
    aspect = np.arctan2(-grad_x, grad_y)
    altitude = math.radians(35.0)
    shades = []
    for azimuth_deg in (315.0, 45.0, 135.0, 225.0):
        azimuth = math.radians(azimuth_deg)
        shade = (
            math.sin(altitude) * np.cos(slope)
            + math.cos(altitude) * np.sin(slope) * np.cos(azimuth - aspect)
        )
        shades.append(shade)
    combined = np.mean(shades, axis=0) + 0.35 * np.std(shades, axis=0)
    return _normalize_image(combined)


def save_diagnostics(
    dtm: np.ndarray,
    score: np.ndarray,
    candidates: List[Dict[str, Any]],
    pixel_size_m: float,
    hillshade_path: Path,
    heatmap_path: Path,
    candidates_path: Path,
) -> None:
    hillshade = multi_hillshade(dtm, pixel_size_m)
    Image.fromarray(hillshade, mode="L").save(hillshade_path)

    finite = np.where(np.isfinite(score), score, np.nan)
    normalized_score = _normalize_image(np.nan_to_num(finite, nan=np.nanmin(finite)))
    heatmap = np.stack(
        [
            normalized_score,
            np.sqrt(normalized_score.astype(np.float32) / 255.0) * 190.0,
            np.zeros_like(normalized_score),
        ],
        axis=-1,
    ).astype(np.uint8)
    Image.fromarray(heatmap, mode="RGB").save(heatmap_path)

    overlay = Image.fromarray(hillshade, mode="L").convert("RGB")
    draw = ImageDraw.Draw(overlay)
    for candidate in candidates:
        row = int(candidate["row"])
        column = int(candidate["column"])
        radius = 7 if candidate["rank"] <= 5 else 4
        color = (255, 40, 30) if candidate["rank"] <= 5 else (255, 190, 20)
        draw.ellipse(
            (column - radius, row - radius, column + radius, row + radius),
            outline=color,
            width=2,
        )
        draw.text((column + radius + 2, row - radius), str(candidate["rank"]), fill=color)
    overlay.save(candidates_path)


def build_detection_result(
    input_path: Path,
    source_sidecar_path: Path,
    bbox: Sequence[float],
    crs: str,
    modality: str,
    original_shape: Sequence[int],
    analysis_shape: Sequence[int],
    pixel_size_m: float,
    downsample: int,
    top_k: int,
    minimum_distance_m: float,
    feature_metadata: Dict[str, Any],
    major_radii_m: Sequence[float],
    aspects: Sequence[float],
    angles_deg: Sequence[float],
    families: Sequence[str],
    response_normalization: str,
    candidates: List[Dict[str, Any]],
    diagnostic_paths: Iterable[Path],
) -> Dict[str, Any]:
    implementation_names = (
        "ij_terrain.py",
        "archaeology.py",
        "ij_sources.py",
        "ij_casebook.py",
        "ij_common.py",
        "requirements.txt",
    )
    implementation_root = Path(__file__).resolve().parent
    diagnostics = [
        {"path": str(path), "sha256": sha256_file(path)}
        for path in diagnostic_paths
    ]
    return {
        "schemaVersion": "1.0",
        "algorithm": ALGORITHM_VERSIONS[response_normalization],
        "generatedAt": utc_now(),
        "runtime": {
            "pythonVersion": platform.python_version(),
            "numpyVersion": np.__version__,
            "pillowVersion": pillow_version,
        },
        "implementation": [
            {
                "path": f"scripts/{name}",
                "sha256": sha256_file(implementation_root / name),
            }
            for name in implementation_names
        ],
        "input": {
            "path": str(input_path),
            "sha256": sha256_file(input_path),
            "sourceSidecarPath": str(source_sidecar_path) if source_sidecar_path.exists() else None,
            "sourceSidecarSha256": (
                sha256_file(source_sidecar_path) if source_sidecar_path.exists() else None
            ),
            "crs": crs,
            "coordinateUnit": "metre",
            "modality": modality,
            "bbox": [float(value) for value in bbox],
            "originalShape": list(original_shape),
        },
        "parameters": {
            "analysisShape": list(analysis_shape),
            "pixelSizeM": pixel_size_m,
            "downsample": downsample,
            "topK": top_k,
            "minimumDistanceM": minimum_distance_m,
            "majorRadiiM": list(major_radii_m),
            "aspects": list(aspects),
            "anglesDeg": list(angles_deg),
            "families": list(families),
            "responseNormalization": response_normalization,
            **feature_metadata,
        },
        "scoreSemantics": "relative classical-template score; not a calibrated probability",
        "diagnostics": diagnostics,
        "candidates": candidates,
        "limitations": [
            "Detects enclosure-like terrain geometry only.",
            "Modern, geological, agricultural, and processing features can score highly.",
            "A non-detection is not evidence of archaeological absence.",
            "Every candidate requires independent expert and contextual review.",
        ],
    }


def score_against_ground_truth(
    candidate_result: Dict[str, Any],
    ground_truth: Dict[str, Any],
) -> Dict[str, Any]:
    if ground_truth.get("crs") != candidate_result.get("input", {}).get("crs"):
        raise ValueError("Candidate and ground-truth CRS values do not match")
    target_x = float(ground_truth["x"])
    target_y = float(ground_truth["y"])
    tolerance = float(ground_truth.get("toleranceM", 150.0))
    scored = []
    hit_rank = None
    for candidate in candidate_result.get("candidates", []):
        distance = math.hypot(float(candidate["x"]) - target_x, float(candidate["y"]) - target_y)
        hit = distance <= tolerance
        if hit and hit_rank is None:
            hit_rank = int(candidate["rank"])
        scored.append(
            {
                "rank": int(candidate["rank"]),
                "candidateId": candidate["candidateId"],
                "distanceM": round(distance, 3),
                "withinTolerance": hit,
            }
        )
    return {
        "schemaVersion": "1.0",
        "generatedAt": utc_now(),
        "candidateArtifactSha256": None,
        "groundTruth": {
            "siteId": ground_truth.get("siteId"),
            "name": ground_truth.get("name"),
            "crs": ground_truth.get("crs"),
            "toleranceM": tolerance,
            "source": ground_truth.get("source"),
            "sensitivity": ground_truth.get("sensitivity", "restricted"),
        },
        "result": {
            "hit": hit_rank is not None,
            "hitRank": hit_rank,
            "top1Hit": hit_rank == 1,
            "top5Hit": hit_rank is not None and hit_rank <= 5,
            "top10Hit": hit_rank is not None and hit_rank <= 10,
            "candidatesScored": len(scored),
        },
        "distances": scored,
        "claimBoundary": "Known-site rediscovery benchmark only; not evidence of a new site.",
    }
