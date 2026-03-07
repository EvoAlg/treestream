Implement the next TreeStream task focused on the primary transport workflow:

Goal
- Support end-to-end directory -> .treestream -> plain-text email/clipboard body -> reconstruction.

Required behavior
- Reconstruction must accept structural CRLF (\r\n) line endings in input and normalize them to logical LF for parsing.
- Serialization output must remain LF-only for all structural lines.
- CRLF normalization applies only to structural markers/newlines; content bytes remain opaque and must not be modified.
- E6 behavior must reflect the relaxed reconstruction parser rules (CRLF accepted; invalid standalone CR still rejected).

Scope for this implementation task
- Update parser logic under IMPLEMENTATION/ to support CRLF-tolerant reconstruction input.
- Add or update tests to cover:
  - Email-style CRLF conversion round-trip
  - Clipboard CRLF conversion round-trip
  - LF-only serialization output invariant
  - Negative case: standalone CR in structural regions rejected with E6

Constraints
- Python 3.11+ standard library only
- Windows semantics only
- Deterministic behavior preserved
- Binary mode I/O preserved
- Length-prefixed parsing remains governed strictly by CONTENT_BYTES

Deliverables
- Updated implementation code under IMPLEMENTATION/
- Updated automated tests covering the new workflow
- TEST_REPORT.md evidence for the new CRLF-tolerance scenarios and invariants
