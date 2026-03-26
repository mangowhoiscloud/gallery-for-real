from __future__ import annotations

from agent_harvest.utils import make_unique_id, slugify


class TestSlugify:
    def test_basic_slugification(self) -> None:
        assert slugify("Python DateTime Parsing!") == "python-datetime-parsing"

    def test_lowercase(self) -> None:
        assert slugify("UPPER CASE") == "upper-case"

    def test_replaces_spaces_with_hyphens(self) -> None:
        assert slugify("hello world") == "hello-world"

    def test_replaces_special_chars(self) -> None:
        assert slugify("foo@bar.baz") == "foo-bar-baz"

    def test_collapses_multiple_hyphens(self) -> None:
        assert slugify("foo---bar") == "foo-bar"

    def test_collapses_multiple_spaces(self) -> None:
        assert slugify("foo   bar") == "foo-bar"

    def test_strips_leading_hyphens(self) -> None:
        assert slugify("!hello") == "hello"

    def test_strips_trailing_hyphens(self) -> None:
        assert slugify("hello!") == "hello"

    def test_strips_both_edge_hyphens(self) -> None:
        assert slugify("!hello!") == "hello"

    def test_max_length_truncation(self) -> None:
        result = slugify("a" * 100, max_length=60)
        assert len(result) == 60

    def test_max_length_default_is_60(self) -> None:
        result = slugify("a" * 100)
        assert len(result) == 60

    def test_max_length_shorter_string_unchanged(self) -> None:
        result = slugify("hello", max_length=60)
        assert result == "hello"

    def test_max_length_exact(self) -> None:
        result = slugify("a" * 60, max_length=60)
        assert result == "a" * 60

    def test_numbers_preserved(self) -> None:
        assert slugify("python3 is great") == "python3-is-great"

    def test_empty_string(self) -> None:
        assert slugify("") == ""

    def test_only_special_chars(self) -> None:
        assert slugify("!@#$%") == ""

    def test_unicode_replaced(self) -> None:
        # Non-ascii chars are replaced by hyphens
        result = slugify("caf\u00e9 mocha")
        assert result == "caf-mocha"

    def test_mixed_separators(self) -> None:
        assert slugify("foo_bar-baz.qux") == "foo-bar-baz-qux"

    def test_max_length_zero(self) -> None:
        assert slugify("hello", max_length=0) == ""


class TestMakeUniqueId:
    def test_no_collision(self) -> None:
        assert make_unique_id("foo", set()) == "foo"

    def test_no_collision_with_others(self) -> None:
        assert make_unique_id("foo", {"bar", "baz"}) == "foo"

    def test_single_collision(self) -> None:
        assert make_unique_id("foo", {"foo"}) == "foo-2"

    def test_double_collision(self) -> None:
        assert make_unique_id("foo", {"foo", "foo-2"}) == "foo-3"

    def test_triple_collision(self) -> None:
        assert make_unique_id("foo", {"foo", "foo-2", "foo-3"}) == "foo-4"

    def test_gap_in_sequence(self) -> None:
        # foo-2 is taken but foo-3 is free — should return foo-2 ... wait, no:
        # foo is taken, so we try foo-2; foo-2 is also taken, try foo-3
        # But if foo-2 is NOT in existing_ids we return it
        assert make_unique_id("foo", {"foo", "foo-3"}) == "foo-2"

    def test_empty_existing(self) -> None:
        assert make_unique_id("slug", set()) == "slug"

    def test_large_collision_set(self) -> None:
        existing = {"foo"} | {f"foo-{i}" for i in range(2, 11)}
        assert make_unique_id("foo", existing) == "foo-11"

    def test_does_not_mutate_existing_ids(self) -> None:
        existing: set[str] = {"foo"}
        original = set(existing)
        make_unique_id("foo", existing)
        assert existing == original
