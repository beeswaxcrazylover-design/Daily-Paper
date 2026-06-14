import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.history_manager import HistoryManager


class HistoryManagerTests(unittest.TestCase):
    def test_historical_rerun_ignores_same_and_future_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.json"
            path.write_text(
                json.dumps(
                    {
                        "recommendations": [
                            {"date": "2026-06-12", "paper_id": "old"},
                            {"date": "2026-06-13", "paper_id": "same"},
                            {"date": "2026-06-14", "paper_id": "future"},
                        ],
                        "successful_dates": [],
                    }
                ),
                encoding="utf-8",
            )
            history = HistoryManager(path, 60)

            self.assertTrue(
                history.is_in_cooldown(
                    "old", as_of_date=date(2026, 6, 13)
                )
            )
            self.assertFalse(
                history.is_in_cooldown(
                    "same", as_of_date=date(2026, 6, 13)
                )
            )
            self.assertFalse(
                history.is_in_cooldown(
                    "future", as_of_date=date(2026, 6, 13)
                )
            )

    def test_record_success_replaces_target_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "history.json"
            path.write_text(
                json.dumps(
                    {
                        "recommendations": [
                            {
                                "date": "2026-06-13",
                                "paper_id": "duplicate",
                            },
                            {
                                "date": "2026-06-14",
                                "paper_id": "keep",
                            },
                        ],
                        "successful_dates": [
                            "2026-06-13",
                            "2026-06-14",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            history = HistoryManager(path, 60)
            history.record_success(
                [
                    {
                        "paper_id": "new",
                        "title": "New paper",
                        "role": "review",
                    }
                ],
                date(2026, 6, 13),
            )
            data = history.load()
            june_13 = [
                item
                for item in data["recommendations"]
                if item["date"] == "2026-06-13"
            ]

            self.assertEqual([item["paper_id"] for item in june_13], ["new"])
            self.assertTrue(
                any(
                    item["paper_id"] == "keep"
                    for item in data["recommendations"]
                )
            )


if __name__ == "__main__":
    unittest.main()
