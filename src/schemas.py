from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class BookRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    product_url: str
    price_text: str
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str
    price_gbp: float = Field(ge=0.0)

    @field_validator("title", "price_text", "availability_text", "rating_text")
    @classmethod
    def require_non_empty_string(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("product_url", "source_page")
    @classmethod
    def require_http_url(cls, value: str) -> str:
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return value

    @field_validator("fetched_at")
    @classmethod
    def require_iso8601_timestamp(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("must be an ISO 8601 timestamp string")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("must be an ISO 8601 timestamp string") from exc
        return value

    @classmethod
    def from_raw(cls, raw_record: dict[str, Any]) -> "BookRecord":
        normalized_record = dict(raw_record)
        normalized_record["price_gbp"] = normalize_price_gbp(raw_record.get("price_text"))
        return cls.model_validate(normalized_record)


def normalize_price_gbp(price_text: Any) -> float:
    if not isinstance(price_text, str):
        raise ValueError("price_text must be a string")

    cleaned = re.sub(r"[^0-9.]", "", price_text).strip()
    if not cleaned:
        raise ValueError("price_text does not contain a numeric value")

    try:
        return float(cleaned)
    except ValueError as exc:
        raise ValueError(f"could not parse price_text: {price_text!r}") from exc


def format_validation_error(exc: Exception) -> Any:
    if isinstance(exc, ValidationError):
        return exc.errors()
    return str(exc)

