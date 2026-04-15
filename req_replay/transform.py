"""Request transformation utilities for modifying captured requests before replay."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

from req_replay.models import CapturedRequest


@dataclass
class TransformConfig:
    """Configuration for transforming a request before replay."""
    base_url: Optional[str] = None
    override_headers: Dict[str, str] = field(default_factory=dict)
    remove_headers: list = field(default_factory=list)
    override_query_params: Dict[str, str] = field(default_factory=dict)
    remove_query_params: list = field(default_factory=list)
    override_body: Optional[str] = None


def _apply_base_url(url: str, base_url: str) -> str:
    """Replace scheme + host of url with those from base_url."""
    parsed_original = urlparse(url)
    parsed_base = urlparse(base_url)
    replaced = parsed_original._replace(
        scheme=parsed_base.scheme or parsed_original.scheme,
        netloc=parsed_base.netloc or parsed_original.netloc,
    )
    return urlunparse(replaced)


def _apply_query_params(
    url: str,
    overrides: Dict[str, str],
    removals: list,
) -> str:
    """Merge, override, and remove query parameters on a URL."""
    parsed = urlparse(url)
    params: Dict[str, list] = parse_qs(parsed.query, keep_blank_values=True)

    for key in removals:
        params.pop(key, None)

    for key, value in overrides.items():
        params[key] = [value]

    new_query = urlencode({k: v[0] for k, v in params.items()})
    return urlunparse(parsed._replace(query=new_query))


def transform_request(
    request: CapturedRequest,
    config: TransformConfig,
) -> CapturedRequest:
    """Return a new CapturedRequest with transformations applied."""
    url = request.url

    if config.base_url:
        url = _apply_base_url(url, config.base_url)

    if config.override_query_params or config.remove_query_params:
        url = _apply_query_params(
            url, config.override_query_params, config.remove_query_params
        )

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in [r.lower() for r in config.remove_headers]}
    headers.update(config.override_headers)

    body = config.override_body if config.override_body is not None else request.body

    return CapturedRequest(
        id=request.id,
        timestamp=request.timestamp,
        method=request.method,
        url=url,
        headers=headers,
        body=body,
        tags=request.tags,
    )
