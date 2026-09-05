from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup, Tag


class ExtractionError(ValueError):
    pass


def _text_or_none(node: Optional[Tag]) -> Optional[str]:
    if node is None:
        return None
    text = node.get_text(" ", strip=True)
    return text or None


def _required_text(scope: Tag, selector: str, field_name: str) -> str:
    text = _text_or_none(scope.select_one(selector))
    if text is None:
        raise ExtractionError(f"missing required field: {field_name}")
    return text


def _rating_text(product_main: Tag) -> str:
    rating_node = product_main.select_one("p.star-rating")
    if rating_node is None:
        raise ExtractionError("missing required field: rating_text")

    classes = rating_node.get("class", [])
    for class_name in classes:
        if class_name != "star-rating":
            return class_name

    raise ExtractionError("missing rating value in star-rating class")


def extract_book(html: str, product_url: str, source_page: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one("div.product_main")
    if product_main is None:
        raise ExtractionError("missing product_main section")

    description = _text_or_none(soup.select_one("#product_description + p"))

    return {
        "title": _required_text(product_main, "h1", "title"),
        "product_url": product_url,
        "price_text": _required_text(product_main, "p.price_color", "price_text"),
        "availability_text": _required_text(product_main, "p.availability", "availability_text"),
        "rating_text": _rating_text(product_main),
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

