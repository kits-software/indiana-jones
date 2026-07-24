from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
CLI = SCRIPT_DIR / "search_plan.py"
sys.path.insert(0, str(SCRIPT_DIR))

from ij_errors import diagnostic, error_code


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


class ErrorContractTests(unittest.TestCase):
    def test_invalid_invocation_is_typed_json_without_traceback(self) -> None:
        result = _run("validate")
        self.assertEqual(2, result.returncode)
        value = json.loads(result.stderr)
        self.assertEqual("IJ_INVOCATION_INVALID", value["error"]["code"])
        self.assertEqual("$", value["error"]["path"])
        self.assertTrue(value["error"]["hint"])
        self.assertNotIn("Traceback", result.stderr)

    def test_truncated_json_and_invalid_utf8_are_invalid_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fixtures = {
                "truncated.json": b'{"schemaVersion":"2.0"',
                "invalid-utf8.json": (
                    b'{"schemaVersion":"2.0","name":"' + bytes([0xFF]) + b'"}'
                ),
            }
            for name, payload in fixtures.items():
                with self.subTest(name=name):
                    path = root / name
                    path.write_bytes(payload)
                    result = _run("validate", "--plan", str(path))
                    self.assertEqual(3, result.returncode)
                    value = json.loads(result.stderr)
                    self.assertEqual("IJ_SCHEMA_INVALID", value["error"]["code"])
                    self.assertTrue(value["error"]["path"])
                    self.assertTrue(value["error"]["hint"])
                    self.assertNotIn("Traceback", result.stderr)

    def test_structurally_invalid_plan_uses_schema_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "wrong-root.json"
            path.write_text('{"schemaVersion":"2.0","nodes":[7]}', encoding="utf-8")
            result = _run("validate", "--plan", str(path))
            self.assertEqual(3, result.returncode)
            value = json.loads(result.stdout)
            self.assertFalse(value["ok"])
            self.assertEqual("IJ_SCHEMA_INVALID", value["error"]["code"])
            self.assertTrue(value["errors"])
            self.assertNotIn("Traceback", result.stderr)

    def test_partial_journal_is_an_integrity_failure(self) -> None:
        error = ValueError("journal line 3 is invalid JSON: truncated")
        self.assertEqual(("IJ_INTEGRITY_FAILURE", 7), error_code(error))
        value = diagnostic(error)
        self.assertEqual("IJ_INTEGRITY_FAILURE", value["error"]["code"])
        self.assertIn("audit", value["error"]["hint"])

    def test_provider_and_budget_failures_have_stable_exit_classes(self) -> None:
        self.assertEqual(
            ("IJ_PROVIDER_FAILURE", 6),
            error_code(TimeoutError("provider timed out")),
        )
        self.assertEqual(
            ("IJ_BUDGET_STOP", 5),
            error_code(ValueError("budget-exhausted:max-records")),
        )


if __name__ == "__main__":
    unittest.main()
