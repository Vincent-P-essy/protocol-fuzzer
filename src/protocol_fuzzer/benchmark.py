"""Deterministic benchmark across all protocols.

Runs a fixed-seed campaign for every protocol ``iterations`` times, verifies the
discovered crash signatures against the committed ground truth, confirms the
discovery is byte-identical across passes via a single stable hash, replays every
crash as a regression case, and measures wall time.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .engine import run_campaign
from .models import CampaignConfig, Protocol
from .regression import replay_all, to_regression_cases
from .resources import packaged_path


@dataclass(frozen=True)
class BenchmarkResult:
    iterations: int
    protocols: int
    total_unique_crashes: int
    ground_truth_verified: bool
    deterministic: bool
    regressions_reproduced: bool
    report_hash: str
    total_executions: int
    total_coverage_edges: int
    latency_campaign_p50_ms: float
    latency_campaign_p95_ms: float
    elapsed_seconds: float
    source_revision: str
    source_tree_state: str


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return round(ordered[rank], 4)


def ground_truth() -> dict[str, dict[str, object]]:
    """Compute the reviewed signature set for each protocol from one campaign."""

    truth: dict[str, dict[str, object]] = {}
    for protocol in Protocol:
        result, _crashes = run_campaign(CampaignConfig(protocol=protocol))
        truth[protocol.value] = {
            "signatures": sorted(result.crash_signatures),
            "unique_crashes": result.unique_crashes,
        }
    return truth


def committed_ground_truth() -> dict[str, dict[str, object]]:
    data: dict[str, dict[str, object]] = json.loads(
        packaged_path("ground-truth.json").read_text(encoding="utf-8")
    )
    return data


def _hash(payload: dict[str, dict[str, object]]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def benchmark(iterations: int = 20) -> BenchmarkResult:
    declared = committed_ground_truth()
    durations_ms: list[float] = []
    hashes: set[str] = set()
    verified = True
    reproduced = True
    total_unique = 0
    total_exec = 0
    total_edges = 0
    started = time.perf_counter()

    for iteration in range(iterations):
        pass_signatures: dict[str, dict[str, object]] = {}
        for protocol in Protocol:
            start = time.perf_counter()
            result, _crashes = run_campaign(CampaignConfig(protocol=protocol))
            durations_ms.append((time.perf_counter() - start) * 1000)
            pass_signatures[protocol.value] = {
                "signatures": sorted(result.crash_signatures),
                "unique_crashes": result.unique_crashes,
            }
            if iteration == 0:
                total_unique += result.unique_crashes
                total_exec += result.executions
                total_edges += result.coverage_edges
                if pass_signatures[protocol.value] != declared[protocol.value]:
                    verified = False
                cases = to_regression_cases(result)
                if not all(replay_all(cases).values()):
                    reproduced = False
        hashes.add(_hash(pass_signatures))

    elapsed = time.perf_counter() - started
    return BenchmarkResult(
        iterations=iterations,
        protocols=len(Protocol),
        total_unique_crashes=total_unique,
        ground_truth_verified=verified,
        deterministic=len(hashes) == 1,
        regressions_reproduced=reproduced,
        report_hash=next(iter(hashes)) if hashes else "",
        total_executions=total_exec,
        total_coverage_edges=total_edges,
        latency_campaign_p50_ms=_percentile(durations_ms, 50),
        latency_campaign_p95_ms=_percentile(durations_ms, 95),
        elapsed_seconds=round(elapsed, 4),
        source_revision=os.environ.get("PROTOFUZZ_SOURCE_REVISION", "unknown"),
        source_tree_state=os.environ.get("PROTOFUZZ_SOURCE_TREE_STATE", "unknown"),
    )


def write_benchmark(out_dir: Path, result: BenchmarkResult) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "benchmark.json"
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
