# TreeStream Scenario and Acceptance Test Report

- Date/time (local): 2026-03-10T21:14:04+11:00
- OS: Windows-10-10.0.19045-SP0
- Python: 3.12.1
- Shell: PowerShell 5.1
- Working directory: `C:\Users\edwar\OneDrive\Documents\Programming\TreeStream`

## Commands Executed

- `python -m py_compile IMPLEMENTATION\treestream\__init__.py IMPLEMENTATION\treestream\format.py IMPLEMENTATION\treestream\serializer.py IMPLEMENTATION\treestream\reconstructor.py IMPLEMENTATION\treestream\cli.py IMPLEMENTATION\cli.py`
- `python -` (inline scenario and acceptance runner; evidence written under `artifacts/`, summary in `artifacts/scenario_results.json`)

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
- S23: PASS

## Acceptance Criteria Gate Summary (`ACCEPTANCE_CRITERIA.md`)

- Gate A: PASS
  - S01-S23 passed with zero failures.
- Gate B: PASS
  - SHA-256 run1: `5d41f33eee17c41363907795fe694ca7ded5032844337427821bcebb202396ff`
  - SHA-256 run2: `5d41f33eee17c41363907795fe694ca7ded5032844337427821bcebb202396ff`
  - Binary compare: identical (`True`)
- Gate C: PASS
  - `fixtures/roundtrip/` and `artifacts/roundtrip_reconstructed/` had identical relative paths and byte content.
- Gate D: PASS
  - Header matched `v0.1.11`
  - Structural lines were LF-only
  - Content blocks were valid RFC 4648 Base64 with decoded byte count equal to `CONTENT_BYTES`
  - Record ordering matched ordinal `PATH` sort
- Gate E: PASS
  - Verified E4, E5, E6, E7, E8, E9, E10, E11, E12
  - Verification was performed directly against the committed `v0.1.11` fixtures in `fixtures/errors/`
- Gate F: PASS
  - LF payload reconstruction: success
  - CRLF-structural payload reconstruction: success
  - Trailing-blank-lines payload reconstruction: success
  - Reconstructed trees matched byte-for-byte
  - Re-serialized output remained LF-only

## Summary

- Total scenarios: 23
- Passed: 23
- Failed: 0
- Skipped: 0

Implementation self-verification passed for the exercised scenario suite and acceptance-gate checks. Per `AGENT_RULES.md`, final acceptance still requires independent verification by a human or a separate agent role.
