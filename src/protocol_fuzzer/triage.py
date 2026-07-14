"""Crash triage: deduplicate raw crashes into stable buckets.

A crash is bucketed by a signature over its exception type and the deepest
target-module location that raised it. This collapses the thousands of inputs a
fuzzer throws at a bug into one bucket per distinct defect, with a severity
heuristic that ranks the classes a memory-unsafe re-implementation would care
about (out-of-bounds indexing, runaway recursion) above simple validation slips.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .models import CrashBucket, Protocol, Severity

# Exception classes ranked by how dangerous the same bug would be in a
# memory-unsafe parser processing the same bytes.
_HIGH = {"RecursionError", "MemoryError", "OverflowError"}
_MEDIUM = {"IndexError", "struct.error", "error", "UnicodeDecodeError", "OverflowError"}


@dataclass(frozen=True)
class Crash:
    data: bytes
    exception_type: str
    location: str
    message: str


def signature(exception_type: str, location: str) -> str:
    digest = hashlib.sha256(f"{exception_type}@{location}".encode()).hexdigest()
    return digest[:16]


def _severity(exception_type: str) -> Severity:
    if exception_type in _HIGH:
        return Severity.HIGH
    if exception_type in _MEDIUM:
        return Severity.MEDIUM
    return Severity.LOW


def bucket_crashes(crashes: list[Crash], protocol: Protocol) -> tuple[CrashBucket, ...]:
    """Collapse raw crashes into deduplicated, severity-ranked buckets."""

    order: list[str] = []
    grouped: dict[str, list[Crash]] = {}
    for crash in crashes:
        key = signature(crash.exception_type, crash.location)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(crash)

    buckets: list[CrashBucket] = []
    for key in order:
        members = grouped[key]
        # The smallest input is the most useful reproducer for a bucket.
        sample = min(members, key=lambda crash: len(crash.data))
        buckets.append(
            CrashBucket(
                signature=key,
                protocol=protocol,
                exception_type=sample.exception_type,
                location=sample.location,
                severity=_severity(sample.exception_type),
                count=len(members),
                sample_hex=sample.data.hex(),
                sample_repr=repr(sample.data)[:120],
            )
        )
    buckets.sort(key=lambda bucket: (_severity_rank(bucket.severity), -bucket.count), reverse=True)
    return tuple(buckets)


def _severity_rank(severity: Severity) -> int:
    return {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}[severity]
