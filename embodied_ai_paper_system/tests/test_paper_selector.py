import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src.models import Paper
from src.paper_selector import PaperSelector


class StubHistory:
    def is_in_cooldown(self, paper_id, cooldown_days=None) -> bool:
        return False


class StubClient:
    pass


class PaperSelectorTests(unittest.TestCase):
    def _selector(self, prompt_file: Path) -> PaperSelector:
        return PaperSelector(
            StubClient(),
            StubHistory(),
            prompt_file,
            ["Robot Learning"],
            180,
        )

    @staticmethod
    def _paper(paper_id: str, age_days: int) -> Paper:
        return Paper(
            paper_id=paper_id,
            title=f"Robot paper {paper_id}",
            abstract="A robot learning method with real robot experiments.",
            publication_date=(
                date.today() - timedelta(days=age_days)
            ).isoformat(),
            source_pool="high_impact",
        )

    def test_rejects_two_old_technical_papers_when_recent_exists(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "prompt.txt"
            prompt.write_text("prompt", encoding="utf-8")
            selector = self._selector(prompt)
            candidates = [
                self._paper("review", 1000),
                self._paper("deep", 1000),
                self._paper("application", 1000),
                self._paper("recent", 30),
            ]
            selections = [
                {"role": "review", "paper_id": "review"},
                {"role": "deep_dive", "paper_id": "deep"},
                {"role": "application", "paper_id": "application"},
            ]

            self.assertFalse(selector._valid(selections, candidates))

    def test_accepts_recent_technical_paper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prompt = Path(temp_dir) / "prompt.txt"
            prompt.write_text("prompt", encoding="utf-8")
            selector = self._selector(prompt)
            candidates = [
                self._paper("review", 1000),
                self._paper("deep", 30),
                self._paper("application", 1000),
            ]
            selections = [
                {"role": "review", "paper_id": "review"},
                {"role": "deep_dive", "paper_id": "deep"},
                {"role": "application", "paper_id": "application"},
            ]

            self.assertTrue(selector._valid(selections, candidates))


if __name__ == "__main__":
    unittest.main()
