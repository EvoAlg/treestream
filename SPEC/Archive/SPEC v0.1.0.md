# TreeStream Specification
Version: v0.1.0
Status: Draft

## 1. Purpose

TreeStream is a deterministic directory serialization and reconstruction tool for text-based file systems.

It converts a root directory containing text files into a single structured UTF-8 text representation that preserves relative paths and exact file contents.

It also reconstructs the original directory structure and file contents from that structured text representation.
## 2. Definitions

**Root Directory**  
The top-level directory provided as input to the serialization process.  
All processed files and subdirectories must exist within this directory.

**Directory Tree**  
The hierarchical structure consisting of the root directory, its subdirectories, and all contained files.

**Text File**  
A file whose contents are valid UTF-8 encoded text.  
Binary files are out of scope.

**Relative Path**  
The path of a file or subdirectory expressed relative to the root directory, using forward slashes (/) as separators regardless of operating system.

**Serialized Representation**  
A single UTF-8 encoded text file produced by TreeStream that contains the structured representation of the directory tree, including relative paths and exact file contents.

**Serialization**  
The deterministic transformation of a directory tree into a serialized representation.

**Serialized File**  
The single UTF-8 encoded text file written by TreeStream during serialization.  
It contains the serialized representation of the input directory tree.

**Reconstruction**  
The deterministic transformation of a serialized representation back into a directory tree.

**Deterministic**  
A property whereby identical inputs produce byte-for-byte identical outputs across executions and supported platforms.

**Overwrite Mode**  
A configurable behaviour that determines whether existing files in the target reconstruction directory may be replaced.

**Target Directory**  
The directory into which a serialized representation is reconstructed.

**Round-Trip Integrity**  
The property that reconstruct(serialize(directory)) produces a directory tree identical to the original, including structure and file contents.
## 3. Functional Requirements

**FR1 — Root Directory Input**  
The system shall accept a root directory path as input for serialization.

**FR2 — Recursive Traversal**  
The system shall recursively traverse all subdirectories within the root directory.

**FR3 — Text File Inclusion**  
The system shall include all UTF-8 text files within the directory tree in the serialized output.

**FR4 — Relative Path Preservation**  
The system shall preserve each file’s relative path from the root directory in the serialized representation.

**FR5 — Exact Content Preservation**  
The system shall preserve file contents exactly, without modification, trimming, normalization, or transformation.

**FR6 — Deterministic Ordering**  
The system shall process files and directories in a deterministic and platform-independent order.

**FR7 — Single Serialized File Output**  
The system shall produce exactly one Serialized File per serialization operation.

**FR8 — Reconstruction Input**  
The system shall accept a Serialized File as input for reconstruction.

**FR9 — Directory Structure Reconstruction**  
The system shall recreate the directory structure described in the Serialized File within a specified target directory.

**FR10 — File Content Reconstruction**  
The system shall recreate each file with contents identical to those contained in the Serialized File.

**FR11 — Overwrite Behaviour**  
The system shall support configurable overwrite behaviour during reconstruction.  
If overwrite mode is disabled, existing files shall not be replaced.

**FR12 — Round-Trip Integrity**  
Serializing a directory and subsequently reconstructing it shall produce a directory tree identical in structure and file contents to the original.

## 4. Non-Functional Requirements

**NFR1 — Determinism**  
The system shall produce byte-for-byte identical Serialized Files for identical input directory trees across executions on supported Windows environments.

**NFR2 — Encoding Standard**  
All Serialized Files shall be encoded in UTF-8 without byte order mark (BOM).

**NFR3 — Target Platform**  
The system shall operate on Microsoft Windows environments only for Version 1.

**NFR4 — Windows Filesystem Semantics**  
The system shall interpret paths and filesystem behaviour according to Windows filesystem rules.

**NFR5 — Path Normalisation**  
Relative paths within the Serialized Representation shall use forward slashes (/) as separators, regardless of Windows native path separator conventions.

**NFR6 — No Source Modification**  
The system shall not modify, rename, or alter any files within the input root directory during serialization.

**NFR7 — Error Transparency**  
All errors shall be explicit and descriptive. Silent failures are prohibited.

**NFR8 — Predictable Failure Behaviour**  
The system shall fail deterministically when encountering unsupported files, permission errors, or encoding violations.

**NFR9 — Standard Library Constraint**  
The implementation shall use only the Python 3.11+ standard library.

**NFR10 — Resource Predictability**  
The system shall not perform unbounded memory growth beyond what is required to process the directory tree and file contents.

