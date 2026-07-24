from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from ij_sources import (
    _normalize_stac_datetime,
    _stac_search_url,
    _strip_osm_labels,
    build_overpass_query,
    build_raster_sidecar,
    load_verified_sidecar,
    validate_projected_crs,
)
from ij_common import atomic_write_json


class SourceTests(unittest.TestCase):
    def test_registered_raster_is_bound_to_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            raster = Path(temporary_directory) / "surface.tif"
            raster.write_bytes(b"II*\x00placeholder")
            sidecar_path = Path(f"{raster}.source.json")
            sidecar = build_raster_sidecar(
                raster,
                [500000.0, 4100000.0, 501000.0, 4101000.0],
                "EPSG:32632",
                "metre",
                "https://example.test/item",
                "test",
                "terrain",
                "test sensor",
                "2025-01-01",
                "",
                False,
            )
            atomic_write_json(sidecar_path, sidecar)
            self.assertEqual(sidecar, load_verified_sidecar(raster, sidecar_path))
            raster.write_bytes(b"II*\x00changed")
            with self.assertRaisesRegex(ValueError, "does not match"):
                load_verified_sidecar(raster, sidecar_path)

    def test_metric_kernels_reject_geographic_or_non_metre_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "longitude/latitude"):
            validate_projected_crs("EPSG:4326", "metre")
        with self.assertRaisesRegex(ValueError, "expressed in metres"):
            validate_projected_crs("EPSG:2263", "foot")
        self.assertEqual("EPSG:32718", validate_projected_crs("EPSG:32718", "metre"))

    def test_osm_heritage_labels_are_opt_in(self) -> None:
        bbox = [50.0, 19.0, 50.01, 19.01]
        negative_control = build_overpass_query(bbox, False)
        corroboration = build_overpass_query(bbox, True)
        self.assertNotIn('nwr["historic"]', negative_control)
        self.assertIn('nwr["historic"]', corroboration)
        sanitized = _strip_osm_labels(
            {
                "elements": [
                    {
                        "tags": {
                            "building": "yes",
                            "historic": "archaeological_site",
                            "name": "Known fort",
                        }
                    }
                ]
            }
        )
        self.assertEqual(
            {"building": "yes"},
            sanitized["elements"][0]["tags"],
        )

    def test_stac_endpoint_is_https_and_normalized(self) -> None:
        self.assertEqual(
            "https://catalog.test/v1/search",
            _stac_search_url("https://catalog.test/v1"),
        )
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            _stac_search_url("http://catalog.test/v1")
        self.assertEqual(
            "2025-06-01T00:00:00Z/2025-06-30T23:59:59Z",
            _normalize_stac_datetime("2025-06-01/2025-06-30"),
        )


if __name__ == "__main__":
    unittest.main()
