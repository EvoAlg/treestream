# TreeStream Test Report

- Date/time (local): 2026-03-23
- OS: Windows-10-10.0.19045-SP0
- Python: 3.12.1
- Shell: PowerShell 5.1
- Working directory: `C:\Users\edwar\OneDrive\Documents\Programming\TreeStream`
- Implementation target: `SPEC.md` v0.1.16

## Verification Scope

This run executed the combined automated suite for:

- `tests.test_core` covering scenarios `S01-S24`
- `tests.test_exclusion_filter` covering scenarios `S25-S36` plus a small number of non-scenario regression checks

Evidence that `S01-S24` now have automated coverage:

- `tests/test_core.py` is present in the repository test suite.
- The command below imported and executed `tests.test_core.TestTreeStreamCore`.
- The unittest output lists one named test method for each scenario `S01-S24`.

## Command Executed

- `$env:PYTHONPATH='IMPLEMENTATION'; python -m unittest -v tests.test_core tests.test_exclusion_filter`

## Full Test Method Results

### tests.test_core

- `test_s01_basic_round_trip_integrity`: PASS
- `test_s02_nested_directory_structure`: PASS
- `test_s03_empty_file_handling`: PASS
- `test_s04_crlf_preservation`: PASS
- `test_s05_deterministic_ordering`: PASS
- `test_s06_empty_root_directory`: PASS
- `test_s07_nonexistent_target_directory_created`: PASS
- `test_s08_invalid_utf8_triggers_e4`: PASS
- `test_s09_symlink_triggers_e5`: PASS
- `test_s10_atomic_no_preexisting_output`: PASS
- `test_s11_atomic_preexisting_output_preserved`: PASS
- `test_s12_incorrect_spec_version_triggers_e7`: PASS
- `test_s13_content_bytes_mismatch_triggers_e8`: PASS
- `test_s14_missing_eof_marker_triggers_e8`: PASS
- `test_s15_nonblank_trailing_bytes_triggers_e6`: PASS
- `test_s16_path_traversal_triggers_e9`: PASS
- `test_s17_case_insensitive_collision_triggers_e9`: PASS
- `test_s18_overwrite_prohibited_triggers_e11`: PASS
- `test_s19_target_cannot_be_created_triggers_e10`: PASS
- `test_s20_email_crlf_round_trip`: PASS
- `test_s21_clipboard_crlf_round_trip`: PASS
- `test_s22_trailing_blank_lines_tolerated`: PASS
- `test_s23_base64_encoding_round_trip`: PASS
- `test_s24_root_directory_name_preserved`: PASS

### tests.test_exclusion_filter

- `test_cli_accepts_repeatable_exclude`: PASS
- `test_gate_g_identical_inputs_and_exclusions_are_deterministic`: PASS
- `test_no_exclude_flag_matches_explicit_empty_exclusions`: PASS
- `test_s25_excludes_directory_by_exact_name`: PASS
- `test_s26_excludes_files_by_glob_pattern`: PASS
- `test_s27_multiple_exclusion_patterns_apply_independently`: PASS
- `test_s28_non_matching_pattern_matches_baseline_byte_for_byte`: PASS
- `test_s29_excluded_directory_is_not_descended`: PASS
- `test_s30_root_treestreamignore_excludes_files_and_ignores_comments_and_blank_lines`: PASS
- `test_s31_root_treestreamignore_excludes_directory_without_descent`: PASS
- `test_s32_absent_ignore_matches_baseline_and_empty_ignore_matches_without_ignore`: PASS
- `test_s33_ignore_file_and_cli_exclude_are_merged`: PASS
- `test_s34_root_ignore_is_never_serialized_and_subdirectory_ignore_is_normal_file`: PASS
- `test_s35_ignore_file_inputs_are_deterministic`: PASS
- `test_s36_invalid_root_ignore_raises_e13_and_writes_no_output`: PASS

## Scenario Status

- S01: PASS
- S02: PASS
- S03: PASS
- S04: PASS
- S05: PASS
- S06: PASS
- S07: PASS
- S08: PASS
- S09: PASS
- S10: PASS
- S11: PASS
- S12: PASS
- S13: PASS
- S14: PASS
- S15: PASS
- S16: PASS
- S17: PASS
- S18: PASS
- S19: PASS
- S20: PASS
- S21: PASS
- S22: PASS
- S23: PASS
- S24: PASS
- S25: PASS
- S26: PASS
- S27: PASS
- S28: PASS
- S29: PASS
- S30: PASS
- S31: PASS
- S32: PASS
- S33: PASS
- S34: PASS
- S35: PASS
- S36: PASS

## Suite Summary

- Total tests run: 39
- Passed: 39
- Failed: 0
- Errors: 0
- Overall result: `OK`

Implementation self-verification passed for this run. Per `AGENT_RULES.md`, formal acceptance still requires independent verification by a human or a separate agent role.
