from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from ij_casebook import add_source, new_case, validate_case
from ij_common import atomic_write_json


class CasebookTests(unittest.TestCase):
    def test_new_case_is_read_only_by_default(self) -> None:
        case = new_case(
            "Test case",
            "What is visible?",
            "Generalized study area",
            "restricted",
            [],
        )
        self.assertEqual([], validate_case(case))
        self.assertFalse(case["authorization"]["writeActions"])
        self.assertFalse(case["authorization"]["fieldActions"])
        self.assertEqual([], case["authorization"]["authenticatedPlatforms"])

    def test_authenticated_source_requires_named_platform(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            case_path = Path(temporary_directory) / "case.json"
            case = new_case(
                "Authorized case",
                "What does the supplied account source add?",
                "Generalized study area",
                "restricted",
                ["facebook"],
            )
            atomic_write_json(case_path, case)
            source = add_source(
                case_path,
                "https://www.facebook.com/example/posts/1",
                "lead-only",
                "user-authorized",
                "unknown",
                "Read-only user-authorized source",
                "facebook",
            )
            self.assertEqual("facebook", source["platform"])
            persisted = json.loads(case_path.read_text(encoding="utf-8"))
            self.assertEqual(1, len(persisted["sources"]))

    def test_public_access_cannot_mask_authenticated_facebook(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            case_path = Path(temporary_directory) / "case.json"
            atomic_write_json(
                case_path,
                new_case("Test", "Question", "Area", "restricted", []),
            )
            with self.assertRaises(ValueError):
                add_source(
                    case_path,
                    "https://www.facebook.com/example/posts/1",
                    "lead-only",
                    "public",
                    "unknown",
                    "",
                    "",
                )

    def test_validator_rejects_injected_unauthorized_source(self) -> None:
        case = new_case("Test", "Question", "Area", "restricted", [])
        case["sources"].append(
            {
                "sourceId": "src_injected",
                "kind": "lead-only",
                "accessBasis": "user-authorized",
                "platform": "facebook",
            }
        )
        self.assertIn(
            "sources[0].platform is not authorized for this case",
            validate_case(case),
        )


if __name__ == "__main__":
    unittest.main()
