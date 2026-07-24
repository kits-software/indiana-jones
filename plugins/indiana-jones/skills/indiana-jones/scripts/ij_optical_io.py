from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import urllib.parse
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw

from ij_sources import validate_metric_bbox
from ij_spatial import validate_projected_crs


REQUIRED_BANDS = {"red", "nir"}
OPTIONAL_BANDS = {"blue", "green", "swir1", "swir2", "rededge1"}
ALLOWED_BANDS = REQUIRED_BANDS | OPTIONAL_BANDS
MAX_OBSERVATIONS = 1_000_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 128_000_000
EPSILON = 1e-8
SENSITIVE_QUERY_KEYS = {
    "access-token",
    "apikey",
    "api-key",
    "auth",
    "authorization",
    "awsaccesskeyid",
    "credential",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
    "x-amz-credential",
    "x-amz-security-token",
    "x-amz-signature",
    "x-goog-credential",
    "x-goog-signature",
}
SOURCE_RECORD_KEYS = {
    "accessBasis",
    "accessedAt",
    "acquiredAt",
    "assets",
    "collection",
    "itemId",
    "itemUrl",
    "license",
    "processingVersion",
}
ASSET_RECORD_KEYS = {"href", "sha256"}


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _require_concrete_text(value: Any, field: str) -> str:
    text = _require_text(value, field)
    normalized = text.lower()
    if "<" in text or ">" in text or normalized.startswith(
        ("record ", "document ", "replace ")
    ):
        raise ValueError(f"{field} still contains template placeholder text")
    return text


