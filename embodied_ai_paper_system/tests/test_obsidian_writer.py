import tempfile
import unittest
from datetime import date
from pathlib import Path

from config.settings import Settings
from src.models import Paper, PaperAnalysis, SelectedPaper
from src.obsidian_writer import ObsidianWriter


class ObsidianWriterTests(unittest.TestCase):
    def test_pdf_is_written_as_external_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(obsidian_vault_path=Path(temp_dir))
            paper = Paper(
                paper_id="paper-1",
                title="Example Paper",
                abstract="Abstract",
                open_access_pdf="https://arxiv.org/pdf/1234.5678",
            )
            analysis = PaperAnalysis(
                chinese_abstract="摘要",
                key_points=[],
                innovations=[],
                related_papers=[],
                tags=[],
            )
            note = ObsidianWriter(settings).write(
                [(SelectedPaper("review", paper), analysis)],
                run_date=date(2026, 6, 13),
            )
            content = note.read_text(encoding="utf-8")

            self.assertIn(
                "[在浏览器中打开](https://arxiv.org/pdf/1234.5678)",
                content,
            )
            self.assertNotIn("[[Attachments/Papers", content)
            self.assertIn("重点关注: false", content)
            self.assertTrue(
                (
                    Path(temp_dir)
                    / "Daily Embodied AI"
                    / "重点论文日索引.md"
                ).exists()
            )

    def test_rerun_preserves_highlight_property(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(obsidian_vault_path=Path(temp_dir))
            writer = ObsidianWriter(settings)
            paper = Paper(
                paper_id="paper-1",
                title="Example Paper",
                abstract="Abstract",
            )
            analysis = PaperAnalysis(
                chinese_abstract="摘要",
                key_points=[],
                innovations=[],
                related_papers=[],
                tags=[],
            )
            run_date = date(2026, 6, 13)
            note = writer.write(
                [(SelectedPaper("review", paper), analysis)],
                run_date=run_date,
            )
            content = note.read_text(encoding="utf-8").replace(
                "重点关注: false", "重点关注: true"
            )
            note.write_text(content, encoding="utf-8")

            writer.write(
                [(SelectedPaper("review", paper), analysis)],
                run_date=run_date,
            )

            self.assertIn(
                "重点关注: true", note.read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
