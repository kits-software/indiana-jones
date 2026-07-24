from __future__ import annotations

import argparse
import ipaddress
import json
import math
import os
import tempfile
from html import escape as escape_html
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.parse import parse_qsl, urlparse
from xml.sax.saxutils import escape


DISCLOSURES = {"public", "restricted", "heritage-authority-only"}
LOCATION_CLASSES = {
    "possible-new",
    "vulnerable",
    "sacred",
    "burial",
    "non-public",
    "known-public",
    "cleared-public",
    "ordinary",
}
FEATURE_ROLES = {
    "candidate-point",
    "candidate-footprint",
    "research-aoi",
    "image-point",
    "image-footprint",
    "known-site",
    "control",
}
PUBLIC_BLOCKED_LOCATION_CLASSES = {"vulnerable", "sacred", "burial", "non-public"}
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


class HandoffError(ValueError):
    pass


def bounded_float(value: Any, minimum: float, maximum: float, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise HandoffError(f"{label} must be numeric") from error
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise HandoffError(f"{label} must be between {minimum} and {maximum}")
    return number


def latitude(value: str) -> float:
    try:
        return bounded_float(value, -90.0, 90.0, "latitude")
    except HandoffError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def longitude(value: str) -> float:
    try:
        return bounded_float(value, -180.0, 180.0, "longitude")
    except HandoffError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _position(value: Any, field: str) -> list[float]:
    if not isinstance(value, list) or len(value) < 2:
        raise HandoffError(f"{field} must be [longitude, latitude]")
    longitude_value = bounded_float(value[0], -180.0, 180.0, f"{field}[0]")
    latitude_value = bounded_float(value[1], -90.0, 90.0, f"{field}[1]")
    return [longitude_value, latitude_value]


def _polygon_coordinates(value: Any, field: str) -> list[list[list[float]]]:
    if not isinstance(value, list) or not value:
        raise HandoffError(f"{field} must contain at least one linear ring")
    rings: list[list[list[float]]] = []
    for ring_index, raw_ring in enumerate(value):
        ring_field = f"{field}[{ring_index}]"
        if not isinstance(raw_ring, list) or len(raw_ring) < 4:
            raise HandoffError(f"{ring_field} must contain at least four positions")
        ring = [
            _position(position, f"{ring_field}[{position_index}]")
            for position_index, position in enumerate(raw_ring)
        ]
        if ring[0] != ring[-1]:
            raise HandoffError(f"{ring_field} must be closed")
        rings.append(ring)
    return rings


def _text_property(properties: Mapping[str, Any], key: str, default: str) -> str:
    value = properties.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise HandoffError(f"feature.properties.{key} must be non-empty text")
    return value.strip()


def normalize_feature(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("type") != "Feature":
        raise HandoffError(f"features[{index}] must be a GeoJSON Feature")
    geometry = raw.get("geometry")
    if not isinstance(geometry, dict):
        raise HandoffError(f"features[{index}].geometry must be an object")
    geometry_type = geometry.get("type")
    if geometry_type == "Point":
        coordinates: Any = _position(
            geometry.get("coordinates"),
            f"features[{index}].geometry.coordinates",
        )
    elif geometry_type == "Polygon":
        coordinates = _polygon_coordinates(
            geometry.get("coordinates"),
            f"features[{index}].geometry.coordinates",
        )
    else:
        raise HandoffError(
            f"features[{index}].geometry.type must be Point or Polygon"
        )

    properties = raw.get("properties", {})
    if not isinstance(properties, dict):
        raise HandoffError(f"features[{index}].properties must be an object")
    normalized_properties = dict(properties)
    normalized_properties["name"] = _text_property(
        properties,
        "name",
        f"Spatial feature {index + 1}",
    )
    default_role = "candidate-point" if geometry_type == "Point" else "research-aoi"
    role = _text_property(properties, "featureRole", default_role)
    if role not in FEATURE_ROLES:
        raise HandoffError(
            f"features[{index}].properties.featureRole must be one of "
            + ", ".join(sorted(FEATURE_ROLES))
        )
    normalized_properties["featureRole"] = role
    location_class = properties.get("locationClass")
    if location_class is not None and location_class not in LOCATION_CLASSES:
        raise HandoffError(
            f"features[{index}].properties.locationClass is unsupported"
        )
    for image_field in ("imagePath", "imageUrl", "imageSourceId", "imageCaption"):
        image_value = properties.get(image_field)
        if image_value is not None and (
            not isinstance(image_value, str) or not image_value.strip()
        ):
            raise HandoffError(
                f"features[{index}].properties.{image_field} must be text"
            )

    feature_id = raw.get("id", f"feature-{index + 1:03d}")
    if not isinstance(feature_id, (str, int)):
        raise HandoffError(f"features[{index}].id must be text or an integer")
    return {
        "type": "Feature",
        "id": str(feature_id),
        "properties": normalized_properties,
        "geometry": {"type": geometry_type, "coordinates": coordinates},
    }


def load_feature_collection(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HandoffError(f"cannot read spatial features: {error}") from error
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise HandoffError("--features must contain a GeoJSON FeatureCollection")
    raw_features = payload.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        raise HandoffError("--features must contain at least one feature")
    features = [
        normalize_feature(feature, index)
        for index, feature in enumerate(raw_features)
    ]
    ids = [feature["id"] for feature in features]
    if len(ids) != len(set(ids)):
        raise HandoffError("spatial feature ids must be unique")
    return features


def feature_from_args(args: argparse.Namespace) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "name": args.title,
        "featureRole": args.feature_role
        or ("candidate-point" if args.geometry == "point" else "research-aoi"),
        "locationClass": args.location_class,
    }
    if args.sensitivity:
        properties["sensitivity"] = args.sensitivity
    if args.image:
        properties["imagePath"] = args.image
    if args.image_source_id:
        properties["imageSourceId"] = args.image_source_id
    if args.image_caption:
        properties["imageCaption"] = args.image_caption
    if args.geometry == "point":
        if args.latitude is None or args.longitude is None:
            raise HandoffError("point handoffs require --latitude and --longitude")
        geometry = {
            "type": "Point",
            "coordinates": [args.longitude, args.latitude],
        }
    else:
        bounds = (args.west, args.south, args.east, args.north)
        if any(value is None for value in bounds):
            raise HandoffError("AOI handoffs require --west --south --east --north")
        if args.west >= args.east or args.south >= args.north:
            raise HandoffError("AOI bounds must have west < east and south < north")
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [
                    [args.west, args.south],
                    [args.east, args.south],
                    [args.east, args.north],
                    [args.west, args.north],
                    [args.west, args.south],
                ]
            ],
        }
    return normalize_feature(
        {
            "type": "Feature",
            "id": "feature-001",
            "properties": properties,
            "geometry": geometry,
        },
        0,
    )


