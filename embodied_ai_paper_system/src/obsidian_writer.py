"""生成 Obsidian Daily Note，并使用外部 PDF 链接。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from config.settings import Settings
from src.models import PaperAnalysis, SelectedPaper

ROLE_TITLES = {
    "review": "📌 综述",
    "deep_dive": "🔬 深度研究",
    "application": "🛠️ 系统应用",
}


class ObsidianWriter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def write(
        self,
        results: list[tuple[SelectedPaper, PaperAnalysis]],
    ) -> Path:
        today = date.today()
        note_dir = self.settings.obsidian_vault_path / "Daily Embodied AI"
        note_dir.mkdir(parents=True, exist_ok=True)
        note_path = note_dir / f"{today.isoformat()}_Daily_Embodied_AI.md"
        tags = {"论文日更", "Embodied_AI"}
        for _, analysis in results:
            tags.update(tag.lstrip("#").replace(" ", "_") for tag in analysis.tags)
        front_matter = yaml.safe_dump(
            {"date": today.isoformat(), "tags": sorted(tags)},
            allow_unicode=True,
            sort_keys=False,
        ).strip()
        blocks = [f"---\n{front_matter}\n---\n", "# 每日具身智能论文\n"]
        for selected, analysis in results:
            paper = selected.paper
            blocks.append(f"## {ROLE_TITLES[selected.role]}：{paper.title}\n")
            blocks.append(
                f"- **作者**：{', '.join(paper.authors) or '未知'}\n"
                f"- **发表时间**：{paper.publication_date or paper.year or '未知'}\n"
                f"- **引用量**：{paper.citation_count}\n"
                f"- **Semantic Scholar**：[页面]({paper.url})\n"
            )
            if paper.open_access_pdf:
                blocks.append(f"- **PDF**：[在浏览器中打开]({paper.open_access_pdf})\n")
            else:
                blocks.append("- **PDF**：未能获取开放版本\n")
            blocks.append(f"\n### 中文摘要\n\n{analysis.chinese_abstract}\n")
            blocks.append("\n### 论文重点\n")
            blocks.extend(f"- {item}\n" for item in analysis.key_points)
            blocks.append("\n### 核心创新\n")
            blocks.extend(f"- {item}\n" for item in analysis.innovations)
            blocks.append("\n### 强相关论文\n")
            blocks.extend(
                f"- [[{title.replace('|', '-')}]]\n"
                for title in analysis.related_papers
            )
            blocks.append(
                "\n> [!NOTE] 我的阅读心得\n"
                "> \n"
                "> \n\n"
            )
        note_path.write_text("".join(blocks), encoding="utf-8")
        return note_path
