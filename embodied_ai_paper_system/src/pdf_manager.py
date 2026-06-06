"""PDF 单点存储、下载与前两页文本提取。"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pdfplumber

from config.settings import Settings
from src.http_client import ResilientHttpClient
from src.models import Paper


class PdfManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http = ResilientHttpClient(
            settings.request_timeout,
            settings.request_interval,
            settings.max_retries,
        )
        self.logger = logging.getLogger(__name__)

    def daily_directory(self, role: str) -> Path:
        today = date.today()
        role_dir = {
            "review": "review",
            "deep_dive": "deep_dive",
            "application": "application",
        }[role]
        path = (
            self.settings.obsidian_vault_path
            / "Attachments"
            / "Papers"
            / str(today.year)
            / f"{today:%m月%d日}论文"
            / role_dir
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _safe_name(title: str) -> str:
        clean = re.sub(r'[<>:"/\\|?*]', "_", title)
        return clean[:140].strip(" .") or "paper"

    @staticmethod
    def _normalize_pdf_url(url: str) -> str:
        if "arxiv.org/abs/" in url:
            return url.replace("/abs/", "/pdf/") + ".pdf"
        return url

    def download(self, paper: Paper, role: str) -> Path | None:
        if not paper.open_access_pdf:
            self.logger.warning("无开放 PDF：%s", paper.title)
            return None
        target = self.daily_directory(role) / f"{self._safe_name(paper.title)}.pdf"
        if target.exists() and target.stat().st_size > 1024:
            return target
        try:
            response = self.http.request(
                "GET",
                self._normalize_pdf_url(paper.open_access_pdf),
                stream=True,
                headers={"User-Agent": "EmbodiedAIResearchBot/1.0"},
            )
            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" not in content_type and urlparse(
                response.url
            ).path.lower().endswith(".pdf") is False:
                raise RuntimeError("下载地址没有返回 PDF")
            with target.open("wb") as file:
                for chunk in response.iter_content(1024 * 64):
                    if chunk:
                        file.write(chunk)
            return target
        except Exception:
            self.logger.exception("PDF 下载失败：%s", paper.title)
            if target.exists():
                target.unlink()
            return None

    def extract_first_pages(self, path: Path | None, pages: int = 2) -> str:
        if path is None:
            return ""
        try:
            with pdfplumber.open(path) as pdf:
                return "\n".join(
                    page.extract_text() or "" for page in pdf.pages[:pages]
                )
        except Exception:
            self.logger.exception("PDF 文本提取失败：%s", path)
            return ""

