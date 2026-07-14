# Security policy

Report vulnerabilities through GitHub private vulnerability reporting. Include
the affected commit, the protocol, the crashing input as hex, the expected
behaviour, and the observed exception.

This tool fuzzes in-process Python parsers that ship with the project. It opens
no network connections, spawns no subprocesses, and touches no filesystem while
fuzzing; a "crash" is an unhandled exception (or runaway recursion) in a target
parser, caught by the harness. The target parsers are intentionally imperfect
teaching examples — do not treat them as reference implementations.

Do not point this tool at software you are not authorized to test. Coverage-
guided fuzzing generates untrusted inputs by design; run untrusted targets under
the container's resource limits (read-only, capability-dropped, memory- and
PID-limited) and never feed discovered inputs to a production system.

The seed corpus, grammars, and crash inputs are synthetic. The mutation engine
uses a seeded non-cryptographic PRNG on purpose so campaigns are reproducible.