def _require_finite_number(
    value: Any,
    field: str,
    *,
    positive: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        qualifier = "positive finite" if positive else "finite"
        raise ValueError(f"{field} must be a {qualifier} number")
    parsed = float(value)
    if not math.isfinite(parsed) or (positive and parsed <= 0.0):
        qualifier = "positive finite" if positive else "finite"
        raise ValueError(f"{field} must be a {qualifier} number")
    return parsed


def _require_timestamp(value: Any, field: str) -> str:
    text = _require_concrete_text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 date or timestamp") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.isoformat().replace("+00:00", "Z")


def validate_safe_locator(value: Any, field: str) -> str:
    text = _require_concrete_text(value, field)
    if re.search(r"(?i)(?:^|\s)(?:bearer|basic)\s+\S+", text):
        raise ValueError(
            f"{field} contains authorization material; "
            "record a stable non-secret locator"
        )
    parsed = urllib.parse.urlsplit(text)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(
            f"{field} contains URL credentials; record a stable non-secret locator"
        )
    if parsed.fragment:
        raise ValueError(
            f"{field} contains a URL fragment; record a canonical fragment-free locator"
        )
    query_keys = set()
    for part in re.split(r"[&;]", parsed.query):
        raw_key = part.partition("=")[0]
        decoded_key = urllib.parse.unquote_plus(raw_key).strip().lower()
        normalized_key = re.sub(r"[^a-z0-9]+", "-", decoded_key).strip("-")
        if normalized_key:
            query_keys.add(normalized_key)
    decoded_query = urllib.parse.unquote_plus(parsed.query).lower()
    embedded_sensitive_assignment = re.search(
        (
            r"(?:access[-_ ]?token|api[-_ ]?key|authorization|credential|"
            r"password|secret|signature|token|x[-_ ]?amz[-_ ]?"
            r"(?:credential|security[-_ ]?token|signature)|x[-_ ]?goog[-_ ]?"
            r"(?:credential|signature))\s*="
        ),
        decoded_query,
    )
    sensitive = sorted(
        key
        for key in query_keys
        if key in SENSITIVE_QUERY_KEYS
        or key.endswith(
            (
                "-credential",
                "-key",
                "-password",
                "-secret",
                "-signature",
                "-token",
            )
        )
    )
    if sensitive or embedded_sensitive_assignment:
        raise ValueError(
            f"{field} contains credential-bearing query material; "
            "record a stable unsigned locator instead"
        )
    return text


def _resolve_array_path(manifest_path: Path, value: Any) -> Path:
    array_path = Path(_require_text(value, "arrayPath")).expanduser()
    if not array_path.is_absolute():
        array_path = manifest_path.parent / array_path
    return array_path.resolve()


def _validate_sources(
    sources: Any,
    dates: Sequence[str],
    bands: Sequence[str],
) -> List[Dict[str, Any]]:
    if not isinstance(sources, list) or not sources:
        raise ValueError("sourceAssets must contain at least one provenance record")
    resolved: List[Dict[str, Any]] = []
    allowed_dates = set(dates)
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"sourceAssets[{index}] must be an object")
        unknown_source_keys = sorted(set(source) - SOURCE_RECORD_KEYS)
        if unknown_source_keys:
            raise ValueError(
                f"sourceAssets[{index}] contains unsupported fields "
                f"{unknown_source_keys}; do not embed credentials or provider payloads"
            )
        record = {
            "itemId": _require_concrete_text(
                source.get("itemId"),
                f"sourceAssets[{index}].itemId",
            ),
            "itemUrl": validate_safe_locator(
                source.get("itemUrl"),
                f"sourceAssets[{index}].itemUrl",
            ),
            "collection": _require_concrete_text(
                source.get("collection"),
                f"sourceAssets[{index}].collection",
            ),
            "processingVersion": _require_concrete_text(
                source.get("processingVersion"),
                f"sourceAssets[{index}].processingVersion",
            ),
        }
        acquired_at = _require_timestamp(
            source.get("acquiredAt"),
            f"sourceAssets[{index}].acquiredAt",
        )
        record["acquiredAt"] = acquired_at
        record["accessedAt"] = _require_timestamp(
            source.get("accessedAt"),
            f"sourceAssets[{index}].accessedAt",
        )
        record["license"] = _require_concrete_text(
            source.get("license"),
            f"sourceAssets[{index}].license",
        )
        access_basis = source.get("accessBasis")
        if access_basis not in {
            "public",
            "local-user-provided",
            "user-authorized",
        }:
            raise ValueError(
                f"sourceAssets[{index}].accessBasis must state how the pixels were accessed"
            )
        record["accessBasis"] = access_basis
        assets = source.get("assets")
        if not isinstance(assets, dict) or set(assets) != set(bands):
            raise ValueError(
                f"sourceAssets[{index}].assets must map every declared band exactly"
            )
        resolved_assets: Dict[str, Dict[str, str]] = {}
        for band_name, asset in assets.items():
            if not isinstance(asset, dict):
                raise ValueError(
                    f"sourceAssets[{index}].assets.{band_name} must be an object"
                )
            unknown_asset_keys = sorted(set(asset) - ASSET_RECORD_KEYS)
            if unknown_asset_keys:
                raise ValueError(
                    f"sourceAssets[{index}].assets.{band_name} contains unsupported "
                    f"fields {unknown_asset_keys}; do not embed credentials"
                )
            resolved_asset = {
                "href": validate_safe_locator(
                    asset.get("href"),
                    f"sourceAssets[{index}].assets.{band_name}.href",
                )
            }
            asset_hash = str(asset.get("sha256") or "")
            if asset_hash:
                if not re.fullmatch(r"[0-9a-fA-F]{64}", asset_hash):
                    raise ValueError(
                        f"sourceAssets[{index}].assets.{band_name}.sha256 is invalid"
                    )
                resolved_asset["sha256"] = asset_hash.lower()
            resolved_assets[band_name] = resolved_asset
        record["assets"] = resolved_assets
        if acquired_at not in allowed_dates:
            raise ValueError(
                f"sourceAssets[{index}].acquiredAt is not listed in dates"
            )
        resolved.append(record)
    missing_dates = allowed_dates - {
        str(record.get("acquiredAt")) for record in resolved
    }
    if missing_dates:
        raise ValueError(
            f"sourceAssets has no provenance record for dates: {sorted(missing_dates)}"
        )
    return resolved


