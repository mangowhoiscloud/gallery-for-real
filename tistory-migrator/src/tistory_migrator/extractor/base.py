from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from tistory_migrator.models import TistoryPost


class BaseExtractor(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def extract(
        self,
        category: str | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[TistoryPost]: ...
