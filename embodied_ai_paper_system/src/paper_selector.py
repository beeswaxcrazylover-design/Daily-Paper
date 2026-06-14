"""使用 DeepSeek 从 Top 15 中选出三种角色。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.deepseek_client import DeepSeekClient
from src.history_manager import HistoryManager
from src.models import Paper, SelectedPaper
from src.ranking import freshness_score, role_score

ROLES = {"review", "deep_dive", "application"}


class PaperSelector:
    def __init__(
        self,
        client: DeepSeekClient,
        history: HistoryManager,
        prompt_file: Path,
        keywords: list[str],
        landmark_cooldown_days: int,
    ) -> None:
        self.client = client
        self.history = history
        self.system_prompt = prompt_file.read_text(encoding="utf-8")
        self.keywords = keywords
        self.landmark_cooldown_days = landmark_cooldown_days

    def select(
        self, candidates: list[Paper], run_date: date
    ) -> list[SelectedPaper]:
        available = [
            paper
            for paper in candidates
            if not self.history.is_in_cooldown(
                paper.paper_id,
                self.landmark_cooldown_days
                if paper.source_pool == "landmark"
                else None,
                as_of_date=run_date,
            )
        ]
        if len(available) < 3:
            raise RuntimeError(
                "冷却期外候选不足 3 篇。系统不会解除去重限制，请扩大检索池或"
                "缩短冷却期。"
            )
        payload = [
            {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "abstract": paper.abstract,
                "year": paper.year,
                "citations": paper.citation_count,
                "pool": paper.source_pool,
                "score": paper.score,
                "freshness_score": freshness_score(paper),
                "deep_dive_score": role_score(
                    paper, "deep_dive", self.keywords
                ),
                "application_score": role_score(
                    paper, "application", self.keywords
                ),
                "is_landmark": paper.source_pool == "landmark",
                "has_pdf": bool(paper.open_access_pdf),
            }
            for paper in available
        ]
        selections = []
        for _ in range(2):
            try:
                result = self.client.complete_json(
                    self.system_prompt,
                    "候选论文如下：\n"
                    + json.dumps(payload, ensure_ascii=False),
                )
                selections = result.get("selections", [])
                if self._valid(selections, available):
                    break
            except Exception:
                continue
        if not self._valid(selections, available):
            return self._fallback(available)
        by_id = {paper.paper_id: paper for paper in available}
        return [
            SelectedPaper(item["role"], by_id[item["paper_id"]])
            for item in selections
        ]

    def _valid(self, selections: list[dict], candidates: list[Paper]) -> bool:
        candidate_ids = {paper.paper_id for paper in candidates}
        ids = [item.get("paper_id") for item in selections]
        structurally_valid = (
            len(selections) == 3
            and {item.get("role") for item in selections} == ROLES
            and len(set(ids)) == 3
            and all(paper_id in candidate_ids for paper_id in ids)
        )
        if not structurally_valid:
            return False

        by_id = {paper.paper_id: paper for paper in candidates}
        role_ids = {
            item["role"]: item["paper_id"] for item in selections
        }
        technical = [
            by_id[role_ids["deep_dive"]],
            by_id[role_ids["application"]],
        ]
        has_recent_candidate = any(
            freshness_score(paper) >= 0.9 for paper in candidates
        )
        if has_recent_candidate and not any(
            freshness_score(paper) >= 0.9 for paper in technical
        ):
            return False
        return True

    def _fallback(self, candidates: list[Paper]) -> list[SelectedPaper]:
        remaining = list(candidates)

        def take(predicate, role: str) -> Paper:
            ranked = sorted(
                enumerate(remaining),
                key=lambda item: role_score(
                    item[1], role, self.keywords
                ),
                reverse=True,
            )
            for index, paper in ranked:
                if predicate(paper):
                    return remaining.pop(index)
            best_index = ranked[0][0]
            return remaining.pop(best_index)

        review = take(
            lambda paper: paper.source_pool == "landmark"
            or any(
                word in paper.title.lower()
                for word in ("survey", "review", "foundation")
            ),
            "review",
        )
        pairs = [
            (deep, application)
            for deep in remaining
            for application in remaining
            if deep.paper_id != application.paper_id
        ]
        if any(
            freshness_score(paper) >= 0.9 for paper in remaining
        ):
            constrained = [
                pair
                for pair in pairs
                if any(freshness_score(paper) >= 0.9 for paper in pair)
            ]
            if constrained:
                pairs = constrained
        deep_dive, application = max(
            pairs,
            key=lambda pair: (
                role_score(pair[0], "deep_dive", self.keywords)
                + role_score(pair[1], "application", self.keywords)
            ),
        )
        return [
            SelectedPaper("review", review),
            SelectedPaper("deep_dive", deep_dive),
            SelectedPaper("application", application),
        ]
