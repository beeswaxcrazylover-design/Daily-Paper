"""三个候选池的独立评分与配额合并。"""

from __future__ import annotations

import math
import re
from datetime import date, datetime

from config.settings import Settings
from src.models import Paper


def _age_days(paper: Paper) -> int:
    if paper.publication_date:
        try:
            published = datetime.strptime(
                paper.publication_date, "%Y-%m-%d"
            ).date()
            return max((date.today() - published).days, 0)
        except ValueError:
            pass
    if paper.year:
        return max((date.today().year - paper.year) * 365, 0)
    return 3650


def _relevance(paper: Paper, keywords: list[str]) -> float:
    text = f"{paper.title} {paper.abstract}".lower()
    terms = {
        token
        for keyword in keywords
        for token in re.findall(r"[a-zA-Z]{3,}", keyword.lower())
    }
    if not terms:
        return 0.0
    return min(sum(term in text for term in terms) / max(len(terms) / 2, 1), 1)


def score_paper(paper: Paper, keywords: list[str]) -> float:
    age = _age_days(paper)
    relevance = _relevance(paper, keywords)
    citations = min(math.log1p(paper.citation_count) / math.log(5001), 1)
    months = max(age / 30.4, 1)
    velocity = min(
        math.log1p(paper.citation_count / months) / math.log(51), 1
    )
    freshness_365 = max(0.0, 1 - age / 365)
    freshness_90 = max(0.0, 1 - age / 90)
    influential = min(
        math.log1p(paper.influential_citation_count) / math.log(501), 1
    )

    if paper.source_pool == "frontier":
        score = (
            0.45 * relevance
            + 0.35 * freshness_90
            + 0.15 * velocity
            + 0.05 * citations
        )
    elif paper.source_pool == "landmark":
        score = (
            0.30 * relevance
            + 0.35 * citations
            + 0.25 * influential
            + 0.10 * min(age / 3650, 1)
        )
    else:
        score = (
            0.30 * relevance
            + 0.25 * citations
            + 0.25 * velocity
            + 0.20 * freshness_365
        )
    return round(score * 100, 3)


def rank_pool(papers: list[Paper], keywords: list[str]) -> list[Paper]:
    unique: dict[str, Paper] = {}
    for paper in papers:
        if not paper.paper_id or not paper.title or not paper.abstract:
            continue
        paper.score = score_paper(paper, keywords)
        existing = unique.get(paper.paper_id)
        if existing is None or paper.score > existing.score:
            unique[paper.paper_id] = paper
    return sorted(unique.values(), key=lambda item: item.score, reverse=True)


def build_top_candidates(
    pools: dict[str, list[Paper]],
    keywords: list[str],
    settings: Settings,
) -> list[Paper]:
    quotas = {
        "high_impact": settings.high_impact_quota,
        "landmark": settings.landmark_quota,
        "frontier": settings.frontier_quota,
    }
    ranked = {
        name: rank_pool(items, keywords) for name, items in pools.items()
    }
    selected: list[Paper] = []
    used: set[str] = set()
    for name, quota in quotas.items():
        for paper in ranked.get(name, []):
            if paper.paper_id not in used:
                selected.append(paper)
                used.add(paper.paper_id)
            if sum(item.source_pool == name for item in selected) >= quota:
                break

    remainder = sorted(
        [
            paper
            for items in ranked.values()
            for paper in items
            if paper.paper_id not in used
        ],
        key=lambda item: item.score,
        reverse=True,
    )
    selected.extend(remainder[: settings.candidate_limit - len(selected)])
    return selected[: settings.candidate_limit]

