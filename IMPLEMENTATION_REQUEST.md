Implement the next TreeStream task: add `.treestreamignore` support to the serialize command.

Goal
- Allow users to place a `.treestreamignore` file in the root of the directory being serialized.
  Patterns in that file are merged with any `--exclude` patterns and applied together, so that
  binary or unwanted files can be excluded without modifying the CLI invocation each time.

Required behaviour (see SPEC.md v0.1.16, FR14 and Sections 9.11, 7.2)

Reading the ignore file
- Before traversal begins, check whether a file named `.treestreamignore` exists directly in the
  Root Directory (not in any subdirectory).
- If it does not exist, proceed with exactly the same behaviour as v0.1.15 (no change).
- If it exists, read it as UTF-8 (strict error handler). If it cannot be decoded as UTF-8,
  terminate serialization with E13 (Ignore File Read Error — see Section 7.2). The error message
  must clearly identify `.treestreamignore` as the source of the failure and state that it could
  not be read as UTF-8. Do NOT raise E4 for this condition — E4 applies only to content files
  encountered during traversal.
- Process lines as follows:
  - Strip the line terminator only (do not strip other whitespace from the pattern itself).
  - Lines that are empty after stripping the terminator: ignore.
  - Lines whose first character is `#`: ignore (comment lines).
  - All other lines: treat the entire line content (after stripping only the terminator) as an
    Exclusion Pattern.

Merging patterns
- The effective Exclusion Pattern set is the union of:
  - Patterns from `--exclude` (zero or more, as in v0.1.15).
  - Patterns extracted from `.treestreamignore` (zero or more, as above).
- The two sources are combined before traversal. No precedence or deduplication is required;
  duplicates are harmless given that `fnmatch` matching is already O(patterns × entries).
- The matching semantics are identical to existing `--exclude` behaviour: `fnmatch.fnmatch`
  applied to the entry name only (not the full relative path), case-sensitively.

Auto-exclusion of `.treestreamignore` itself
- `.treestreamignore` shall never appear as a record in the Serialized File.
- This exclusion is unconditional: apply it regardless of the file's contents and regardless of
  whether any pattern in the effective set would independently match it.
- Implementation note: the simplest approach is to add `.treestreamignore` to the effective
  exclusion set before traversal, or to check for it explicitly during traversal. Either approach
  is acceptable provided the guarantee holds.

Subdirectory ignore files are not recognised
- A file named `.treestreamignore` located in any subdirectory of the Root Directory must be
  treated as a normal file. It is subject to the same serialization rules as any other file.
  Do not read it as an ignore file. Do not auto-exclude it.

E13 — Ignore File Read Error (new error code)
- E13 is a new serialization-time error code introduced in SPEC.md v0.1.16 (Section 7.2).
- It is triggered exclusively when `.treestreamignore` exists at the Root Directory but cannot be
  read as UTF-8 text (strict error handler).
- E13 is distinct from E4: E4 applies to content files during traversal; E13 applies only to the
  `.treestreamignore` configuration file read before traversal begins.
- The error message must:
  - Identify the operation (serialization).
  - Name `.treestreamignore` as the source of the failure.
  - State that the file could not be read as UTF-8.
- When E13 is raised, no output file shall be written (the atomic output guarantee of Section 7.2
  applies: the temporary file is deleted and the designated output path is not created or modified).

Version strings
- Update all version strings in the implementation to `v0.1.16`.

Scope for this implementation task
- Update `serialize()` (or equivalent entry point) to read and parse `.treestreamignore` from
  the Root Directory before calling the traversal/collection logic.
- Merge the parsed patterns into the effective exclusion set alongside any `--exclude` patterns.
- Ensure `.treestreamignore` at the root is never emitted as a record.
- Raise E13 (not E4) when `.treestreamignore` cannot be decoded as UTF-8.
- Update version strings to `v0.1.16`.
- Add or update automated tests to cover (all tests must pass on Windows with Python 3.11+):
  - `.treestreamignore` present with at least one matching file pattern — matched file absent from output.
  - `.treestreamignore` present with at least one matching directory pattern — no records for any
    file under that directory in the output, and the directory is not descended into.
  - `.treestreamignore` containing comment lines (beginning with `#`) — comments do not cause any
    entry to be excluded.
  - `.treestreamignore` containing blank lines — blank lines do not cause any entry to be excluded.
  - `.treestreamignore` absent — output byte-for-byte identical to prior-version behaviour.
  - `.treestreamignore` present (empty file) — output byte-for-byte identical to a run with no
    `.treestreamignore` present (accounting for the fact that `.treestreamignore` itself is absent
    from both outputs).
  - `.treestreamignore` and `--exclude` both present — entries matching patterns from each source
    are both absent from the output; entries matching neither source are present.
  - `.treestreamignore` itself is never a record in the output, regardless of its content.
  - `.treestreamignore` in a subdirectory is serialized as a normal file (not treated as an ignore
    file), provided it is valid UTF-8 and not otherwise excluded.
  - Determinism: two runs with the same directory and the same `.treestreamignore` content produce
    byte-for-byte identical output.
  - `.treestreamignore` that is not valid UTF-8 triggers E13, identifies `.treestreamignore` in
    the error message, and leaves no output file written. Verify that E4 is NOT raised.

Constraints
- Python 3.11+ standard library only. No external packages.
- Windows semantics only.
- Deterministic behaviour preserved.
- Binary mode I/O for the Serialized File preserved.
- The serialized format is unchanged; only which entries are included changes.
- E4 still applies to non-excluded, non-`.treestreamignore` files that are not valid UTF-8.
- E13 applies only to `.treestreamignore` at the Root Directory level; a `.treestreamignore` in a
  subdirectory that contains non-UTF-8 bytes is subject to E4 like any other content file.
- The implementation agent chooses how to structure the code (function names, module layout, etc.)
  within the existing `IMPLEMENTATION/` directory, subject to the constraints above.

Deliverables
- Updated implementation code under `IMPLEMENTATION/`.
- Updated automated tests covering all scenarios listed above (including S36 — E13 on non-UTF-8
  `.treestreamignore`).
- `TEST_REPORT.md` evidence showing all scenarios (including the new S30–S36) pass.
