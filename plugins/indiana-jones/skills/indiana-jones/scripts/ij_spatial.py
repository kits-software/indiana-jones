from __future__ import annotations

import math
import re


GEOGRAPHIC_CRS_NAMES = {
    "EPSG:4326",
    "OGC:CRS84",
    "CRS:84",
    "WGS84",
    "WGS 84",
}
DISTORTED_GLOBAL_MERCATOR_CODES = {3395, 3857}


def _is_known_metric_epsg(code: int) -> bool:
    return (
        code in {27700, 3031, 3413}
        or 25828 <= code <= 25838
        or 26901 <= code <= 26923
        or 28348 <= code <= 28358
        or 32601 <= code <= 32660
        or 32701 <= code <= 32760
    )


def _validate_with_pyproj(crs: str) -> str | None:
    try:
        from pyproj import CRS
    except ImportError:
        return None

    try:
        parsed = CRS.from_user_input(crs)
    except Exception as error:
        raise ValueError(f"CRS cannot be parsed by pyproj: {crs}") from error
    epsg_code = parsed.to_epsg(min_confidence=0)
    operation = parsed.coordinate_operation
    method_name = str(
        operation.method_name if operation is not None else ""
    ).strip().lower()
    if epsg_code in DISTORTED_GLOBAL_MERCATOR_CODES or (
        method_name.startswith("mercator")
        or "pseudo mercator" in method_name
    ):
        raise ValueError(
            "Global Mercator is unsuitable for meter-accurate detector kernels; "
            "reproject to a suitable local projected CRS"
        )
    if not parsed.is_projected:
        raise ValueError(
            "Geographic longitude/latitude is not metric; reproject the raster to "
            "a suitable local projected CRS"
        )
    if not parsed.axis_info:
        raise ValueError("CRS has no axis-unit metadata")
    for axis in parsed.axis_info:
        unit_name = str(axis.unit_name or "").strip().lower()
        conversion = float(axis.unit_conversion_factor or 0.0)
        if unit_name not in {"metre", "meter"} or not math.isclose(
            conversion,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "Detector kernels are expressed in metres; reproject feet-based "
                "or other rasters before analysis"
            )
    return crs.strip()


def _validate_without_pyproj(crs: str, normalized: str) -> str:
    epsg_match = re.fullmatch(r"EPSG:(\d+)", normalized)
    if epsg_match:
        code = int(epsg_match.group(1))
        if _is_known_metric_epsg(code):
            return crs.strip()
        raise ValueError(
            f"EPSG:{code} is not in the dependency-free metric allowlist; install "
            "pyproj for authoritative unit validation or reproject to a local UTM CRS"
        )

    raise ValueError(
        "Custom WKT and PROJ strings require pyproj for authoritative projection "
        "and unit validation; otherwise use an allowlisted metric EPSG identifier"
    )


def validate_projected_crs(crs: str, coordinate_unit: str) -> str:
    normalized = crs.strip().upper()
    if not normalized:
        raise ValueError("A projected metric CRS is required")
    if coordinate_unit.strip().lower() not in {"metre", "meter"}:
        raise ValueError(
            "Detector kernels are expressed in metres; coordinateUnit must be metre"
        )
    if normalized in GEOGRAPHIC_CRS_NAMES:
        raise ValueError(
            "Geographic longitude/latitude is not metric; reproject the raster to "
            "a suitable local projected CRS"
        )

    epsg_match = re.fullmatch(r"EPSG:(\d+)", normalized)
    if epsg_match and int(epsg_match.group(1)) in DISTORTED_GLOBAL_MERCATOR_CODES:
        raise ValueError(
            "Global Mercator is unsuitable for meter-accurate detector kernels; "
            "reproject to a suitable local projected CRS"
        )
    if not (
        epsg_match
        or normalized.startswith("PROJCRS[")
        or normalized.startswith("+PROJ=")
    ):
        raise ValueError("CRS must be an EPSG identifier, PROJCRS WKT, or PROJ string")

    validated = _validate_with_pyproj(crs)
    if validated is not None:
        return validated
    return _validate_without_pyproj(crs, normalized)
