from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageOps


DISCLOSURES = ("public", "restricted", "heritage-authority-only")
DISCLOSURE_RANK = {name: index for index, name in enumerate(DISCLOSURES)}
KINDS = {"point", "line", "rectangle", "ellipse", "polygon"}
STATUSES = {"observed", "derived", "alternative"}
SOURCE_ROLES = {"analysis", "corroboration", "negative-control"}
GOOGLE_HOSTS = {
    "google.com",
    "google.co.uk",
    "earth.google.com",
    "maps.google.com",
    "maps.googleapis.com",
    "streetviewpixels-pa.googleapis.com",
}
COLORS = {
    "observed": "#ff5a47",
    "derived": "#ffd166",
    "alternative": "#45c4e8",
}


class ManifestError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestError(f"Cannot read annotation manifest: {error}") from error
    if not isinstance(payload, dict):
        raise ManifestError("Annotation manifest must be a JSON object")
    return payload


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be non-empty text")
    return value.strip()


def require_keys(
    payload: Mapping[str, Any],
    required: Iterable[str],
    allowed: Iterable[str],
    field: str,
) -> None:
    required_set = set(required)
    allowed_set = set(allowed)
    missing = sorted(required_set - set(payload))
    extra = sorted(set(payload) - allowed_set)
    if missing:
        raise ManifestError(f"{field} is missing: {', '.join(missing)}")
    if extra:
        raise ManifestError(f"{field} has unsupported fields: {', '.join(extra)}")


def parse_color(value: Any, field: str) -> str:
    color = require_text(value, field)
    if len(color) != 7 or color[0] != "#":
        raise ManifestError(f"{field} must use #RRGGBB")
    try:
        int(color[1:], 16)
    except ValueError as error:
        raise ManifestError(f"{field} must use #RRGGBB") from error
    return color.lower()


def is_google_source(provider: str, *locators: str) -> bool:
    haystack = provider.lower()
    if "google" in haystack or "street view" in haystack:
        return True
    for locator in locators:
        host = (urlparse(locator).hostname or "").lower()
        if any(host == item or host.endswith(f".{item}") for item in GOOGLE_HOSTS):
            return True
    return False


def validate_point(
    point: Any,
    coordinate_space: str,
    width: int,
    height: int,
    field: str,
) -> Tuple[float, float]:
    if (
        not isinstance(point, list)
        or len(point) != 2
        or isinstance(point[0], bool)
        or isinstance(point[1], bool)
        or not isinstance(point[0], (int, float))
        or not isinstance(point[1], (int, float))
    ):
        raise ManifestError(f"{field} must be [x, y]")
    x_value = float(point[0])
    y_value = float(point[1])
    if not math.isfinite(x_value) or not math.isfinite(y_value):
        raise ManifestError(f"{field} must contain finite coordinates")
    if coordinate_space == "normalized":
        if not 0.0 <= x_value <= 1.0 or not 0.0 <= y_value <= 1.0:
            raise ManifestError(f"{field} normalized coordinates must be within 0..1")
    elif not 0.0 <= x_value < width or not 0.0 <= y_value < height:
        raise ManifestError(f"{field} pixel coordinates are outside the source frame")
    return x_value, y_value


def validate_points(
    annotation: Mapping[str, Any],
    coordinate_space: str,
    width: int,
    height: int,
    field: str,
) -> List[Tuple[float, float]]:
    kind = annotation["kind"]
    raw_points = annotation["points"]
    if not isinstance(raw_points, list):
        raise ManifestError(f"{field}.points must be an array")
    required_counts = {"point": 1, "rectangle": 2, "ellipse": 2}
    if kind in required_counts and len(raw_points) != required_counts[kind]:
        raise ManifestError(
            f"{field}.points requires {required_counts[kind]} point(s) for {kind}"
        )
    if kind == "line" and len(raw_points) < 2:
        raise ManifestError(f"{field}.points requires at least 2 points for line")
    if kind == "polygon" and len(raw_points) < 3:
        raise ManifestError(f"{field}.points requires at least 3 points for polygon")
    return [
        validate_point(point, coordinate_space, width, height, f"{field}.points[{index}]")
        for index, point in enumerate(raw_points)
    ]


