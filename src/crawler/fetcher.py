"""
HTTP Fetcher module with headers, session handling, polite rate-limiting, and error handling.
"""

import random
import sys
import time
from typing import Optional, Tuple
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
}


class PoliteFetcher:
    """Handles HTTP requests with realistic User-Agent, retries, and rate limiting."""

    def __init__(
        self,
        headers: Optional[dict] = None,
        timeout: int = 15,
        delay_min: float = 1.5,
        delay_max: float = 2.5,
    ):
        self.headers = headers or DEFAULT_HEADERS
        self.timeout = timeout
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def sleep_polite(self, delay_min: Optional[float] = None, delay_max: Optional[float] = None):
        """Sleep for a random duration to comply with scraping etiquette."""
        d_min = delay_min if delay_min is not None else self.delay_min
        d_max = delay_max if delay_max is not None else self.delay_max
        time.sleep(random.uniform(d_min, d_max))

    def fetch(
        self,
        url: str,
        max_retries: int = 3,
    ) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Fetch HTML content of a URL.
        Handles HTTP 429 backoff retries and network exceptions.

        Returns:
            (http_status_code, html_text, error_message)
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 429:
                    backoff = 8.0 * (attempt + 1)
                    print(f"  [Fetcher] HTTP 429 rate limit hit. Backing off for {backoff:.1f}s...")
                    time.sleep(backoff)
                    continue
                return response.status_code, response.text, None
            except requests.RequestException as exc:
                if attempt == max_retries:
                    return None, None, str(exc)
                time.sleep(random.uniform(2.0, 3.5))
        return None, None, "Max retries exceeded"
