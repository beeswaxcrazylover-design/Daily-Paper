"""检索、筛选、解析、写入 Obsidian 的完整编排。"""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import date, timedelta

from config.settings import Settings
from src.deepseek_client import DeepSeekClient
from src.history_manager import HistoryManager
from src.landmark_discovery import LandmarkDiscovery
from src.obsidian_writer import ObsidianWriter
from src.paper_analyzer import PaperAnalyzer
from src.paper_selector import PaperSelector
from src.ranking import build_top_candidates
from src.semantic_scholar import SemanticScholarClient


class DailyPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.scholar = SemanticScholarClient(settings)
        self.deepseek = DeepSeekClient(settings)
        self.history = HistoryManager(
            settings.history_file, settings.recommendation_cooldown_days
        )
        self.landmarks = LandmarkDiscovery(
            settings, self.scholar, self.deepseek
        )

    def run(self, force: bool = False) -> None:
        self.settings.validate()
        if self.history.was_successful_today() and not force:
            self.logger.info("今天已成功生成日报，跳过重复运行")
            return
        config = self.settings.load_keywords()
        keywords = config.get("keywords", [])
        high_impact = []
        frontier = []
        one_year_ago = date.today() - timedelta(days=365)
        ninety_days_ago = date.today() - timedelta(days=90)
        for keyword in keywords:
            try:
                papers = self.scholar.search_last_year(keyword)
            except Exception:
                self.logger.exception("每日检索失败，跳过关键词：%s", keyword)
                continue
            for paper in papers:
                try:
                    published = date.fromisoformat(paper.publication_date)
                except ValueError:
                    continue
                if published >= one_year_ago:
                    high_impact.append(
                        replace(paper, source_pool="high_impact")
                    )
                if published >= ninety_days_ago:
                    frontier.append(replace(paper, source_pool="frontier"))
        landmarks = self.landmarks.update()
        pools = {
            "high_impact": high_impact,
            "frontier": frontier,
            "landmark": landmarks,
        }
        candidates = build_top_candidates(pools, keywords, self.settings)
        if len(candidates) < 3:
            raise RuntimeError("有效候选不足 3 篇，请检查关键词或 API 响应")
        self.settings.candidate_dir.mkdir(parents=True, exist_ok=True)
        candidate_file = (
            self.settings.candidate_dir / f"{date.today().isoformat()}.json"
        )
        candidate_file.write_text(
            json.dumps(
                [paper.to_dict() for paper in candidates],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        selector = PaperSelector(
            self.deepseek,
            self.history,
            self.settings.prompt_dir / "paper_selection.txt",
        )
        selected = selector.select(candidates)
        analyzer = PaperAnalyzer(
            self.deepseek,
            self.settings.prompt_dir / "paper_analysis.txt",
        )
        results = []
        for item in selected:
            try:
                related = self.scholar.recommendations(item.paper.paper_id)
            except Exception:
                self.logger.exception("相关论文获取失败：%s", item.paper.title)
                related = []
            try:
                analysis = analyzer.analyze(item.paper, "", related)
            except Exception:
                self.logger.exception(
                    "AI 深度解析失败，使用摘要降级：%s", item.paper.title
                )
                analysis = analyzer.fallback(item.paper, related)
            results.append((item, analysis))
        note_path = ObsidianWriter(self.settings).write(results)
        self.history.record_success(
            [
                {
                    "paper_id": item.paper.paper_id,
                    "title": item.paper.title,
                    "role": item.role,
                }
                for item in selected
            ]
        )
        self.logger.info("日报已生成：%s", note_path)
