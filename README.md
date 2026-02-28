# TreeStream

TreeStream is a deterministic directory serialization and reconstruction tool for UTF-8 text files.

It converts a root directory into a single structured serialized file and can reconstruct the original directory from that file. Behavior is defined strictly by the project specification.

## Specification

Authoritative specification: `SPEC.md`
Current version: **v0.1.9**

All implementation decisions must conform exactly to the specification. The specification is the sole source of truth.

## Platform

* Target platform: Microsoft Windows
* Python version: 3.11+
* Standard library only
* No external dependencies

## Core Guarantees

* Deterministic output (byte-for-byte identical for identical inputs)
* Exact file content preservation
* Forward-slash relative path canonicalisation
* Length-prefixed record format
* Strict UTF-8 validation
* Explicit, deterministic error handling

## Repository Structure

* `SPEC.md` — Authoritative specification
* `SCENARIOS.feature` — Behaviour-level validation scenarios
* `treestream/` — Implementation package
* `tests/` — Scenario-driven test scaffolding
* `REVIEW.md` — Independent AI review artifact
* `TEST_REPORT.md` — Scenario execution report

## Development Model

TreeStream follows a specification-driven workflow:

1. Finalise specification
2. Define behaviour scenarios
3. Generate implementation
4. Review against specification
5. Execute scenarios
6. Produce structured test report

Implementation code must not be manually edited. Any behaviour changes require specification revision and regeneration.