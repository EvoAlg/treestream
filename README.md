# TreeStream

TreeStream is a deterministic directory serialisation and reconstruction 
tool for UTF-8 text files.

It converts a root directory into a single structured `.treestream` file 
and can reconstruct the original directory from that file. Output is 
byte-for-byte identical for identical inputs.

## Usage

**Serialise a directory:**
```
python -m treestream serialize <source_dir> <output_file>
```

**Reconstruct from a serialised file:**
```
python -m treestream reconstruct <input_file> <target_dir>
```

**Exclude files or directories by glob pattern:**
```
python -m treestream serialize <source_dir> <output_file> --exclude __pycache__ --exclude *.pyc
```

**Ignore file:**
Place a `.treestreamignore` file in the root of the directory being 
serialised. Each non-comment line is treated as a glob exclusion pattern. 
Patterns from `.treestreamignore` and `--exclude` are merged.
```
# Example .treestreamignore
.git
__pycache__
*.pyc
artifacts
```

## Platform

- Target platform: Microsoft Windows
- Python version: 3.11+
- Standard library only — no external dependencies

## Core Guarantees

- Deterministic output — byte-for-byte identical for identical inputs
- Exact file content preservation via base64 encoding
- Forward-slash relative path canonicalisation
- Strict UTF-8 validation for content files
- Explicit, deterministic error handling

## Specification

Authoritative specification: `SPEC.md` (current version: v0.1.16)

All behaviour is defined strictly by the specification. The specification 
is the single source of truth.

## Repository Structure

- `SPEC.md` — Authoritative specification
- `SCENARIOS.feature` — Behaviour-level validation scenarios (S01–S36)
- `ACCEPTANCE_CRITERIA.md` — Acceptance gates
- `IMPLEMENTATION/treestream/` — Implementation package
- `tests/` — Automated test suite (S01–S36, 39 tests)
- `TEST_REPORT.md` — Test execution report
- `REVIEW.md` — Independent review artifact
- `archive/` — Versioned snapshots of spec artifacts

## Running the Test Suite
```
$env:PYTHONPATH='IMPLEMENTATION'; python -m unittest -v tests.test_core tests.test_exclusion_filter
```

## Development Methodology

TreeStream is developed using the Dark Factory (DF) methodology — a 
multi-agent AI development workflow where multiple AI models operate in 
defined, non-overlapping roles to produce higher-quality outputs than any 
single model alone.

See `DARK_FACTORY_METHODOLOGY.md` for the full methodology specification.
See `DF_CONFIG.md` for the role assignments used in this project.
See `AGENT_START_HERE.md` if you are an AI agent beginning work on this repo.