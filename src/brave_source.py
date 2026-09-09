"""Brave Search source.

Reddit closed unauthenticated access to its .json endpoints, so every request the
old crawler made returns a 403 HTML page. This replaces it with Brave's Search
API, which is a real independent index rather than a scrape, and which the rest
of the platform already uses for customer intelligence reports.

Results are normalised into the same shape `store_posts` already expects, so the
analyser and emailer downstream are unchanged.
"""
import hashlib
import logging
import time
from datetime import datetime, timezone

import requests

from src.config import (
    BRAVE_API_KEY,
    BRAVE_ENDPOINT,
    BRAVE_RESULTS_PER_QUERY,
    BRAVE_REQUEST_DELAY,
    SEARCH_KEYWORDS,
    SUBREDDIT_GROUPS,
    USER_AGENT,
)

logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
})


def _stable_id(url: str) -> str:
    """A deterministic id so re-running a query updates rather than duplicates.

    The column is still named reddit_id because the table predates this change and
    renaming it would mean a migration for no behavioural gain. It holds a source
    id, whatever the source happens to be.
    """
    return "brave:" + hashlib.sha256(url.encode()).hexdigest()[:22]


def parse_result(result: dict, topic: str) -> dict | None:
    """Normalise one Brave result into the shape store_posts expects."""
    url = result.get("url") or ""
    title = (result.get("title") or "").strip()
    if not url or not title:
        return None

    return {
        "reddit_id": _stable_id(url),
        "subreddit": topic,
        "title": title,
        "body": (result.get("description") or "").strip(),
        "score": 0,
        "num_comments": 0,
        "url": url,
        "permalink": url,
        "posted_at": result.get("page_age") or datetime.now(timezone.utc).isoformat(),
        "top_comments": [],
    }


def search(query: str, topic: str) -> list[dict]:
    """One Brave query. Raises on auth or quota failures, because those are not
    conditions to shrug at: a silent empty result is what hid the Reddit outage
    for seven weeks."""
    try:
        resp = session.get(
            BRAVE_ENDPOINT,
            params={"q": query, "count": BRAVE_RESULTS_PER_QUERY},
            headers={"X-Subscription-Token": BRAVE_API_KEY},
            timeout=20,
        )
    except Exception as e:
        logger.warning("Brave request failed for %r: %s", query, e)
        return []

    if resp.status_code in (401, 403):
        raise RuntimeError(
            f"Brave rejected the API key ({resp.status_code}). Check BRAVE_API_KEY."
        )
    if resp.status_code == 429:
        raise RuntimeError("Brave rate limit hit (429). Lower BRAVE_REQUEST_DELAY or the query count.")
    if not resp.ok:
        logger.warning("Brave returned %s for %r", resp.status_code, query)
        return []

    results = (resp.json().get("web") or {}).get("results") or []
    out = [p for p in (parse_result(r, topic) for r in results) if p]
    logger.info("  %-28s %2d results  %r", topic, len(out), query[:52])
    return out


def crawl_all() -> dict:
    """Run every keyword against every topic group.

    Returns the same stats shape the old Reddit crawler did, plus which topics
    produced nothing, so the caller and the daily email can say what actually
    happened rather than reporting a bare zero.
    """
    from src.crawler import store_posts  # storage is shared, not source-specific

    if not BRAVE_API_KEY:
        raise RuntimeError("BRAVE_API_KEY is not set. The spider cannot run without a source.")

    seen: set[str] = set()
    all_posts: list[dict] = []
    succeeded: list[str] = []
    failed: list[str] = []

    for topic, terms in SUBREDDIT_GROUPS.items():
        subject = terms[0] if terms else topic
        for keyword in SEARCH_KEYWORDS:
            query = f"{subject} {keyword}"
            try:
                results = search(query, topic)
            except RuntimeError:
                raise                      # auth and quota failures stop the run
            except Exception as e:
                logger.warning("Query failed %r: %s", query, e)
                failed.append(query)
                continue

            if results:
                succeeded.append(query)
            else:
                failed.append(query)

            for p in results:
                if p["reddit_id"] not in seen:
                    seen.add(p["reddit_id"])
                    all_posts.append(p)

            time.sleep(BRAVE_REQUEST_DELAY)

    stored = store_posts(all_posts)
    logger.info("Brave crawl: %d unique results, %d stored, %d queries OK, %d empty",
                len(all_posts), stored, len(succeeded), len(failed))

    return {
        "posts_crawled": stored,
        "results_seen": len(all_posts),
        "searches_succeeded": succeeded,
        "searches_failed": failed,
        "source": "brave",
    }
