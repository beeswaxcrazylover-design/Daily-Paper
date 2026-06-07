import unittest

import requests

from src.http_client import ResilientHttpClient


class HttpClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ResilientHttpClient(10, 0, 3)

    def test_numeric_retry_after(self) -> None:
        self.assertEqual(self.client._parse_retry_after("60"), 60)

    def test_invalid_retry_after(self) -> None:
        self.assertIsNone(self.client._parse_retry_after("invalid"))

    def test_429_without_header_uses_long_backoff(self) -> None:
        response = requests.Response()
        response.status_code = 429
        error = requests.HTTPError(response=response)
        self.assertEqual(self.client._retry_wait(error, 1), 15)
        self.assertEqual(self.client._retry_wait(error, 2), 30)


if __name__ == "__main__":
    unittest.main()
