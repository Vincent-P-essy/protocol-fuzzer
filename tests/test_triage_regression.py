from __future__ import annotations

from protocol_fuzzer.engine import run_campaign
from protocol_fuzzer.models import CampaignConfig, Protocol, Severity
from protocol_fuzzer.regression import replay, replay_all, to_regression_cases
from protocol_fuzzer.triage import Crash, bucket_crashes, signature


def test_signature_is_stable() -> None:
    assert signature("ValueError", "parse_http:40") == signature("ValueError", "parse_http:40")
    assert signature("ValueError", "parse_http:40") != signature("ValueError", "parse_http:41")


def test_bucket_dedup_and_sort() -> None:
    crashes = [
        Crash(b"a", "ValueError", "parse_http:40", "x"),
        Crash(b"aa", "ValueError", "parse_http:40", "x"),
        Crash(b"b", "IndexError", "parse_tlv:70", "y"),
    ]
    buckets = bucket_crashes(crashes, Protocol.HTTP)
    assert len(buckets) == 2
    # IndexError (medium) sorts above ValueError (low).
    assert buckets[0].severity is Severity.MEDIUM
    value_bucket = next(b for b in buckets if b.exception_type == "ValueError")
    assert value_bucket.count == 2
    assert value_bucket.sample_bytes == b"a"  # smallest reproducer retained


def test_regression_cases_reproduce() -> None:
    result, _ = run_campaign(CampaignConfig(protocol=Protocol.TLV, iterations=1000))
    cases = to_regression_cases(result)
    assert cases
    outcomes = replay_all(cases)
    assert all(outcomes.values())
    assert replay(cases[0]) is True
