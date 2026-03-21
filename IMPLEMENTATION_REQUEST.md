Implement the next TreeStream task: add exclusion filter support to the serialize command.

Goal
- Allow users to exclude files and directories by name-based glob patterns when serializing,
  enabling serialization of directories that contain binary or irrelevant files (e.g. __pycache__,
  .git) without triggering E4 errors or including unwanted content.

Required behavior (see SPEC.md v0.1.14, FR13 and Section 9.10)
- The serialize subcommand shall accept --exclude PATTERN (repeatable, zero or more times).
- Pattern matching uses Python's fnmatch.fnmatch applied to the entry name only (not the full path).
- If an entry's name matches any supplied pattern it is excluded:
  - For file entries: no record is written and no UTF-8 validation is performed.
  - For directory entries: the directory is not descended into and all its contents are skipped.
- Excluded entries produce no error output.
- Supplying no --exclude flag produces output byte-for-byte identical to prior behaviour.
- Determinism is preserved: identical directory + identical exclusion patterns → identical output.
- Pattern matching is case-sensitive (consistent with ordinal Unicode ordering used elsewhere).

Scope for this implementation task
- Update cli.py: add --exclude PATTERN argument (action="append", dest="exclude", default=[]).
- Update serialize() signature to accept exclude: list[str] | None = None.
- Update _collect_files() to filter entries by name against the exclusion patterns using fnmatch.
- Apply exclusion to both file and directory entries during traversal.
- Update version strings to v0.1.14.
- Add or update tests to cover:
  - --exclude by directory name (__pycache__, .git)
  - --exclude by file glob (*.pyc)
  - Multiple --exclude patterns
  - Non-matching --exclude produces identical output to no-exclusion run
  - Excluded directory subtree not descended (no records for any child)
  - Determinism: two runs with same exclusions are byte-for-byte identical
  - No --exclude flag: behaviour unchanged from prior versions

Constraints
- Python 3.11+ standard library only (fnmatch is stdlib)
- Windows semantics only
- Deterministic behaviour preserved
- Binary mode I/O preserved
- Format of serialized file unchanged; only which entries are included changes
- E4 still applies to non-excluded files that are not valid UTF-8

Deliverables
- Updated implementation code under IMPLEMENTATION/
- Updated automated tests covering the new exclusion filter behaviour
- TEST_REPORT.md evidence for the new exclusion scenarios
