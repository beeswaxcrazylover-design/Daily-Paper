"""Semantic Scholar 检索、详情与推荐论文接口。"""

from __future__ import annotations

from datetime import date
from typing import Any

from config.settings import Settings
from src.http_client import ResilientHttpClient
from src.models import Paper

PAPER_FIELDS = ",".join(
    [
        "paperId",
        "title",
        "abstract",
        "citationCount",
        "influentialCitationCount",
        "publicationDate",
        "year",
        "openAccessPdf",
        "url",
        "authors",
        "venue",
    ]
)


class SemanticScholarClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http = ResilientHttpClient(
            settings.request_timeout,
            settings.request_interval,
            settings.max_retries,
        )
        self.headers = {}
        if settings.semantic_scholar_api_key:
            self.headers["x-api-key"] = settings.semantic_scholar_api_key

    def search(
        self,
        query: str,
        limit: int = 50,
        year: str | None = None,
        source_pool: str = "",
    ) -> list[Paper]:
        params: dict[str, Any] = {
            "query": query.replace("-", " "),
            "limit": min(limit, 100),
            "fields": PAPER_FIELDS,
        }
        if year:
            params["year"] = year
        response = self.http.request(
            "GET",
            f"{self.settings.semantic_scholar_base_url}/paper/search",
            params=params,
            headers=self.headers,
        )
        return [
            Paper.from_s2(item, source_pool)
            for item in response.json().get("data", [])
        ]

    def search_last_year(self, query: str, limit: int = 60) -> list[Paper]:
        today = date.today()
        return self.search(
            query,
            limit=limit,
            year=f"{today.year - 1}-{today.year}",
            source_pool="high_impact",
        )

    def recommendations(self, paper_id: str, limit: int = 5) -> list[Paper]:
        url = (
            "https://api.semanticscholar.org/recommendations/v1/papers/"
            f"forpaper/{paper_id}"
        )
        response = self.http.request(
            "GET",
            url,
            params={"limit": limit, "fields": PAPER_FIELDS},
            headers=self.headers,
        )
        return [
            Paper.from_s2(item, "related")
            for item in response.json().get("recommendedPapers", [])
        ]

