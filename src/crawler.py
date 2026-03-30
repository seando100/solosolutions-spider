import logging
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

from src.config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    USER_AGENT, REQUEST_DELAY, POSTS_PER_SUBREDDIT,
    TOP_COMMENTS_PER_POST, MIN_SCORE_FOR_COMMENTS,
    MIN_COMMENTS_FOR_FETCH, ALL_SUBREDDITS,
)

logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def fetch_subreddit_posts(subreddit: str) -> list[dict]:
    """Fetch hot posts from a subreddit via public JSON feed."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    params = {"limit": POSTS_PER_SUBREDDIT, "raw_json": 1}

    try:
        resp = session.get(url, params=params, timeout=15)

        if resp.status_code == 429:
            logger.warning(f"Rate limited on r/{subreddit}, sleeping 60s...")
            time.sleep(60)
            resp = session.get(url, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            if post.get("stickied"):
                continue  # skip pinned mod posts

            posts.append({
                "reddit_id": post["id"],
                "subreddit": subreddit,
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
            })

        logger.info(f"r/{subreddit}: fetched {len(posts)} posts")
        return posts

    except Exception as e:
        logger.error(f"r/{subreddit}: failed to fetch — {e}")
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
    """Crawl all configured subreddits. Returns stats."""
    all_posts = []
    succeeded = []
    failed = []

    for sub in ALL_SUBREDDITS:
        posts = fetch_subreddit_posts(sub)
        if posts:
            succeeded.append(sub)
            all_posts.extend(posts)
        else:
            failed.append(sub)
        time.sleep(REQUEST_DELAY)

    # Fetch comments for high-engagement posts
    comment_count = 0
    for post in all_posts:
        if post["score"] >= MIN_SCORE_FOR_COMMENTS or post["num_comments"] >= MIN_COMMENTS_FOR_FETCH:
            post["top_comments"] = fetch_top_comments(post["reddit_id"])
            comment_count += 1
            time.sleep(REQUEST_DELAY)

    logger.info(f"Fetched comments for {comment_count} high-engagement posts")

    stored = store_posts(all_posts)

    stats = {
        "posts_crawled": len(all_posts),
        "posts_stored": stored,
        "comments_fetched": comment_count,
        "subreddits_succeeded": succeeded,
        "subreddits_failed": failed,
    }

    logger.info(f"Crawl complete: {stats['posts_crawled']} posts from {len(succeeded)} subreddits")
    return stats
