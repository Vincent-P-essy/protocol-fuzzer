"""Target parsers under test.

Each parser has a contract: reject malformed input by raising :class:`ParseError`
and nothing else. Any other exception that escapes is a robustness bug, and the
fuzzer treats it as a crash. The parsers are pure and side-effect free; they
touch no network, filesystem, or subprocess. Several contain deliberate,
documented gaps so the fuzzer has real bugs to find on synthetic protocols.

These are Python parsers, so a "crash" is an unhandled exception (or a runaway
recursion), not memory corruption. The tool finds robustness and input-validation
defects, which is the class of bug that matters for a memory-safe parser.
"""

from __future__ import annotations

import json
import struct
from collections.abc import Callable
from typing import Any

from .models import Protocol


class ParseError(Exception):
    """The only exception a well-behaved parser may raise on bad input."""


def parse_http(data: bytes) -> dict[str, Any]:
    """Parse a minimal HTTP/1.1 request. Contains input-validation gaps."""

    if not data:
        raise ParseError("empty request")
    head = data.split(b"\r\n\r\n", 1)[0]
    lines = head.split(b"\r\n")
    parts = lines[0].split(b" ")
    # BUG: assumes exactly three tokens; a bad request line leaks ValueError.
    method, target, version = parts
    if not target.startswith(b"/"):
        raise ParseError("request target must be an absolute path")
    if not version.startswith(b"HTTP/"):
        raise ParseError("unsupported version token")
    headers: dict[bytes, bytes] = {}
    for line in lines[1:]:
        if not line:
            continue
        # BUG: a header without a colon leaks ValueError from the unpack.
        name, value = line.split(b":", 1)
        headers[name.strip().lower()] = value.strip()
    if b"content-length" in headers:
        # BUG: a non-numeric Content-Length leaks ValueError from int().
        declared = int(headers[b"content-length"])
        if declared < 0:
            raise ParseError("negative content-length")
    return {"method": method, "target": target, "version": version, "headers": headers}


def parse_tlv(data: bytes) -> Any:
    """Parse a tag-length-value record. Contains type-confusion gaps."""

    if len(data) < 3:
        raise ParseError("short TLV header")
    tag = data[0]
    (length,) = struct.unpack(">H", data[1:3])
    value = data[3 : 3 + length]
    if len(value) != length:
        raise ParseError("truncated TLV value")
    if tag == 0xFF:
        # BUG: an empty value here leaks IndexError instead of ParseError.
        count = value[0]
        return [value[index] for index in range(count)]
    if tag == 0x02:
        # BUG: a value whose length is not 4 leaks struct.error.
        return struct.unpack(">I", value)[0]
    return value


def parse_jsonrpc(data: bytes) -> dict[str, Any]:
    """Parse a JSON-RPC-ish request. Contains schema-assumption gaps."""

    try:
        obj = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid json: {exc}") from exc
    if not isinstance(obj, dict):
        raise ParseError("request must be a JSON object")
    # BUG: a missing method leaks KeyError.
    method = obj["method"]
    if not isinstance(method, str):
        raise ParseError("method must be a string")
    params = obj.get("params", [])
    # BUG: params assumed indexable list; a scalar leaks TypeError, a dict KeyError.
    first = params[0] if params else None
    return {"method": method, "first_param": first}


TARGETS: dict[Protocol, Callable[[bytes], Any]] = {
    Protocol.HTTP: parse_http,
    Protocol.TLV: parse_tlv,
    Protocol.JSONRPC: parse_jsonrpc,
}

# Exceptions a parser is allowed to raise; anything else is a crash.
EXPECTED_EXCEPTIONS: tuple[type[Exception], ...] = (ParseError,)
