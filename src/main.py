from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from typing import Any, List

from src.cache import DiskCache
from src.config import (
    BOOKS_OUTPUT_PATH,
    CACHE_DIR,
    ERRORS_OUTPUT_PATH,
    INTENTIONAL_404_URL,
    OUTPUT_DIR,
    RUN_REPORT_OUTPUT_PATH,
)
from src.crawler import DiscoveredBook, discover_books
from src.fetcher import PoliteFetcher
from src.parser import ExtractionError, extract_book
from src.schemas import BookRecord, format_validation_error


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Polite Scraper pipeline.")
    parser.add_argument(
        "--inject-bad-url",
        action="store_true",
        help="Replace one discovered book URL with an intentional 404 to verify fault tolerance.",
    )
    return parser.parse_args()


def write_json(path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_failure_injection(discovered_books: List[DiscoveredBook]) -> List[DiscoveredBook]:
    if not discovered_books:
        return discovered_books
    injected = list(discovered_books)
    original = injected[-1]
    injected[-1] = DiscoveredBook(url=INTENTIONAL_404_URL, source_page=original.source_page)
    return injected


def main() -> int:
    args = parse_args()
    started_monotonic = time.perf_counter()
    started_at = utc_now_iso()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cache = DiskCache(CACHE_DIR)
    fetcher = PoliteFetcher(cache)

    records: List[dict] = []
    errors: List[dict] = []
    invalid_records = 0

    discovered_books, crawl_errors = discover_books(fetcher)
    errors.extend(crawl_errors)

    if len(discovered_books) != 60:
        errors.append(
            {
                "stage": "discovery",
                "reason": f"expected 60 unique book URLs, discovered {len(discovered_books)}",
            }
        )

    if args.inject_bad_url:
        discovered_books = apply_failure_injection(discovered_books)

    for discovered_book in discovered_books:
        outcome = fetcher.fetch(discovered_book.url)
        if outcome.html is None:
            errors.append(
                {
                    "stage": "fetch",
                    "url": discovered_book.url,
                    "source_page": discovered_book.source_page,
                    "reason": outcome.error or "unknown fetch error",
                    "status_code": outcome.status_code,
                }
            )
            continue

        try:
            raw_record = extract_book(
                outcome.html,
                product_url=discovered_book.url,
                source_page=discovered_book.source_page,
            )
            validated_record = BookRecord.from_raw(raw_record)
            records.append(validated_record.model_dump())
        except ExtractionError as exc:
            invalid_records += 1
            errors.append(
                {
                    "stage": "extraction",
                    "url": discovered_book.url,
                    "source_page": discovered_book.source_page,
                    "reason": str(exc),
                }
            )
        except Exception as exc:
            invalid_records += 1
            errors.append(
                {
                    "stage": "validation",
                    "url": discovered_book.url,
                    "source_page": discovered_book.source_page,
                    "reason": format_validation_error(exc),
                }
            )

    ended_at = utc_now_iso()
    duration_seconds = round(time.perf_counter() - started_monotonic, 2)

    run_report = {
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration_seconds,
        "pages_fetched": fetcher.pages_fetched,
        "cache_hits": fetcher.cache_hits,
        "discovered_urls": len(discovered_books),
        "valid_records": len(records),
        "invalid_records": invalid_records,
        "failed_pages": fetcher.failed_pages,
    }

    write_json(BOOKS_OUTPUT_PATH, records)
    write_json(ERRORS_OUTPUT_PATH, errors)
    write_json(RUN_REPORT_OUTPUT_PATH, run_report)

    print(
        "DONE "
        f"discovered={len(discovered_books)} "
        f"valid={len(records)} "
        f"invalid={invalid_records} "
        f"failed_pages={fetcher.failed_pages}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

