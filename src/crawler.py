import logging
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

from src.config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    USER_AGENT, REQUEST_DELAY, SEARCH_RESULTS_PER_QUERY,
    TOP_COMMENTS_PER_POST, MIN_SCORE_FOR_COMMENTS,
    MIN_COMMENTS_FOR_FETCH, ALL_SUBREDDITS, SEARCH_KEYWORDS,
)

logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def parse_post(child: dict, source_sub: str = "") -> dict | None:
    """Parse a Reddit post JSON object into our format."""
    post = child.get("data", {})
    if post.get("stickied"):
        return None

    return {
        "reddit_id": post["id"],
        "subreddit": post.get("subreddit", source_sub),
        "title": post.get("title", ""),
        "body": post.get("selftext", ""),
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "url": post.get("url", ""),
        "permalink": f"https://www.reddit.com{post.get('permalink', '')}",
        "posted_at": datetime.fromtimestamp(
            post.get("created_utc", 0), tz=timezone.utc
        ).isoformat(),
        "top_comments": [],
    }


def search_reddit(query: str, subreddit: str | None = None) -> list[dict]:
    """Search Reddit for posts matching a query. Optionally scoped to a subreddit."""
    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",
            "sort": "relevance",
            "t": "week",
            "limit": SEARCH_RESULTS_PER_QUERY,
            "raw_json": 1,
        }
    else:
        url = "https://www.reddit.com/search.json"
        params = {
            "q": query,
            "sort": "relevance",
            "t": "week",
            "limit": SEARCH_RESULTS_PER_QUERY,
            "raw_json": 1,
        }

    try:
        resp = session.get(url, params=params, timeout=15)

        if resp.status_code == 429:
            logger.warning(f"Rate limited searching '{query}', sleeping 60s...")
            time.sleep(60)
            resp = session.get(url, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            parsed = parse_post(child)
            if parsed:
                posts.append(parsed)

        scope = f"r/{subreddit}" if subreddit else "all"
        logger.info(f"Search '{query}' in {scope}: {len(posts)} posts")
        return posts

    except Exception as e:
        scope = f"r/{subreddit}" if subreddit else "all"
        logger.error(f"Search '{query}' in {scope}: failed — {e}")
        return []


def fetch_top_comments(reddit_id: str) -> list[dict]:
    """Fetch top comments for a post."""
    url = f"https://www.reddit.com/comments/{reddit_id}.json"
    params = {"raw_json": 1, "limit": TOP_COMMENTS_PER_POST, "sort": "top"}

    try:
        resp = session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        comments = []
        if len(data) > 1:
            for child in data[1].get("data", {}).get("children", []):
                comment = child.get("data", {})
                if child.get("kind") != "t1":
                    continue
                comments.append({
                    "body": comment.get("body", ""),
                    "score": comment.get("score", 0),
                })

        return comments[:TOP_COMMENTS_PER_POST]

    except Exception as e:
        logger.warning(f"Comments for {reddit_id}: failed — {e}")
        return []


def store_posts(posts: list[dict]) -> int:
    """Upsert posts into spider_raw_posts. Returns count stored."""
    if not posts:
        return 0

    stored = 0
    for post in posts:
        try:
            supabase.table("spider_raw_posts").upsert(
                post, on_conflict="reddit_id"
            ).execute()
            stored += 1
        except Exception as e:
            logger.warning(f"Failed to store post {post['reddit_id']}: {e}")

    return stored


def crawl_all() -> dict:
    """Search Reddit for pain points using keywords. Returns stats."""
    all_posts = {}  # keyed by reddit_id to deduplicate across searches
    searches_succeeded = []
    searches_failed = []

    # Search each keyword across all of Reddit (broader net)
    for keyword in SEARCH_KEYWORDS:
        posts = search_reddit(keyword)
        if posts:
            searches_succeeded.append(keyword)
            for p in posts:
                all_posts[p["reddit_id"]] = p
        else:
            searches_failed.append(keyword)
        time.sleep(REQUEST_DELAY)

    # Also search within our target subreddits for broader terms
    broad_terms = ["struggling", "overwhelmed", "can't keep up", "burned out"]
    for sub in ALL_SUBREDDITS:
        for term in broad_terms:
            posts = search_reddit(term, subreddit=sub)
            if posts:
                for p in posts:
                    all_posts[p["reddit_id"]] = p
            time.sleep(REQUEST_DELAY)

    unique_posts = list(all_posts.values())

    # Fetch comments for posts with engagement
    comment_count = 0
    for post in unique_posts:
        if post["score"] >= MIN_SCORE_FOR_COMMENTS or post["num_comments"] >= MIN_COMMENTS_FOR_FETCH:
            post["top_comments"] = fetch_top_comments(post["reddit_id"])
            comment_count += 1
            time.sleep(REQUEST_DELAY)

    logger.info(f"Fetched comments for {comment_count} posts with engagement")

    stored = store_posts(unique_posts)

    stats = {
        "posts_crawled": len(unique_posts),
        "posts_stored": stored,
        "comments_fetched": comment_count,
        "searches_succeeded": searches_succeeded,
        "searches_failed": searches_failed,
    }

    logger.info(f"Crawl complete: {stats['posts_crawled']} unique posts, "
                f"{len(searches_succeeded)} keyword searches OK, "
                f"{len(searches_failed)} failed")
    return stats
