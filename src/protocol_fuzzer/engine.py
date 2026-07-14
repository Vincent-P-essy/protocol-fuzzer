"""The coverage-guided fuzzing engine.

A campaign seeds a corpus, then repeatedly picks an input, mutates it, and runs
the target under coverage. Inputs that reach new lines are retained (a simple
power schedule), so the fuzzer drifts toward unexplored parser states. Crashes
are collected and handed to triage. The loop is fully deterministic in its seed:
the same configuration always discovers the same crash buckets, which is what
lets the benchmark treat discovery as reproducible evidence.
"""

from __future__ import annotations

import random

from .corpus import build_corpus
from .coverage import Edge, execute
from .models import CampaignConfig, CampaignResult
from .mutators import mutate
from .targets import EXPECTED_EXCEPTIONS, TARGETS
from .triage import Crash, bucket_crashes

# Cap the retained corpus so a long campaign cannot grow without bound.
MAX_CORPUS = 400


def run_campaign(config: CampaignConfig) -> tuple[CampaignResult, list[Crash]]:
    """Run a fuzzing campaign and return its result and raw crashes."""

    rng = random.Random(config.seed)
    target = TARGETS[config.protocol]
    seeds = build_corpus(config.protocol, semantic=config.semantic_corpus)
    corpus: list[bytes] = [data for data, _origin in seeds]

    coverage: set[Edge] = set()
    crashes: list[Crash] = []
    executions = 0

    def observe(data: bytes) -> None:
        nonlocal executions
        outcome = execute(target, data, EXPECTED_EXCEPTIONS)
        executions += 1
        if not outcome.edges <= coverage:
            coverage.update(outcome.edges)
            if len(corpus) < MAX_CORPUS and data not in corpus:
                corpus.append(data)
        if outcome.crashed and outcome.exception_type and outcome.location:
            crashes.append(
                Crash(
                    data=data,
                    exception_type=outcome.exception_type,
                    location=outcome.location,
                    message=outcome.message,
                )
            )

    # Seed pass establishes baseline coverage and finds seed-level crashes.
    for seed in list(corpus):
        observe(seed)

    for _ in range(config.iterations):
        base = corpus[rng.randrange(len(corpus))]
        mutant, _kind = mutate(base, rng)
        observe(mutant[: config.max_input_bytes])

    buckets = bucket_crashes(crashes, config.protocol)
    result = CampaignResult(
        protocol=config.protocol,
        seed=config.seed,
        executions=executions,
        corpus_size=len(corpus),
        coverage_edges=len(coverage),
        total_crashes=len(crashes),
        unique_crashes=len(buckets),
        buckets=buckets,
    )
    return result, crashes