**NFR11 — Human Readability**  
The Serialized Representation shall remain human-readable plain text.

**NFR12 — Scope Limitation**  
The system shall not introduce compression, encryption, binary file support, or external service integration.

**NFR13 — Version Traceability**  
The implementation shall embed its version identifier and that version shall correspond to the specification version.
## 5. Serialization Format

### 5.1 Overview
The Serialized File shall be a single UTF-8 encoded plain text file (no BOM) containing a header followed by zero or more file entries.  
Each file entry shall represent exactly one Text File from the Root Directory, including its Relative Path and exact file contents.

### 5.2 Line Endings
The Serialized File shall use LF (`\n`) line endings.  
During serialization, any Windows-native CRLF (`\r\n`) line endings within source files shall be preserved exactly as bytes within the stored file content (see Section 5.5), meaning TreeStream shall not normalise file content line endings.

### 5.3 Path Canonicalization
All paths stored in the Serialized File shall be Relative Paths using forward slashes (`/`) as separators.  
Relative Paths shall not start with a slash and shall not contain `.` or `..` segments.

### 5.4 Header
The Serialized File shall begin with the following header lines in the order shown:

- `TREESTREAM 1`
- `SPEC_VERSION: v0.1.0`
- `ENCODING: UTF-8`
- `NEWLINES: LF`
- `RECORDS: FILE`
- `END_HEADER`

Header keys and values shall be ASCII and shall not contain newline characters.

### 5.5 File Entry Record Format (Length-Prefixed)
Each file entry shall be encoded as a record with a fixed set of metadata lines followed by a raw content block whose length is explicitly declared in bytes.

A file entry shall have this exact structure:

1. `FILE`
2. `PATH: <relative_path>`
3. `CONTENT_BYTES: <non_negative_integer>`
4. `BEGIN_CONTENT`
5. `<exactly CONTENT_BYTES bytes of file content>`
6. `END_CONTENT`
7. `END_FILE`

Rules:
- `<relative_path>` shall conform to Section 5.3.
- `CONTENT_BYTES` shall be the exact number of bytes in the file’s UTF-8 content.
- The content block begins immediately after the newline terminating `BEGIN_CONTENT` and ends after exactly `CONTENT_BYTES` bytes, which may include any characters, including sequences that resemble markers such as `END_CONTENT`.
- After the content bytes, the next bytes in the Serialized File shall be a newline followed by `END_CONTENT` on its own line.
- Empty files shall be represented with `CONTENT_BYTES: 0` and an empty content block between `BEGIN_CONTENT` and `END_CONTENT`.

### 5.6 Deterministic Record Ordering
File entries shall appear in deterministic order sorted by their stored `PATH` value.  
Sorting shall be ordinal by Unicode code point of the `PATH` string (case-sensitive) to ensure stable ordering.

### 5.7 Whitespace and Blank Lines
No additional blank lines are permitted between records beyond those required by the format.  
All marker lines (`FILE`, `BEGIN_CONTENT`, `END_CONTENT`, `END_FILE`, and header lines) shall appear exactly as specified with no leading or trailing whitespace.

### 5.8 Minimal Example (Illustrative)
Example layout for a single file `notes/todo.txt` with content `Hi`:

- `FILE`
- `PATH: notes/todo.txt`
- `CONTENT_BYTES: 2`
- `BEGIN_CONTENT`
- `Hi`
- `END_CONTENT`
- `END_FILE`

## 6. Reconstruction Rules

### 6.1 Overview
Reconstruction is the deterministic transformation of a valid Serialized File into a directory tree within a specified Target Directory.  
The system shall recreate the directory structure and file contents exactly as described in the Serialized File.

### 6.2 Input Validation
Before reconstruction begins, the system shall:

- Validate that the Serialized File header conforms exactly to Section 5.4.
- Validate that `TREESTREAM 1` is present and supported.
- Validate that `SPEC_VERSION` matches the supported specification version.
- Validate that `ENCODING` is `UTF-8`.
- Validate that `NEWLINES` is `LF`.
- Validate that `RECORDS` is `FILE`.

If any header validation fails, reconstruction shall terminate with an explicit error.

### 6.3 Record Parsing
For each file record, the system shall:

1. Confirm the presence and order of required markers:
   - `FILE`
   - `PATH:`
   - `CONTENT_BYTES:`
   - `BEGIN_CONTENT`
   - `END_CONTENT`
   - `END_FILE`

