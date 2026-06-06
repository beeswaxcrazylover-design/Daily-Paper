"""核心数据模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str = ""
    citation_count: int = 0
    influential_citation_count: int = 0
    publication_date: str = ""
    year: int | None = None
    open_access_pdf: str = ""
    url: str = ""
    authors: list[str] = field(default_factory=list)
    venue: str = ""
    source_pool: str = ""
    score: float = 0.0

    @classmethod
    def from_s2(cls, item: dict[str, Any], source_pool: str = "") -> "Paper":
        pdf = item.get("openAccessPdf") or {}
        return cls(
            paper_id=item.get("paperId") or "",
            title=(item.get("title") or "").strip(),
            abstract=(item.get("abstract") or "").strip(),
            citation_count=item.get("citationCount") or 0,
            influential_citation_count=item.get(
                "influentialCitationCount"
            ) or 0,
            publication_date=item.get("publicationDate") or "",
            year=item.get("year"),
            open_access_pdf=pdf.get("url") or "",
            url=item.get("url") or "",
            authors=[
                author.get("name", "")
                for author in item.get("authors") or []
                if author.get("name")
            ],
            venue=item.get("venue") or "",
            source_pool=source_pool,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelectedPaper:
    role: str
    paper: Paper


@dataclass
class PaperAnalysis:
    chinese_abstract: str
    key_points: list[str]
    innovations: list[str]
    related_papers: list[str]
    tags: list[str]

