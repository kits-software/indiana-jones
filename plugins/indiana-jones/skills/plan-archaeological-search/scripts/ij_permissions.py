from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
import re


PERMISSION_KEYS = {
    "jurisdiction",
    "landAccess",
    "detecting",
    "excavation",
    "heritage",
    "findsReporting",
    "communityAuthority",
}
ALWAYS_CONFIRMED_KEYS = {"jurisdiction", "heritage", "findsReporting"}
RESTRICTED_CHANNELS = {"case-vault", "authority-portal", "encrypted-delivery"}
SELF_DELIVERY = re.compile(
    r"(?i)(?:^|[^a-z])(?:self|myself|me|chat|ordinary.chat|public.chat)(?:$|[^a-z])"
)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _timestamp(value: Any) -> datetime | None:
    if not _text(value):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _official_locator(value: Any) -> bool:
    if not _text(value):
        return False
    parsed = urlparse(str(value))
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )


def permission_instrument_ids(case: dict[str, Any]) -> set[str]:
    bundle = case.get("permissionBundle")
    if not isinstance(bundle, dict):
        return set()
    return {
        str(permission["instrumentId"])
        for permission in bundle.values()
        if isinstance(permission, dict)
        and permission.get("state") == "confirmed"
        and _text(permission.get("instrumentId"))
    }


def _string_array(value: Any) -> list[str] | None:
    if (
        not isinstance(value, list)
        or not value
        or any(not _text(item) for item in value)
    ):
        return None
    return [str(item) for item in value]


def _request_value(case: dict[str, Any], key: str, override: str | None) -> str | None:
    if _text(override):
        return str(override)
    request = case.get("permissionRequest")
    value = request.get(key) if isinstance(request, dict) else None
    return str(value) if _text(value) else None


def restricted_permission_errors(
    case: dict[str, Any],
    *,
    method: str | None = None,
    area_id: str | None = None,
    provider: str | None = None,
    account: str | None = None,
    require_restricted_handling: bool = True,
) -> list[str]:
    errors: list[str] = []
    method = _request_value(case, "method", method)
    area_id = _request_value(case, "areaId", area_id)
    provider = _request_value(case, "provider", provider)
    account = _request_value(case, "account", account)
    if method is None:
        errors.append("permission request method is required")
    if area_id is None:
        errors.append("permission request areaId is required")
    bundle = case.get("permissionBundle")
    if not isinstance(bundle, dict):
        return errors + ["case.permissionBundle is required for permission-gated work"]
    now = datetime.now(timezone.utc)
    for key in sorted(PERMISSION_KEYS):
        permission = bundle.get(key)
        prefix = f"case.permissionBundle.{key}"
        if not isinstance(permission, dict):
            errors.append(f"{prefix} is required")
            continue
        state = permission.get("state")
        for field in (
            "basis",
            "scope",
            "issuer",
            "instrumentId",
            "verifier",
            "verifiedAt",
            "validFrom",
            "validUntil",
        ):
            if not _text(permission.get(field)):
                errors.append(f"{prefix}.{field} is required")
        for field in ("issuer", "verifier"):
            value = permission.get(field)
            if _text(value) and SELF_DELIVERY.search(str(value)):
                errors.append(f"{prefix}.{field} cannot be self-asserted or ordinary chat")
        verified_at = _timestamp(permission.get("verifiedAt"))
        if verified_at is None:
            errors.append(f"{prefix}.verifiedAt must be a timezone-aware ISO timestamp")
        elif verified_at > now:
            errors.append(f"{prefix}.verifiedAt cannot be in the future")
        if not _official_locator(permission.get("officialLocator")):
            errors.append(
                f"{prefix}.officialLocator must identify the approving source "
                "with a stable public HTTPS URL"
            )
        if state == "not-required":
            if key in ALWAYS_CONFIRMED_KEYS:
                errors.append(f"{prefix}.state must be confirmed")
        elif state != "confirmed":
            errors.append(f"{prefix}.state must be confirmed or not-required")

        activities = _string_array(permission.get("permittedActivities"))
        if activities is None:
            errors.append(f"{prefix}.permittedActivities must be a non-empty string array")
        elif method is not None and method not in activities:
            errors.append(
                f"{prefix}.permittedActivities does not authorize requested "
                f"activity {method!r}"
            )

        bindings = permission.get("scopeBindings")
        if not isinstance(bindings, dict):
            errors.append(f"{prefix}.scopeBindings must be an object")
        else:
            methods = _string_array(bindings.get("methods"))
            areas = _string_array(bindings.get("areaIds"))
            if methods is None:
                errors.append(f"{prefix}.scopeBindings.methods is required")
            elif method is not None and method not in methods:
                errors.append(f"{prefix} is not bound to requested method {method!r}")
            if areas is None:
                errors.append(f"{prefix}.scopeBindings.areaIds is required")
            elif area_id is not None and area_id not in areas:
                errors.append(f"{prefix} is not bound to requested area {area_id!r}")
            for request_value, field in ((provider, "providers"), (account, "accounts")):
                if request_value is None:
                    continue
                values = _string_array(bindings.get(field))
                if values is None or request_value not in values:
                    errors.append(
                        f"{prefix} is not bound to requested {field[:-1]} "
                        f"{request_value!r}"
                    )

        valid_from = _timestamp(permission.get("validFrom"))
        valid_until = _timestamp(permission.get("validUntil"))
        if valid_from is None or valid_until is None:
            errors.append(f"{prefix} validity must use timezone-aware ISO timestamps")
        elif valid_from > valid_until:
            errors.append(f"{prefix} permission has an invalid validity interval")
        elif now < valid_from:
            errors.append(f"{prefix} permission is not yet valid")
        elif now > valid_until:
            errors.append(f"{prefix} permission is expired")

    if not require_restricted_handling:
        return errors
    handling = case.get("restrictedHandling")
    if not isinstance(handling, dict):
        return errors + ["case.restrictedHandling is required for restricted output"]
    for field in (
        "destinationId",
        "recipientOrganization",
        "responsibleProfessional",
        "verifier",
        "verifiedAt",
    ):
        if not _text(handling.get(field)):
            errors.append(f"case.restrictedHandling.{field} is required")
    channel_type = handling.get("channelType")
    if channel_type not in RESTRICTED_CHANNELS:
        errors.append(
            "case.restrictedHandling.channelType must be case-vault, "
            "authority-portal, or encrypted-delivery"
        )
    for field in (
        "destinationId",
        "recipientOrganization",
        "responsibleProfessional",
        "verifier",
    ):
        value = handling.get(field)
        if _text(value) and SELF_DELIVERY.search(str(value)):
            errors.append(
                f"case.restrictedHandling.{field} cannot designate self or ordinary chat"
            )
    roles = handling.get("recipientRoles")
    if not isinstance(roles, list) or not roles or any(not _text(role) for role in roles):
        errors.append("case.restrictedHandling.recipientRoles must be a non-empty string array")
    if handling.get("accessControlled") is not True:
        errors.append("case.restrictedHandling.accessControlled must be true")
    if handling.get("exactLocationAuthorized") is not True:
        errors.append("case.restrictedHandling.exactLocationAuthorized must be true")
    handling_verified_at = _timestamp(handling.get("verifiedAt"))
    if handling_verified_at is None:
        errors.append(
            "case.restrictedHandling.verifiedAt must be a timezone-aware ISO timestamp"
        )
    elif handling_verified_at > now:
        errors.append("case.restrictedHandling.verifiedAt cannot be in the future")
    return errors