def _public_feature_error(feature: Mapping[str, Any]) -> Optional[str]:
    properties = feature["properties"]
    location_class = properties.get("locationClass")
    if location_class in PUBLIC_BLOCKED_LOCATION_CLASSES:
        return f"locationClass {location_class!r} cannot use public disclosure"
    sensitivity = properties.get("sensitivity")
    spatial_restriction = properties.get("spatialRestriction")
    if sensitivity in {
        "restricted",
        "private",
        "non-public",
        "vulnerable",
        "sacred",
        "burial",
    }:
        return "feature sensitivity cannot use public disclosure"
    if spatial_restriction in {
        "withhold",
        "withheld",
        "authority-only",
        "heritage-authority-only",
        "restricted",
        "private",
        "non-public",
        "vulnerable",
        "sacred",
        "burial",
    }:
        return "spatially restricted feature cannot use public disclosure"
    if sensitivity != "public" and spatial_restriction != "public":
        return (
            "public spatial feature requires explicit sensitivity=public "
            "or spatialRestriction=public"
        )
    image_path = properties.get("imagePath")
    if isinstance(image_path, str):
        candidate = Path(image_path)
        if candidate.is_absolute() or ".." in candidate.parts or "\\" in image_path:
            return "public imagePath must be a safe relative path"
    image_url = properties.get("imageUrl")
    if isinstance(image_url, str):
        parsed = urlparse(image_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            return "public imageUrl must be a credential-free HTTPS URL"
        if parsed.hostname.casefold() == "localhost":
            return "public imageUrl cannot use a private host"
        try:
            if ipaddress.ip_address(parsed.hostname).is_private:
                return "public imageUrl cannot use a private host"
        except ValueError:
            pass
        query_keys = {key.casefold() for key, _ in parse_qsl(parsed.query)}
        if query_keys.intersection(SENSITIVE_QUERY_KEYS):
            return "public imageUrl cannot contain signed or credential query values"
    return None


def feature_positions(feature: Mapping[str, Any]) -> Iterable[list[float]]:
    geometry = feature["geometry"]
    if geometry["type"] == "Point":
        yield geometry["coordinates"]
        return
    for ring in geometry["coordinates"]:
        yield from ring


def google_maps_link(feature: Mapping[str, Any], zoom: int) -> str:
    geometry = feature["geometry"]
    if geometry["type"] == "Point":
        longitude_value, latitude_value = geometry["coordinates"]
        return (
            "https://www.google.com/maps/search/?api=1&query="
            f"{latitude_value:.6f}%2C{longitude_value:.6f}"
        )
    positions = list(feature_positions(feature))
    longitude_values = [position[0] for position in positions]
    latitude_values = [position[1] for position in positions]
    longitude_value = (min(longitude_values) + max(longitude_values)) / 2
    latitude_value = (min(latitude_values) + max(latitude_values)) / 2
    return (
        f"https://www.google.com/maps/@{latitude_value:.6f},"
        f"{longitude_value:.6f},{zoom}z"
    )


def _kml_description(properties: Mapping[str, Any]) -> str:
    link = properties["googleMapsLink"]
    lines = [
        (
            f'<a href="{escape_html(link, quote=True)}">'
            "Open in Google Maps</a>"
        ),
        f"Feature role: {escape_html(properties['featureRole'])}",
    ]
    for key, label in (
        ("locationClass", "Location class"),
        ("imagePath", "Image"),
        ("imageUrl", "Image URL"),
        ("imageSourceId", "Image source"),
        ("imageCaption", "Image caption"),
        ("observation", "Observation"),
    ):
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            lines.append(
                f"{escape_html(label)}: {escape_html(value.strip())}"
            )
    return "<![CDATA[" + "<br/>".join(lines) + "]]>"


def _kml_geometry(feature: Mapping[str, Any]) -> str:
    geometry = feature["geometry"]
    if geometry["type"] == "Point":
        longitude_value, latitude_value = geometry["coordinates"]
        return (
            "<Point><coordinates>"
            f"{longitude_value:.8f},{latitude_value:.8f},0"
            "</coordinates></Point>"
        )
    outer = geometry["coordinates"][0]
    coordinate_text = "\n".join(
        f"              {position[0]:.8f},{position[1]:.8f},0"
        for position in outer
    )
    return f"""<Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
{coordinate_text}
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>"""


def kml_document(title: str, features: Sequence[Mapping[str, Any]]) -> str:
    placemarks = []
    for feature in features:
        properties = feature["properties"]
        style = (
            "#evidence-point"
            if feature["geometry"]["type"] == "Point"
            else "#evidence-area"
        )
        placemarks.append(
            f"""    <Placemark id="{escape(str(feature['id']))}">
      <name>{escape(properties['name'])}</name>
      <description>{_kml_description(properties)}</description>
      <styleUrl>{style}</styleUrl>
      {_kml_geometry(feature)}
    </Placemark>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{escape(title)}</name>
    <Style id="evidence-point">
      <IconStyle><color>ff476fff</color><scale>1.1</scale></IconStyle>
    </Style>
    <Style id="evidence-area">
      <LineStyle><color>ff2a6fdb</color><width>3</width></LineStyle>
      <PolyStyle><color>332a6fdb</color></PolyStyle>
    </Style>
{chr(10).join(placemarks)}
  </Document>
</kml>
"""


def feature_summary(
    feature: Mapping[str, Any],
    link: str,
) -> dict[str, Any]:
    properties = feature["properties"]
    image_fields = {
        key: properties[key]
        for key in ("imagePath", "imageUrl", "imageSourceId", "imageCaption")
        if key in properties
    }
    return {
        "featureId": feature["id"],
        "name": properties["name"],
        "featureRole": properties["featureRole"],
        "geometryType": feature["geometry"]["type"],
        "geometry": feature["geometry"],
        "locationClass": properties.get("locationClass"),
        "googleMapsLink": link,
        "image": image_fields or None,
    }


def create_handoff(args: argparse.Namespace) -> Mapping[str, Any]:
    if args.disclosure not in DISCLOSURES:
        raise HandoffError("unsupported disclosure class")
    features = (
        load_feature_collection(args.features)
        if args.features
        else [feature_from_args(args)]
    )
    if args.disclosure == "public":
        for feature in features:
            problem = _public_feature_error(feature)
            if problem:
                raise HandoffError(problem)
    output_directory = args.out_dir
    kml_path = output_directory / "map-handoff.kml"
    geojson_path = output_directory / "map-handoff.geojson"
    manifest_path = output_directory / "map-handoff.manifest.json"
    links = [google_maps_link(feature, args.zoom) for feature in features]
    for feature, link in zip(features, links):
        feature["properties"]["googleMapsLink"] = link
    summaries = [
        feature_summary(feature, link)
        for feature, link in zip(features, links)
    ]
    geojson = {
        "type": "FeatureCollection",
        "disclosure": args.disclosure,
        "containsPreciseCoordinates": True,
        "features": features,
    }
    geometry_types = {feature["geometry"]["type"] for feature in features}
    precision_class = (
        "exact-point"
        if len(features) == 1 and geometry_types == {"Point"}
        else "exact-aoi"
        if len(features) == 1 and geometry_types == {"Polygon"}
        else "exact-feature-collection"
    )
    manifest = {
        "schemaVersion": "2.0",
        "title": args.title,
        "disclosure": args.disclosure,
        "precisionClass": precision_class,
        "containsPreciseCoordinates": True,
        "featureCount": len(features),
        "pointCount": sum(
            feature["geometry"]["type"] == "Point" for feature in features
        ),
        "areaCount": sum(
            feature["geometry"]["type"] == "Polygon" for feature in features
        ),
        "imageLinkedFeatureCount": sum(
            summary["image"] is not None for summary in summaries
        ),
        "features": summaries,
        "googleMapsLink": links[0],
        "googleMapsLinks": links,
        "kml": kml_path.name,
        "geojson": geojson_path.name,
        "claimBoundary": (
            "Points and AOIs preserve the reported spatial evidence. "
            "A mapped location does not by itself confirm an archaeological interpretation "
            "or authorize entry, collection, detecting, excavation, or disturbance."
        ),
    }
    atomic_write_text(kml_path, kml_document(args.title, features))
    atomic_write_json(geojson_path, geojson)
    atomic_write_json(manifest_path, manifest)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create Google Maps, KML, and GeoJSON handoffs containing exact "
            "archaeological points, AOIs, and image-linked spatial features"
        )
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument(
        "--disclosure",
        choices=tuple(sorted(DISCLOSURES)),
        required=True,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--geometry", choices=("point", "aoi"))
    source.add_argument("--features", type=Path)
    parser.add_argument(
        "--location-class",
        choices=tuple(sorted(LOCATION_CLASSES)),
        default="possible-new",
    )
    parser.add_argument("--feature-role", choices=tuple(sorted(FEATURE_ROLES)))
    parser.add_argument(
        "--sensitivity",
        choices=(
            "public",
            "restricted",
            "non-public",
            "vulnerable",
            "sacred",
            "burial",
        ),
    )
    parser.add_argument("--latitude", type=latitude)
    parser.add_argument("--longitude", type=longitude)
    parser.add_argument("--west", type=longitude)
    parser.add_argument("--south", type=latitude)
    parser.add_argument("--east", type=longitude)
    parser.add_argument("--north", type=latitude)
    parser.add_argument("--image")
    parser.add_argument("--image-source-id")
    parser.add_argument("--image-caption")
    parser.add_argument("--zoom", type=int, default=16)
    parser.add_argument(
        "--not-target-centered",
        action="store_true",
        help="Deprecated compatibility flag; exact spatial evidence is preserved.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = create_handoff(args)
    except HandoffError as error:
        print(f"error: {error}")
        return 2
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
