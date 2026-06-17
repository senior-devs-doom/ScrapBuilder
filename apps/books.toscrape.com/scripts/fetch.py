"""HTTP layer: polite, retrying. (Standard ScrapBuilder fetcher.)"""
from __future__ import annotations

import time
import urllib.robotparser as robotparser
from urllib.parse import urlparse

import requests


class Fetcher:
    def __init__(self, user_agent: str, rate_limit: float = 1.0, timeout: float = 20.0,
                 max_retries: int = 3, respect_robots: bool = True):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries
        self.respect_robots = respect_robots
        self._last_request = 0.0
        self._robots: dict[str, robotparser.RobotFileParser] = {}

    def _throttle(self) -> None:
        wait = self.rate_limit - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlparse(url)
        root = f"{parts.scheme}://{parts.netloc}"
        rp = self._robots.get(root)
        if rp is None:
            rp = robotparser.RobotFileParser()
            rp.set_url(f"{root}/robots.txt")
            try:
                rp.read()
            except Exception:
                pass
            self._robots[root] = rp
        return rp.can_fetch(self.session.headers["User-Agent"], url)

    def get(self, url: str) -> str:
        if not self._allowed(url):
            raise PermissionError(f"robots.txt disallows fetching {url}")
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"status {resp.status_code}")
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or resp.encoding
                return resp.text
            except Exception as e:  # noqa: BLE001
                last_err = e
                time.sleep(2 ** attempt)
        raise RuntimeError(f"failed to fetch {url}: {last_err}")
