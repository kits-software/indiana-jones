from __future__ import annotations

import ipaddress
import re
import socket
import urllib.request
import xml.etree.ElementTree as ET
import xml.parsers.expat
from typing import Any
from urllib.parse import urlparse

from ij_safety import safe_url_problem


_SECRET_KEY = re.compile(
    r"(?i)(?:^|[_\-.])(?:api[_-]?key|access[_-]?token|auth(?:orization)?|"
    r"bearer|client[_-]?secret|credential|cookie|pass(?:word|wd)?|secret|token)"
    r"(?:$|[_\-.])"
)
_SECRET_VALUE = re.compile(
    r"(?i)(?:\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}|"
    r"\b(?:api[_-]?key|access[_-]?token|authorization|client[_-]?secret|"
    r"credential|password)\b\s*[:=]\s*\S+)"
)


def validate_query_artifact(query: Any) -> None:
    seen = 0

    def visit(value: Any, path: str, depth: int) -> None:
        nonlocal seen
        seen += 1
        if depth > 64 or seen > 100_000:
            raise ValueError("query artifact exceeds safe structural limits")
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key)
                if _SECRET_KEY.search(key_text):
                    raise ValueError(f"query artifact contains credential key at {path}")
                visit(nested, f"{path}.{key_text}", depth + 1)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{path}[{index}]", depth + 1)
        elif isinstance(value, str):
            parsed = urlparse(value)
            if parsed.username is not None or parsed.password is not None:
                raise ValueError(f"query artifact contains URL credentials at {path}")
            if _SECRET_VALUE.search(value):
                raise ValueError(f"query artifact contains credential value at {path}")

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