def validate_manifest(
    payload: Dict[str, Any],
    width: int,
    height: int,
) -> Dict[str, Any]:
    require_keys(
        payload,
        (
            "schemaVersion",
            "title",
            "disclosure",
            "coordinateSpace",
            "source",
            "frame",
            "annotations",
        ),
        (
            "schemaVersion",
            "title",
            "disclosure",
            "coordinateSpace",
            "source",
            "frame",
            "annotations",
        ),
        "manifest",
    )
    if payload["schemaVersion"] != "1.0":
        raise ManifestError("schemaVersion must be 1.0")
    payload["title"] = require_text(payload["title"], "title")
    disclosure = require_text(payload["disclosure"], "disclosure")
    if disclosure not in DISCLOSURES:
        raise ManifestError(f"disclosure must be one of {', '.join(DISCLOSURES)}")
    coordinate_space = require_text(payload["coordinateSpace"], "coordinateSpace")
    if coordinate_space not in {"normalized", "pixel"}:
        raise ManifestError("coordinateSpace must be normalized or pixel")

    source = payload["source"]
    if not isinstance(source, dict):
        raise ManifestError("source must be an object")
    source_fields = (
        "sourceId",
        "provider",
        "product",
        "sensor",
        "acquiredAt",
        "resolution",
        "license",
        "attribution",
        "locator",
        "publicLocator",
        "sourceRole",
        "derivativeUseAuthorized",
    )
    require_keys(source, source_fields, source_fields, "source")
    for field in source_fields[:-2]:
        source[field] = require_text(source[field], f"source.{field}")
    source["sourceRole"] = require_text(source["sourceRole"], "source.sourceRole")
    if source["sourceRole"] not in SOURCE_ROLES:
        raise ManifestError(
            f"source.sourceRole must be one of {', '.join(sorted(SOURCE_ROLES))}"
        )
    if source["derivativeUseAuthorized"] is not True:
        raise ManifestError("source.derivativeUseAuthorized must be true")
    if is_google_source(
        source["provider"],
        source["locator"],
        source["publicLocator"],
    ):
        raise ManifestError(
            "Google Maps, Earth, and Street View remain manual references and "
            "cannot be rendered by this annotation utility"
        )

    frame = payload["frame"]
    if not isinstance(frame, dict):
        raise ManifestError("frame must be an object")
    frame_fields = ("viewType", "orientation", "locationLabel", "processing")
    require_keys(frame, frame_fields, frame_fields, "frame")
    frame["viewType"] = require_text(frame["viewType"], "frame.viewType")
    if frame["viewType"] not in {"source-measurement", "derived-visualization"}:
        raise ManifestError(
            "frame.viewType must be source-measurement or derived-visualization"
        )
    frame["orientation"] = require_text(frame["orientation"], "frame.orientation")
    frame["locationLabel"] = require_text(
        frame["locationLabel"], "frame.locationLabel"
    )
    if (
        not isinstance(frame["processing"], list)
        or not frame["processing"]
        or any(not isinstance(item, str) or not item.strip() for item in frame["processing"])
    ):
        raise ManifestError("frame.processing must contain at least one text entry")
    frame["processing"] = [item.strip() for item in frame["processing"]]

    annotations = payload["annotations"]
    if not isinstance(annotations, list) or not annotations:
        raise ManifestError("annotations must contain at least one annotation")
    seen_ids = set()
    normalized_annotations = []
    annotation_fields = (
        "id",
        "kind",
        "points",
        "label",
        "observation",
        "status",
        "sensitivity",
        "color",
    )
    for index, item in enumerate(annotations):
        field = f"annotations[{index}]"
        if not isinstance(item, dict):
            raise ManifestError(f"{field} must be an object")
        require_keys(item, annotation_fields[:-1], annotation_fields, field)
        item["id"] = require_text(item["id"], f"{field}.id")
        if item["id"] in seen_ids:
            raise ManifestError(f"{field}.id must be unique")
        seen_ids.add(item["id"])
        item["kind"] = require_text(item["kind"], f"{field}.kind")
        if item["kind"] not in KINDS:
            raise ManifestError(f"{field}.kind must be one of {', '.join(sorted(KINDS))}")
        item["label"] = require_text(item["label"], f"{field}.label")
        item["observation"] = require_text(item["observation"], f"{field}.observation")
        item["status"] = require_text(item["status"], f"{field}.status")
        if item["status"] not in STATUSES:
            raise ManifestError(
                f"{field}.status must be one of {', '.join(sorted(STATUSES))}"
            )
        item["sensitivity"] = require_text(
            item["sensitivity"], f"{field}.sensitivity"
        )
        if item["sensitivity"] not in DISCLOSURES:
            raise ManifestError(
                f"{field}.sensitivity must be one of {', '.join(DISCLOSURES)}"
            )
        if DISCLOSURE_RANK[item["sensitivity"]] > DISCLOSURE_RANK[disclosure]:
            raise ManifestError(
                f"{field} is more sensitive than the plate disclosure"
            )
        item["color"] = parse_color(
            item.get("color", COLORS[item["status"]]),
            f"{field}.color",
        )
        item["_points"] = validate_points(
            item,
            coordinate_space,
            width,
            height,
            field,
        )
        normalized_annotations.append(item)
    payload["annotations"] = normalized_annotations
    return payload


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def rgb(color: str) -> Tuple[int, int, int]:
    return tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))


