"""Serializable domain model for fuzzing campaigns.

Runtime-hot types (seeds, raw crash observations) are plain dataclasses defined
next to the code that uses them; this module holds the frozen, JSON-friendly
models that cross the CLI, API, and report boundaries. Raw bytes are carried as
hex so a result is safe to serialize and diff.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Protocol(StrEnum):
    HTTP = "http"
    TLV = "tlv"
    JSONRPC = "jsonrpc"


class MutationKind(StrEnum):
    BIT_FLIP = "bit_flip"
    BYTE_FLIP = "byte_flip"
    BOUNDARY = "boundary"
    TRUNCATE = "truncate"
    DUPLICATE = "duplicate"
    INSERT = "insert"
    FORMAT_CONFUSION = "format_confusion"


class SeedOrigin(StrEnum):
    GRAMMAR = "grammar"
    SEMANTIC = "semantic"
    MUTATION = "mutation"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CampaignConfig(Frozen):
    """Reproducible campaign parameters."""

    protocol: Protocol
    iterations: int = Field(default=2_000, ge=1, le=1_000_000)
    seed: int = Field(default=1337, ge=0, le=2**63)
    max_input_bytes: int = Field(default=512, ge=1, le=65_536)
    semantic_corpus: bool = True


class CrashBucket(Frozen):
    """A deduplicated crash class, keyed by a stable signature."""

    signature: str
    protocol: Protocol
    exception_type: str
    location: str
    severity: Severity
    count: int = Field(ge=1)
    sample_hex: str
    sample_repr: str

    @property
    def sample_bytes(self) -> bytes:
        return bytes.fromhex(self.sample_hex)


class RegressionCase(Frozen):
    """A minimized crash promoted to a permanent regression test."""

    id: str
    protocol: Protocol
    input_hex: str
    exception_type: str
    location: str


class CampaignResult(Frozen):
    """The measured outcome of a fuzzing campaign."""

    protocol: Protocol
    seed: int
    executions: int
    corpus_size: int
    coverage_edges: int
    total_crashes: int
    unique_crashes: int
    buckets: tuple[CrashBucket, ...]

    @property
    def crash_signatures(self) -> tuple[str, ...]:
        return tuple(bucket.signature for bucket in self.buckets)
