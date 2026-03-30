import json
import logging
from datetime import datetime, timedelta, timezone
from openai import OpenAI
from supabase import create_client

from src.config import (
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
    OPENAI_API_KEY, OPENAI_MODEL, MAX_BODY_CHARS,
    SUBREDDIT_GROUPS,
)

logger = logging.getLogger(__name__)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
openai = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a market research analyst for SoloSolutionsAI, a platform that helps solo professionals and small business owners automate client interactions.

Analyze these Reddit posts from small business communities and extract actionable intelligence.

Return a JSON object with exactly this structure:
{
  "themes": [
    {"theme": "short theme name", "frequency": number_of_posts_mentioning_it, "example_quote": "verbatim quote from a post"}
  ],
  "phrases": ["exact verbatim phrase 1", "exact verbatim phrase 2"],
  "hooks": ["compelling hook that could be used in social media or ads"],
  "angles": [
    {"angle": "messaging angle name", "rationale": "why this would resonate"}
  ]
}

Rules:
- Return exactly 5 themes, 10 phrases, 5 hooks, and 3 angles
- Phrases must be VERBATIM from the posts — do not paraphrase
- Hooks should be ready to use in social media posts or ads
- Focus on pain points related to: missed calls, lost leads, being overwhelmed, wearing too many hats, work-life balance, client communication gaps
- Be concise and specific. No generic insights."""


def get_recent_posts(hours: int = 24) -> list[dict]:
    """Pull posts crawled in the last N hours."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    result = supabase.table("spider_raw_posts") \
        .select("*") \
        .gte("crawled_at", cutoff) \
        .order("score", desc=True) \
        .execute()

    return result.data or []


def group_posts(posts: list[dict]) -> dict[str, list[dict]]:
    """Group posts by subreddit group."""
    # Build reverse lookup: subreddit -> group
    sub_to_group = {}
    for group, subs in SUBREDDIT_GROUPS.items():
        for s in subs:
            sub_to_group[s] = group

    grouped = {g: [] for g in SUBREDDIT_GROUPS}
    for post in posts:
        group = sub_to_group.get(post["subreddit"])
        if group:
            grouped[group].append(post)

    return grouped


def format_posts_for_prompt(posts: list[dict]) -> str:
    """Format posts into a compact text block for the LLM."""
    lines = []
    for i, post in enumerate(posts[:250], 1):  # cap at 250 per group
        body = (post.get("body") or "")[:MAX_BODY_CHARS]
        comments = post.get("top_comments") or []
        comment_text = " | ".join(
            c.get("body", "")[:200] for c in comments[:3]
        )

        lines.append(
            f"[{i}] r/{post['subreddit']} | Score: {post['score']} | "
            f"Comments: {post['num_comments']}\n"
            f"Title: {post['title']}\n"
            f"{body}\n"
            f"Top comments: {comment_text}\n"
        )

    return "\n---\n".join(lines)


def analyze_group(posts: list[dict], group_name: str) -> dict | None:
    """Send a group of posts to OpenAI for analysis."""
    if not posts:
        logger.info(f"No posts for group '{group_name}', skipping")
        return None

    formatted = format_posts_for_prompt(posts)

    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze these {len(posts)} posts from the '{group_name}' category:\n\n{formatted}"},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        logger.info(f"Group '{group_name}': analyzed {len(posts)} posts")
        return result

    except Exception as e:
        logger.error(f"OpenAI analysis failed for '{group_name}': {e}")
        return None


def store_insights(group_name: str, insights: dict, post_count: int):
    """Store insights in spider_insights table."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        supabase.table("spider_insights").upsert({
            "date": today,
            "subreddit_group": group_name,
            "themes": insights.get("themes", []),
            "phrases": insights.get("phrases", []),
            "hooks": insights.get("hooks", []),
            "angles": insights.get("angles", []),
            "raw_post_count": post_count,
        }, on_conflict="date,subreddit_group").execute()

    except Exception as e:
        logger.error(f"Failed to store insights for '{group_name}': {e}")


def analyze_all() -> list[dict]:
    """Pull recent posts, analyze by group, store insights. Returns insight list."""
    posts = get_recent_posts(hours=24)
    logger.info(f"Analyzing {len(posts)} posts from last 24h")

    if not posts:
        return []

    grouped = group_posts(posts)
    all_insights = []

    # Analyze each group
    for group_name, group_posts_list in grouped.items():
        insights = analyze_group(group_posts_list, group_name)
        if insights:
            store_insights(group_name, insights, len(group_posts_list))
            all_insights.append({
                "group": group_name,
                "post_count": len(group_posts_list),
                **insights,
            })

    # Cross-cutting analysis (top 50 posts by score across all groups)
    top_posts = sorted(posts, key=lambda p: p["score"], reverse=True)[:50]
    cross_insights = analyze_group(top_posts, "all")
    if cross_insights:
        store_insights("all", cross_insights, len(top_posts))
        all_insights.append({
            "group": "all",
            "post_count": len(top_posts),
            **cross_insights,
        })

    logger.info(f"Analysis complete: {len(all_insights)} insight groups")
    return all_insights