def map_points(
    points: Sequence[Tuple[float, float]],
    coordinate_space: str,
    width: int,
    height: int,
) -> List[Tuple[int, int]]:
    if coordinate_space == "pixel":
        return [(round(x_value), round(y_value)) for x_value, y_value in points]
    return [
        (round(x_value * (width - 1)), round(y_value * (height - 1)))
        for x_value, y_value in points
    ]


def draw_annotation(
    draw: ImageDraw.ImageDraw,
    annotation: Mapping[str, Any],
    coordinate_space: str,
    width: int,
    height: int,
    label_font: ImageFont.ImageFont,
) -> None:
    points = map_points(annotation["_points"], coordinate_space, width, height)
    color = rgb(annotation["color"])
    line_width = max(2, round(min(width, height) / 300))
    kind = annotation["kind"]
    if kind == "point":
        x_value, y_value = points[0]
        radius = max(6, line_width * 3)
        draw.ellipse(
            (x_value - radius, y_value - radius, x_value + radius, y_value + radius),
            outline=color,
            width=line_width,
        )
        anchor = (x_value + radius, y_value - radius)
    elif kind in {"rectangle", "ellipse"}:
        first, second = points
        box = (
            min(first[0], second[0]),
            min(first[1], second[1]),
            max(first[0], second[0]),
            max(first[1], second[1]),
        )
        if kind == "rectangle":
            draw.rectangle(box, outline=color, width=line_width)
        else:
            draw.ellipse(box, outline=color, width=line_width)
        anchor = (box[0], box[1])
    elif kind == "polygon":
        draw.line(points + [points[0]], fill=color, width=line_width, joint="curve")
        anchor = points[0]
    else:
        draw.line(points, fill=color, width=line_width, joint="curve")
        anchor = points[0]
    label = str(annotation["id"])
    label_box = draw.textbbox(anchor, label, font=label_font, stroke_width=1)
    padding = max(3, line_width)
    background = (
        label_box[0] - padding,
        label_box[1] - padding,
        label_box[2] + padding,
        label_box[3] + padding,
    )
    draw.rounded_rectangle(background, radius=padding, fill=(20, 20, 20))
    draw.text(
        anchor,
        label,
        fill=color,
        font=label_font,
        stroke_width=1,
        stroke_fill=(20, 20, 20),
    )


