"""Tests for BaseExtractor ABC."""
from __future__ import annotations

import pytest
from datetime import datetime

from tistory_migrator.extractor import BaseExtractor
from tistory_migrator.extractor.base import BaseExtractor as BaseExtractorDirect
from tistory_migrator.models import TistoryPost


# ---------------------------------------------------------------------------
# Helper: minimal concrete implementation
# ---------------------------------------------------------------------------

class ConcreteExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "test"

    def extract(
        self,
        category: str | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[TistoryPost]:
        return []


class MissingNameExtractor(BaseExtractor):
    """Missing name property — should raise TypeError on instantiation."""

    def extract(
        self,
        category: str | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[TistoryPost]:
        return []


class MissingExtractExtractor(BaseExtractor):
    """Missing extract method — should raise TypeError on instantiation."""

    @property
    def name(self) -> str:
        return "missing_extract"


# ---------------------------------------------------------------------------
# Abstract instantiation tests
# ---------------------------------------------------------------------------

class TestAbstractInstantiation:
    def test_cannot_instantiate_base_extractor(self) -> None:
        with pytest.raises(TypeError):
            BaseExtractor()  # type: ignore[abstract]

    def test_missing_name_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            MissingNameExtractor()  # type: ignore[abstract]

    def test_missing_extract_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            MissingExtractExtractor()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Concrete subclass tests
# ---------------------------------------------------------------------------

class TestConcreteExtractor:
    def setup_method(self) -> None:
        self.extractor = ConcreteExtractor()

    def test_instantiation_succeeds(self) -> None:
        assert self.extractor is not None

    def test_name_property_returns_string(self) -> None:
        assert self.extractor.name == "test"

    def test_extract_returns_list(self) -> None:
        result = self.extractor.extract()
        assert isinstance(result, list)

    def test_extract_default_category_is_none(self) -> None:
        """extract() can be called with no args — all defaults are None."""
        # ConcreteExtractor ignores filters; we just verify no TypeError
        result = self.extractor.extract()
        assert result == []

    def test_extract_accepts_category_filter(self) -> None:
        result = self.extractor.extract(category="Python")
        assert result == []

    def test_extract_accepts_after_filter(self) -> None:
        result = self.extractor.extract(after=datetime(2024, 1, 1))
        assert result == []

    def test_extract_accepts_before_filter(self) -> None:
        result = self.extractor.extract(before=datetime(2024, 12, 31))
        assert result == []

    def test_extract_accepts_all_filters(self) -> None:
        result = self.extractor.extract(
            category="Python",
            after=datetime(2024, 1, 1),
            before=datetime(2024, 12, 31),
        )
        assert result == []

    def test_filter_defaults_are_none(self) -> None:
        """Verify the signature allows all-None defaults by calling with no args."""
        import inspect
        sig = inspect.signature(BaseExtractor.extract)
        params = sig.parameters
        assert params["category"].default is None
        assert params["after"].default is None
        assert params["before"].default is None


# ---------------------------------------------------------------------------
# Package import tests
# ---------------------------------------------------------------------------

class TestPackageImports:
    def test_import_from_package(self) -> None:
        from tistory_migrator.extractor import BaseExtractor as BE
        assert BE is BaseExtractor

    def test_import_from_base_module(self) -> None:
        assert BaseExtractorDirect is BaseExtractor

    def test_base_extractor_in_all(self) -> None:
        import tistory_migrator.extractor as pkg
        assert "BaseExtractor" in pkg.__all__

    def test_is_abstract(self) -> None:
        import inspect
        assert inspect.isabstract(BaseExtractor)
