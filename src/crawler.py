from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.config import ENTRYPOINT_URL, MAX_CATALOGUE_PAGES
from src.fetcher import PoliteFetcher


@dataclass(frozen=True)
class DiscoveredBook:
    url: str
    source_page: str


def discover_books(
    fetcher: PoliteFetcher,
    entrypoint_url: str = ENTRYPOINT_URL,
    max_pages: int = MAX_CATALOGUE_PAGES,
) -> Tuple[List[DiscoveredBook], List[dict]]:
    discovered: Dict[str, DiscoveredBook] = {}
    errors: List[dict] = []
    current_url = entrypoint_url

    for _ in range(max_pages):
        outcome = fetcher.fetch(current_url)
        if outcome.html is None:
            errors.append(
                {
                    "stage": "catalogue_fetch",
                    "url": current_url,
                    "reason": outcome.error or "unknown fetch error",
                    "status_code": outcome.status_code,
                }
            )
            break

        soup = BeautifulSoup(outcome.html, "html.parser")

        for link in soup.select("ol.row article.product_pod h3 a[href]"):
            absolute_url = urljoin(current_url, link["href"])
            discovered.setdefault(
                absolute_url,
                DiscoveredBook(url=absolute_url, source_page=current_url),
            )

        next_link = soup.select_one("li.next a[href]")
        if next_link is None:
            break
        current_url = urljoin(current_url, next_link["href"])

    return list(discovered.values()), errors

