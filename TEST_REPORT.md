# TreeStream Scenario and Acceptance Test Report

- Date/time (local): 2026-03-12T08:43:35+11:00
  - Updated exclusion-filter verification: 2026-03-22T10:04:36.7044986+11:00
- OS: Windows-10-10.0.19045-SP0
- Python: 3.12.1
- Shell: PowerShell 5.1
- Working directory: `C:\Users\edwar\OneDrive\Documents\Programming\TreeStream`

## Commands Executed

- `python -m py_compile IMPLEMENTATION\treestream\__init__.py IMPLEMENTATION\treestream\version.py IMPLEMENTATION\treestream\format.py IMPLEMENTATION\treestream\serializer.py IMPLEMENTATION\treestream\reconstructor.py IMPLEMENTATION\treestream\cli.py`
- `python -` (inline scenario and acceptance runner for S01-S24 and Gates A-F)
- `python -m py_compile IMPLEMENTATION\treestream\__init__.py IMPLEMENTATION\treestream\version.py IMPLEMENTATION\treestream\format.py IMPLEMENTATION\treestream\serializer.py IMPLEMENTATION\treestream\reconstructor.py IMPLEMENTATION\treestream\cli.py tests\test_exclusion_filter.py`
- `$env:PYTHONPATH='IMPLEMENTATION'; python -m unittest -v tests.test_exclusion_filter`
- `python -` (inline Gate G evidence generator writing `artifacts/gate_g_*.treestream`)

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
- S24: PASS
- S25: PASS
- S26: PASS
- S27: PASS
- S28: PASS
- S29: PASS

## Acceptance Criteria Gate Summary (`ACCEPTANCE_CRITERIA.md`)

- Gate A: PASS
  - S01-S24 passed with zero failures.
- Gate B: PASS
  - SHA-256 run1: `18ef14f0ec25a77e6a2ed2a63c325d3e71327976ec787cd9db740390f6eea41b`
  - SHA-256 run2: `18ef14f0ec25a77e6a2ed2a63c325d3e71327976ec787cd9db740390f6eea41b`
  - Binary compare: identical (`True`)
- Gate C: PASS
  - `fixtures/roundtrip/` and the reconstructed `roundtrip/` subtree beneath the target directory had identical relative paths and byte content.
- Gate D: PASS
  - Header matched `v0.1.14`
  - `ROOT_NAME: determinism` matched the serialized root directory name
  - Structural lines were LF-only
  - Content blocks were valid RFC 4648 Base64 with decoded byte count equal to `CONTENT_BYTES`
  - Record ordering matched ordinal `PATH` sort
- Gate E: PASS
  - Verified E4, E5, E5a, E6, E7, E8, E9, E10, E11, E12
  - Self-verification used committed repository fixtures where available and temporary `v0.1.12` payloads for new `ROOT_NAME` and `E5a` cases
- Gate F: PASS
  - LF payload reconstruction: success
  - CRLF-structural payload reconstruction: success
  - Trailing-blank-lines payload reconstruction: success
  - Reconstructed trees matched byte-for-byte
  - Re-serialized output remained LF-only
- Gate G: PASS
  - CLI accepted repeatable `--exclude` arguments.
  - S25 exact-name directory exclusion omitted `__pycache__/` and kept `src/main.py`.
  - S26 glob exclusion omitted `src/main.pyc` and kept `src/main.py` plus `notes.txt`.
  - S27 multiple exclusions omitted both `__pycache__/` and `.git/` subtrees independently.
  - S28 non-matching exclusion matched the no-exclusion baseline byte-for-byte.
  - S29 traversal instrumentation confirmed no descent into excluded `skip_dir/`.
  - Safe baseline SHA-256: `8202d9c62d6af1945a4bd46d87442eb9079c8571f640faad4e9aa9ff94fd759e`
  - Safe non-matching SHA-256: `8202d9c62d6af1945a4bd46d87442eb9079c8571f640faad4e9aa9ff94fd759e`
  - Excluded run 1 SHA-256: `6af2141b3dac81fdcf8b86818601afd17075b1f63241ead827b999b2aab42316`
  - Excluded run 2 SHA-256: `6af2141b3dac81fdcf8b86818601afd17075b1f63241ead827b999b2aab42316`
  - Safe baseline vs non-matching exclusion binary compare: identical (`True`)
  - Excluded run 1 vs excluded run 2 binary compare: identical (`True`)
  - Safe baseline record paths: `docs/readme.txt`, `notes.txt`, `src/main.py`
  - Excluded-output record paths: `docs/readme.txt`, `keep/data.txt`, `notes.txt`, `src/main.py`

## Summary

- Total scenarios: 29
- Passed: 29
- Failed: 0
- Skipped: 0

Implementation self-verification passed for the exercised scenario suite and acceptance-gate checks, including the exclusion-filter additions in SPEC `v0.1.14`. Per `AGENT_RULES.md`, final acceptance still requires independent verification by a human or a separate agent role.
