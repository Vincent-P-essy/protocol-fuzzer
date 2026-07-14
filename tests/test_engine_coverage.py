from __future__ import annotations

import random

from protocol_fuzzer.coverage import execute
from protocol_fuzzer.engine import run_campaign
from protocol_fuzzer.models import CampaignConfig, MutationKind, Protocol
from protocol_fuzzer.mutators import _OPERATORS, mutate
from protocol_fuzzer.targets import EXPECTED_EXCEPTIONS, parse_http


def test_execute_records_coverage_for_clean_input() -> None:
    outcome = execute(parse_http, b"GET / HTTP/1.1\r\nHost: x\r\n\r\n", EXPECTED_EXCEPTIONS)
    assert outcome.crashed is False
    assert len(outcome.edges) > 0


def test_execute_flags_crash_with_location() -> None:
    outcome = execute(parse_http, b"GET / HTTP/1.1 extra\r\n\r\n", EXPECTED_EXCEPTIONS)
    assert outcome.crashed is True
    assert outcome.exception_type == "ValueError"
    assert outcome.location is not None and outcome.location.startswith("parse_http:")


def test_execute_treats_parse_error_as_clean() -> None:
    outcome = execute(parse_http, b"", EXPECTED_EXCEPTIONS)
    assert outcome.crashed is False


def test_every_mutator_returns_bytes_and_handles_empty() -> None:
    rng = random.Random(1)
    for kind, operator in _OPERATORS.items():
        assert isinstance(operator(b"", rng), bytes)
        assert isinstance(operator(b"seed-data", rng), bytes)
        assert isinstance(kind, MutationKind)


def test_mutation_is_deterministic() -> None:
    a = [mutate(b"seed", random.Random(7))[0] for _ in range(5)]
    b = [mutate(b"seed", random.Random(7))[0] for _ in range(5)]
    assert a == b


def test_campaign_is_deterministic_and_finds_crashes() -> None:
    config = CampaignConfig(protocol=Protocol.HTTP, iterations=500)
    first, _ = run_campaign(config)
    second, _ = run_campaign(config)
    assert first.crash_signatures == second.crash_signatures
    assert first.unique_crashes >= 3
    assert first.coverage_edges > 0


def test_semantic_corpus_runs_both_ways() -> None:
    with_semantic, _ = run_campaign(
        CampaignConfig(protocol=Protocol.JSONRPC, iterations=300, semantic_corpus=True)
    )
    without, _ = run_campaign(
        CampaignConfig(protocol=Protocol.JSONRPC, iterations=300, semantic_corpus=False)
    )
    # Both are valid campaigns; the semantic corpus reaches at least as many bugs.
    assert with_semantic.unique_crashes >= 1
    assert with_semantic.unique_crashes >= without.unique_crashes
