"""使用 DeepSeek 从 Top 15 中选出三种角色。"""

from __future__ import annotations

import json
from pathlib import Path

from src.deepseek_client import DeepSeekClient
from src.history_manager import HistoryManager
from src.models import Paper, SelectedPaper

ROLES = {"review", "deep_dive", "application"}


class PaperSelector:
    def __init__(
        self,
        client: DeepSeekClient,
        history: HistoryManager,
        prompt_file: Path,
    ) -> None:
        self.client = client
        self.history = history
        self.system_prompt = prompt_file.read_text(encoding="utf-8")

    def select(self, candidates: list[Paper]) -> list[SelectedPaper]:
        available = [
            paper
            for paper in candidates
            if not self.history.is_in_cooldown(paper.paper_id)
        ]
        if len(available) < 3:
            available = candidates
        payload = [
            {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "abstract": paper.abstract,
                "year": paper.year,
                "citations": paper.citation_count,
                "pool": paper.source_pool,
                "score": paper.score,
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

    @staticmethod
    def _valid(selections: list[dict], candidates: list[Paper]) -> bool:
        candidate_ids = {paper.paper_id for paper in candidates}
        ids = [item.get("paper_id") for item in selections]
        return (
            len(selections) == 3
            and {item.get("role") for item in selections} == ROLES
            and len(set(ids)) == 3
            and all(paper_id in candidate_ids for paper_id in ids)
        )

    @staticmethod
    def _fallback(candidates: list[Paper]) -> list[SelectedPaper]:
        remaining = sorted(candidates, key=lambda paper: paper.score, reverse=True)

        def take(predicate) -> Paper:
            for index, paper in enumerate(remaining):
                if predicate(paper):
                    return remaining.pop(index)
            return remaining.pop(0)

        review = take(
            lambda paper: paper.source_pool == "landmark"
            or any(
                word in paper.title.lower()
                for word in ("survey", "review", "foundation")
            )
        )
        application = take(
            lambda paper: any(
                word in f"{paper.title} {paper.abstract}".lower()
                for word in (
                    "system",
                    "real-world",
                    "real robot",
                    "deployment",
                    "benchmark",
                )
            )
        )
        deep_dive = take(lambda paper: True)
        return [
            SelectedPaper("review", review),
            SelectedPaper("deep_dive", deep_dive),
            SelectedPaper("application", application),
        ]