def wrapped_lines(text: str, width: int) -> List[str]:
    return textwrap.wrap(text, width=max(width, 12), break_long_words=False) or [""]


def render_plate(source: Image.Image, payload: Mapping[str, Any]) -> Image.Image:
    source_rgb = ImageOps.exif_transpose(source).convert("RGB")
    annotated = source_rgb.copy()
    annotation_draw = ImageDraw.Draw(annotated)
    image_width, image_height = source_rgb.size
    base_size = max(14, min(24, round(image_width / 55)))
    body_font = font(base_size)
    body_bold = font(base_size, bold=True)
    title_font = font(max(base_size + 8, 24), bold=True)
    small_font = font(max(base_size - 2, 12))
    for annotation in payload["annotations"]:
        draw_annotation(
            annotation_draw,
            annotation,
            payload["coordinateSpace"],
            image_width,
            image_height,
            body_bold,
        )

    gutter = max(20, round(image_width * 0.025))
    margin = max(24, round(image_width * 0.035))
    panel_label_height = base_size * 2
    title_size = getattr(title_font, "size", base_size + 8)
    header_height = margin + title_size + 8 + base_size + margin
    chars_per_line = max(50, round((image_width * 2 + gutter) / (base_size * 0.58)))
    legend_lines = []
    for annotation in payload["annotations"]:
        text = (
            f"{annotation['id']} · {annotation['status'].upper()} · "
            f"{annotation['label']} — {annotation['observation']}"
        )
        legend_lines.extend(wrapped_lines(text, chars_per_line))
        legend_lines.append("")
    source = payload["source"]
    frame = payload["frame"]
    metadata = (
        f"{source['provider']} · {source['product']} · {source['sensor']} · "
        f"{source['acquiredAt']} · {source['resolution']} · {frame['orientation']} · "
        f"{payload['disclosure']}"
    )
    processing = "Processing: " + "; ".join(frame["processing"])
    attribution = "Attribution/licence: " + source["attribution"] + " · " + source["license"]
    footer_lines = (
        wrapped_lines(metadata, chars_per_line)
        + wrapped_lines(processing, chars_per_line)
        + wrapped_lines(attribution, chars_per_line)
        + ["Candidate evidence plate — not a confirmed archaeological identification."]
    )
    line_height = base_size + 8
    legend_height = max(line_height * len(legend_lines), line_height)
    footer_height = line_height * (len(footer_lines) + 1)
    plate_width = margin * 2 + image_width * 2 + gutter
    plate_height = (
        header_height
        + panel_label_height
        + image_height
        + margin
        + legend_height
        + footer_height
        + margin
    )
    plate = Image.new("RGB", (plate_width, plate_height), color=(245, 242, 234))
    draw = ImageDraw.Draw(plate)
    draw.text((margin, margin), payload["title"], fill=(30, 28, 24), font=title_font)
    view_label = (
        "SOURCE FRAME"
        if frame["viewType"] == "source-measurement"
        else "DERIVED VIEW"
    )
    subtitle = (
        f"{frame['locationLabel']} · paired conservative and annotation view · "
        f"{frame['viewType']}"
    )
    draw.text(
        (margin, margin + title_size + 8),
        subtitle,
        fill=(80, 74, 64),
        font=body_font,
    )
    image_y = header_height + panel_label_height
    left_x = margin
    right_x = margin + image_width + gutter
    label_y = header_height
    draw.text(
        (left_x, label_y),
        f"A · CONSERVATIVE {view_label}",
        fill=(30, 28, 24),
        font=body_bold,
    )
    draw.text(
        (right_x, label_y),
        "B · ANNOTATED OBSERVATIONS",
        fill=(30, 28, 24),
        font=body_bold,
    )
    plate.paste(source_rgb, (left_x, image_y))
    plate.paste(annotated, (right_x, image_y))
    draw.rectangle(
        (left_x, image_y, left_x + image_width - 1, image_y + image_height - 1),
        outline=(70, 66, 58),
        width=2,
    )
    draw.rectangle(
        (right_x, image_y, right_x + image_width - 1, image_y + image_height - 1),
        outline=(70, 66, 58),
        width=2,
    )
    cursor_y = image_y + image_height + margin
    draw.text((margin, cursor_y), "ANNOTATION LEDGER", fill=(30, 28, 24), font=body_bold)
    cursor_y += line_height
    for line in legend_lines:
        if line:
            draw.text((margin, cursor_y), line, fill=(46, 43, 38), font=body_font)
        cursor_y += line_height
    draw.line(
        (margin, cursor_y, plate_width - margin, cursor_y),
        fill=(150, 142, 126),
        width=1,
    )
    cursor_y += line_height
    for line in footer_lines:
        draw.text((margin, cursor_y), line, fill=(64, 59, 51), font=small_font)
        cursor_y += line_height
    return plate


