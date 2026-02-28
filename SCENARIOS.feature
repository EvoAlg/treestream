Feature: TreeStream Serialization and Reconstruction
  TreeStream deterministically serializes a directory tree to a single UTF-8 file
  and reconstructs it byte-for-byte. All behaviour is deterministic and error
  conditions terminate with a defined error code.

  # ---------------------------------------------------------------------------
  # SERIALIZATION — HAPPY PATH
  # ---------------------------------------------------------------------------

  Scenario: S01 — Basic round-trip integrity
    Given a root directory containing "a.txt" with content "Hello"
    When the directory is serialized
    And the output is reconstructed into a new target directory
    Then the target contains "a.txt"
    And the content of "a.txt" is byte-for-byte identical to the source

  Scenario: S02 — Nested directory structure
    Given a root directory containing
      | path                |
      | docs/readme.txt     |
      | docs/sub/notes.txt  |
    When the directory is serialized
    And the output is reconstructed into a new target directory
    Then the reconstructed directory hierarchy is identical to the source
    And all file contents are byte-for-byte identical to their sources

  Scenario: S03 — Empty file handling
    Given a root directory containing "empty.txt" with zero bytes
    When the directory is serialized
    Then the record for "empty.txt" contains CONTENT_BYTES: 0
    And reconstruction recreates "empty.txt" as a zero-byte file

  Scenario: S04 — CRLF preservation
    Given a root directory containing "crlf.txt" whose bytes include CR LF sequences
    When the directory is serialized
    Then the serialized content block preserves the exact byte sequence including CR LF
    And reconstruction reproduces bytes identical to the source file

  Scenario: S05 — Deterministic ordering
    Given a root directory containing
      | path   |
      | b.txt  |
      | a.txt  |
      | aa.txt |
    When the directory is serialized twice in succession without modification
    Then records in each output are sorted by case-sensitive ordinal Unicode code-point comparison on PATH
    And the two output files are byte-for-byte identical

  Scenario: S06 — Empty root directory
    Given a root directory containing no files or subdirectories
    When the directory is serialized
    Then the output file contains only the global header and the EOF marker
    And reconstruction of that output produces an empty target directory

  Scenario: S07 — Non-existent target directory is created
    Given a serialized file representing a valid directory tree
    And the target directory path does not exist on the filesystem
    When reconstruction is attempted
    Then the system creates the target directory including any necessary parent directories
    And reconstruction completes successfully with all files written correctly

  # ---------------------------------------------------------------------------
  # SERIALIZATION — ERROR CONDITIONS
  # ---------------------------------------------------------------------------

  Scenario: S08 — File content contains bytes invalid under UTF-8 strict decoding
    Given a root directory containing "binary.bin" whose content is not valid UTF-8
    When serialization is attempted
    Then serialization terminates with error code E4

  Scenario: S09 — Symlink or junction encountered
    Given a root directory containing a symlink or NTFS junction point
    When serialization is attempted
    Then serialization terminates with error code E5

  Scenario: S10 — Atomic output on serialization failure with no pre-existing output file
    Given a root directory that will cause serialization to fail mid-process
    And no output file exists at the designated path prior to serialization
    When serialization terminates with an error
    Then the designated output file does not exist
    And any temporary working file has been deleted

  Scenario: S11 — Atomic output on serialization failure with pre-existing output file
    Given a root directory that will cause serialization to fail mid-process
    And an output file already exists at the designated path prior to serialization
    When serialization terminates with an error
    Then the pre-existing output file is byte-for-byte identical to its state before serialization began
    And any temporary working file has been deleted

  # ---------------------------------------------------------------------------
  # RECONSTRUCTION — ERROR CONDITIONS
  # ---------------------------------------------------------------------------

  Scenario: S12 — Incorrect SPEC_VERSION in header
    Given a serialized file whose SPEC_VERSION does not match the supported version
    When reconstruction is attempted
    Then reconstruction terminates with error code E7

  Scenario: S13 — CONTENT_BYTES mismatch
    Given a serialized file where CONTENT_BYTES for a record does not match the actual byte length of its content block
    When reconstruction is attempted
    Then reconstruction terminates with error code E8

  Scenario: S14 — Missing EOF marker
    Given a serialized file that is truncated before the EOF marker
    When reconstruction is attempted
    Then reconstruction terminates with error code E8

  Scenario: S15 — Trailing bytes after final record
    Given a serialized file that contains additional bytes after the final END_FILE line
    When reconstruction is attempted
    Then reconstruction terminates with error code E6

  Scenario: S16 — Path traversal via ".." component
    Given a serialized file containing a PATH value with a ".." component
    When reconstruction is attempted
    Then reconstruction terminates with error code E9

  Scenario: S17 — Case-insensitive path collision
    Given a serialized file containing records for both "File.txt" and "file.txt"
    When reconstruction is attempted
    Then reconstruction terminates with error code E9

  Scenario: S18 — Overwrite prohibited
    Given a target directory already containing "a.txt"
    And overwrite mode is disabled
    And the serialized file contains a record for "a.txt"
    When reconstruction is attempted
    Then reconstruction terminates with error code E11

  Scenario: S19 — Target directory cannot be created
    Given a target directory path whose parent is not writable due to permission restrictions
    When reconstruction is attempted
    Then reconstruction terminates with error code E10
