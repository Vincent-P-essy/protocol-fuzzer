"""Serialize campaign results and crash buckets into review artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CampaignResult, CrashBucket


def bucket_to_dict(bucket: CrashBucket) -> dict[str, Any]:
    return {
        "signature": bucket.signature,
        "protocol": bucket.protocol.value,
        "exception_type": bucket.exception_type,
        "location": bucket.location,
        "severity": bucket.severity.value,
        "count": bucket.count,
        "sample_hex": bucket.sample_hex,
        "sample_repr": bucket.sample_repr,
    }


def result_to_dict(result: CampaignResult) -> dict[str, Any]:
    return {
        "protocol": result.protocol.value,
        "seed": result.seed,
        "executions": result.executions,
        "corpus_size": result.corpus_size,
        "coverage_edges": result.coverage_edges,
        "total_crashes": result.total_crashes,
        "unique_crashes": result.unique_crashes,
        "buckets": [bucket_to_dict(bucket) for bucket in result.buckets],
    }


def render_markdown(result: CampaignResult) -> str:
    lines = [
        f"# Fuzzing campaign: {result.protocol.value}",
        "",
        f"- Seed: `{result.seed}`",
        f"- Executions: **{result.executions}**",
        f"- Coverage edges: **{result.coverage_edges}**",
        f"- Crashes: **{result.total_crashes}** total, **{result.unique_crashes}** unique",
        "",
        "| Severity | Exception | Location | Count | Sample |",
        "|---|---|---|---:|---|",
    ]
    for bucket in result.buckets:
        lines.append(
            f"| {bucket.severity.value} | `{bucket.exception_type}` | `{bucket.location}` | "
            f"{bucket.count} | `{bucket.sample_repr}` |"
        )
    return "\n".join(lines) + "\n"


def write_report(out_dir: Path, result: CampaignResult) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"campaign-{result.protocol.value}.json"
    md_path = out_dir / f"campaign-{result.protocol.value}.md"
    json_path.write_text(
        json.dumps(result_to_dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
