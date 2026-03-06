Regenerate TreeStream implementation to conform to SPEC.md v0.1.9.

Read the following files:
- SPEC.md
- REVIEW.md
- SCENARIOS.feature
- ACCEPTANCE_CRITERIA.md

Use REVIEW.md as the authoritative list of required fixes.

Required fixes:

CRITICAL FIX (must implement exactly):

During reconstruction, do NOT enforce any requirement that records are sorted by PATH. Remove any check that raises E6 for "records are not sorted by PATH".

Instead:
- Parse the Serialized File records sequentially as per Section 6.3.
- For each record, extract the raw PATH value and validate it per Section 6.4.
- Additionally, perform a GLOBAL case-insensitive Unicode collision check across ALL PATH values in the file:
  - Collect all PATH values encountered.
  - If any two PATH values are identical under case-insensitive comparison, terminate with E9.
- This E9 collision detection must not be pre-empted by any ordering validation.

Acceptance criteria:
- fixtures/errors_v0.1.9/recon_E9_case_collision.treestream must fail with E9 (not E6).
- No E6 should be raised solely due to record ordering.
- Keep all other behavior unchanged.

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