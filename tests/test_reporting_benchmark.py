from __future__ import annotations

import json
from pathlib import Path

from protocol_fuzzer.benchmark import (
    _percentile,
    benchmark,
    committed_ground_truth,
    ground_truth,
    write_benchmark,
)
from protocol_fuzzer.engine import run_campaign
from protocol_fuzzer.models import CampaignConfig, Protocol
from protocol_fuzzer.reporting import bucket_to_dict, render_markdown, result_to_dict, write_report


def test_percentile() -> None:
    assert _percentile([], 50) == 0.0
    assert _percentile([1.0, 2.0, 3.0], 50) == 2.0


def test_ground_truth_matches_committed_fixture() -> None:
    assert ground_truth() == committed_ground_truth()


def test_benchmark_is_deterministic() -> None:
    result = benchmark(iterations=3)
    assert result.deterministic is True
    assert result.ground_truth_verified is True
    assert result.regressions_reproduced is True
    assert result.total_unique_crashes == 10
    assert result.report_hash


def test_write_benchmark(tmp_path: Path) -> None:
    path = write_benchmark(tmp_path, benchmark(iterations=2))
    assert json.loads(path.read_text(encoding="utf-8"))["iterations"] == 2


def test_report_render(tmp_path: Path) -> None:
    result, _ = run_campaign(CampaignConfig(protocol=Protocol.HTTP, iterations=500))
    markdown = render_markdown(result)
    assert "Fuzzing campaign" in markdown
    assert set(result_to_dict(result)) >= {"protocol", "buckets", "coverage_edges"}
    assert "signature" in bucket_to_dict(result.buckets[0])

    paths = write_report(tmp_path, result)
    assert paths["json"].exists()
    assert paths["markdown"].exists()
