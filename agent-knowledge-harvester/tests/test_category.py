"""Tests for category.py — keyword-based category classification."""

from agent_harvest.category import classify_category


# ── Basic per-category classification ──────────────────────────────────────


def test_error_recovery_error_keyword() -> None:
    assert classify_category("unhandled error in the main loop") == "error-recovery"


def test_error_recovery_exception_keyword() -> None:
    assert classify_category("caught an exception during startup") == "error-recovery"


def test_error_recovery_crash_keyword() -> None:
    assert classify_category("the process crash on boot") == "error-recovery"


def test_error_recovery_fail_keyword() -> None:
    assert classify_category("connection fail without retry") == "error-recovery"


def test_error_recovery_fallback_keyword() -> None:
    assert classify_category("implement a fallback strategy") == "error-recovery"


def test_error_recovery_retry_keyword() -> None:
    assert classify_category("retry logic for transient errors") == "error-recovery"


def test_error_recovery_handle_keyword() -> None:
    assert classify_category("handle missing config gracefully") == "error-recovery"


def test_error_recovery_catch_keyword() -> None:
    assert classify_category("catch all exceptions at the boundary") == "error-recovery"


def test_error_recovery_recover_keyword() -> None:
    assert classify_category("recover from partial writes") == "error-recovery"


def test_error_recovery_fix_keyword() -> None:
    assert classify_category("fix the serialization bug") == "error-recovery"


def test_error_recovery_bug_keyword() -> None:
    assert classify_category("bug in the validation logic") == "error-recovery"


def test_library_quirk_library_keyword() -> None:
    assert classify_category("library loading order matters") == "library-quirk"


def test_library_quirk_import_keyword() -> None:
    assert classify_category("import order affects initialization") == "library-quirk"


def test_library_quirk_api_keyword() -> None:
    assert classify_category("API returns null for empty list") == "library-quirk"


def test_library_quirk_behavior_keyword() -> None:
    assert classify_category("unexpected behavior when nested calls") == "library-quirk"


def test_library_quirk_quirk_keyword() -> None:
    assert classify_category("this is a known quirk of the ORM") == "library-quirk"


def test_library_quirk_workaround_keyword() -> None:
    assert classify_category("workaround for the SDK limitation") == "library-quirk"


def test_library_quirk_gotcha_keyword() -> None:
    assert classify_category("gotcha: headers are case-insensitive") == "library-quirk"


def test_library_quirk_caveat_keyword() -> None:
    assert classify_category("caveat: requires exact version pin") == "library-quirk"


def test_compatibility_version_keyword() -> None:
    assert classify_category("version incompatibility between packages") == "compatibility"


def test_compatibility_migrate_keyword() -> None:
    assert classify_category("migrate to the new schema format") == "compatibility"


def test_compatibility_upgrade_keyword() -> None:
    assert classify_category("upgrade path from v1 to v2") == "compatibility"


def test_compatibility_downgrade_keyword() -> None:
    assert classify_category("downgrade required for older clients") == "compatibility"


def test_compatibility_breaking_keyword() -> None:
    assert classify_category("breaking change in the release cycle") == "compatibility"


def test_compatibility_deprecated_keyword() -> None:
    assert classify_category("deprecated function removed in v3") == "compatibility"


def test_compatibility_legacy_keyword() -> None:
    assert classify_category("legacy code path still in use") == "compatibility"


def test_pattern_pattern_keyword() -> None:
    assert classify_category("use the repository pattern for data access") == "pattern"


def test_pattern_architecture_keyword() -> None:
    assert classify_category("architecture decision for service layer") == "pattern"


def test_pattern_design_keyword() -> None:
    assert classify_category("design choice for module boundaries") == "pattern"


def test_pattern_approach_keyword() -> None:
    assert classify_category("approach chosen for module layout") == "pattern"


def test_pattern_strategy_keyword() -> None:
    assert classify_category("strategy for cache invalidation") == "pattern"


def test_pattern_refactor_keyword() -> None:
    assert classify_category("refactor the service into smaller units") == "pattern"


def test_pattern_structure_keyword() -> None:
    assert classify_category("structure of the module hierarchy") == "pattern"


def test_pattern_convention_keyword() -> None:
    assert classify_category("naming convention for test files") == "pattern"


def test_performance_keyword() -> None:
    assert classify_category("performance bottleneck in DB queries") == "performance"


def test_performance_slow_keyword() -> None:
    assert classify_category("slow startup time on first run") == "performance"


