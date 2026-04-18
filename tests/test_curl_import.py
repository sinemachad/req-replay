"""Tests for req_replay.curl_import."""
import pytest

from req_replay.curl_import import CurlParseError, parse_curl


def test_simple_get():
    req = parse_curl("curl https://example.com/api")
    assert req.method == "GET"
    assert req.url == "https://example.com/api"
    assert req.body is None


def test_explicit_method():
    req = parse_curl("curl -X DELETE https://example.com/item/1")
    assert req.method == "DELETE"


def test_long_flag_method():
    req = parse_curl("curl --request PATCH https://example.com/x")
    assert req.method == "PATCH"


def test_headers_parsed():
    req = parse_curl(
        'curl -H "Content-Type: application/json" -H "Authorization: Bearer tok" https://api.example.com'
    )
    assert req.headers["Content-Type"] == "application/json"
    assert req.headers["Authorization"] == "Bearer tok"


def test_body_sets_post_when_no_method():
    req = parse_curl("curl -d '{\"k\": 1}' https://example.com/post")
    assert req.method == "POST"
    assert req.body == '{"k": 1}'


def test_explicit_post_with_body():
    req = parse_curl("curl -X POST -d 'hello' https://example.com")
    assert req.method == "POST"
    assert req.body == "hello"


def test_data_raw_flag():
    req = parse_curl("curl --data-raw 'raw body' https://example.com")
    assert req.body == "raw body"


def test_missing_url_raises():
    with pytest.raises(CurlParseError, match="No URL"):
        parse_curl("curl -X GET")


def test_not_curl_raises():
    with pytest.raises(CurlParseError, match="must start with"):
        parse_curl("wget https://example.com")


def test_url_without_scheme_raises():
    with pytest.raises(CurlParseError, match="missing scheme"):
        parse_curl("curl example.com/path")


def test_invalid_header_raises():
    with pytest.raises(CurlParseError, match="Invalid header"):
        parse_curl("curl -H 'BadHeader' https://example.com")


def test_tags_default_empty():
    req = parse_curl("curl https://example.com")
    assert req.tags == []


def test_metadata_default_empty():
    req = parse_curl("curl https://example.com")
    assert req.metadata == {}
