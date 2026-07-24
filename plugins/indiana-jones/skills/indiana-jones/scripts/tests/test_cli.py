from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
CLI_PATH = SCRIPT_DIR / "archaeology.py"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_common import atomic_write_json
from ij_sources import build_raster_sidecar


class CliTests(unittest.TestCase):
    def test_terrain_detector_rejects_optical_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            raster = Path(temporary_directory) / "index.tif"
            raster.write_bytes(b"II*\x00placeholder")
            sidecar = build_raster_sidecar(
                raster,
                [500000.0, 4100000.0, 501000.0, 4101000.0],
                "EPSG:32632",
                "metre",
                "https://example.test/item",
                "test",
                "optical-index",
                "test sensor",
                "2025-01-01",
                "",
                False,
            )
            atomic_write_json(Path(f"{raster}.source.json"), sidecar)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI_PATH),
                    "detect-enclosures",
                    "--input",
                    str(raster),
                    "--out-dir",
                    str(Path(temporary_directory) / "run"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            self.assertIn("supports terrain rasters only", completed.stderr)


if __name__ == "__main__":
    unittest.main()
