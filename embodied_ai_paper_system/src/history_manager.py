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

    def is_in_cooldown(
        self,
        paper_id: str,
        cooldown_days: int | None = None,
        as_of_date: date | None = None,
    ) -> bool:
        reference_date = as_of_date or date.today()
        effective_cooldown = cooldown_days or self.cooldown_days
        for item in self.load().get("recommendations", []):
            if item.get("paper_id") != paper_id:
                continue
            recommended = datetime.strptime(item["date"], "%Y-%m-%d").date()
            # 重跑历史日期时，只参考该日期之前的推荐记录。
            if recommended >= reference_date:
                continue
            if (reference_date - recommended).days < effective_cooldown:
                return True
        return False

    def was_successful(self, run_date: date) -> bool:
        return run_date.isoformat() in self.load().get(
            "successful_dates", []
        )

    def record_success(self, selected: list[dict], run_date: date) -> None:
        data = self.load()
        target_date = run_date.isoformat()
        data["recommendations"] = [
            item
            for item in data.get("recommendations", [])
            if item.get("date") != target_date
        ]
        for item in selected:
            data.setdefault("recommendations", []).append(
                {
                    "date": target_date,
                    "paper_id": item["paper_id"],
                    "title": item["title"],
                    "role": item["role"],
                }
            )
        if target_date not in data.setdefault("successful_dates", []):
            data["successful_dates"].append(target_date)
        data["successful_dates"] = sorted(set(data["successful_dates"]))
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
