"""Deterministic mutation operators.

Each operator takes an input and a seeded ``random.Random`` and returns a mutated
copy plus the :class:`MutationKind` applied. Because the RNG is injected, a
campaign started from the same seed applies the same mutations in the same order,
which is what makes crash discovery reproducible.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from .models import MutationKind

Operator = Callable[[bytes, random.Random], bytes]

# Boundary bytes that frequently expose off-by-one and sign errors.
_BOUNDARY_BYTES = (0x00, 0x01, 0x7F, 0x80, 0xFF)
# Protocol metacharacters used to provoke format confusion across parsers.
_METACHARS = (b":", b" ", b"\r\n", b'"', b"{", b"}", b"\x00", b"\xff\xff", b"HTTP/9.9")


def _bit_flip(data: bytes, rng: random.Random) -> bytes:
    if not data:
        return b"\x00"
    index = rng.randrange(len(data))
    bit = 1 << rng.randrange(8)
    mutable = bytearray(data)
    mutable[index] ^= bit
    return bytes(mutable)


def _byte_flip(data: bytes, rng: random.Random) -> bytes:
    if not data:
        return bytes([rng.randrange(256)])
    index = rng.randrange(len(data))
    mutable = bytearray(data)
    mutable[index] = rng.randrange(256)
    return bytes(mutable)


def _boundary(data: bytes, rng: random.Random) -> bytes:
    if not data:
        return bytes([rng.choice(_BOUNDARY_BYTES)])
    index = rng.randrange(len(data))
    mutable = bytearray(data)
    mutable[index] = rng.choice(_BOUNDARY_BYTES)
    return bytes(mutable)


def _truncate(data: bytes, rng: random.Random) -> bytes:
    if not data:
        return data
    return data[: rng.randrange(len(data) + 1)]


def _duplicate(data: bytes, rng: random.Random) -> bytes:
    if not data:
        return data
    start = rng.randrange(len(data))
    end = rng.randrange(start, len(data)) + 1
    chunk = data[start:end]
    return data[:end] + chunk + data[end:]


def _insert(data: bytes, rng: random.Random) -> bytes:
    index = rng.randrange(len(data) + 1) if data else 0
    blob = bytes(rng.randrange(256) for _ in range(rng.randint(1, 4)))
    return data[:index] + blob + data[index:]


def _format_confusion(data: bytes, rng: random.Random) -> bytes:
    token = rng.choice(_METACHARS)
    index = rng.randrange(len(data) + 1) if data else 0
    return data[:index] + token + data[index:]


_OPERATORS: dict[MutationKind, Operator] = {
    MutationKind.BIT_FLIP: _bit_flip,
    MutationKind.BYTE_FLIP: _byte_flip,
    MutationKind.BOUNDARY: _boundary,
    MutationKind.TRUNCATE: _truncate,
    MutationKind.DUPLICATE: _duplicate,
    MutationKind.INSERT: _insert,
    MutationKind.FORMAT_CONFUSION: _format_confusion,
}

_KINDS = tuple(_OPERATORS)


def mutate(data: bytes, rng: random.Random) -> tuple[bytes, MutationKind]:
    """Apply one randomly chosen operator and return ``(mutant, kind)``."""

    kind = rng.choice(_KINDS)
    operator = _OPERATORS[kind]
    return operator(data, rng), kind
