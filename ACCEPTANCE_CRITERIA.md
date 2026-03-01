# TreeStream Acceptance Criteria (SPEC v0.1.9)

Version pin: **v0.1.9**

This document defines the **mandatory acceptance gates** for TreeStream against **SPEC.md v0.1.9**.  
**All five gates (A–E) must pass. Any single gate failing is an overall FAIL.**  
A reviewer must be able to verify each gate **using only the repository contents and local execution results**, without needing any knowledge of the generation process.

---

## Gate A — Scenario Validation (SCENARIOS.feature)

**Pass condition:**  
All scenarios defined in `SCENARIOS.feature` execute and pass with **zero failures** on a Windows environment using the repository's documented test runner and commands (as provided by the repository's test harness).

**Fail condition:**  
Any scenario fails, errors, is skipped, or cannot be executed.

**Evidence to capture:**  
- Test run output showing all scenarios passed.
- A `TEST_REPORT.md` entry or section that records:
  - Date/time (local), machine/environment summary (Windows version, Python version)
  - Command(s) executed
  - Result summary (passed/failed counts)

---

## Gate B — Deterministic Serialization Output (Byte-for-Byte)

**Objective:**  
For identical input directory trees, serialization must produce **byte-for-byte identical serialized files** across two runs.

### Fixed Determinism Fixture (must be used)

The determinism fixture is a directory tree located at:

`fixtures/determinism_v0.1.9/`

It must exist in the repo and contain **at minimum** the following structure and content characteristics (the fixture contents must be committed and not altered during verification):

**Required structure (minimum depth 3):**
- At least **3 directory levels deep** somewhere in the tree.
- At least **8 files** total across multiple directories.

**Required file diversity:**
- At least **one empty file** (`CONTENT_BYTES: 0` expected).
- At least **one small file** (1–20 bytes).
- At least **one medium file** (200–2,000 bytes).
- At least **one larger file** (10,000+ bytes).
- At least **one file containing Windows CRLF bytes** (`\r\n`) in its content.
- At least **one file containing non-ASCII Unicode** (e.g., `Ω`, `漢`, emoji), valid UTF-8.
- At least **one file containing the Unicode NULL character** `U+0000` somewhere in the text content (valid UTF-8).

**Required naming/path diversity:**
- At least one file path with spaces in a component (e.g., `notes and drafts/`).
- At least one path that would differ only by case if duplicated (to ensure the fixture does **not** contain case-colliding duplicates). The fixture must not include two files whose relative paths are identical under case-insensitive comparison.

### Verification procedure (must be followed exactly)

1. Delete any previous outputs:
   - `artifacts/serialize_run1.treestream`
   - `artifacts/serialize_run2.treestream`

2. Run serialization twice on the **same fixture directory**:
   - Run 1 output path: `artifacts/serialize_run1.treestream`
   - Run 2 output path: `artifacts/serialize_run2.treestream`

3. Compare outputs as raw bytes (not text diff):
   - Compute and record a cryptographic hash for both outputs (e.g., SHA-256).
   - Additionally, perform a binary compare.

**Pass condition:**  
- The two serialized outputs are **exactly identical byte-for-byte**, proven by:
  - Equal SHA-256 hashes, and
  - A successful binary compare (no differing bytes).

**Fail condition:**  
Any byte differs between the two serialized outputs.

**Evidence to capture:**  
- Commands used to serialize twice.
- Hash values for both outputs (must match).
- Binary compare result (must indicate identical).

---

## Gate C — Round-Trip Integrity (Fixed Non-Trivial Fixture)

**Objective:**  
Reconstruction of a serialized directory must reproduce the original tree exactly in **structure and file contents**, for a fixture fixed in advance.

### Fixed Round-Trip Fixture (must be used)

The round-trip fixture is a directory tree located at:

`fixtures/roundtrip_v0.1.9/`

It must exist in the repo and contain **at minimum**:

- At least **3 directory levels deep** somewhere in the tree.
- At least **10 files** total.
- At least **one empty file**.
- At least **one file containing CRLF bytes**.
- At least **one file containing non-ASCII Unicode** (valid UTF-8).
- At least **one file size over 10,000 bytes**.
- At least **two sibling directories** each containing at least two files (to validate multi-branch traversal and reconstruction).

The fixture contents must be **committed** and must not be altered during verification.

### Verification procedure (must be followed exactly)

1. Serialize the fixture directory:
   - Input: `fixtures/roundtrip_v0.1.9/`
   - Output: `artifacts/roundtrip_source.treestream`

2. Reconstruct into a fresh target directory:
   - Target: `artifacts/roundtrip_reconstructed/`
   - Ensure the target directory does not exist before reconstruction begins (delete it if present).

3. Compare the original fixture tree to the reconstructed tree:
   - The comparison must verify:
     - Identical relative path set (same files, same directories implied by those files)
     - Identical file contents **byte-for-byte** for every file
   - Comparison must not rely on timestamps or filesystem metadata.

**Pass condition:**  
- Every file in the original fixture exists in the reconstructed tree at the same relative path, and
- Every file's content matches **exactly** as bytes, and
- No extra files exist in the reconstructed tree beyond those implied by the serialized file.

**Fail condition:**  
Any missing file, extra file, path mismatch, or any byte-level content mismatch.

**Evidence to capture:**  
- Commands used for serialize and reconstruct.
- A recorded directory listing of both trees (relative paths).
- A byte-level verification result (hash or binary compare per file, or an equivalent deterministic script output).

---

## Gate D — Format Conformance to SPEC.md v0.1.9

