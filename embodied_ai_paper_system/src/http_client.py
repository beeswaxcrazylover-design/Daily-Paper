"""带限速、重试和错误日志的 HTTP 客户端。"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests


class ResilientHttpClient:
    def __init__(
        self,
        timeout: int,
        interval: float,
        max_retries: int,
    ) -> None:
        self.timeout = timeout
        self.interval = interval
        self.max_retries = max_retries
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.interval)
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                if response.status_code == 429 or response.status_code >= 500:
                    raise requests.HTTPError(
                        f"服务暂不可用：HTTP {response.status_code}",
                        response=response,
                    )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_error = exc
                wait = min(2 ** attempt, 20)
                self.logger.warning(
                    "请求失败（%s/%s）：%s；%s 秒后重试",
                    attempt,
                    self.max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)
        raise RuntimeError(f"请求最终失败：{url}") from last_error

