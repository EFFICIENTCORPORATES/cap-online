from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

@dataclass(slots=True)
class DocumentMeta:
    path: Path
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def paper(self) -> Optional[int]:
        return _int_or_none(self.raw.get("paper"))
    @property
    def module(self) -> Optional[int]:
        return _int_or_none(self.raw.get("module"))
    @property
    def chapter(self) -> Optional[int]:
        return _int_or_none(self.raw.get("chapter"))
    @property
    def unit(self) -> Optional[int]:
        return _int_or_none(self.raw.get("unit"))
    @property
    def paper_title(self) -> str:
        return str(self.raw.get("paper_title") or "")
    @property
    def chapter_title(self) -> str:
        return str(self.raw.get("chapter_title") or "")
    @property
    def unit_title(self) -> str:
        return str(self.raw.get("unit_title") or "")

@dataclass(slots=True)
class Block:
    meta: dict[str, Any]
    content: str
    document: DocumentMeta
    ordinal: int

    @property
    def id(self) -> str:
        return str(self.meta.get("id") or "")
    @property
    def type(self) -> str:
        return str(self.meta.get("type") or self.meta.get("retrieval_type") or "")
    @property
    def category(self) -> str:
        return str(self.meta.get("category") or "")
    @property
    def pair_key(self) -> str:
        return str(self.meta.get("pair_key") or "")
    @property
    def number(self):
        return self.meta.get("number")
    @property
    def paper(self) -> Optional[int]:
        return _int_or_none(self.meta.get("paper", self.document.paper))
    @property
    def module(self) -> Optional[int]:
        return _int_or_none(self.meta.get("module", self.document.module))
    @property
    def chapter(self) -> Optional[int]:
        return _int_or_none(self.meta.get("chapter", self.document.chapter))
    @property
    def unit(self) -> Optional[int]:
        return _int_or_none(self.meta.get("unit", self.document.unit))
    @property
    def topic_number(self) -> str:
        return str(self.meta.get("topic_number") or "")
    @property
    def page_start(self) -> Optional[int]:
        return _int_or_none(self.meta.get("page_start"))
    @property
    def page_end(self) -> Optional[int]:
        return _int_or_none(self.meta.get("page_end"))
    @property
    def printed_page_start(self) -> str:
        return str(self.meta.get("printed_page_start") or "")
    @property
    def printed_page_end(self) -> str:
        return str(self.meta.get("printed_page_end") or "")
    @property
    def source_pdf(self) -> str:
        return str(self.meta.get("source_pdf") or self.document.raw.get("source_pdf") or "")

    def sort_key(self):
        # null unit/chapter-scope sorts before numbered units within the chapter.
        unit = -1 if self.unit is None else self.unit
        return (self.paper or 0, self.module or 0, self.chapter or 0, unit, self.ordinal)

@dataclass(slots=True)
class QuerySpec:
    types: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    paper: Optional[int] = None
    module: Optional[int] = None
    chapter: Optional[int] = None
    unit: Optional[int] = None
    topic: Optional[str] = None
    include_answers: bool = False
    questions_only: bool = False
    everything: bool = False
    title: str = "CA Foundation Retrieval"
    original_query: str = ""


def _int_or_none(value):
    if value is None or value == "" or str(value).lower() == "null":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
