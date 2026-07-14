"""Turn discovered crashes into a permanent regression suite.

Each crash bucket becomes a :class:`RegressionCase` keyed by its signature and
carrying the minimal reproducing input. ``replay`` re-runs the target on that
input and confirms it still crashes with the same exception class, so a fixed bug
that regresses is caught immediately.
"""

from __future__ import annotations

from .coverage import execute
from .models import CampaignResult, Protocol, RegressionCase
from .targets import EXPECTED_EXCEPTIONS, TARGETS


def to_regression_cases(result: CampaignResult) -> list[RegressionCase]:
    return [
        RegressionCase(
            id=bucket.signature,
            protocol=result.protocol,
            input_hex=bucket.sample_hex,
            exception_type=bucket.exception_type,
            location=bucket.location,
        )
        for bucket in result.buckets
    ]


def replay(case: RegressionCase) -> bool:
    """Return ``True`` if the case still reproduces its original crash."""

    target = TARGETS[Protocol(case.protocol)]
    outcome = execute(target, bytes.fromhex(case.input_hex), EXPECTED_EXCEPTIONS)
    return outcome.crashed and outcome.exception_type == case.exception_type


def replay_all(cases: list[RegressionCase]) -> dict[str, bool]:
    return {case.id: replay(case) for case in cases}
