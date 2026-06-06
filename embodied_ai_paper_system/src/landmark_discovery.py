"""每周低频更新行业基石论文库。"""

from __future__ import annotations

import json
from datetime import date, datetime

from config.settings import Settings
from src.deepseek_client import DeepSeekClient
from src.models import Paper
from src.semantic_scholar import SemanticScholarClient


class LandmarkDiscovery:
    def __init__(
        self,
        settings: Settings,
        scholar: SemanticScholarClient,
        deepseek: DeepSeekClient,
    ) -> None:
        self.settings = settings
        self.scholar = scholar
        self.deepseek = deepseek

    def is_due(self) -> bool:
        if not self.settings.landmark_file.exists():
            return True
        data = json.loads(
            self.settings.landmark_file.read_text(encoding="utf-8")
        )
        if not data.get("last_updated"):
            return True
        last = datetime.strptime(data["last_updated"], "%Y-%m-%d").date()
        return (date.today() - last).days >= self.settings.landmark_refresh_days

    def update(self, force: bool = False) -> list[Paper]:
        if not force and not self.is_due():
            return self.load()
        queries = self.settings.load_keywords().get("landmark_queries", [])
        candidates: dict[str, Paper] = {}
        for query in queries:
            for paper in self.scholar.search(query, limit=80):
                if paper.year and paper.year <= date.today().year - 3:
                    candidates[paper.paper_id] = paper
        ranked = sorted(
            candidates.values(),
            key=lambda item: (
                item.influential_citation_count,
                item.citation_count,
            ),
            reverse=True,
        )[:60]
        prompt = (
            "你是具身智能史与机器人学习领域专家。从候选中挑选最多 30 篇真正具有"
            "奠基性、方法范式影响或长期社区影响的论文。禁止编造，只返回候选 paper_id。"
            '输出 JSON：{"paper_ids": ["..."]}。'
        )
        try:
            response = self.deepseek.complete_json(
                prompt,
                json.dumps(
                    [paper.to_dict() for paper in ranked], ensure_ascii=False
                ),
            )
            selected_ids = set(response.get("paper_ids", []))
            selected = [
                paper for paper in ranked if paper.paper_id in selected_ids
            ]
        except Exception:
            # 模型不可用时保留高影响候选，避免每周任务完全无结果。
            selected = ranked[:30]
        for paper in selected:
            paper.source_pool = "landmark"
        payload = {
            "last_updated": date.today().isoformat(),
            "papers": [paper.to_dict() for paper in selected],
        }
        self.settings.landmark_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return selected

    def load(self) -> list[Paper]:
        data = json.loads(
            self.settings.landmark_file.read_text(encoding="utf-8")
        )
        papers = []
        for item in data.get("papers", []):
            fields = Paper.__dataclass_fields__
            papers.append(
                Paper(
                    **{
                        key: value
                        for key, value in item.items()
                        if key in fields
                    }
                )
            )
        return papers
