from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import archaeology
import methodology


class PublicCaseDefaultTests(unittest.TestCase):
    def test_general_case_cli_defaults_to_public(self) -> None:
        args = archaeology.build_parser().parse_args(
            [
                "new-case",
                "--title",
                "Public case",
                "--question",
                "What is documented?",
                "--study-area",
                "Named public area",
                "--out",
                "case.json",
            ]
        )
        self.assertEqual("public", args.disclosure)

    def test_methodology_case_cli_defaults_to_public(self) -> None:
        args = methodology.build_parser().parse_args(
            [
                "new-case",
                "--title",
                "Public method case",
                "--question",
                "What proxy repeats?",
                "--study-area",
                "Named public area",
                "--expected-proxy",
                "soil mark",
                "--visibility-condition",
                "bare soil",
                "--target-scale",
                "20-100 m",
                "--alternative-explanation",
                "modern drainage",
                "--decision-rule",
                "two sources agree",
                "--falsifier",
                "mapped drainage",
                "--interpretive-prior",
                "labels unknown",
                "--out",
                "case.json",
            ]
        )
        self.assertEqual("public", args.disclosure)

    def test_restricted_remains_an_explicit_option(self) -> None:
        args = archaeology.build_parser().parse_args(
            [
                "new-case",
                "--title",
                "Restricted case",
                "--question",
                "What is documented?",
                "--study-area",
                "Protected area",
                "--disclosure",
                "restricted",
                "--out",
                "case.json",
            ]
        )
        self.assertEqual("restricted", args.disclosure)


if __name__ == "__main__":
    unittest.main()
