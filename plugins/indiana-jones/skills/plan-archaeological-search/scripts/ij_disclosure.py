from __future__ import annotations

import math
from typing import Any


MAX_PUBLIC_DEPTH = 64
MAX_PUBLIC_VALUES = 100_000


def lint_public_value(value: Any, path: str = "$") -> None:
    stack: list[tuple[Any, str, int]] = [(value, path, 0)]
    inspected = 0
    while stack:
        current, current_path, depth = stack.pop()
        inspected += 1
        if inspected > MAX_PUBLIC_VALUES:
            raise ValueError(
                f"public artifact exceeds {MAX_PUBLIC_VALUES} inspected values"
            )
        if depth > MAX_PUBLIC_DEPTH:
            raise ValueError(
                f"public artifact exceeds maximum nesting depth at {current_path}"
            )
        if isinstance(current, dict):
            for key, nested in reversed(list(current.items())):
                stack.append((nested, f"{current_path}.{key}", depth + 1))
        elif isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append(
                    (current[index], f"{current_path}[{index}]", depth + 1)
                )
        elif isinstance(current, float) and not math.isfinite(current):
            raise ValueError(
                f"public artifact contains a non-finite number at {current_path}"
            )
