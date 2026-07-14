"""Seed corpus construction.

Two sources feed the fuzzer. *Grammar* seeds are well-formed protocol messages
that establish baseline coverage. *Semantic* seeds are edge cases that are still
structurally plausible — the boundary shapes where parsers tend to break. The
semantic generator is a deterministic stand-in for an LLM corpus generator: it
produces the same class of "valid but unusual" inputs an LLM would, through a
pluggable interface, without a network call or nondeterminism. Real fuzzing value
still comes from mutation and coverage feedback on top of these seeds.
"""

from __future__ import annotations

from .models import Protocol, SeedOrigin


def _tlv(tag: int, value: bytes) -> bytes:
    return bytes([tag]) + len(value).to_bytes(2, "big") + value


_GRAMMAR: dict[Protocol, tuple[bytes, ...]] = {
    Protocol.HTTP: (
        b"GET / HTTP/1.1\r\nHost: example\r\n\r\n",
        b"POST /submit HTTP/1.1\r\nHost: example\r\nContent-Length: 3\r\n\r\nabc",
    ),
    Protocol.TLV: (
        _tlv(0x10, b"\xaa\xbb"),
        _tlv(0x02, b"\x00\x00\x00\x2a"),
    ),
    Protocol.JSONRPC: (
        b'{"method":"ping","params":[1,2]}',
        b'{"method":"status"}',
    ),
}

_SEMANTIC: dict[Protocol, tuple[bytes, ...]] = {
    Protocol.HTTP: (
        b"GET / HTTP/1.1 extra\r\n\r\n",  # too many request-line tokens
        b"GET\r\n\r\n",  # too few request-line tokens
        b"GET / HTTP/1.1\r\nBadHeaderNoColon\r\n\r\n",  # header without a colon
        b"GET / HTTP/1.1\r\nContent-Length: abc\r\n\r\n",  # non-numeric length
        b"GET / HTTP/1.1\r\nContent-Length: -1\r\n\r\n",  # negative length (clean reject)
    ),
    Protocol.TLV: (
        _tlv(0xFF, b""),  # count marker with an empty value
        _tlv(0x02, b"\xaa\xbb"),  # 32-bit decode of a 2-byte value
        _tlv(0x02, b"\x00\x00\x00\x01"),  # valid 32-bit value
        _tlv(0x10, b"\xaa"),  # header claims more than is present would truncate
    ),
    Protocol.JSONRPC: (
        b'{"params":[1]}',  # missing method
        b'{"method":"x","params":5}',  # scalar params
        b'{"method":"x","params":{"a":1}}',  # object params indexed by position
        b"[1,2,3]",  # not an object (clean reject)
        b"{not json",  # invalid json (clean reject)
    ),
}


def grammar_seeds(protocol: Protocol) -> tuple[bytes, ...]:
    return _GRAMMAR[protocol]


def semantic_seeds(protocol: Protocol) -> tuple[bytes, ...]:
    return _SEMANTIC[protocol]


def build_corpus(protocol: Protocol, *, semantic: bool = True) -> list[tuple[bytes, SeedOrigin]]:
    """Return the initial seed corpus with each seed's origin."""

    corpus: list[tuple[bytes, SeedOrigin]] = [
        (seed, SeedOrigin.GRAMMAR) for seed in grammar_seeds(protocol)
    ]
    if semantic:
        corpus.extend((seed, SeedOrigin.SEMANTIC) for seed in semantic_seeds(protocol))
    return corpus
