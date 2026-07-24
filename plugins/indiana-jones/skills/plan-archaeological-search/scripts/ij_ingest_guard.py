from __future__ import annotations

import ipaddress
import math
import re
import socket
import urllib.request
import xml.etree.ElementTree as ET
import xml.parsers.expat
from typing import Any
from urllib.parse import unquote, urlparse

from ij_safety import safe_url_problem


_SECRET_KEY = re.compile(
    r"(?i)(?:^|[_\-.])(?:api[_-]?key|access[_-]?token|auth(?:orization)?|"
    r"bearer|client[_-]?secret|credential|cookie|pass(?:word|wd)?|secret|token)"
    r"(?:$|[_\-.])"
)
_SECRET_VALUE = re.compile(
    r"(?i)(?:\b(?:bearer|basic)\s+\S+|"
    r"\b(?:api[_-]?key|access[_-]?token|authorization|client[_-]?secret|"
    r"credential|password)\b\s*[:=]\s*\S+)"
)
_RETENTION_PROHIBITION = re.compile(
    r"(?i)(?:(?:do\s+not|no|prohibit(?:ed|s)?|forbid(?:den|s)?)"
    r".{0,40}(?:retain|retention|download|local\s+cop(?:y|ies)|store|storage)|"
    r"(?:retain|retention|download|local\s+cop(?:y|ies)|store|storage)"
    r".{0,40}(?:prohibit(?:ed|s)?|not\s+(?:permit|allow)ed|forbid(?:den|s)?))"
)


def validate_query_artifact(query: Any) -> None:
    seen = 0

    def decoded(text: str) -> str:
        for _ in range(3):
            expanded = unquote(text)
            if expanded == text:
                break
            text = expanded
        return text

    def visit(value: Any, path: str, depth: int) -> None:
        nonlocal seen
        seen += 1
        if depth > 64 or seen > 100_000:
            raise ValueError("query artifact exceeds safe structural limits")
        if isinstance(value, dict):
            for key, nested in value.items():
                if not isinstance(key, str):
                    raise ValueError(f"query artifact key at {path} must be a string")
                key_text = decoded(key)
                if _SECRET_KEY.search(key_text):
                    raise ValueError(f"query artifact contains credential key at {path}")
                visit(nested, f"{path}.{key_text}", depth + 1)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]", depth + 1)
        elif isinstance(value, str):
            value = decoded(value)
            parsed = urlparse(value)
            if parsed.username is not None or parsed.password is not None:
                raise ValueError(f"query artifact contains URL credentials at {path}")
            if _SECRET_VALUE.search(value):
                raise ValueError(f"query artifact contains credential value at {path}")
        elif isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"query artifact contains a non-finite number at {path}")
        elif value is not None and not isinstance(value, (bool, int, float)):
            raise ValueError(f"query artifact contains a non-JSON value at {path}")

    if not isinstance(query, dict):
        raise ValueError("query artifact must be an object")
    visit(query, "query", 0)


def public_host_problem(locator: str) -> str | None:
    host = urlparse(locator).hostname
    if not host:
        return "URL hostname is required"
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as error:
        return f"URL hostname could not be resolved: {error}"
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            return "URL resolves to a private, loopback, link-local, or reserved address"
    return None


def validate_public_url(locator: str) -> None:
    problem = safe_url_problem(locator) or public_host_problem(locator)
    if problem:
        raise ValueError(problem)


def automation_access_problem(source: dict[str, Any], locator: str) -> str | None:
    if urlparse(locator).scheme not in {"http", "https"}:
        return None
    acquisition = source.get("acquisition")
    acquisition = acquisition if isinstance(acquisition, dict) else {}
    authorized = (
        source.get("automationAuthorized") is True
        or acquisition.get("automationAuthorized") is True
    )
    basis = source.get("automationBasis") or acquisition.get("automationBasis")
    checked_at = source.get("automationCheckedAt") or acquisition.get(
        "automationCheckedAt"
    )
    terms = source.get("providerTerms")
    license_name = source.get("license")
    retention_policy = acquisition.get("retentionPolicy")
    retention_basis = acquisition.get("retentionBasis")
    retention_decision = acquisition.get("retentionDecision")
    retention_evidence = acquisition.get("retentionEvidenceLocator")
    retention_checked_at = acquisition.get("retentionCheckedAt")
    rate_limit = acquisition.get("rateLimit")
    adapter_version = acquisition.get("adapterVersion")
    if not authorized or not basis or not checked_at:
        return "remote source lacks an explicit, dated automation authorization decision"
    placeholders = {"", "unknown", "tbd", "n/a", "verify source terms", "test fixture"}
    if not isinstance(terms, str) or terms.strip().casefold() in placeholders:
        return "remote source providerTerms decision is required"
    if (
        not isinstance(license_name, str)
        or license_name.strip().casefold() in placeholders
    ):
        return "remote source license is required"
    if _RETENTION_PROHIBITION.search(terms) or _RETENTION_PROHIBITION.search(
        license_name
    ):
        return "remote source terms or licence prohibit the snapshot retention this adapter requires"
    if retention_policy != "retain-snapshot" or not isinstance(
        retention_basis, str
    ) or not retention_basis.strip():
        return "remote source requires an explicit retain-snapshot policy and basis"
    if (
        retention_decision != "permitted"
        or not isinstance(retention_evidence, str)
        or safe_url_problem(retention_evidence) is not None
        or not isinstance(retention_checked_at, str)
        or not retention_checked_at.strip()
    ):
        return "remote snapshot retention requires a dated permitted decision and evidence URL"
    if not isinstance(adapter_version, str) or not re.fullmatch(
        r"\d+\.\d+\.\d+", adapter_version
    ):
        return "remote source requires a semantic adapterVersion"
    if (
        not isinstance(rate_limit, dict)
        or not isinstance(rate_limit.get("requestsPerMinute"), int)
        or isinstance(rate_limit.get("requestsPerMinute"), bool)
        or not 1 <= rate_limit["requestsPerMinute"] <= 600
        or not isinstance(rate_limit.get("maxConcurrency"), int)
        or isinstance(rate_limit.get("maxConcurrency"), bool)
        or not 1 <= rate_limit["maxConcurrency"] <= 16
    ):
        return "remote source requires bounded requestsPerMinute and maxConcurrency"
    return None


class ValidatingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request: urllib.request.Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> urllib.request.Request | None:
        validate_public_url(new_url)
        return super().redirect_request(
            request,
            file_pointer,
            code,
            message,
            headers,
            new_url,
        )


def safe_xml_root(payload: bytes) -> ET.Element:
    parser = xml.parsers.expat.ParserCreate()

    def reject(*_args: Any) -> None:
        raise ValueError("XML document type and entity declarations are not allowed")

    parser.StartDoctypeDeclHandler = reject
    parser.EntityDeclHandler = reject
    parser.UnparsedEntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    parser.Parse(payload, True)
    return ET.fromstring(payload)
