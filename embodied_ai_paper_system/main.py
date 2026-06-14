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


def configure_logging(
    settings: Settings, log_date: date | None = None
) -> None:
    target_date = log_date or date.today()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                settings.log_dir / f"{target_date.isoformat()}.log",
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
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        help="按 YYYY-MM-DD 指定日报日期，仅适用于 daily",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings()
    configure_logging(settings, args.date)
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
    if args.date and args.date > date.today():
        raise ValueError("不能生成未来日期的日报")
    DailyPipeline(settings).run(force=args.force, run_date=args.date)


if __name__ == "__main__":
    main()
