You are performing an independent implementation review for the TreeStream project.

Specification:
Read and treat SPEC.md (version v0.1.9) as the authoritative source of truth.

Implementation:
Review all Python files under the IMPLEMENTATION directory.

Your task is to determine whether the implementation fully conforms to the specification.

Review requirements:

1. Verify all Functional Requirements (FR1–FR12).
2. Verify all Non-Functional Requirements (NFR1–NFR13).
3. Verify the serialization format in Section 5 exactly matches the specification.
4. Verify reconstruction rules in Section 6.
5. Verify error handling rules in Section 7.
6. Verify determinism requirements in Section 8.
7. Verify constraints in Section 9.

Important rules:

- Do not assume behavior.
- Only report what the code actually does.
- Quote specification sections where violations occur.

Output format:

Produce a structured review report with the following sections:

SUMMARY

CONFORMANCE CHECK
- Functional Requirements
- Non-Functional Requirements
- Serialization Format
- Reconstruction Rules
- Error Handling
- Determinism

DETECTED ISSUES
Each issue must include:
- Severity (Critical / Major / Minor)
- Specification section
- Explanation
- Suggested correction

FINAL VERDICT
One of:
PASS
PASS WITH MINOR ISSUES
FAIL

Write the report to REVIEW.md.