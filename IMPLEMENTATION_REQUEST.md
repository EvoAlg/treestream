Generate a complete Python 3.11+ implementation of TreeStream that conforms exactly to SPEC.md v0.1.9.

Hard constraints:
- Standard library only
- Windows-only semantics
- Deterministic output and deterministic failure behaviour
- Binary mode I/O for serialized files (no newline translation)
- Length-prefixed parsing strictly governed by CONTENT_BYTES
- Deterministic traversal and PATH sorting exactly as specified
- Explicit errors with correct E-codes per SPEC.md

Repository constraints:
- Write all implementation code under IMPLEMENTATION/
- Do not modify SPEC.md
- Do not modify SCENARIOS.feature
- Do not modify fixtures
- Embed version identifier v0.1.9 in implementation metadata

Deliverables:
- CLI entry point
- serialize: root directory → serialized file
- reconstruct: serialized file → target directory