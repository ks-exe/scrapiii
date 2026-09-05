from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional


class DiskCache:
    """Simple URL-keyed disk cache for raw HTML responses."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def path_for_url(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.html"

    def read(self, url: str) -> Optional[str]:
        path = self.path_for_url(url)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def write(self, url: str, html: str) -> None:
        path = self.path_for_url(url)
        path.write_text(html, encoding="utf-8")