def _read_manifest(manifest_path: Path) -> Tuple[Dict[str, Any], str]:
    raw = manifest_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON manifest: {manifest_path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {manifest_path}")
    return value, digest


def _hash_open_file(handle: Any) -> str:
    digest = hashlib.sha256()
    handle.seek(0)
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    handle.seek(0)
    return digest.hexdigest()


def _inspect_npz(
    handle: Any,
    expected_names: Sequence[str],
    expected_dates: int,
) -> None:
    handle.seek(0)
    try:
        with zipfile.ZipFile(handle) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            expected_files = {f"{name}.npy" for name in expected_names}
            actual_files = {info.filename for info in infos}
            if actual_files != expected_files or len(infos) != len(expected_files):
                raise ValueError(
                    "Optical cube archive members must match declared bands plus valid"
                )
            uncompressed = sum(info.file_size for info in infos)
            if uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError(
                    f"Optical cube expands to {uncompressed:,} bytes; tile below the "
                    f"{MAX_ARCHIVE_UNCOMPRESSED_BYTES:,}-byte safety limit"
                )
            shapes = set()
            for info in infos:
                with archive.open(info) as member:
                    version = np.lib.format.read_magic(member)
                    if version == (1, 0):
                        shape, _, dtype = np.lib.format.read_array_header_1_0(member)
                    elif version == (2, 0):
                        shape, _, dtype = np.lib.format.read_array_header_2_0(member)
                    else:
                        raise ValueError(
                            f"Unsupported NPY member format {version} in {info.filename}"
                        )
                if dtype.hasobject or np.issubdtype(dtype, np.complexfloating):
                    raise ValueError(
                        "Optical cube arrays must contain real numeric values, not "
                        "objects or complex numbers"
                    )
                allowed_kinds = (
                    {"b", "i", "u"}
                    if info.filename == "valid.npy"
                    else {"f", "i", "u"}
                )
                if dtype.kind not in allowed_kinds:
                    raise ValueError(
                        f"{info.filename} has unsupported dtype {dtype}; use real "
                        "numeric reflectance and a boolean or integer valid mask"
                    )
                if len(shape) != 3 or shape[0] != expected_dates:
                    raise ValueError(
                        f"{info.filename} must have shape [date, row, column]"
                    )
                observations = int(np.prod(shape))
                if observations > MAX_OBSERVATIONS:
                    raise ValueError(
                        f"Cube contains {observations:,} observations; tile below "
                        f"the {MAX_OBSERVATIONS:,} safety limit"
                    )
                if observations * dtype.itemsize > info.file_size:
                    raise ValueError(f"{info.filename} declares more data than it stores")
                shapes.add(tuple(int(value) for value in shape))
            if len(shapes) != 1:
                raise ValueError("Every optical cube array must share one shape")
    except zipfile.BadZipFile as error:
        raise ValueError("Optical cube is not a valid NPZ archive") from error
    finally:
        handle.seek(0)


def load_optical_cube(
    manifest_path: Path,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray], np.ndarray]:
    manifest, manifest_hash = _read_manifest(manifest_path)
    if manifest.get("schemaVersion") != "1.0":
        raise ValueError("Optical cube schemaVersion must be 1.0")
    if manifest.get("modality") != "multispectral-optical":
        raise ValueError("Optical cube modality must be multispectral-optical")
    if manifest.get("targetLabelsUsed") is not False:
        raise ValueError(
            "Candidate generation requires targetLabelsUsed to be explicitly false"
        )
    if manifest.get("northUp") is not True:
        raise ValueError("Optical cube must be a north-up projected grid")

    crs = validate_projected_crs(
        _require_text(manifest.get("crs"), "crs"),
        _require_text(manifest.get("coordinateUnit"), "coordinateUnit"),
    )
    bbox_value = manifest.get("bbox")
    if not isinstance(bbox_value, list) or len(bbox_value) != 4:
        raise ValueError("bbox must contain four finite metre coordinates")
    bbox = validate_metric_bbox(
        [
            _require_finite_number(value, f"bbox[{index}]")
            for index, value in enumerate(bbox_value)
        ],
        max_area_km2=400.0,
    )
    pixel_size_m = _require_finite_number(
        manifest.get("pixelSizeM"),
        "pixelSizeM",
        positive=True,
    )

    dates_raw = manifest.get("dates")
    if not isinstance(dates_raw, list) or len(dates_raw) < 2:
        raise ValueError("dates must contain at least two acquisition timestamps")
    dates = [_require_timestamp(value, "dates[]") for value in dates_raw]
    if len(set(dates)) != len(dates):
        raise ValueError("dates must be unique")

    bands_raw = manifest.get("bands")
    if not isinstance(bands_raw, list):
        raise ValueError("bands must be an array")
    band_names = [_require_text(value, "bands[]").lower() for value in bands_raw]
    if len(set(band_names)) != len(band_names):
        raise ValueError("bands must not contain duplicates")
    missing = REQUIRED_BANDS - set(band_names)
    unsupported = set(band_names) - ALLOWED_BANDS
    if missing:
        raise ValueError(f"Optical cube is missing required bands: {sorted(missing)}")
    if unsupported:
        raise ValueError(f"Optical cube contains unsupported bands: {sorted(unsupported)}")

    if manifest.get("unit") != "surface-reflectance":
        raise ValueError("unit must be surface-reflectance")
    _require_concrete_text(manifest.get("sensor"), "sensor")
    _require_concrete_text(manifest.get("processingLevel"), "processingLevel")
    _require_concrete_text(manifest.get("maskPolicy"), "maskPolicy")
    _require_concrete_text(manifest.get("resampling"), "resampling")
    if manifest.get("disclosure") not in {
        "public",
        "restricted",
        "heritage-authority-only",
    }:
        raise ValueError("disclosure must be public, restricted, or heritage-authority-only")
    native_gsd_raw = manifest.get("nativeGsdM")
    if not isinstance(native_gsd_raw, dict) or set(native_gsd_raw) != set(band_names):
        raise ValueError("nativeGsdM must map every declared band exactly")
    native_gsd: Dict[str, float] = {}
    for band_name, value in native_gsd_raw.items():
        resolved_gsd = _require_finite_number(
            value,
            f"nativeGsdM.{band_name}",
            positive=True,
        )
        native_gsd[band_name] = resolved_gsd
    scale = _require_finite_number(
        manifest.get("reflectanceScale", 1.0),
        "reflectanceScale",
        positive=True,
    )
    offset = _require_finite_number(
        manifest.get("reflectanceOffset", 0.0),
        "reflectanceOffset",
    )

    array_path = _resolve_array_path(manifest_path, manifest.get("arrayPath"))
    if not array_path.is_file():
        raise ValueError(f"Optical cube array does not exist: {array_path}")
    expected_hash = _require_text(manifest.get("arraySha256"), "arraySha256")
    with array_path.open("rb") as handle:
        actual_hash = _hash_open_file(handle)
        if expected_hash.lower() != actual_hash:
            raise ValueError("arraySha256 does not match the optical cube")
        _inspect_npz(handle, [*band_names, "valid"], len(dates))
        with np.load(handle, allow_pickle=False) as archive:
            valid = np.asarray(archive["valid"])
            if valid.ndim != 3 or valid.shape[0] != len(dates):
                raise ValueError("valid must have shape [date, row, column]")
            observations = int(np.prod(valid.shape))
            if observations > MAX_OBSERVATIONS:
                raise ValueError(
                    f"Cube contains {observations:,} observations; tile below "
                    f"the {MAX_OBSERVATIONS:,} safety limit"
                )
            if valid.dtype != np.bool_:
                if not np.isin(valid, [0, 1]).all():
                    raise ValueError("valid must be boolean or contain only 0 and 1")
                valid = valid.astype(bool)
            arrays: Dict[str, np.ndarray] = {}
            for name in band_names:
                array = np.asarray(archive[name], dtype=np.float64)
                if array.shape != valid.shape:
                    raise ValueError(f"{name} shape does not match valid")
                arrays[name] = array * scale + offset
        if _hash_open_file(handle) != actual_hash:
            raise ValueError("Optical cube changed while it was being loaded")

    rows, columns = valid.shape[1:]
    expected_width = columns * pixel_size_m
    expected_height = rows * pixel_size_m
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    tolerance = max(pixel_size_m * 0.01, 1e-6)
    if abs(width - expected_width) > tolerance or abs(height - expected_height) > tolerance:
        raise ValueError("bbox, pixelSizeM, and cube shape describe different grids")

    finite = np.ones(valid.shape, dtype=bool)
    for array in arrays.values():
        finite &= np.isfinite(array)
    declared_valid_nonfinite = int(np.count_nonzero(valid & ~finite))
    if declared_valid_nonfinite:
        raise ValueError(
            "valid marks "
            f"{declared_valid_nonfinite:,} date-pixel observations with non-finite "
            "reflectance as usable; fix the cube or its mask"
        )
    valid &= finite
    if not np.any(valid):
        raise ValueError("Optical cube has no finite valid observations")

    sources = _validate_sources(manifest.get("sourceAssets"), dates, band_names)
    resolved = dict(manifest)
    resolved.update(
        {
            "arrayPath": str(array_path),
            "arraySha256": actual_hash,
            "bands": band_names,
            "dates": dates,
            "bbox": list(bbox),
            "crs": crs,
            "coordinateUnit": "metre",
            "pixelSizeM": pixel_size_m,
            "nativeGsdM": native_gsd,
            "reflectanceScale": scale,
            "reflectanceOffset": offset,
            "sourceAssets": sources,
            "_manifestSha256": manifest_hash,
        }
    )
    return resolved, arrays, valid


