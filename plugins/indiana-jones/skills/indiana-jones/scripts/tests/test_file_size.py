from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2]


class FileSizeTests(unittest.TestCase):
    def test_authored_text_files_stay_below_700_lines(self) -> None:
        oversized = []
        for path in SKILL_DIR.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".md"}:
                continue
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count >= 700:
                oversized.append(f"{path.relative_to(SKILL_DIR)}: {line_count}")
        self.assertEqual([], oversized, "Oversized authored files: " + ", ".join(oversized))


if __name__ == "__main__":
    unittest.main()
