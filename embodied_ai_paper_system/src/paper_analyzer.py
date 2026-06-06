"""论文中文精炼与相关论文整理。"""

from __future__ import annotations

import json
from pathlib import Path

from src.deepseek_client import DeepSeekClient
from src.models import Paper, PaperAnalysis


class PaperAnalyzer:
    def __init__(self, client: DeepSeekClient, prompt_file: Path) -> None:
        self.client = client
        self.system_prompt = prompt_file.read_text(encoding="utf-8")

    def analyze(
        self,
        paper: Paper,
        extracted_text: str,
        related: list[Paper],
    ) -> PaperAnalysis:
        payload = {
            "title": paper.title,
            "abstract": paper.abstract,
            "first_two_pages": extracted_text[:12000],
            "related_candidates": [
                {"title": item.title, "abstract": item.abstract}
                for item in related
            ],
        }
        result = self.client.complete_json(
            self.system_prompt,
            json.dumps(payload, ensure_ascii=False),
        )
        return PaperAnalysis(
            chinese_abstract=result.get("chinese_abstract", ""),
            key_points=result.get("key_points", [])[:5],
            innovations=result.get("innovations", [])[:5],
            related_papers=result.get("related_papers", [])[:5],
            tags=result.get("tags", [])[:6],
        )

    @staticmethod
    def fallback(paper: Paper, related: list[Paper]) -> PaperAnalysis:
        return PaperAnalysis(
            chinese_abstract=paper.abstract or "AI 解析失败，请直接阅读原文。",
            key_points=["AI 解析暂时失败，已保留论文原始摘要。"],
            innovations=[],
            related_papers=[item.title for item in related[:5]],
            tags=["待人工复核"],
        )
