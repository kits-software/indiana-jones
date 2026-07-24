from __future__ import annotations

import json
from typing import Any


def error_code(error: Exception) -> tuple[str, int]:
    message = str(error).casefold()
    if any(term in message for term in ("hash chain", "event hash", "integrity", "changed:")):
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
    if any(
        term in message
        for term in ("invalid", "schema", "json", "must be", "unknown source", "not ready")
    ):
        return "IJ_DATA_INVALID", 3
    return "IJ_INVOCATION_INVALID", 2


def diagnostic(error: Exception, *, path: str | None = None) -> dict[str, Any]:
    code, _ = error_code(error)
    value: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": code,
            "message": str(error),
        },
    }
    if path:
        value["error"]["path"] = path
    return value


def diagnostic_json(error: Exception, *, path: str | None = None) -> str:
    return json.dumps(diagnostic(error, path=path), ensure_ascii=False, sort_keys=True)