def _atomic_save_npz(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".npz",
        dir=str(path.parent),
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        np.savez_compressed(temporary_path, **arrays)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def save_optical_diagnostics(
    out_dir: Path,
    scores: Mapping[str, Any],
    candidates: Sequence[Mapping[str, Any]],
) -> Dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    arrays_path = out_dir / "optical-scores.npz"
    _atomic_save_npz(
        arrays_path,
        peakScore=np.asarray(scores["peakScore"], dtype=np.float32),
        repeatCount=np.asarray(scores["repeatCount"], dtype=np.int16),
        peakDateIndex=np.asarray(scores["peakDateIndex"], dtype=np.int16),
        perDate=np.asarray(scores["perDate"], dtype=np.float32),
    )
    heatmap = np.asarray(scores["peakScore"], dtype=np.float64)
    finite = heatmap[np.isfinite(heatmap)]
    upper = float(np.percentile(finite, 99.5)) if finite.size else 1.0
    scaled = np.clip(heatmap / max(upper, EPSILON), 0.0, 1.0)
    image = Image.fromarray(np.uint8(scaled * 255.0)).convert("RGB")
    draw = ImageDraw.Draw(image)
    for candidate in candidates:
        row = int(candidate["peak"]["row"])
        column = int(candidate["peak"]["column"])
        draw.rectangle(
            (column - 2, row - 2, column + 2, row + 2),
            outline=(255, 64, 64),
            width=1,
        )
    heatmap_path = out_dir / "optical-anomalies.png"
    image.save(heatmap_path)
    return {"scoreArrays": arrays_path, "anomalyPreview": heatmap_path}
