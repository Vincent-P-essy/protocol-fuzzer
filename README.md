# Protocol Fuzzer

**A coverage-guided, grammar-based fuzzer that finds real robustness bugs in
protocol parsers, triages the crashes into deduplicated buckets, and turns each
one into a regression test — deterministically, so every run finds the same bugs.**

[![CI](https://github.com/Vincent-P-essy/protocol-fuzzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Vincent-P-essy/protocol-fuzzer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%E2%80%933.12-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-2f6f4e)](LICENSE)

Protocol Fuzzer combines the pieces of a modern fuzzer into one small, readable,
deterministic tool: a grammar seed corpus, a semantic edge-case generator (a
pluggable stand-in for an LLM corpus generator), seven mutation operators, a
line-coverage tracer that guides the search, automatic crash triage, and a
regression suite built from the crashes it finds. It fuzzes three synthetic
protocol parsers — HTTP/1.1, a TLV binary format, and a JSON-RPC subset — that
carry deliberate, documented bugs.

Because the whole loop is seeded, a campaign is reproducible: the same
configuration always discovers the same crash buckets, so "which bugs were found"
becomes evidence you can hash and diff. It is a portfolio-grade prototype over
synthetic parsers, not a production fuzzing platform.

## Measured evidence

| Measurement | Reviewed result | Scope |
|---|---:|---|
| Distinct bugs found | **10** | 3 protocols; deduplicated `(exception, location)` buckets |
| Discovery vs committed ground truth | **verified** | `benchmark` output vs `fixtures/ground-truth.json` |
| Determinism across 20 passes | **1 identical outcome hash** | Per-protocol signature sets, hash excludes timing |
| Crashes replayable as regressions | **10/10** | Every bucket reproduces from its minimal input |
| Executions per pass | **~6,000** | ~2,000 per protocol |
| Campaign latency p50 / p95 | **~70 / ~88 ms** | Per protocol, includes `sys.settrace` coverage |
| Test coverage | **92.13%** | Branch-aware source coverage |

See the [methodology](docs/METHODOLOGY.md) and [reviewed reference run](benchmarks/reference/README.md).

## A bug the fuzzer found that its author did not expect

The JSON-RPC target guards `json.loads` with `except json.JSONDecodeError`. The
fuzzer discovered that non-UTF-8 bytes make `json.loads` raise
`UnicodeDecodeError` — a *sibling* of `JSONDecodeError`, not a subclass — which
escapes the handler. That is exactly the kind of overlooked edge a fuzzer exists
to surface, and it appears here as a distinct, reproducible crash bucket rather
than a footnote.

## What is implemented

- **Grammar + semantic corpus** (`corpus.py`): well-formed protocol messages for
  baseline coverage, plus boundary-shaped edge cases. The semantic generator is a
  deterministic, pluggable stand-in for an LLM corpus generator.
- **Mutation engine** (`mutators.py`): bit flips, byte flips, boundary values,
  truncation, chunk duplication, insertion, and protocol format-confusion, all
  driven by a seeded PRNG for reproducibility.
- **Coverage-guided loop** (`engine.py`): inputs that reach new target lines are
  retained (a power schedule), steering the search toward unexplored states.
- **Coverage tracer** (`coverage.py`): `sys.settrace` line coverage that saves and
  restores any outer tracer, so instrumenting a target never disables the tool's
  own coverage measurement.
- **Crash triage** (`triage.py`): crashes deduplicated into buckets keyed by
  exception and source location, ranked by a severity heuristic that puts
  out-of-bounds indexing and runaway recursion above validation slips.
- **Regression capture** (`regression.py`): every bucket becomes a case that is
  replayed to confirm it still reproduces.
- CLI, local API, dependency-free dashboard, JSON/Markdown reports, Docker, CI,
  and a deterministic benchmark.

## Quick start

Requirements: Python 3.11 or 3.12 and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync --frozen --all-extras

# Fuzz one protocol and print triaged crash buckets
uv run protofuzz fuzz --protocol jsonrpc --iterations 2000

# Confirm every discovered crash replays from its regression case
uv run protofuzz regress --protocol tlv

# Measure all three protocols (deterministic)
uv run protofuzz benchmark --iterations 20
```

Start the API and dashboard:

```bash
uv run protofuzz serve --host 127.0.0.1 --port 8080
```

Open <http://127.0.0.1:8080> to launch campaigns and browse crash buckets.
OpenAPI is at `/docs`.

## Important limitations

- Targets are **memory-safe Python**, so the tool finds robustness and
  input-validation bugs (unhandled exceptions, runaway recursion), not memory
  corruption.
- The coverage signal is **line coverage** via `sys.settrace`, not edge- or
  path-coverage or compiler instrumentation.
- The three protocols are **small synthetic parsers** with deliberate bugs.
- The semantic corpus is a deterministic **stand-in** for an LLM generator, not a
  live model.
- The local API is unauthenticated and must be bound to loopback. Only fuzz
  software you are authorized to test.

See [architecture](docs/ARCHITECTURE.md), [methodology](docs/METHODOLOGY.md), and
[limitations](docs/LIMITATIONS.md).
