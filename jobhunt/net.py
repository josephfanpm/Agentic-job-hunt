"""One polite HTTP GET with an on-disk cache. Standard library only."""
from __future__ import annotations

import gzip
import hashlib
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "agentic-job-hunt/0.2"


class FetchError(Exception):
    pass


def get(url: str, *, cache_dir: Path | None = None, ttl_hours: float = 0,
        timeout: int = 30, retries: int = 1) -> bytes:
    """Fetch a URL. With cache_dir and ttl_hours, reuse a recent copy.

    Caching matters for manners as much as speed: some free job boards ask
    clients to call only a few times a day.
    """
    cache_file = None
    if cache_dir and ttl_hours > 0:
        cache_file = Path(cache_dir) / (hashlib.sha1(url.encode()).hexdigest() + ".bin")
        if cache_file.exists() and time.time() - cache_file.stat().st_mtime < ttl_hours * 3600:
            return cache_file.read_bytes()
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json, application/xml, text/xml, */*",
        "Accept-Encoding": "gzip"})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
            if cache_file:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_bytes(body)
            return body
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code < 500 and e.code != 429:
                break  # a 404 won't get better
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = str(getattr(e, "reason", e))
        if attempt < retries:
            time.sleep(1.5)
    raise FetchError(f"{url.split('?')[0]}: {last}")