**Objective:**  
The serialized output format must conform **exactly** to `SPEC.md v0.1.9`, including header, record structure, declared content lengths, and structural LF usage.

### Header conformance checks

A serialized file must begin with these exact header lines in order (LF line endings), matching `SPEC.md v0.1.9`:

- `TREESTREAM 1`
- `SPEC_VERSION: v0.1.9`
- `ENCODING: UTF-8`
- `NEWLINES: LF`
- `RECORDS: FILE`
- `END_HEADER`

**Pass condition:**  
Header matches exactly, including:
- Exact spelling and casing
- Exact spacing (e.g., `KEY: VALUE` with one space after colon where required)
- **LF-only** for all structural line endings (0x0A), no CRLF translation

### Record structure checks (each file record)

Each record must follow the exact structure defined in `SPEC.md v0.1.9` Section 5.5:

1. `FILE`
2. `PATH: <relative_path>`
3. `CONTENT_BYTES: <non_negative_integer>`
4. `BEGIN_CONTENT`
5. Exactly `CONTENT_BYTES` bytes of content
6. A single structural LF byte (0x0A) following the content bytes
7. `END_CONTENT` (LF-terminated)
8. `END_FILE` (LF-terminated)

Additional required checks:
- Records appear sorted by `PATH` in ordinal Unicode code point order (case-sensitive) as a flat string.
- No extra blank lines between records.
- After the final `END_FILE` line terminator, the file must end (no extra bytes).

**Pass condition:**  
A reviewer can validate, by inspection and/or a deterministic validator script, that:
- Header matches exactly.
- All structural newlines are LF bytes.
- Each record matches the required marker order and spacing rules.
- Each `CONTENT_BYTES` equals the exact number of bytes in the content block.
- Record ordering is correct.
- End-of-file contains no trailing bytes beyond the last record terminator.

**Fail condition:**  
Any deviation from the spec structure, markers, spacing, ordering, content length, structural newlines, or trailing bytes.

**Evidence to capture:**  
- A validation output proving:
  - Header exact match
  - LF-only structural lines
  - Record marker order integrity
  - Content-length correctness
  - Correct ordering by PATH
  - No trailing bytes after final record

---

## Gate E — Error Handling and E-Code Mapping to SPEC.md

**Objective:**  
Observed error behavior must map to the error codes and conditions defined in `SPEC.md v0.1.9`, and messages must be explicit.

### Scope

This gate applies to both operations:
- Serialization errors (E1–E5)
- Reconstruction errors (E6–E11)

### Verification requirements

1. The repository must contain a **documented mapping** from error conditions to:
   - The SPEC-defined E-code
   - The triggering condition
   - The required message elements (operation + path/file where applicable + condition)

2. Verification must be performed using **predefined negative fixtures** committed in the repo under:
- `fixtures/errors_v0.1.9/`

Negative fixtures must be designed so the triggering condition is deterministic and reproducible.

3. For each tested error case:
- The observed error must include the correct E-code (exactly) and an explicit message.
- The reviewer must verify correctness by **diffing the observed behavior against SPEC.md definitions**, not merely confirming the error exists.

### Pass condition

For each executed negative test case:
- The operation fails as required.
- The emitted E-code matches the SPEC-defined code for that condition.
- The error message is explicit and includes:
  - Operation name (serialization or reconstruction)
  - The path/file involved where applicable
  - The specific condition that caused failure (aligned with the relevant SPEC clause)

### Fail condition

Any of the following:
- Wrong E-code
- Missing E-code
- Vague message that does not identify operation/path/condition where applicable
- Non-deterministic failure stage for identical inputs
- "Silent" behavior (e.g., skipping files, partial success treated as success)
- Errors classified in a way that does not align to SPEC definitions

**Evidence to capture:**
- For each negative test case:
  - Command executed
  - Fixture used
  - Full error output (captured verbatim)
  - A short verification note referencing the SPEC clause and why the code/message match

---

## Reviewer Notes (Gotchas and Audit Checks)

### Notes for Gate B (Determinism)
- Determinism must be assessed on **raw bytes** of the serialized file, not text-normalized output.
- Ensure the serializer writes in binary mode and does not introduce platform-dependent newline translation.
- The fixture must remain unchanged between runs; verify via `git status` clean and/or fixture hashing.
- Record ordering must be stable and derived from sorted `PATH` strings, not filesystem enumeration order.

### Notes for Gate C (Round-Trip Integrity)
- The "non-trivial fixture" is **fixed** by this document: only `fixtures/roundtrip_v0.1.9/` is valid for Gate C.
- Comparison must be byte-level for file contents (hashing per file is acceptable).
- Ignore filesystem metadata; only paths and contents matter.
- Ensure reconstruction does not create extra files beyond those in the serialized representation.

### Notes for Gate E (E-code Mapping)
- The reviewer must verify **correctness** by comparing observed failures to SPEC-defined conditions (E1–E11), not by checking that "an error happened."
- Be careful with ambiguous OS-dependent errors:
  - The fixture design must make the triggering condition deterministic (e.g., explicit invalid PATH in serialized file for E9; explicit header mismatch for E7).
- Ensure the implementation does not "auto-recover" (e.g., skipping invalid entries) because the spec prohibits silent fallback.
- The message must name the operation and identify the failing path/file when applicable; generic stack traces without an explicit TreeStream error classification are insufficient.

---

## Acceptance Decision

**ACCEPTED** only if Gates **A, B, C, D, and E** are all **PASS** with captured evidence.  
Otherwise: **REJECTED**.