2. Validate that `CONTENT_BYTES` is a non-negative integer.
3. Read exactly `CONTENT_BYTES` bytes following `BEGIN_CONTENT`.
4. Confirm that `END_CONTENT` and `END_FILE` markers appear exactly as specified.

If any structural deviation is detected, reconstruction shall terminate with an explicit error.

### 6.4 Path Validation and Safety
For each `PATH` value:

- The path shall be interpreted as a Relative Path.
- The path shall not contain absolute path indicators.
- The path shall not contain `..` segments.
- The path shall not escape the Target Directory.
- The path shall conform to Windows filesystem naming rules.

If any path violates these constraints, reconstruction shall terminate with an explicit error.

### 6.5 Directory Creation
For each valid file record:

- All necessary parent directories shall be created within the Target Directory before file creation.
- Directory creation shall follow Windows filesystem semantics.
- Existing directories shall not be removed or modified.

### 6.6 File Creation
For each valid file record:

- The file shall be created at the resolved path within the Target Directory.
- The file contents shall be written exactly as read from the Serialized File.
- No content transformation, trimming, or newline normalisation shall occur.

### 6.7 Overwrite Behaviour
If a file already exists at the target path:

- If overwrite mode is enabled, the existing file shall be replaced.
- If overwrite mode is disabled, reconstruction shall terminate with an explicit error and no further files shall be processed.

Overwrite behaviour shall be deterministic.

### 6.8 Reconstruction Ordering
File records shall be processed in the order they appear in the Serialized File.  
Given that serialization enforces deterministic ordering, reconstruction order shall therefore also be deterministic.

### 6.9 Round-Trip Integrity
If the Serialized File was produced by a compliant implementation of this specification and no external modification has occurred, reconstruction shall produce a directory tree identical in structure and file contents to the original source directory.

### 6.10 Failure Handling
Upon encountering any structural, encoding, permission, or filesystem error during reconstruction:

- The system shall halt immediately.
- The system shall emit a descriptive error.
- The system shall not attempt partial silent recovery.

## 7. Error Handling

### 7.1 General Principles
All errors shall be explicit, descriptive, and deterministic.  
Silent failures, implicit fallbacks, and automatic recovery attempts are prohibited.

Error messages shall clearly indicate:
- The operation being performed (serialization or reconstruction).
- The file or path involved, where applicable.
- The specific condition that caused failure.

### 7.2 Serialization Errors

The system shall terminate serialization with an explicit error if any of the following occur:

**E1 — Invalid Root Directory**  
The provided Root Directory does not exist or is not accessible.

**E2 — Permission Denied**  
The system lacks permission to read a file or directory within the Root Directory.

**E3 — Unsupported File Type**  
A file is not a valid UTF-8 Text File as defined in Section 2.

**E4 — Encoding Violation**  
A file contains bytes that cannot be decoded as UTF-8.

**E5 — Filesystem Access Error**  
An unexpected filesystem error occurs during traversal or file reading.

No partial Serialized File shall be considered valid if serialization fails.

### 7.3 Reconstruction Errors

The system shall terminate reconstruction with an explicit error if any of the following occur:

**E6 — Invalid Serialized File Structure**  
The header or record structure does not conform exactly to Section 5.

**E7 — Header Mismatch**  
The `TREESTREAM` version, `SPEC_VERSION`, or required header fields are unsupported or incorrect.

**E8 — Content Length Mismatch**  
The number of bytes read does not match the declared `CONTENT_BYTES` value.

**E9 — Invalid Path**  
A `PATH` value is malformed, absolute, contains traversal segments (`..`), or violates Windows filesystem rules.

**E10 — Target Write Permission Denied**  
The system lacks permission to create directories or write files in the Target Directory.

**E11 — Overwrite Prohibited**  
A file already exists and overwrite mode is disabled.

### 7.4 Deterministic Failure Behaviour
For identical invalid inputs, the system shall fail in the same manner and at the same validation stage across executions.

### 7.5 Partial State on Failure
If reconstruction fails after some files have been written:

- The system shall not silently roll back prior writes.
- The system shall report failure immediately.
- The resulting partial directory state shall be considered invalid and outside the scope of guarantee.

Rollback or transactional behaviour is out of scope for Version 1.

## 8. Determinism Requirements

### 8.1 Deterministic Serialization Function
Serialization shall behave as a pure deterministic function:

serialize(directory) → Serialized File

For identical input directory trees, the system shall produce byte-for-byte identical Serialized Files across executions on supported Windows environments.

