from __future__ import annotations

import struct

import pytest

from protocol_fuzzer.targets import ParseError, parse_http, parse_jsonrpc, parse_tlv


def _tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + len(value).to_bytes(2, "big") + value


def test_http_accepts_valid_request() -> None:
    parsed = parse_http(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
    assert parsed["method"] == b"GET"


def test_http_clean_rejections() -> None:
    with pytest.raises(ParseError):
        parse_http(b"")
    with pytest.raises(ParseError):
        parse_http(b"GET rel HTTP/1.1\r\n\r\n")  # target not absolute
    with pytest.raises(ParseError):
        parse_http(b"GET / HTTP/1.1\r\nContent-Length: -1\r\n\r\n")


def test_http_leaked_bugs() -> None:
    with pytest.raises(ValueError):
        parse_http(b"GET / HTTP/1.1 extra\r\n\r\n")  # too many request-line tokens
    with pytest.raises(ValueError):
        parse_http(b"GET / HTTP/1.1\r\nNoColonHeader\r\n\r\n")
    with pytest.raises(ValueError):
        parse_http(b"GET / HTTP/1.1\r\nContent-Length: abc\r\n\r\n")


def test_tlv_accepts_and_rejects() -> None:
    assert parse_tlv(_tlv(0x10, b"\xaa\xbb")) == b"\xaa\xbb"
    assert parse_tlv(_tlv(0x02, b"\x00\x00\x00\x2a")) == 42
    with pytest.raises(ParseError):
        parse_tlv(b"\x00")  # short header
    with pytest.raises(ParseError):
        parse_tlv(_tlv(0x10, b"\xaa")[:-1] + b"")  # header claims more than present


def test_tlv_leaked_bugs() -> None:
    with pytest.raises(IndexError):
        parse_tlv(_tlv(0xFF, b""))  # count marker with empty value
    with pytest.raises(struct.error):
        parse_tlv(_tlv(0x02, b"\xaa\xbb"))  # 32-bit decode of a short value


def test_jsonrpc_accepts_and_rejects() -> None:
    parsed = parse_jsonrpc(b'{"method":"ping","params":[1,2]}')
    assert parsed["method"] == "ping"
    with pytest.raises(ParseError):
        parse_jsonrpc(b"{not json")
    with pytest.raises(ParseError):
        parse_jsonrpc(b"[1,2,3]")


def test_jsonrpc_leaked_bugs() -> None:
    with pytest.raises(KeyError):
        parse_jsonrpc(b'{"params":[1]}')  # missing method
    with pytest.raises(TypeError):
        parse_jsonrpc(b'{"method":"x","params":5}')  # scalar params
    with pytest.raises(KeyError):
        parse_jsonrpc(b'{"method":"x","params":{"a":1}}')  # dict indexed by position
    with pytest.raises(UnicodeDecodeError):
        parse_jsonrpc(b'{"method":"\xff\xfe"}')  # invalid UTF-8 escapes JSONDecodeError
