# Methodology

How the measured evidence is produced and what it does and does not cover.

## Ground truth

`benchmark.ground_truth()` runs one fixed-seed campaign per protocol and records
the sorted set of crash signatures it discovers. That set is committed to
`fixtures/ground-truth.json`, and a test asserts the two are identical so the
fixture cannot drift from the engine.

## Discovery and determinism

`protofuzz benchmark` runs every protocol's campaign `iterations` times. It
verifies the discovered signatures against the committed ground truth
(`ground_truth_verified`), and hashes the per-protocol signature map each pass;
`deterministic == true` means every pass produced one identical hash. Because the
loop is seeded, the same configuration always finds the same bugs.

## Reproduction

Every discovered crash is promoted to a regression case carrying its minimal
reproducing input, and `benchmark` replays all of them
(`regressions_reproduced`). A bug that is fixed and later regresses is caught the
next run.

## Coverage guidance

`execute` records the set of target-module lines each input reaches. An input
that reaches a new line is retained in the corpus (a simple power schedule), so
mutation drifts toward unexplored parser states rather than re-testing the same
paths. The semantic corpus seeds boundary shapes an LLM generator would produce;
it is deterministic so the campaign stays reproducible, and it is pluggable so a
real model could be substituted.

## What the numbers mean and do not mean

- **Unique crashes** is the count of distinct `(exception, location)` buckets, not
  raw crash count.
- **Coverage edges** is line coverage of the small target parsers, not of a real
  application, and not branch- or path-coverage.
- **Latency** is machine dependent and not asserted in CI. Reproduce locally:

```bash
uv run protofuzz benchmark --iterations 20
```

The targets are deliberately buggy teaching parsers over synthetic protocols;
the numbers demonstrate the *method*, not the security of any real software.
