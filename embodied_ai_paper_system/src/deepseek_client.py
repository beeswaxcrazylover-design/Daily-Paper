"""DeepSeek JSON 模式客户端。"""

from __future__ import annotations

import json
import logging

from config.settings import Settings
from src.http_client import ResilientHttpClient


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.http = ResilientHttpClient(
            settings.request_timeout,
            settings.request_interval,
            settings.max_retries,
        )
        self.logger = logging.getLogger(__name__)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        response = self.http.request(
            "POST",
            f"{self.settings.deepseek_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        content = response.json()["choices"][0]["message"]["content"]
        if not content:
            raise RuntimeError("DeepSeek 返回了空内容")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            self.logger.error("DeepSeek 非法 JSON：%s", content[:500])
            raise RuntimeError("DeepSeek 未返回合法 JSON") from exc