Identical input directory trees are defined as having:
- Identical relative paths
- Identical file contents at the byte level
- Identical directory structure

File metadata such as timestamps, permissions, and filesystem attributes shall not influence serialization output.

---

### 8.2 Deterministic Traversal
Directory traversal order shall not depend on underlying filesystem enumeration order.

The system shall:
- Collect all eligible file paths.
- Canonicalise them as Relative Paths.
- Sort them deterministically using ordinal Unicode code point ordering (case-sensitive).
- Serialize records strictly in that sorted order.

No platform-dependent collation or locale-based sorting shall be used.

---

### 8.3 Deterministic Header Emission
Header lines shall:
- Appear in fixed order as defined in Section 5.4.
- Contain no additional whitespace.
- Contain no environment-dependent values.
- Not include timestamps, hostnames, or execution-specific metadata.

---

### 8.4 Deterministic Content Handling
File contents shall be written exactly as read, with:
- No newline normalisation.
- No trimming.
- No whitespace modification.
- No encoding conversion beyond UTF-8 validation.

The number of bytes written for each record shall match the declared `CONTENT_BYTES` value exactly.

---

### 8.5 Deterministic Failure Conditions
For identical invalid inputs, the system shall:
- Fail at the same validation stage.
- Emit the same error classification.
- Avoid non-deterministic partial recovery attempts.

---

### 8.6 Reconstruction Determinism
Reconstruction shall be deterministic with respect to the Serialized File.

For identical Serialized Files and identical overwrite mode configuration, reconstruction shall produce identical directory structures and file contents.

Filesystem metadata such as creation time or last-modified time is outside the determinism guarantee.

## 9. Constraints

### 9.1 Language and Runtime
The implementation shall be written in Python 3.11 or later.  
No external packages or third-party libraries shall be used.  
Only the Python standard library is permitted.

### 9.2 Platform Constraint
Version 1 shall target Microsoft Windows environments only.  
Behaviour on non-Windows systems is out of scope.

### 9.3 Text-Only Scope
The system shall operate exclusively on UTF-8 Text Files as defined in Section 2.  
Binary files, mixed-encoding files, and non-UTF-8 content are out of scope.

### 9.4 No Compression or Encryption
The system shall not introduce compression, encryption, obfuscation, or encoding transformations beyond UTF-8 validation.

### 9.5 No Metadata Preservation
The system shall not preserve or reconstruct filesystem metadata, including but not limited to:
- File timestamps
- File permissions
- Extended attributes
- Alternate data streams

Only directory structure and file contents are within scope.

### 9.6 No Concurrency Requirement
The system is not required to support parallel processing or concurrent execution.

### 9.7 No Transactional Guarantees
The system shall not provide transactional rollback or atomic reconstruction guarantees.

### 9.8 Deterministic Output Requirement
All outputs defined in this specification shall conform strictly to the format and determinism rules defined in Sections 5 and 8.

### 9.9 No User Interface Requirement
Version 1 does not require a graphical user interface.  
Command-line execution or equivalent programmatic invocation is sufficient.

## 10. Out of Scope

The following capabilities and behaviours are explicitly out of scope for Version 1 of TreeStream:

### 10.1 Cross-Platform Support
Support for non-Windows operating systems is not required.

### 10.2 Binary File Support
Serialization or reconstruction of binary files, mixed-encoding files, or non-UTF-8 files is not supported.

### 10.3 Filesystem Metadata Preservation
Preservation or reconstruction of:
- File creation times
- Last-modified times
- File permissions
- Extended attributes
- Alternate data streams  
is not supported.

### 10.4 Compression or Encryption
Compression, encryption, obfuscation, or any form of content transformation beyond UTF-8 validation is not supported.

### 10.5 Incremental or Differential Serialization
Partial updates, patch-based serialisation, or delta encoding between directory versions are not supported.

### 10.6 Transactional Reconstruction
Atomic reconstruction, rollback mechanisms, or automatic cleanup of partially written directories on failure are not supported.

### 10.7 Graphical User Interface
A graphical user interface is not required.

### 10.8 Network or External Service Integration
Integration with email systems, cloud storage providers, remote APIs, or external services is not supported.

### 10.9 Performance Optimisation Features
Parallel processing, multi-threading, streaming optimisations, or large-scale performance tuning are not required.

### 10.10 Backward Compatibility Guarantees
Compatibility with future specification versions is not guaranteed in Version 1.