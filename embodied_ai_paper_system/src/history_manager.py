"""推荐历史、冷却期和每日幂等状态。"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path


class HistoryManager:
    def __init__(self, path: Path, cooldown_days: int) -> None:
        self.path = path
        self.cooldown_days = cooldown_days
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        if not self.path.exists():
            return {"recommendations": [], "successful_dates": []}
        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def is_in_cooldown(self, paper_id: str) -> bool:
        today = date.today()
        for item in self.load().get("recommendations", []):
            if item.get("paper_id") != paper_id:
                continue
            recommended = datetime.strptime(item["date"], "%Y-%m-%d").date()
            if (today - recommended).days < self.cooldown_days:
                return True
        return False

    def was_successful_today(self) -> bool:
        return date.today().isoformat() in self.load().get(
            "successful_dates", []
        )

    def record_success(self, selected: list[dict]) -> None:
        data = self.load()
        today = date.today().isoformat()
        for item in selected:
            data.setdefault("recommendations", []).append(
                {
                    "date": today,
                    "paper_id": item["paper_id"],
                    "title": item["title"],
                    "role": item["role"],
                }
            )
        if today not in data.setdefault("successful_dates", []):
            data["successful_dates"].append(today)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