def test_performance_optimize_keyword() -> None:
    assert classify_category("optimize the hot path") == "performance"


def test_performance_cache_keyword() -> None:
    assert classify_category("cache the parsed schema in memory") == "performance"


def test_performance_latency_keyword() -> None:
    assert classify_category("high latency on cold start") == "performance"


def test_performance_throughput_keyword() -> None:
    assert classify_category("throughput limited by serialization") == "performance"


def test_testing_test_keyword() -> None:
    assert classify_category("test coverage for edge cases") == "testing"


def test_testing_assert_keyword() -> None:
    assert classify_category("assert the response shape is correct") == "testing"


def test_testing_mock_keyword() -> None:
    assert classify_category("mock the external service call") == "testing"


def test_testing_fixture_keyword() -> None:
    assert classify_category("fixture for temporary directories") == "testing"


def test_testing_coverage_keyword() -> None:
    assert classify_category("coverage drops for new module") == "testing"


def test_testing_pytest_keyword() -> None:
    assert classify_category("pytest configuration for test discovery") == "testing"


def test_testing_jest_keyword() -> None:
    assert classify_category("jest timer mocking for async") == "testing"


def test_testing_verify_keyword() -> None:
    assert classify_category("verify the output matches the schema") == "testing"


# ── Default to "pattern" ───────────────────────────────────────────────────


def test_default_no_keywords() -> None:
    assert classify_category("no keywords here") == "pattern"


def test_default_empty_string() -> None:
    assert classify_category("") == "pattern"


def test_default_unrelated_text() -> None:
    assert classify_category("the quick brown fox jumps over the lazy dog") == "pattern"


# ── Case insensitivity ─────────────────────────────────────────────────────


def test_case_insensitive_upper() -> None:
    assert classify_category("ERROR in the handler") == "error-recovery"


def test_case_insensitive_mixed() -> None:
    assert classify_category("Unexpected BEHAVIOR from the SDK") == "library-quirk"


def test_case_insensitive_title() -> None:
    assert classify_category("Cache Invalidation Is Hard") == "performance"


# ── Priority ordering when multiple categories match ──────────────────────


def test_priority_error_over_library() -> None:
    # "error" (error-recovery) + "library" (library-quirk) → error-recovery wins
    assert classify_category("error in the library loading code") == "error-recovery"


def test_priority_error_over_compatibility() -> None:
    # "fix" (error-recovery) + "version" (compatibility) → error-recovery wins
    assert classify_category("fix version incompatibility") == "error-recovery"


def test_priority_library_over_compatibility() -> None:
    # "quirk" (library-quirk) + "version" (compatibility) — library-quirk wins
    assert classify_category("quirk in version selection") == "library-quirk"


def test_priority_library_over_pattern() -> None:
    # "import" (library-quirk) + "structure" (pattern) → library-quirk wins
    assert classify_category("import structure reorganization") == "library-quirk"


def test_priority_compatibility_over_pattern() -> None:
    # "migrate" (compatibility) + "pattern" (pattern) → compatibility wins
    assert classify_category("migrate using the adapter pattern") == "compatibility"


def test_priority_compatibility_over_performance() -> None:
    # "upgrade" (compatibility) + "performance" (performance) → compatibility wins
    assert classify_category("upgrade for performance improvements") == "compatibility"


def test_priority_pattern_over_performance() -> None:
    # "architecture" (pattern) + "cache" (performance) → pattern wins
    assert classify_category("cache architecture decision") == "pattern"


def test_priority_pattern_over_testing() -> None:
    # "convention" (pattern) + "test" (testing) → pattern wins
    assert classify_category("test naming convention") == "pattern"


def test_priority_performance_over_testing() -> None:
    # "optimize" (performance) + "coverage" (testing) → performance wins
    assert classify_category("optimize test coverage overhead") == "performance"


# ── Whole-word boundary matching ──────────────────────────────────────────


def test_no_partial_match_error() -> None:
    # "errors" has word boundary — still matches
    assert classify_category("multiple errors found") == "error-recovery"


def test_no_partial_match_inside_word() -> None:
    # "discourage" contains "age" but should NOT match any keyword
    assert classify_category("we discourage this approach") == "pattern"


def test_acceptance_example_error_recovery() -> None:
    assert classify_category("error handling with retry fallback") == "error-recovery"


def test_acceptance_example_library_quirk() -> None:
    assert classify_category("import version API quirk") == "library-quirk"


def test_acceptance_example_default_pattern() -> None:
    assert classify_category("no keywords here") == "pattern"
