from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


ZERO_HASH = "0" * 64


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def value_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"journal does not exist: {path}")
    events: list[dict[str, Any]] = []
    previous_hash = ZERO_HASH
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"journal line {line_number} is invalid JSON: {error}") from error
        if not isinstance(event, dict):
            raise ValueError(f"journal line {line_number} must be an object")
        event_hash = event.get("eventHash")
        payload = {key: value for key, value in event.items() if key != "eventHash"}
        if event.get("sequence") != len(events) + 1:
            raise ValueError(f"journal line {line_number} has a broken sequence")
        if event.get("previousHash") != previous_hash:
            raise ValueError(f"journal line {line_number} has a broken hash chain")
        if event.get("previousEventHash") != previous_hash:
            raise ValueError(f"journal line {line_number} has a broken event-hash link")
        if not isinstance(event_hash, str) or event_hash != value_sha256(payload):
            raise ValueError(f"journal line {line_number} has an invalid event hash")
        if event.get("payloadHash") != value_sha256(event.get("payload")):
            raise ValueError(f"journal line {line_number} has an invalid payload hash")
        if not isinstance(event.get("eventId"), str) or not event["eventId"].startswith(
            "evt_"
        ):
            raise ValueError(f"journal line {line_number} has an invalid event id")
        if (
            not isinstance(event.get("commandId"), str)
            or event.get("idempotencyKey") != event.get("commandId")
        ):
            raise ValueError(f"journal line {line_number} has an invalid command identity")
        events.append(event)
        previous_hash = event_hash
    if not events:
        raise ValueError("journal must contain at least one event")
    return events


def append_event(
    path: Path,
    run_id: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    occurred_at: float | None = None,
) -> dict[str, Any]:
    events = read_events(path) if path.exists() else []
    previous_hash = events[-1]["eventHash"] if events else ZERO_HASH
    sequence = len(events) + 1
    occurred = occurred_at if occurred_at is not None else time.time()
    command_id = payload.get("idempotencyKey") or value_sha256(
        {
            "runId": run_id,
            "eventType": event_type,
            "sequence": sequence,
            "payload": payload,
        }
    )
    event = {
        "schemaVersion": "1.0",
        "eventId": "evt_"
        + hashlib.sha256(
            f"{run_id}:{sequence}:{occurred}:{previous_hash}".encode("utf-8")
        ).hexdigest()[:24],
        "sequence": sequence,
        "previousHash": previous_hash,
        "previousEventHash": previous_hash,
        "runId": run_id,
        "eventType": event_type,
        "occurredAt": occurred,
        "actor": {"kind": "agent", "id": "codex-runtime"},
        "commandId": command_id,
        "idempotencyKey": command_id,
        "payloadHash": value_sha256(payload),
        "payload": payload,
    }
    event["eventHash"] = value_sha256(event)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    return event


def _read_lock(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _pid_is_alive(value: Any) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        return False
    try:
        os.kill(value, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def run_lock(run_dir: Path, lease_seconds: int = 120) -> Iterator[str]:
    if lease_seconds < 1 or lease_seconds > 3600:
        raise ValueError("lease_seconds must be between 1 and 3600")
    lock_path = run_dir / ".run.lock"
    now = time.time()
    existing = _read_lock(lock_path)
    if (
        existing
        and float(existing.get("expiresAt", now + 1)) <= now
        and not _pid_is_alive(existing.get("pid"))
    ):
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
    lease_id = hashlib.sha256(f"{os.getpid()}:{time.time_ns()}".encode()).hexdigest()[:24]
    descriptor: int | None = None
    try:
        descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        lease = {
            "leaseId": lease_id,
            "pid": os.getpid(),
            "createdAt": now,
            "expiresAt": now + lease_seconds,
        }
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = None
            stream.write(json.dumps(lease, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        yield lease_id
    except FileExistsError as error:
        active = _read_lock(lock_path) or {}
        raise ValueError(
            "run is locked by another process"
            + (f" until {active.get('expiresAt')}" if active.get("expiresAt") else "")
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        active = _read_lock(lock_path)
        if active and active.get("leaseId") == lease_id:
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
