from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASE_URL = "https://books.toscrape.com/"
ENTRYPOINT_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/your-username/scraper)"
REQUEST_HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT_SECONDS = 7.0
POLITENESS_DELAY_SECONDS = 0.5
RETRY_DELAY_SECONDS = 0.75
MAX_RETRIES = 1

CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"
BOOKS_OUTPUT_PATH = OUTPUT_DIR / "books.json"
ERRORS_OUTPUT_PATH = OUTPUT_DIR / "errors.json"
RUN_REPORT_OUTPUT_PATH = OUTPUT_DIR / "run-report.json"

INTENTIONAL_404_URL = "https://books.toscrape.com/catalogue/polite-scraper-intentional-404.html"

