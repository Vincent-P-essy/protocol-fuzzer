# Limitations

This is a portfolio-grade prototype. It demonstrates the mechanics of a modern
coverage-guided, grammar-based fuzzer — seed corpus, mutation, coverage feedback,
crash triage, regression capture — over synthetic parsers, not a production
fuzzing platform.

- **Python targets.** The parsers are memory-safe Python, so the tool finds
  robustness and input-validation bugs (unhandled exceptions, runaway recursion),
  not memory corruption. There is no sanitizer integration or native-code
  harnessing.
- **Line coverage only.** The coverage signal is target-module line coverage via
  `sys.settrace`. It is not edge-, branch-, or path-coverage, and it does not use
  hardware or compiler instrumentation.
- **Small synthetic protocols.** HTTP/1.1, a TLV format, and a JSON-RPC subset,
  each a few dozen lines with deliberate bugs. Real protocol stacks are far
  larger and statefully connected.
- **Semantic corpus is a stand-in.** The "semantic" generator is a deterministic
  grammar-driven edge-case producer behind a pluggable interface, not a live LLM.
  It shows where an LLM corpus generator would slot in; it is not one.
- **No minimization pass.** Crash inputs are the smallest observed reproducer per
  bucket, not delta-debugged minimal cases.
- **In-process only.** No forkserver, no persistent-mode harness, no distributed
  campaigns, and no fuzzing of software the user does not own.
- **Local API.** Unauthenticated and for loopback only.

See the [architecture](ARCHITECTURE.md) and [methodology](METHODOLOGY.md) before
drawing conclusions from a campaign.
