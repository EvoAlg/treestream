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
    Then the target contains a subdirectory matching the root directory name
    And that subdirectory contains "a.txt"
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
    Then the serialized content block contains the base64 encoding of the original bytes, preserving CR LF within the decoded content
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
    And reconstruction of that output creates an empty subdirectory named after the root directory inside the target

  Scenario: S07 — Non-existent target directory is created
    Given a serialized file representing a valid directory tree
    And the target directory path does not exist on the filesystem
    When reconstruction is attempted
    Then the system creates the target directory including any necessary parent directories
    And reconstruction completes successfully with all files written correctly

  Scenario: S20 — Email body round-trip with CRLF-normalized structure
    Given a root directory containing representative UTF-8 text files
    When the directory is serialized to a ".treestream" text payload
    And the payload is copied into a plain-text email body that normalizes structural line endings to CR LF
    And the received email body text is reconstructed
    Then reconstruction succeeds with byte-for-byte file content integrity
    And any subsequent serialization output remains LF-only for structural lines

  Scenario: S21 — Clipboard round-trip with CRLF structural input tolerance
    Given a valid ".treestream" payload copied through a clipboard path that converts structural newlines to CR LF
    When reconstruction is performed from the pasted plain text payload
    Then reconstruction succeeds without requiring manual newline edits
    And reconstructed files are byte-for-byte identical to the original source tree

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

  Scenario: S15 — Non-blank trailing bytes after final record
    Given a serialized file that contains non-blank bytes after the final END_FILE line
    When reconstruction is attempted
    Then reconstruction terminates with error code E6

  Scenario: S22 — Trailing blank lines after final record are tolerated
    Given a serialized file that contains one or more blank lines after the final END_FILE line
    When reconstruction is attempted
    Then reconstruction succeeds
    And reconstructed files are byte-for-byte identical to the original source tree

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

  Scenario: S23 — Base64 content encoding round-trip integrity
    Given a root directory containing files with varied byte content including non-ASCII UTF-8 and control characters
    When the directory is serialized
    Then each content block in the serialized file contains valid standard Base64 (RFC 4648) with no line wrapping
    And CONTENT_BYTES for each record equals the decoded byte count of its content block
    And reconstruction produces files byte-for-byte identical to the originals

  Scenario: S24 — Root directory name is preserved through round-trip
    Given a root directory named "MyProject" containing at least one text file
    When the directory is serialized
    Then the serialized header contains "ROOT_NAME: MyProject"
    And when the serialized file is reconstructed into a target directory
    Then a subdirectory named "MyProject" is created inside the target directory
    And all files are present inside that subdirectory at their correct relative paths
    And file contents are byte-for-byte identical to the originals

  # ---------------------------------------------------------------------------
  # EXCLUSION FILTER
  # ---------------------------------------------------------------------------

  Scenario: S25 — Exclude a directory by exact name
    Given a root directory containing
      | path                        |
      | src/main.py                 |
      | __pycache__/main.cpython.pyc |
    When the directory is serialized with --exclude __pycache__
    Then the serialized file contains a record for "src/main.py"
    And the serialized file contains no record for any path under "__pycache__"

  Scenario: S26 — Exclude files by glob pattern
    Given a root directory containing
      | path             |
      | src/main.py      |
      | src/main.pyc     |
      | notes.txt        |
    When the directory is serialized with --exclude *.pyc
    Then the serialized file contains records for "src/main.py" and "notes.txt"
    And the serialized file contains no record for "src/main.pyc"

  Scenario: S27 — Multiple exclusion patterns apply independently
    Given a root directory containing
      | path                          |
      | src/main.py                   |
      | __pycache__/main.cpython.pyc  |
      | .git/config                   |
      | notes.txt                     |
    When the directory is serialized with --exclude __pycache__ --exclude .git
    Then the serialized file contains records for "src/main.py" and "notes.txt"
    And the serialized file contains no record for any path under "__pycache__"
    And the serialized file contains no record for any path under ".git"

  Scenario: S28 — Exclusion with no matching entries is identical to baseline
    Given a root directory containing only text files with no names matching the pattern
    When the directory is serialized with --exclude __pycache__
    Then the output is byte-for-byte identical to serializing the same directory without any exclusion flag

  Scenario: S29 — Excluded directory containing text files omits those text files
    Given a root directory containing
      | path                  |
      | keep/data.txt         |
      | skip_dir/readme.txt   |
      | skip_dir/notes.txt    |
    When the directory is serialized with --exclude skip_dir
    Then the serialized file contains a record for "keep/data.txt"
    And the serialized file contains no record for "skip_dir/readme.txt"
    And the serialized file contains no record for "skip_dir/notes.txt"
    And no descent into "skip_dir" is performed during traversal

  # ---------------------------------------------------------------------------
  # IGNORE FILE (.treestreamignore)
  # ---------------------------------------------------------------------------

  Scenario: S30 — .treestreamignore with matching patterns excludes those entries
    Given a root directory containing
      | path                  |
      | src/main.py           |
      | build/output.bin      |
      | notes.txt             |
    And the root directory contains a ".treestreamignore" file with the line "build"
    When the directory is serialized without any --exclude flag
    Then the serialized file contains a record for "src/main.py"
    And the serialized file contains a record for "notes.txt"
    And the serialized file contains no record for any path under "build"

  Scenario: S31 — .treestreamignore comment lines and blank lines are ignored
    Given a root directory containing
      | path        |
      | keep.txt    |
      | skip.tmp    |
    And the root directory contains a ".treestreamignore" file with the content:
      """
      # This is a comment
      *.tmp

      # Another comment
      """
    When the directory is serialized without any --exclude flag
    Then the serialized file contains a record for "keep.txt"
    And the serialized file contains no record for "skip.tmp"

  Scenario: S32 — Absent .treestreamignore produces behaviour identical to prior versions
    Given a root directory containing text files only
    And no ".treestreamignore" file exists in the root directory
    When the directory is serialized without any --exclude flag
    Then the output is byte-for-byte identical to serializing the same directory under prior version behaviour (no exclusions)

  Scenario: S33 — .treestreamignore and --exclude patterns are merged and applied together
    Given a root directory containing
      | path                        |
      | src/main.py                 |
      | __pycache__/main.cpython.pyc |
      | dist/output.js              |
      | notes.txt                   |
    And the root directory contains a ".treestreamignore" file with the line "dist"
    When the directory is serialized with --exclude __pycache__
    Then the serialized file contains a record for "src/main.py"
    And the serialized file contains a record for "notes.txt"
    And the serialized file contains no record for any path under "__pycache__"
    And the serialized file contains no record for any path under "dist"

  Scenario: S34 — .treestreamignore itself is not present in the serialized output
    Given a root directory containing
      | path       |
      | readme.txt |
    And the root directory contains a ".treestreamignore" file with any content
    When the directory is serialized
    Then the serialized file contains a record for "readme.txt"
    And the serialized file contains no record for ".treestreamignore"

  Scenario: S35 — Empty .treestreamignore produces behaviour identical to no ignore file
    Given a root directory containing the same text files as a baseline run
    And the root directory contains an empty ".treestreamignore" file
    When the directory is serialized without any --exclude flag
    Then the serialized output (excluding the absence of any .treestreamignore record) is byte-for-byte identical to serializing the same directory with no ".treestreamignore" present
