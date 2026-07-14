"""Smoke-test the installed wheel from outside the source checkout."""

from __future__ import annotations

from protocol_fuzzer.benchmark import committed_ground_truth, ground_truth
from protocol_fuzzer.engine import run_campaign
from protocol_fuzzer.models import CampaignConfig, Protocol
from protocol_fuzzer.regression import replay_all, to_regression_cases


def main() -> int:
    if ground_truth() != committed_ground_truth():
        print("ground truth drift")
        return 1
    total = 0
    for protocol in Protocol:
        result, _ = run_campaign(CampaignConfig(protocol=protocol, iterations=500))
        cases = to_regression_cases(result)
        if not all(replay_all(cases).values()):
            print(f"regression replay failed for {protocol.value}")
            return 1
        total += result.unique_crashes
    print(f"ok: {total} unique crashes across {len(Protocol)} protocols, all reproduced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
