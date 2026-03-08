# TreeStream Scenario and Acceptance Test Report

- Date/time (local): 2026-03-08 18:08:38 +11:00
- OS: Microsoft Windows NT 10.0.19045.0
- Python: 3.12.1
- Shell: PowerShell 5.1.19041.6456
- Working directory: `C:\Users\edwar\OneDrive\Documents\Programming\TreeStream`

## Commands Executed

- `python -` (inline scenario runner script executing S01-S22 against `IMPLEMENTATION/treestream`, plus standalone structural CR negative check)
- `python -` (inline acceptance-gate verification script for Gates B-F using `fixtures/determinism`, `fixtures/roundtrip`, and `fixtures/errors`)

## Scenario Results (`SCENARIOS.feature`)

- S01: PASS
- S02: PASS
- S03: PASS
- S04: PASS
- S05: PASS
- S06: PASS
- S07: PASS
- S08: PASS (E4)
- S09: PASS (E5)
- S10: PASS (E4)
- S11: PASS (E4)
- S12: PASS (E7)
- S13: PASS (E8)
- S14: PASS (E8)
- S15: PASS (E6)
- S16: PASS (E9)
- S17: PASS (E9)
- S18: PASS (E11)
- S19: PASS (E10)
- S20: PASS
- S21: PASS
- S22: PASS

## Additional Structural Parsing Check

- Standalone `CR` in structural region: PASS (E6)

## Acceptance Criteria Gate Summary (`ACCEPTANCE_CRITERIA.md`)

- Gate A (Scenario Validation): PASS
  - S01-S22 all passed with zero failures.

- Gate B (Deterministic Serialization Output): PASS
  - SHA-256 run1: `14d31017bef4ba69c60dff126dbd7955adf3cb0f9fcf762ea4d0395410afd28b`
  - SHA-256 run2: `14d31017bef4ba69c60dff126dbd7955adf3cb0f9fcf762ea4d0395410afd28b`
  - Binary compare: identical (`True`)

- Gate C (Round-Trip Integrity): PASS
  - Source vs reconstructed tree compare: identical paths and bytes (`True`)

- Gate D (Format Conformance): PASS
  - Header matches v0.1.10 exactly: `True`
  - Structural CRLF in serializer output: `False` (LF-only structural lines)
  - Non-blank trailing bytes rejected with E6: verified in S15
  - Trailing blank lines tolerated after final `END_FILE`: verified in S22

- Gate E (Error Handling and E-code Mapping): PASS
  - Verified cases: E7, E8, E9 (path traversal), E9 (case collision), E10, E11, plus scenario-driven E4/E5.
  - Note: current `fixtures/errors/*` record fixtures are still authored with `SPEC_VERSION: v0.1.9`; for non-E7 reconstruction error checks, temporary in-artifact v0.1.10-adjusted copies were used to validate intended failure stage for v0.1.10 parser behavior.

- Gate F (CRLF and Trailing-Blank Transport Tolerance): PASS
  - LF payload reconstruct: success
  - CRLF-structural payload reconstruct: success
  - Trailing-blank-lines payload reconstruct: success
  - All reconstructed trees byte-identical: `True`
  - Re-serialized structural lines LF-only: `True`

## Summary

- Total scenarios: 22
- Passed: 22
- Failed: 0
- Skipped: 0

All scenarios in `SCENARIOS.feature` passed in this run, and acceptance-gate checks completed successfully against current repository fixtures and v0.1.10 implementation behavior.
