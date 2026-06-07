"""带限速、重试和错误日志的 HTTP 客户端。"""

from __future__ import annotations

import logging
import random
import time
from email.utils import parsedate_to_datetime
from typing import Any

import requests


class ResilientHttpClient:
    def __init__(
        self,
        timeout: int,
        interval: float,
        max_retries: int,
        rate_limit_max_wait: int = 120,
    ) -> None:
        self.timeout = timeout
        self.interval = interval
        self.max_retries = max_retries
        self.rate_limit_max_wait = rate_limit_max_wait
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
                if attempt >= self.max_retries:
                    break
                wait = self._retry_wait(exc, attempt)
                self.logger.warning(
                    "请求失败（%s/%s）：%s；%s 秒后重试",
                    attempt,
                    self.max_retries,
                    exc,
                    wait,
                )
                time.sleep(wait)
        raise RuntimeError(f"请求最终失败：{url}") from last_error

    def _retry_wait(
        self, error: requests.RequestException, attempt: int
    ) -> int:
        response = getattr(error, "response", None)
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "").strip()
            parsed = self._parse_retry_after(retry_after)
            if parsed is not None:
                return min(max(parsed, 1), self.rate_limit_max_wait)
            # 匿名 Semantic Scholar 配额可能需要等待一分钟以上。
            return min(15 * (2 ** (attempt - 1)), self.rate_limit_max_wait)
        return min(2 ** attempt + random.randint(0, 2), 30)

    @staticmethod
    def _parse_retry_after(value: str) -> int | None:
        if not value:
            return None
        if value.isdigit():
            return int(value)
        try:
            retry_time = parsedate_to_datetime(value)
            seconds = retry_time.timestamp() - time.time()
            return max(int(seconds), 1)
        except (TypeError, ValueError, OverflowError):
            return None
