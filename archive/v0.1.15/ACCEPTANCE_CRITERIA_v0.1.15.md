# TreeStream Acceptance Criteria (SPEC v0.1.15)

Version pin: **v0.1.15**

This document defines the **mandatory acceptance gates** for TreeStream against **SPEC.md v0.1.15**.
**All eight gates (A–H) must pass. Any single gate failing is an overall FAIL.**
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

`fixtures/determinism/`

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

`fixtures/roundtrip/`

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
   - Input: `fixtures/roundtrip/`
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

## Gate D — Format Conformance to SPEC.md v0.1.15

**Objective:**
The serialized output format must conform **exactly** to `SPEC.md v0.1.15`, including header, record structure, base64-encoded content blocks, declared original content lengths, and structural LF usage.

### Header conformance checks

A serialized file must begin with these exact header lines in order (LF line endings), matching `SPEC.md v0.1.15`:

- `TREESTREAM 1`
- `SPEC_VERSION: v0.1.15`
- `ENCODING: UTF-8`
- `NEWLINES: LF`
- `RECORDS: FILE`
- `ROOT_NAME: <directory_name>`
- `END_HEADER`

**Pass condition:**
Header matches exactly, including:
- Exact spelling and casing
- Exact spacing (e.g., `KEY: VALUE` with one space after colon where required)
- **LF-only** for all structural line endings (0x0A), no CRLF translation
- `ROOT_NAME` present and non-empty, value contains no path separators (`/` or `\`)

### Record structure checks (each file record)

Each record must follow the exact structure defined in `SPEC.md v0.1.15` Section 5.5:

1. `FILE`
2. `PATH: <relative_path>`
3. `CONTENT_BYTES: <non_negative_integer>`
4. `BEGIN_CONTENT`
5. A base64-encoded content block (RFC 4648 standard alphabet, no line wrapping); the decoded byte count must equal `CONTENT_BYTES`
6. A single structural LF byte (0x0A) following the content block
7. `END_CONTENT` (LF-terminated)
8. `END_FILE` (LF-terminated)

Additional required checks:
- Records appear sorted by `PATH` in ordinal Unicode code point order (case-sensitive) as a flat string.
- No extra blank lines between records.
- After the final `END_FILE` line terminator, trailing blank lines (LF or CRLF sequences only) shall be permitted and ignored. Any non-blank bytes after the final record shall cause rejection with E6.

**Pass condition:**
A reviewer can validate, by inspection and/or a deterministic validator script, that:
- Header matches exactly.
- All structural newlines are LF bytes.
- Each record matches the required marker order and spacing rules.
- Each content block contains valid standard Base64 (RFC 4648, no line wrapping).
- The decoded byte count of each content block equals its `CONTENT_BYTES` value.
- `CONTENT_BYTES` reflects the original (pre-encoding) file byte count, not the base64-encoded length.
- Record ordering is correct.
- Trailing blank lines (LF or CRLF sequences only) after the final `END_FILE` are permitted and ignored; any non-blank trailing bytes cause rejection with E6.

**Fail condition:**
Any deviation from the spec structure, markers, spacing, ordering, base64 encoding, content length, structural newlines, or trailing bytes.

**Evidence to capture:**
- A validation output proving:
  - Header exact match
  - LF-only structural lines
  - `ROOT_NAME` value matches the serialized root directory name
  - Record marker order integrity
  - Base64 validity and no line wrapping for each content block
  - Decoded content length matches `CONTENT_BYTES` for each record
  - Correct ordering by PATH
  - Trailing blank lines after final record are tolerated; non-blank trailing bytes are rejected with E6

---

## Gate E — Error Handling and E-Code Mapping to SPEC.md

**Objective:**
Observed error behavior must map to the error codes and conditions defined in `SPEC.md v0.1.15`, and messages must be explicit.

### Scope

This gate applies to both operations:
- Serialization errors (E1–E5, E5a)
- Reconstruction errors (E6–E12)

### Verification requirements

1. The repository must contain a **documented mapping** from error conditions to:
   - The SPEC-defined E-code
   - The triggering condition
   - The required message elements (operation + path/file where applicable + condition)

2. Verification must be performed using **predefined negative fixtures** committed in the repo under:
- `fixtures/errors/`

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

## Gate F — CRLF Tolerance for Reconstruction Input

**Objective:**
Validate the core transport workflow where serialized plain text is passed through channels (email body or clipboard) that may convert structural newlines from LF to CRLF.

### Verification procedure (must be followed exactly)

1. Start with a valid LF-only serialized file produced by TreeStream.
2. Create a CRLF-variant of that payload that changes only structural line endings from LF to CRLF.
   - Content bytes inside each `BEGIN_CONTENT`/`END_CONTENT` block must remain unchanged.
3. Reconstruct from both inputs:
   - Original LF payload
   - CRLF-variant payload
4. Create a trailing-blank-lines variant by appending one or more blank lines after the final `END_FILE` line of the LF payload.
5. Reconstruct from the trailing-blank-lines variant and verify it succeeds.
6. Compare all reconstructed directory trees:
   - Identical relative path set
   - Byte-for-byte identical file contents
7. Re-serialize at least one reconstructed output and verify serialized structural newlines are LF-only.

**Pass condition:**
- Reconstruction succeeds for LF, CRLF structural-input, and trailing-blank-lines variants.
- All reconstructed trees are byte-for-byte identical.
- Serialization output remains LF-only.

**Fail condition:**
Any reconstruction failure caused by CRLF structural input or trailing blank lines, any content/path mismatch between variants, or any serializer output containing structural CRLF.

**Evidence to capture:**
- Commands/scripts used to generate CRLF-variant and trailing-blank-lines-variant inputs.
- Reconstruction outputs for all three input variants.
- Byte-level comparison result of reconstructed trees.
- Verification output demonstrating LF-only structural newlines in serializer output.

---

## Gate G — Exclusion Filter (FR13, Section 9.10)

**Objective:**
Validate that the `--exclude` option correctly omits matching files and directories from serialization without altering the format or breaking determinism.

### Verification requirements

1. The `serialize` command shall accept `--exclude PATTERN` (repeatable). Supplying no `--exclude` flag shall produce output identical to the behaviour of prior versions.

2. Verification must use a test directory that contains:
   - At least one text file that should be included.
   - At least one directory whose name matches an exclusion pattern (e.g., `__pycache__`) containing files.
   - At least one file whose name matches an exclusion pattern (e.g., `*.pyc`).

3. Run serialization with the appropriate `--exclude` flags and verify:
   - Excluded files produce no record in the serialized output.
   - Excluded directories produce no records for any files they contain.
   - Included files are present with correct content.

4. Run serialization twice with identical inputs and identical `--exclude` flags and verify byte-for-byte identical output (determinism with exclusions).

5. Run serialization with `--exclude` patterns that match nothing in the input directory. Verify the output is byte-for-byte identical to the same serialization without any `--exclude` flag.

### Pass condition

- The `--exclude` flag is accepted by the CLI.
- Entries matching an exclusion pattern are absent from the serialized output.
- No error is raised for excluded entries regardless of their content type.
- Excluded directory subtrees are not descended into.
- Output with exclusions is a valid TreeStream file conforming to Sections 5 and 8.
- Two runs with identical inputs and identical exclusion patterns produce byte-for-byte identical output.
- A run with non-matching exclusion patterns is byte-for-byte identical to a run with no exclusions.

### Fail condition

Any of the following:
- Excluded entries appear as records in the output.
- An error is raised for a correctly excluded entry.
- Included entries are missing from the output.
- Output is not a valid TreeStream file.
- Determinism is broken when exclusion patterns are supplied.

**Evidence to capture:**
- Command(s) used, including `--exclude` arguments.
- Directory listing of test input showing both included and excluded entries.
- Serialized output listing showing records present (included) and absent (excluded).
- Hash comparison proving determinism across two runs with identical exclusions.
- Hash comparison proving identical output between a non-matching-exclusion run and a no-exclusion run.

---

## Reviewer Notes (Gotchas and Audit Checks)

### Notes for Gate B (Determinism)
- Determinism must be assessed on **raw bytes** of the serialized file, not text-normalized output.
- Ensure the serializer writes in binary mode and does not introduce platform-dependent newline translation.
- The fixture must remain unchanged between runs; verify via `git status` clean and/or fixture hashing.
- Record ordering must be stable and derived from sorted `PATH` strings, not filesystem enumeration order.

### Notes for Gate C (Round-Trip Integrity)
- The "non-trivial fixture" is **fixed** by this document: only `fixtures/roundtrip/` is valid for Gate C.
- Comparison must be byte-level for file contents (hashing per file is acceptable).
- Ignore filesystem metadata; only paths and contents matter.
- Ensure reconstruction does not create extra files beyond those in the serialized representation.

### Notes for Gate E (E-code Mapping)
- The reviewer must verify **correctness** by comparing observed failures to SPEC-defined conditions (E1–E5, E5a, E6–E12), not by checking that "an error happened."
- Be careful with ambiguous OS-dependent errors:
  - The fixture design must make the triggering condition deterministic (e.g., explicit invalid PATH in serialized file for E9; explicit header mismatch for E7).
- **E5a**: Triggered at serialization time when the root directory name has leading or trailing whitespace. The triggering fixture must use a directory whose final path component has leading or trailing whitespace.
- **E7 (expanded)**: Now also covers a missing or invalid `ROOT_NAME` header field during reconstruction. A fixture with a header that omits `ROOT_NAME`, or supplies an empty/separator-containing value, must trigger E7.
- Ensure the implementation does not "auto-recover" (e.g., skipping invalid entries) because the spec prohibits silent fallback.
- The message must name the operation and identify the failing path/file when applicable; generic stack traces without an explicit TreeStream error classification are insufficient.

### Notes for Gate F (CRLF Tolerance)
- CRLF tolerance applies only to structural parsing in reconstruction input.
- Content blocks are opaque bytes and must not be newline-normalized.
- Validation should explicitly prove that serializer output is still LF-only after successful reconstruction.

### Notes for Gate H (.treestreamignore)
- The `.treestreamignore` file must never appear as a record in the serialized output regardless of its contents.
- Verify the merge behaviour by confirming that patterns from both `--exclude` and `.treestreamignore` suppress the correct entries.
- An empty `.treestreamignore` must not change the output compared to no ignore file being present.
- Comment lines (beginning with `#`) and blank lines must never be treated as patterns.
- Determinism must hold: identical `.treestreamignore` content and identical `--exclude` flags produce byte-for-byte identical output across runs.
- A `.treestreamignore` in a subdirectory must not be recognised as an ignore file; it must be serialized normally (unless excluded by another pattern).

---

## Gate H — Ignore File Support (FR14, Section 9.11)

**Objective:**
Validate that `.treestreamignore` is correctly read, parsed, and applied during serialization, and that the file itself is never serialized.

### Verification requirements

1. The root directory must contain a `.treestreamignore` file for positive tests. The file must not be present (or must be removed) for baseline comparison runs.

2. Verification must cover:
   - At least one text file whose name matches a pattern in `.treestreamignore` — that file must be absent from the serialized output.
   - At least one directory whose name matches a pattern in `.treestreamignore` — no records for any of its contents must appear in the serialized output.
   - At least one text file whose name does not match any pattern — that file must be present in the serialized output.
   - Comment lines (lines beginning with `#`) and blank lines in `.treestreamignore` must not be treated as patterns.
   - An empty `.treestreamignore` must produce output byte-for-byte identical to serializing the same directory with no `.treestreamignore` present.
   - `.treestreamignore` itself must not appear as a record in the serialized output.

3. Merge verification: serialize a directory with both a `.treestreamignore` containing one set of patterns and `--exclude` supplying a different pattern. Verify that both pattern sets suppress their respective entries and that included entries are present.

4. Determinism: run serialization twice on the same directory with the same `.treestreamignore` and the same `--exclude` flags. Verify byte-for-byte identical output.

5. Subdirectory ignore files are not recognised: place a `.treestreamignore` file inside a subdirectory. Verify it is serialized as a normal file (assuming it is valid UTF-8 and not otherwise excluded).

### Pass condition

- Entries matching patterns from `.treestreamignore` are absent from the serialized output.
- No error is raised for entries excluded via `.treestreamignore`.
- `.treestreamignore` itself is absent from the serialized output in all cases.
- Comment lines and blank lines in `.treestreamignore` produce no exclusion effect.
- An empty `.treestreamignore` produces byte-for-byte identical output to a run with no `.treestreamignore`.
- Patterns from `.treestreamignore` and `--exclude` are merged and both are applied.
- Serialization with a `.treestreamignore` is deterministic (byte-for-byte identical across two runs).
- A `.treestreamignore` in a subdirectory is treated as a normal file and serialized (unless separately excluded).
- Output is a valid TreeStream file conforming to Sections 5 and 8.

### Fail condition

Any of the following:
- A `.treestreamignore` pattern fails to exclude a matching entry.
- `.treestreamignore` itself appears as a record in the serialized output.
- A comment or blank line in `.treestreamignore` causes an entry to be incorrectly excluded.
- An empty `.treestreamignore` changes the serialized output compared to no ignore file.
- Patterns from `--exclude` or `.treestreamignore` are not applied when both are present.
- Determinism is broken across two runs with the same inputs.
- A `.treestreamignore` in a subdirectory is silently ignored rather than serialized.
- Output is not a valid TreeStream file.

**Evidence to capture:**
- Directory listing of the test input showing included entries, excluded entries, and the `.treestreamignore` file.
- Content of the `.treestreamignore` file used.
- Serialized output listing confirming presence of included records and absence of excluded records and the `.treestreamignore` record.
- For the merge test: `--exclude` flag(s) used alongside `.treestreamignore` content, showing both pattern sources suppress their respective entries.
- For the empty-file test: byte-level comparison result proving identical output to the no-ignore-file baseline.
- Hash comparison proving determinism across two runs with identical inputs.
- Evidence that a `.treestreamignore` in a subdirectory is serialized normally.

---

## Acceptance Decision

**ACCEPTED** only if Gates **A, B, C, D, E, F, G, and H** are all **PASS** with captured evidence.
Otherwise: **REJECTED**.
