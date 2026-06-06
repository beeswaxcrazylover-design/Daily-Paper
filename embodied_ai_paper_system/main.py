"""命令行入口。"""

from __future__ import annotations

import argparse
import logging
from datetime import date

from config.settings import Settings
from src.deepseek_client import DeepSeekClient
from src.landmark_discovery import LandmarkDiscovery
from src.pipeline import DailyPipeline
from src.semantic_scholar import SemanticScholarClient


def configure_logging(settings: Settings) -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                settings.log_dir / f"{date.today().isoformat()}.log",
                encoding="utf-8",
            ),
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="具身智能论文自动化系统")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["daily", "landmarks"],
        default="daily",
    )
    parser.add_argument("--force", action="store_true", help="忽略日期状态强制运行")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings()
    configure_logging(settings)
    if args.command == "landmarks":
        settings.validate()
        discovery = LandmarkDiscovery(
            settings,
            SemanticScholarClient(settings),
            DeepSeekClient(settings),
        )
        papers = discovery.update(force=args.force)
        logging.info("基石论文库当前包含 %s 篇论文", len(papers))
        return
    DailyPipeline(settings).run(force=args.force)


if __name__ == "__main__":
    main()

