# Contributing

Every change to the engine, mutators, or triage needs:

1. a test that a valid input is accepted and a malformed input is cleanly
   rejected (`ParseError`) by each affected target;
2. a test that each known bug still leaks its specific exception;
3. a determinism test: the same seed must discover the same crash signatures;
4. a ground-truth review when the discovered signature set changes, kept in sync
   with `fixtures/ground-truth.json` (a test enforces this).

The campaign must stay deterministic in its seed and must not disable the
process trace function it inherits — `execute` saves and restores it so coverage
of the tool itself is never silently switched off. Every discovered crash must
replay from its regression case.

Run before submitting:

```bash
uv sync --frozen --all-extras
make lint
make test
make benchmark
sha256sum --check benchmarks/reference/inputs.sha256
docker compose config --quiet
docker build -t protocol-fuzzer:test .
```

Do not commit real target software, credentials, or generated co-author
trailers. Keep crash claims tied to reproducible, minimized inputs.
