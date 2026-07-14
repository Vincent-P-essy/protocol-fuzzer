# Reviewed reference run

`reference-run.json` is a committed benchmark over all three protocols, produced
by:

```bash
PROTOFUZZ_SOURCE_REVISION=reference PROTOFUZZ_SOURCE_TREE_STATE=clean-checkout \
  uv run protofuzz benchmark --iterations 20 --out benchmarks/reference
```

`inputs.sha256` pins the committed crash ground truth. CI verifies it with
`sha256sum --check benchmarks/reference/inputs.sha256`.

## What the run establishes

- **Discovery.** A fixed-seed campaign per protocol finds the reviewed set of
  crash signatures (`ground_truth_verified == true`), checked against
  `fixtures/ground-truth.json` by a test. Ten distinct bugs are found across the
  three synthetic parsers.
- **Determinism.** Every pass discovers a byte-identical signature set, collapsed
  to one `report_hash` (`deterministic == true`).
- **Reproducibility.** Every discovered crash replays from its regression case
  (`regressions_reproduced == true`).

Latency and coverage-edge counts are machine dependent and are not asserted in
CI; only discovery, determinism, reproduction, and input integrity are.
