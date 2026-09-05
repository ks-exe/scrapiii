# Polite Scraper

A production-style Python scraper for the sandbox site `https://books.toscrape.com/`.

The scraper starts at `https://books.toscrape.com/catalogue/page-1.html`, follows the catalogue `next` pagination links for exactly 3 pages, resolves relative book links with `urllib.parse.urljoin`, deduplicates them, and extracts exactly 60 unique book detail pages.

## Stack

- Python 3.10+
- `requests` for HTTP
- `beautifulsoup4` for HTML parsing
- `pydantic` v2 for schema validation
- No Playwright, Puppeteer, Selenium, or browser automation

## Project Structure

```text
scraper/
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── cache.py
│   ├── config.py
│   ├── crawler.py
│   ├── fetcher.py
│   ├── main.py
│   ├── parser.py
│   └── schemas.py
└── output/
    ├── books.json
    ├── errors.json
    └── run-report.json
```

Runtime cache files are written to `cache/`, which is intentionally ignored by git.

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python -m src.main
```

The normal run writes:

- `output/books.json`: validated book records
- `output/errors.json`: rejected records or failed fetches
- `output/run-report.json`: run statistics

Reruns are idempotent. The output files are overwritten cleanly and a normal successful run produces exactly 60 records in `output/books.json`.

## Politeness And Fault Tolerance

Every live HTTP request sends this User-Agent:

```text
FlyRankInternship-A9/1.0 (+https://github.com/your-username/scraper)
```

The fetcher uses a strict 7 second timeout. Successful live responses are cached to disk. Cache hits print `CACHE HIT` and do not perform network calls. Live requests print `FETCH`, require HTTP 200, save raw HTML to `cache/`, and wait at least 500 ms before the next live request.

Timeouts and HTTP 5xx responses are retried once after a brief pause. HTTP 403 and 404 responses are not retried. Each URL is handled independently so one failed page does not terminate the pipeline.

## Extracted Fields

Each valid book record keeps the raw provenance fields and adds a normalized price:

- `title`
- `product_url`
- `price_text`
- `availability_text`
- `rating_text`
- `description`
- `source_page`
- `fetched_at`
- `price_gbp`

Validation enforces HTTP/HTTPS URLs, required string fields, ISO 8601 timestamps, and `price_gbp >= 0.0`.

## Deliberate Failure Test

Use this flag to replace one discovered book URL with an intentional 404:

```bash
python -m src.main --inject-bad-url
```

Expected behavior:

- scraper exits cleanly
- 59 valid records are written to `output/books.json`
- the failed 404 fetch is written to `output/errors.json`
- `output/run-report.json` reports `failed_pages: 1`

After running the failure test, run the normal command again before final submission:

```bash
python -m src.main
```

## Verification

Compile check:

```bash
python -m compileall src
```

Count valid records:

```bash
python -c "import json; print(len(json.load(open('output/books.json', encoding='utf-8'))))"
```

Expected normal output:

```text
60
```
