from __future__ import annotations

import json
from typing import Any


class IndianaJonesError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        exit_code: int,
        path: str = "$",
        hint: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.path = path
        self.hint = hint


class InvocationError(IndianaJonesError):
    def __init__(self, message: str, *, path: str = "$") -> None:
        super().__init__(
            message,
            code="IJ_INVOCATION_INVALID",
            exit_code=2,
            path=path,
            hint="Review the command syntax and run the subcommand with --help.",
        )


def error_code(error: Exception) -> tuple[str, int]:
    if isinstance(error, IndianaJonesError):
        return error.code, error.exit_code
    if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)):
        return "IJ_SCHEMA_INVALID", 3
    if isinstance(error, (TypeError, KeyError, RecursionError)):
        return "IJ_DATA_INVALID", 3
    message = str(error).casefold()
    if any(
        term in message
        for term in (
            "hash chain",
            "event hash",
            "integrity",
            "changed:",
            "journal line",
            "journal must contain",
        )
    ):
        return "IJ_INTEGRITY_FAILURE", 7
    if any(term in message for term in ("provider", "urlopen", "timed out", "http error")):
        return "IJ_PROVIDER_FAILURE", 6
    if any(term in message for term in ("budget-exhausted", "stop condition")):
        return "IJ_BUDGET_STOP", 5
    if any(
        term in message
        for term in (
            "authorization",
            "permission",
            "prohibited",
            "restricted disclosure",
            "exact high-risk",
        )
    ):
        return "IJ_SAFETY_BLOCK", 4
    if isinstance(error, ValueError) or any(
        term in message
        for term in ("invalid", "schema", "json", "must be", "unknown source", "not ready")
    ):
        return "IJ_DATA_INVALID", 3
    return "IJ_INVOCATION_INVALID", 2


def diagnostic(error: Exception, *, path: str | None = None) -> dict[str, Any]:
    code, _ = error_code(error)
    resolved_path = path or getattr(error, "path", None) or "$"
    hint = getattr(error, "hint", None)
    if hint is None and isinstance(error, json.JSONDecodeError):
        resolved_path = f"$ (line {error.lineno}, column {error.colno})"
        hint = "Provide valid UTF-8 JSON with no truncated values or trailing data."
    if hint is None:
        hint = {
            "IJ_SCHEMA_INVALID": "Provide data that conforms to the declared JSON schema.",
            "IJ_DATA_INVALID": "Correct the value at the reported path and retry.",
            "IJ_SAFETY_BLOCK": (
                "Remove the prohibited physical conduct or use a source you may access."
            ),
            "IJ_BUDGET_STOP": "Inspect the stop reason before explicitly extending a budget.",
            "IJ_PROVIDER_FAILURE": "Retry within the declared source policy and request budget.",
            "IJ_INTEGRITY_FAILURE": "Do not continue; audit the journal and retained artifacts.",
            "IJ_INVOCATION_INVALID": (
                "Review the command syntax and run the subcommand with --help."
            ),
        }[code]
    value: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": code,
            "message": str(error),
            "path": resolved_path,
            "hint": hint,
        },
    }
    return value


def diagnostic_json(error: Exception, *, path: str | None = None) -> str:
    return json.dumps(diagnostic(error, path=path), ensure_ascii=False, sort_keys=True)
