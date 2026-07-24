from __future__ import annotations

import math
from typing import Any, Optional, Sequence


def google_maps_point_link(coordinates: Any) -> Optional[str]:
    if (
        not isinstance(coordinates, Sequence)
        or isinstance(coordinates, (str, bytes))
        or len(coordinates) != 2
    ):
        return None
    longitude, latitude = coordinates
    if (
        not isinstance(longitude, (int, float))
        or isinstance(longitude, bool)
        or not isinstance(latitude, (int, float))
        or isinstance(latitude, bool)
        or not math.isfinite(float(longitude))
        or not math.isfinite(float(latitude))
        or not -180 <= float(longitude) <= 180
        or not -90 <= float(latitude) <= 90
    ):
        return None
    return (
        "https://www.google.com/maps/search/?api=1&query="
        f"{float(latitude):.6f}%2C{float(longitude):.6f}"
    )


def add_google_maps_links(value: Any) -> Any:
    if isinstance(value, dict):
        direct_point = value.get("coordinate")
        if direct_point is None:
            direct_point = value.get("coordinates")
        link = google_maps_point_link(direct_point)
        if link:
            value["googleMapsLink"] = link

        image_link = google_maps_point_link(value.get("imagePoint"))
        if image_link:
            value["imagePointGoogleMapsLink"] = image_link

        geometry = value.get("geometry")
        if (
            value.get("type") == "Feature"
            and isinstance(geometry, dict)
            and geometry.get("type") == "Point"
        ):
            geometry_link = google_maps_point_link(geometry.get("coordinates"))
            if geometry_link:
                properties = value.get("properties")
                if not isinstance(properties, dict):
                    properties = {}
                    value["properties"] = properties
                properties["googleMapsLink"] = geometry_link

        for nested in list(value.values()):
            add_google_maps_links(nested)
    elif isinstance(value, list):
        for nested in value:
            add_google_maps_links(nested)
    return value
