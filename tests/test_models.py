from __future__ import annotations

import pytest
from pydantic import ValidationError

from protocol_fuzzer.models import CampaignConfig, CrashBucket, Protocol, Severity


def test_config_rejects_bad_iterations() -> None:
    with pytest.raises(ValidationError):
        CampaignConfig(protocol=Protocol.HTTP, iterations=0)


def test_config_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        CampaignConfig(protocol=Protocol.HTTP, unexpected=1)  # type: ignore[call-arg]


def test_bucket_sample_bytes_roundtrip() -> None:
    bucket = CrashBucket(
        signature="abc123",
        protocol=Protocol.TLV,
        exception_type="IndexError",
        location="parse_tlv:70",
        severity=Severity.MEDIUM,
        count=3,
        sample_hex="ff0000",
        sample_repr="b'\\xff\\x00\\x00'",
    )
    assert bucket.sample_bytes == b"\xff\x00\x00"
