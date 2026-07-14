"""Command-line interface for the protocol fuzzer."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import uvicorn

from .benchmark import benchmark, write_benchmark
from .engine import run_campaign
from .models import CampaignConfig, Protocol
from .regression import replay_all, to_regression_cases
from .reporting import result_to_dict, write_report

_PROTOCOLS = [p.value for p in Protocol]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="protofuzz", description="Coverage-guided protocol fuzzer")
    commands = root.add_subparsers(dest="command", required=True)

    def add_campaign_args(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--protocol", choices=_PROTOCOLS, required=True)
        sub.add_argument("--iterations", type=int, default=2_000)
        sub.add_argument("--seed", type=int, default=1337)
        sub.add_argument("--max-bytes", type=int, default=512)
        sub.add_argument("--no-semantic", action="store_true")

    fuzz = commands.add_parser("fuzz", help="run a fuzzing campaign")
    add_campaign_args(fuzz)

    report = commands.add_parser("report", help="run a campaign and write a report")
    add_campaign_args(report)
    report.add_argument("--out", type=Path, default=Path("reports"))

    regress = commands.add_parser("regress", help="run a campaign and replay its crashes")
    add_campaign_args(regress)

    run_benchmark = commands.add_parser("benchmark", help="measure all protocols")
    run_benchmark.add_argument("--iterations", type=int, default=20)
    run_benchmark.add_argument("--out", type=Path, default=Path("reports"))

    serve = commands.add_parser("serve", help="start the local API and dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)

    return root


def _config(args: argparse.Namespace) -> CampaignConfig:
    return CampaignConfig(
        protocol=Protocol(args.protocol),
        iterations=args.iterations,
        seed=args.seed,
        max_input_bytes=args.max_bytes,
        semantic_corpus=not args.no_semantic,
    )


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)

    if args.command == "fuzz":
        result, _crashes = run_campaign(_config(args))
        _print(result_to_dict(result))
        return 0

    if args.command == "report":
        result, _crashes = run_campaign(_config(args))
        paths = write_report(args.out, result)
        _print({key: str(path) for key, path in paths.items()})
        return 0

    if args.command == "regress":
        result, _crashes = run_campaign(_config(args))
        cases = to_regression_cases(result)
        outcomes = replay_all(cases)
        _print(
            {
                "protocol": result.protocol.value,
                "unique_crashes": result.unique_crashes,
                "reproduced": sum(1 for ok in outcomes.values() if ok),
                "cases": {cid: ok for cid, ok in outcomes.items()},
            }
        )
        return 0

    if args.command == "benchmark":
        measured = benchmark(iterations=args.iterations)
        path = write_benchmark(args.out, measured)
        _print({"benchmark": str(path), **asdict(measured)})
        return 0

    if args.command == "serve":
        uvicorn.run(
            "protocol_fuzzer.api:create_app",
            host=args.host,
            port=args.port,
            factory=True,
            log_level="info",
        )
        return 0

    return 2  # pragma: no cover - argparse requires a subcommand


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
