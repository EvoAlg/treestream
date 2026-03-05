Regenerate TreeStream implementation to conform to SPEC.md v0.1.9.

Read the following files:
- SPEC.md
- REVIEW.md
- SCENARIOS.feature
- ACCEPTANCE_CRITERIA.md

Use REVIEW.md as the authoritative list of required fixes.

Required fixes:

1. Raw PATH validation
The implementation must validate PATH values before constructing any path object.

Algorithm:
- Extract raw PATH value
- Split on "/"
- Reject if any component equals "." or ".." or "" (empty string)
- Reject if "\" appears in the path
- Only after validation construct PureWindowsPath

2. Strict PATH metadata parsing
The PATH metadata line must match exactly:

PATH: <value>

Rules:
- Prefix must be exactly "PATH: "
- Reject if the value is empty
- Reject if value != value.strip()
- Reject malformed forms such as:
  PATH:file.txt
  PATH:  file.txt
  PATH: file.txt 

Constraints:
- Python 3.11+
- Standard library only
- Windows-only filesystem semantics
- Do not change unrelated behaviour

Write the updated implementation under IMPLEMENTATION/.
Overwrite the existing generated files.

3. Case-insensitive PATH collision must be detected as E9 before any reconstruction ordering check.
If the implementation currently enforces sorted-order during reconstruction, collision detection must occur first so colliding paths always emit E9 even when records are unsorted.