def atomic_save_png(image: Image.Image, path: Path) -> None:
    if path.suffix.lower() != ".png":
        raise ManifestError("Output evidence plate must use a .png suffix")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.",
        suffix=".png",
        dir=str(path.parent),
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        image.save(temporary_path, format="PNG", optimize=True)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


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


def build_artifact_manifest(
    payload: Mapping[str, Any],
    source_path: Path,
    annotation_path: Path,
    output_path: Path,
    output_size: Sequence[int],
) -> Dict[str, Any]:
    source = payload["source"]
    locator = (
        source["publicLocator"]
        if payload["disclosure"] == "public"
        else source["locator"]
    )
    return {
        "schemaVersion": "1.0",
        "artifactType": "paired-archaeological-evidence-plate",
        "title": payload["title"],
        "disclosure": payload["disclosure"],
        "containsPreciseCoordinates": False,
        "source": {
            "sourceId": source["sourceId"],
            "provider": source["provider"],
            "product": source["product"],
            "sensor": source["sensor"],
            "acquiredAt": source["acquiredAt"],
            "resolution": source["resolution"],
            "license": source["license"],
            "attribution": source["attribution"],
            "locator": locator,
            "sourceRole": source["sourceRole"],
            "imageFileName": source_path.name,
            "imageSha256": sha256_file(source_path),
        },
        "annotations": {
            "fileName": annotation_path.name,
            "sha256": sha256_file(annotation_path),
            "count": len(payload["annotations"]),
            "statuses": sorted({item["status"] for item in payload["annotations"]}),
        },
        "renderedOutput": {
            "fileName": output_path.name,
            "sha256": sha256_file(output_path),
            "width": int(output_size[0]),
            "height": int(output_size[1]),
            "metadataStripped": True,
            "pairedSourceAndAnnotatedViews": True,
            "leftViewType": payload["frame"]["viewType"],
        },
        "claimBoundary": "Candidate evidence plate; not a confirmed archaeological identification.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a provenance-bound source/annotation evidence plate"
    )
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if not args.image.is_file():
            raise ManifestError(f"Source image not found: {args.image}")
        if args.out.resolve() in {
            args.image.resolve(),
            args.annotations.resolve(),
            args.manifest_out.resolve(),
        }:
            raise ManifestError("Output plate must not overwrite an input or manifest")
        if args.manifest_out.resolve() in {
            args.image.resolve(),
            args.annotations.resolve(),
        }:
            raise ManifestError("Output manifest must not overwrite an input")
        with Image.open(args.image) as source:
            width, height = ImageOps.exif_transpose(source).size
            payload = validate_manifest(load_manifest(args.annotations), width, height)
            plate = render_plate(source, payload)
        atomic_save_png(plate, args.out)
        artifact_manifest = build_artifact_manifest(
            payload,
            args.image,
            args.annotations,
            args.out,
            plate.size,
        )
        atomic_write_json(artifact_manifest, args.manifest_out)
    except (ManifestError, OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
