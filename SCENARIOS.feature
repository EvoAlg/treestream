## SCENARIOS.feature (v0.1.9)

### Scenario 1 — Basic Round Trip Integrity

**Given** a root directory containing

* `a.txt` with content `Hello`

**When** the directory is serialized and then reconstructed

**Then** the reconstructed directory shall contain

* `a.txt`
* with byte-for-byte identical content

---

### Scenario 2 — Nested Directory Structure

**Given** a root directory containing

* `docs/readme.txt`
* `docs/sub/notes.txt`

**When** serialized and reconstructed

**Then** the directory hierarchy shall be identical
**And** file contents shall match exactly

---

### Scenario 3 — Empty File Handling

**Given** a root directory containing

* `empty.txt` with zero bytes

**When** serialized

**Then** the record shall contain `CONTENT_BYTES: 0`
**And** reconstruction shall recreate a zero-byte file

---

### Scenario 4 — CRLF Preservation

**Given** a file containing Windows CRLF line endings (`\r\n`)

**When** serialized

**Then** the serialized content block shall preserve the exact byte sequence
**And** reconstruction shall reproduce identical bytes

---

### Scenario 5 — Deterministic Ordering

**Given** files

* `b.txt`
* `a.txt`
* `aa.txt`

**When** serialized

**Then** records shall be sorted by ordinal Unicode code point comparison of PATH
**And** repeated serialization runs shall produce byte-for-byte identical output

---

### Scenario 6 — Invalid UTF-8 File

**Given** a file containing bytes invalid under UTF-8 strict decoding

**When** serialization is attempted

**Then** serialization shall terminate with E4

---

### Scenario 7 — Symlink Encounter

**Given** a symlink or junction within the root directory

**When** serialization is attempted

**Then** serialization shall terminate with E5

---

### Scenario 8 — Invalid Header During Reconstruction

**Given** a serialized file with incorrect `SPEC_VERSION`

**When** reconstruction is attempted

**Then** reconstruction shall terminate with E7

---

### Scenario 9 — Content Length Mismatch

**Given** a serialized file where `CONTENT_BYTES` does not match actual content length

**When** reconstruction is attempted

**Then** reconstruction shall terminate with E8

---

### Scenario 10 — Invalid PATH Rules

**Given** a serialized file containing a path with `..`

**When** reconstruction is attempted

**Then** reconstruction shall terminate with E9

---

### Scenario 11 — Case-Insensitive Path Collision

**Given** a serialized file containing

* `File.txt`
* `file.txt`

**When** reconstruction is attempted

**Then** reconstruction shall terminate with E9

---

### Scenario 12 — Overwrite Prohibited

**Given** a target directory already containing `a.txt`
**And** overwrite mode disabled

**When** reconstruction is attempted

**Then** reconstruction shall terminate with E11

---

### Scenario 13 — Atomic Serialization Output

**Given** serialization fails mid-process

**When** serialization terminates

**Then** the designated output file shall not exist or be modified
**And** any temporary file shall be deleted