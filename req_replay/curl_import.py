"""Parse a curl command string into a CapturedRequest."""
from __future__ import annotations

import re
import shlex
from urllib.parse import urlparse

from req_replay.models import CapturedRequest


class CurlParseError(ValueError):
    pass


def parse_curl(command: str) -> CapturedRequest:
    """Parse a curl command string and return a CapturedRequest.

    Supports: -X/--request, -H/--header, -d/--data/--data-raw, URL.
    """
    try:
        tokens = shlex.split(command.strip())
    except ValueError as exc:
        raise CurlParseError(f"Failed to tokenise curl command: {exc}") from exc

    if not tokens or tokens[0] != "curl":
        raise CurlParseError("Command must start with 'curl'")

    url: str | None = None
    method: str = "GET"
    headers: dict[str, str] = {}
    body: str | None = None

    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-X", "--request"):
            i += 1
            method = tokens[i].upper()
        elif tok in ("-H", "--header"):
            i += 1
            raw = tokens[i]
            if ":" not in raw:
                raise CurlParseError(f"Invalid header: {raw!r}")
            key, _, val = raw.partition(":")
            headers[key.strip()] = val.strip()
        elif tok in ("-d", "--data", "--data-raw", "--data-binary"):
            i += 1
            body = tokens[i]
            if method == "GET":
                method = "POST"
        elif not tok.startswith("-"):
            url = tok
        i += 1

    if url is None:
        raise CurlParseError("No URL found in curl command")

    parsed = urlparse(url)
    if not parsed.scheme:
        raise CurlParseError(f"URL missing scheme: {url!r}")

    return CapturedRequest(
        method=method,
        url=url,
        headers=headers,
        body=body,
        tags=[],
        metadata={},
    )
