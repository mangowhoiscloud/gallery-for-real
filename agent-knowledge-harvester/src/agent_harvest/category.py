"""Category classification for learning entries using keyword-based heuristics."""

import re

# Keywords for each category, ordered by priority (highest → lowest)
# Priority: error-recovery > library-quirk > compatibility > pattern > performance > testing
_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "error-recovery",
        [
            "error",
            "errors",
            "exception",
            "exceptions",
            "crash",
            "crashes",
            "fail",
            "fails",
            "failed",
            "failing",
            "failure",
            "failures",
            "fallback",
            "retry",
            "retries",
            "handle",
            "handles",
            "handling",
            "catch",
            "catches",
            "recover",
            "recovers",
            "recovery",
            "fix",
            "fixes",
            "fixed",
            "fixing",
            "bug",
            "bugs",
        ],
    ),
    (
        "library-quirk",
        [
            "library",
            "libraries",
            "import",
            "imports",
            "api",
            "behavior",
            "behaviors",
            "behaviour",
            "unexpected",
            "quirk",
            "quirks",
            "workaround",
            "workarounds",
            "gotcha",
            "caveat",
            "caveats",
        ],
    ),
    (
        "compatibility",
        [
            "compatible",
            "compatibility",
            "migrate",
            "migrates",
            "migration",
            "migrations",
            "upgrade",
            "upgrades",
            "downgrade",
            "downgrades",
            "breaking",
            "deprecated",
            "deprecate",
            "legacy",
            "polyfill",
            "version",
            "versions",
        ],
    ),
    (
        "pattern",
        [
            "pattern",
            "patterns",
            "architecture",
            "design",
            "approach",
            "strategy",
            "strategies",
            "refactor",
            "structure",
            "convention",
            "conventions",
        ],
    ),
    (
        "performance",
        [
            "performance",
            "slow",
            "fast",
            "optimize",
            "optimizes",
            "optimization",
            "cache",
            "caching",
            "memory",
            "latency",
            "throughput",
            "efficient",
            "efficiency",
        ],
    ),
    (
        "testing",
        [
            "test",
            "tests",
            "tested",
            "testing",
            "assert",
            "asserts",
            "assertion",
            "mock",
            "mocks",
            "mocking",
            "fixture",
            "fixtures",
            "coverage",
            "pytest",
            "jest",
            "spec",
            "specs",
            "verify",
            "verifies",
            "verification",
        ],
    ),
]

# Compile a pattern for each category: match whole words only (word boundary)
_COMPILED: list[tuple[str, re.Pattern[str]]] = [
    (
        category,
        re.compile(
            r"\b(?:" + "|".join(re.escape(kw) for kw in keywords) + r")\b",
            re.IGNORECASE,
        ),
    )
    for category, keywords in _CATEGORY_KEYWORDS
]

_DEFAULT_CATEGORY = "pattern"


def classify_category(text: str) -> str:
    """Classify text into one of 6 categories using keyword heuristics.

    Priority order on overlap: error-recovery > library-quirk > compatibility
    > pattern > performance > testing.  Default is "pattern" if no keywords match.
    """
    for category, pattern in _COMPILED:
        if pattern.search(text):
            return category
    return _DEFAULT_CATEGORY
