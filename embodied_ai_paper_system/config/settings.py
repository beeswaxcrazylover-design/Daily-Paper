"""系统配置：用户私密配置从项目根目录 .env 读取。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    semantic_scholar_api_key: str = os.getenv(
        "SEMANTIC_SCHOLAR_API_KEY", ""
    ).strip()
    obsidian_vault_path: Path = Path(
        os.getenv("OBSIDIAN_VAULT_PATH", "").strip() or "."
    )
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    semantic_scholar_base_url: str = (
        "https://api.semanticscholar.org/graph/v1"
    )
    request_timeout: int = 45
    request_interval: float = 1.2
    max_retries: int = 3
    semantic_scholar_interval: float = 4.0
    semantic_scholar_max_retries: int = 5
    rate_limit_max_wait: int = 120
    candidate_limit: int = 15
    high_impact_quota: int = 6
    landmark_quota: int = 5
    frontier_quota: int = 4
    recommendation_cooldown_days: int = 60
    landmark_cooldown_days: int = 180
    landmark_refresh_days: int = 7

    @property
    def keywords_file(self) -> Path:
        return PROJECT_ROOT / "config" / "keywords.yaml"

    @property
    def landmark_file(self) -> Path:
        return PROJECT_ROOT / "config" / "landmark_papers.json"

    @property
    def history_file(self) -> Path:
        return PROJECT_ROOT / "data" / "history" / "recommendations.json"

    @property
    def log_dir(self) -> Path:
        return PROJECT_ROOT / "logs"

    @property
    def candidate_dir(self) -> Path:
        return PROJECT_ROOT / "data" / "candidates"

    @property
    def prompt_dir(self) -> Path:
        return PROJECT_ROOT / "prompts"

    def load_keywords(self) -> dict:
        with self.keywords_file.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def validate(self, require_deepseek: bool = True) -> None:
        missing: list[str] = []
        if require_deepseek and not self.deepseek_api_key:
            missing.append("DEEPSEEK_API_KEY")
        raw_vault = os.getenv("OBSIDIAN_VAULT_PATH", "").strip()
        if not raw_vault:
            missing.append("OBSIDIAN_VAULT_PATH")
        if missing:
            raise ValueError(
                "请先在 .env 中填写：" + ", ".join(missing)
            )
