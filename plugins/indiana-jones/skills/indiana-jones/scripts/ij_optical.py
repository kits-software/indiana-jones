from __future__ import annotations

import importlib.metadata
import json
import math
import platform
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
from PIL import __version__ as PILLOW_VERSION

from ij_common import sha256_file, stable_id, utc_now
from ij_optical_io import load_optical_cube, save_optical_diagnostics


EPSILON = 1e-8
FEATURE_INPUT_BANDS = {
    "ndvi": {"nir", "red"},
    "savi": {"nir", "red"},
    "ndmi": {"nir", "swir1"},
    "bsi": {"blue", "red", "nir", "swir1"},
    "ndre": {"nir", "rededge1"},
}


def _normalized_difference(
    positive: np.ndarray,
    negative: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    denominator = positive + negative
    result = np.full(positive.shape, np.nan, dtype=np.float64)
    usable = valid & (np.abs(denominator) > EPSILON)
    result[usable] = (positive[usable] - negative[usable]) / denominator[usable]
    return result


def build_features(
    bands: Mapping[str, np.ndarray],
    valid: np.ndarray,
) -> Dict[str, np.ndarray]:
    features: Dict[str, np.ndarray] = {
        name: np.where(valid, value, np.nan)
        for name, value in bands.items()
    }
    red = bands["red"]
    nir = bands["nir"]
    features["ndvi"] = _normalized_difference(nir, red, valid)
    savi = np.full(red.shape, np.nan, dtype=np.float64)
    savi_denominator = nir + red + 0.5
    usable = valid & (np.abs(savi_denominator) > EPSILON)
    savi[usable] = 1.5 * (nir[usable] - red[usable]) / savi_denominator[usable]
    features["savi"] = savi
    if "swir1" in bands:
        features["ndmi"] = _normalized_difference(nir, bands["swir1"], valid)
    if {"blue", "swir1"}.issubset(bands):
        numerator = bands["swir1"] + red - nir - bands["blue"]
        denominator = bands["swir1"] + red + nir + bands["blue"]
        bsi = np.full(red.shape, np.nan, dtype=np.float64)
        usable = valid & (np.abs(denominator) > EPSILON)
        bsi[usable] = numerator[usable] / denominator[usable]
        features["bsi"] = bsi
    if "rededge1" in bands:
        features["ndre"] = _normalized_difference(nir, bands["rededge1"], valid)
    return features


def _box_sum(array: np.ndarray, radius: int) -> np.ndarray:
    padded = np.pad(array, ((radius, radius), (radius, radius)), mode="constant")
    integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant")
    integral = integral.cumsum(axis=0).cumsum(axis=1)
    width = radius * 2 + 1
    return (
        integral[width:, width:]
        - integral[:-width, width:]
        - integral[width:, :-width]
        + integral[:-width, :-width]
    )


def local_standardized_contrast(
    feature: np.ndarray,
    valid: np.ndarray,
    radius: int,
) -> np.ndarray:
    result = np.full(feature.shape, np.nan, dtype=np.float64)
    for date_index in range(feature.shape[0]):
        mask = valid[date_index] & np.isfinite(feature[date_index])
        values = np.where(mask, feature[date_index], 0.0)
        counts = _box_sum(mask.astype(np.float64), radius)
        totals = _box_sum(values, radius)
        squares = _box_sum(values * values, radius)
        usable = mask & (counts >= 9.0)
        means = np.divide(totals, counts, out=np.zeros_like(totals), where=counts > 0)
        variances = np.divide(
            squares,
            counts,
            out=np.zeros_like(squares),
            where=counts > 0,
        ) - means * means
        positive_variances = variances[usable & (variances > 0)]
        floor = (
            max(float(np.median(positive_variances)) * 1e-4, EPSILON)
            if positive_variances.size
            else EPSILON
        )
        deviations = np.sqrt(np.maximum(variances, floor))
        result[date_index, usable] = (
            feature[date_index, usable] - means[usable]
        ) / deviations[usable]
    return result


def _robust_location_scale(values: np.ndarray) -> Tuple[float, float]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 0.0, 1.0
    center = float(np.median(finite))
    mad = float(np.median(np.abs(finite - center)))
    robust_scale = 1.4826 * mad
    if robust_scale <= EPSILON:
        robust_scale = float(np.std(finite))
    return center, max(robust_scale, EPSILON)


def regularized_rx_scores(
    features: Mapping[str, np.ndarray],
    valid: np.ndarray,
    shrinkage: float,
    max_samples: int,
) -> np.ndarray:
    if not 0.0 <= shrinkage <= 1.0:
        raise ValueError("RX shrinkage must be between 0 and 1")
    if max_samples < 100:
        raise ValueError("RX max_samples must be at least 100")
    names = sorted(features)
    dates, rows, columns = valid.shape
    result = np.zeros((dates, rows, columns), dtype=np.float64)
    for date_index in range(dates):
        date_mask = valid[date_index].copy()
        for name in names:
            date_mask &= np.isfinite(features[name][date_index])
        flat_indices = np.flatnonzero(date_mask)
        if flat_indices.size < max(len(names) + 2, 20):
            continue
        matrix = np.column_stack(
            [features[name][date_index].ravel()[flat_indices] for name in names]
        )
        standardized = np.empty_like(matrix)
        for column in range(matrix.shape[1]):
            center, scale = _robust_location_scale(matrix[:, column])
            standardized[:, column] = (matrix[:, column] - center) / scale
        if standardized.shape[0] > max_samples:
            sample_indices = np.linspace(
                0,
                standardized.shape[0] - 1,
                max_samples,
                dtype=np.int64,
            )
            sample = standardized[sample_indices]
        else:
            sample = standardized
        center_vector = np.median(sample, axis=0)
        centered_sample = sample - center_vector
        covariance = np.cov(centered_sample, rowvar=False)
        covariance = np.atleast_2d(covariance)
        dimension = covariance.shape[0]
        target_variance = max(float(np.trace(covariance)) / dimension, EPSILON)
        regularized = (
            (1.0 - shrinkage) * covariance
            + shrinkage * target_variance * np.eye(dimension)
            + EPSILON * np.eye(dimension)
        )
        inverse = np.linalg.solve(regularized, np.eye(dimension))
        centered = standardized - center_vector
        squared = np.einsum("ij,jk,ik->i", centered, inverse, centered)
        distances = np.sqrt(np.maximum(squared, 0.0))
        distance_center, distance_scale = _robust_location_scale(distances)
        rx = np.maximum((distances - distance_center) / distance_scale, 0.0)
        result[date_index].ravel()[flat_indices] = rx
    return result


def score_optical_cube(
    features: Mapping[str, np.ndarray],
    valid: np.ndarray,
    radius: int,
    shrinkage: float,
    max_samples: int,
    threshold: float,
) -> Dict[str, Any]:
    if not math.isfinite(threshold) or threshold <= 0.0:
        raise ValueError("threshold must be positive and finite")
    names = sorted(features)
    local = np.stack(
        [
            local_standardized_contrast(features[name], valid, radius)
            for name in names
        ],
        axis=0,
    )
    local_absolute = np.abs(local)
    finite_local = np.where(np.isfinite(local_absolute), local_absolute, -np.inf)
    local_feature_index = np.argmax(finite_local, axis=0)
    local_best = np.max(finite_local, axis=0)
    local_best[~np.isfinite(local_best)] = 0.0
    rx = regularized_rx_scores(features, valid, shrinkage, max_samples)
    use_rx = rx > local_best
    per_date = np.where(use_rx, rx, local_best)
    per_date[~valid] = 0.0
    peak_date_index = np.argmax(per_date, axis=0)
    peak_score = np.max(per_date, axis=0)
    repeat_count = np.sum(per_date >= threshold, axis=0).astype(np.int16)
    return {
        "featureNames": names,
        "local": local,
        "localFeatureIndex": local_feature_index,
        "rx": rx,
        "useRx": use_rx,
        "perDate": per_date,
        "peakDateIndex": peak_date_index,
        "peakScore": peak_score,
        "repeatCount": repeat_count,
        "valid": valid.copy(),
        "validObservationCount": int(np.count_nonzero(valid)),
        "validSpatialPixelCount": int(np.count_nonzero(np.any(valid, axis=0))),
    }


def _component_pixels(mask: np.ndarray) -> List[np.ndarray]:
    visited = np.zeros(mask.shape, dtype=bool)
    components: List[np.ndarray] = []
    rows, columns = mask.shape
    for row, column in np.argwhere(mask):
        row = int(row)
        column = int(column)
        if visited[row, column]:
            continue
        queue = deque([(row, column)])
        visited[row, column] = True
        pixels: List[Tuple[int, int]] = []
        while queue:
            current_row, current_column = queue.popleft()
            pixels.append((current_row, current_column))
            for row_offset in (-1, 0, 1):
                for column_offset in (-1, 0, 1):
                    if row_offset == 0 and column_offset == 0:
                        continue
                    next_row = current_row + row_offset
                    next_column = current_column + column_offset
                    if (
                        0 <= next_row < rows
                        and 0 <= next_column < columns
                        and mask[next_row, next_column]
                        and not visited[next_row, next_column]
                    ):
                        visited[next_row, next_column] = True
                        queue.append((next_row, next_column))
        components.append(np.asarray(pixels, dtype=np.int32))
    return components


def _feature_native_gsd(feature_name: str, manifest: Mapping[str, Any]) -> float:
    native_gsd = manifest["nativeGsdM"]
    if feature_name == "regularized-rx":
        return max(float(value) for value in native_gsd.values())
    if feature_name in native_gsd:
        return float(native_gsd[feature_name])
    input_bands = FEATURE_INPUT_BANDS.get(feature_name)
    if not input_bands:
        raise ValueError(f"No native-resolution definition for feature {feature_name}")
    return max(float(native_gsd[name]) for name in input_bands)


def _signal_at(
    scores: Mapping[str, Any],
    manifest: Mapping[str, Any],
    date_index: int,
    row: int,
    column: int,
) -> Dict[str, Any]:
    if bool(scores["useRx"][date_index, row, column]):
        feature_name = "regularized-rx"
        polarity = "unsigned"
    else:
        feature_index = int(scores["localFeatureIndex"][date_index, row, column])
        feature_name = scores["featureNames"][feature_index]
        local_value = float(scores["local"][feature_index, date_index, row, column])
        polarity = "positive" if local_value >= 0.0 else "negative"
    return {
        "date": manifest["dates"][date_index],
        "feature": feature_name,
        "polarity": polarity,
        "score": float(scores["perDate"][date_index, row, column]),
        "observableResolutionM": _feature_native_gsd(feature_name, manifest),
    }


def _implementation_identity() -> Dict[str, Any]:
    script_dir = Path(__file__).resolve().parent
    artifact_names = (
        "ij_common.py",
        "ij_optical.py",
        "ij_optical_io.py",
        "ij_sources.py",
        "ij_spatial.py",
        "satellite.py",
    )
    plugin_manifest = Path(__file__).resolve().parents[3] / ".codex-plugin" / "plugin.json"
    plugin_version = "unpackaged"
    plugin_manifest_hash = None
    if plugin_manifest.is_file():
        plugin_manifest_hash = sha256_file(plugin_manifest)
        try:
            parsed = json.loads(plugin_manifest.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and parsed.get("version"):
                plugin_version = str(parsed["version"])
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
    try:
        pyproj_version = importlib.metadata.version("pyproj")
    except importlib.metadata.PackageNotFoundError:
        pyproj_version = None
    return {
        "pluginVersion": plugin_version,
        "pluginManifestSha256": plugin_manifest_hash,
        "artifacts": {
            name: {"sha256": sha256_file(script_dir / name)}
            for name in artifact_names
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pillow": PILLOW_VERSION,
            "pyproj": pyproj_version,
        },
    }


def rank_optical_candidates(
    scores: Mapping[str, Any],
    manifest: Mapping[str, Any],
    threshold: float,
    min_pixels: int,
    min_dates: int,
    min_valid_dates: int,
    top_k: int,
) -> List[Dict[str, Any]]:
    if not math.isfinite(threshold) or threshold <= 0.0:
        raise ValueError("threshold must be positive and finite")
    if min(min_pixels, min_dates, min_valid_dates, top_k) < 1:
        raise ValueError(
            "min_pixels, min_dates, min_valid_dates, and top_k must be positive"
        )
    if min_dates > min_valid_dates:
        raise ValueError("min_dates cannot exceed min_valid_dates")
    x_min, y_min, x_max, y_max = manifest["bbox"]
    pixel_size = float(manifest["pixelSizeM"])
    dates = manifest["dates"]
    valid = scores["valid"]
    per_date = scores["perDate"]
    proposals: List[Dict[str, Any]] = []
    for date_index, date in enumerate(dates):
        components = _component_pixels(per_date[date_index] >= threshold)
        for pixels in components:
            if pixels.shape[0] < min_pixels:
                continue
            rows = pixels[:, 0]
            columns = pixels[:, 1]
            values = per_date[date_index, rows, columns]
            peak_offset = int(np.argmax(values))
            peak_row = int(rows[peak_offset])
            peak_column = int(columns[peak_offset])
            valid_indices = np.flatnonzero(valid[:, peak_row, peak_column])
            support_indices = np.flatnonzero(
                valid[:, peak_row, peak_column]
                & (per_date[:, peak_row, peak_column] >= threshold)
            )
            if (
                valid_indices.size < min_valid_dates
                or support_indices.size < min_dates
            ):
                continue
            support_signals = [
                _signal_at(scores, manifest, int(index), peak_row, peak_column)
                for index in support_indices
            ]
            peak_signal = _signal_at(
                scores,
                manifest,
                date_index,
                peak_row,
                peak_column,
            )
            signal_keys = {
                (signal["feature"], signal["polarity"]) for signal in support_signals
            }
            weights = np.maximum(values, EPSILON)
            centroid_row = float(np.average(rows + 0.5, weights=weights))
            centroid_column = float(np.average(columns + 0.5, weights=weights))
            min_row, max_row = int(rows.min()), int(rows.max())
            min_column, max_column = int(columns.min()), int(columns.max())
            component_resolution = max(
                _signal_at(
                    scores,
                    manifest,
                    date_index,
                    int(row),
                    int(column),
                )["observableResolutionM"]
                for row, column in zip(rows, columns)
            )
            observable_resolution = max(
                component_resolution,
                *(
                    signal["observableResolutionM"]
                    for signal in support_signals
                ),
            )
            identity = (
                f"{manifest['arraySha256']}:{peak_row}:{peak_column}:"
                f"{date_index}:{peak_signal['feature']}"
            )
            proposals.append(
                {
                    "candidateId": stable_id("optical", identity),
                    "rank": 0,
                    "proxy": "spectral or temporal surface-reflectance anomaly",
                    "score": float(values.max()),
                    "scoreType": "standardized anomaly score; not probability",
                    "componentDate": date,
                    "pixelCount": int(pixels.shape[0]),
                    "componentGridAreaM2": float(
                        pixels.shape[0] * pixel_size * pixel_size
                    ),
                    "observableResolutionM": observable_resolution,
                    "centroidProjected": [
                        x_min + centroid_column * pixel_size,
                        y_max - centroid_row * pixel_size,
                    ],
                    "bboxProjected": [
                        x_min + min_column * pixel_size,
                        y_max - (max_row + 1) * pixel_size,
                        x_min + (max_column + 1) * pixel_size,
                        y_max - min_row * pixel_size,
                    ],
                    "peak": {
                        **peak_signal,
                        "row": peak_row,
                        "column": peak_column,
                    },
                    "validDateCountAtPeakPixel": int(valid_indices.size),
                    "supportDateCountAtPeakPixel": int(support_indices.size),
                    "supportFractionAtPeakPixel": float(
                        support_indices.size / valid_indices.size
                    ),
                    "supportSignals": support_signals,
                    "sameFeatureAndPolarityAcrossSupport": len(signal_keys) == 1,
                    "interpretation": (
                        "Candidate only. Test clouds, seams, crop management, drainage, "
                        "soil, geology, and modern infrastructure before archaeological use."
                    ),
                    "_pixelSet": {
                        (int(row), int(column)) for row, column in pixels
                    },
                }
            )
    proposals.sort(
        key=lambda item: (
            -item["supportFractionAtPeakPixel"],
            -item["supportDateCountAtPeakPixel"],
            -item["score"],
            -item["pixelCount"],
            item["candidateId"],
        )
    )
    candidates: List[Dict[str, Any]] = []
    selected_pixels: List[set[Tuple[int, int]]] = []
    for proposal in proposals:
        pixels = proposal.pop("_pixelSet")
        if any(pixels & selected for selected in selected_pixels):
            continue
        selected_pixels.append(pixels)
        candidates.append(proposal)
        if len(candidates) >= top_k:
            break
    for rank, candidate in enumerate(candidates, start=1):
        candidate["rank"] = rank
    return candidates


def build_optical_result(
    manifest_path: Path,
    manifest: Mapping[str, Any],
    scores: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
    parameters: Mapping[str, Any],
    diagnostics: Mapping[str, Path],
) -> Dict[str, Any]:
    return {
        "schemaVersion": "1.0",
        "createdAt": utc_now(),
        "method": {
            "name": "transparent-multitemporal-optical-proxy-baseline",
            "version": "1.2",
            "implementation": _implementation_identity(),
            "features": list(scores["featureNames"]),
            "operations": [
                "per-date local standardized contrast",
                "regularized global RX distance",
                "per-date eight-connected component extraction",
                "exact-peak temporal support accounting",
                "overlap-based cross-date proposal deduplication",
            ],
            "claimBoundary": (
                "Scores are standardized detector outputs whose thresholds change "
                "with the feature set. They are not calibrated probabilities and do "
                "not identify archaeological sites."
            ),
        },
        "input": {
            "manifestPath": str(manifest_path.resolve()),
            "manifestSha256": manifest["_manifestSha256"],
            "arrayPath": manifest["arrayPath"],
            "arraySha256": manifest["arraySha256"],
            "crs": manifest["crs"],
            "coordinateUnit": manifest["coordinateUnit"],
            "bbox": manifest["bbox"],
            "pixelSizeM": manifest["pixelSizeM"],
            "northUp": manifest["northUp"],
            "unit": manifest["unit"],
            "reflectanceScale": manifest["reflectanceScale"],
            "reflectanceOffset": manifest["reflectanceOffset"],
            "nativeGsdM": manifest["nativeGsdM"],
            "dates": manifest["dates"],
            "bands": manifest["bands"],
            "sensor": manifest["sensor"],
            "processingLevel": manifest["processingLevel"],
            "maskPolicy": manifest["maskPolicy"],
            "resampling": manifest["resampling"],
            "targetLabelsUsed": False,
            "sourceAssets": manifest["sourceAssets"],
        },
        "access": {
            "disclosure": manifest["disclosure"],
            "containsPreciseCoordinates": True,
            "sharingWarning": (
                "This analytical artifact contains projected centroids and bounding "
                "boxes. Do not share it beyond the case disclosure class; create a "
                "separate reviewed and spatially redacted public artifact."
            ),
        },
        "parameters": dict(parameters),
        "summary": {
            "validObservations": scores["validObservationCount"],
            "validSpatialPixels": scores["validSpatialPixelCount"],
            "candidateCount": len(candidates),
        },
        "candidates": list(candidates),
        "diagnostics": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in diagnostics.items()
        },
    }
