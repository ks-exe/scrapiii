from __future__ import annotations

from dataclasses import dataclass
from time import sleep
from typing import Optional

import requests

from src.cache import DiskCache
from src.config import (
    MAX_RETRIES,
    POLITENESS_DELAY_SECONDS,
    REQUEST_HEADERS,
    RETRY_DELAY_SECONDS,
    TIMEOUT_SECONDS,
)


@dataclass(frozen=True)
class FetchOutcome:
    url: str
    html: Optional[str]
    from_cache: bool
    status_code: Optional[int] = None
    error: Optional[str] = None


class PoliteFetcher:
    """HTTP client with disk caching, retry rules, and live-request delays."""

    def __init__(self, cache: DiskCache) -> None:
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update(REQUEST_HEADERS)
        self.pages_fetched = 0
        self.cache_hits = 0
        self.failed_pages = 0

    def fetch(self, url: str) -> FetchOutcome:
        cached_html = self.cache.read(url)
        if cached_html is not None:
            self.cache_hits += 1
            print(f"CACHE HIT {url}")
            return FetchOutcome(url=url, html=cached_html, from_cache=True, status_code=200)

        print(f"FETCH {url}")
        attempts = MAX_RETRIES + 1
        last_error = "request failed"
        last_status_code: Optional[int] = None

        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(url, timeout=TIMEOUT_SECONDS)
                last_status_code = response.status_code
                html = response.text

                if response.status_code == 200:
                    self.cache.write(url, html)
                    self.pages_fetched += 1
                    sleep(POLITENESS_DELAY_SECONDS)
                    return FetchOutcome(url=url, html=html, from_cache=False, status_code=200)

                last_error = f"HTTP {response.status_code}"
                sleep(POLITENESS_DELAY_SECONDS)

                if response.status_code in {403, 404}:
                    break
                if 500 <= response.status_code <= 599 and attempt < attempts:
                    sleep(RETRY_DELAY_SECONDS)
                    continue
                break

            except requests.Timeout as exc:
                last_error = f"timeout: {exc}"
                sleep(POLITENESS_DELAY_SECONDS)
                if attempt < attempts:
                    sleep(RETRY_DELAY_SECONDS)
                    continue
                break
            except requests.RequestException as exc:
                last_error = f"request error: {exc}"
                break

        self.failed_pages += 1
        return FetchOutcome(
            url=url,
            html=None,
            from_cache=False,
            status_code=last_status_code,
            error=last_error,
        )

