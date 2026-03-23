# TreeStream Test Report

- Date/time (local): 2026-03-23T12:21:03.4249135+11:00
- OS: Windows-10-10.0.19045-SP0
- Python: 3.12.1
- Shell: PowerShell 5.1
- Working directory: `C:\Users\edwar\OneDrive\Documents\Programming\TreeStream`
- Implementation target: `SPEC.md` v0.1.16

## Verification Scope

This update covers the `.treestreamignore` implementation requested for `SPEC.md` v0.1.16.

- Historical evidence already recorded in this repository:
  - S01-S24: PASS on 2026-03-12
  - S25-S29: PASS on 2026-03-22
- Current rerun for this task:
  - S25-S36 via `tests.test_exclusion_filter` on 2026-03-23

## Commands Executed

- `$env:PYTHONPATH='IMPLEMENTATION'; python -m py_compile IMPLEMENTATION\treestream\__init__.py IMPLEMENTATION\treestream\version.py IMPLEMENTATION\treestream\format.py IMPLEMENTATION\treestream\serializer.py IMPLEMENTATION\treestream\reconstructor.py IMPLEMENTATION\treestream\cli.py tests\test_exclusion_filter.py`
- `$env:PYTHONPATH='IMPLEMENTATION'; python -m unittest -v tests.test_exclusion_filter`

## Scenario Results Verified In This Run

- S25: PASS
- S26: PASS
- S27: PASS
- S28: PASS
- S29: PASS
- S30: PASS
  - Root `.treestreamignore` excluded `skip.pyc`.
  - Comment and blank lines were ignored.
  - `.treestreamignore` itself was absent from serialized records.
- S31: PASS
  - Root `.treestreamignore` excluded directory `skip_dir`.
  - Traversal instrumentation confirmed no descent into `skip_dir`.
- S32: PASS
  - Root without `.treestreamignore` matched baseline byte-for-byte.
  - Empty root `.treestreamignore` matched the no-ignore baseline byte-for-byte.
- S33: PASS
  - Patterns from root `.treestreamignore` and `--exclude` were both applied.
  - Entries matching either source were absent; `keep.txt` remained.
- S34: PASS
  - Root `.treestreamignore` was never serialized.
  - Subdirectory `nested/.treestreamignore` was serialized as a normal file.
- S35: PASS
  - Two runs with identical `.treestreamignore` input produced byte-for-byte identical output.
- S36: PASS
  - Invalid UTF-8 in root `.treestreamignore` raised `E13`.
  - Error text identified `.treestreamignore` and stated it could not be read as UTF-8.
  - `E4` was not raised.
  - No output file was written.

## Current Test Output

`python -m unittest -v tests.test_exclusion_filter` completed with:

- Ran 15 tests in 0.148s
- Result: `OK`

## Cumulative Scenario Status

- S01-S24: PASS (historical evidence retained from prior report entries)
- S25-S36: PASS (current exclusion/ignore regression suite)

Total scenarios with recorded PASS evidence: 36

Implementation self-verification passed for the exercised scope. Per `AGENT_RULES.md`, formal acceptance still requires independent verification by a human or a separate agent role.
