import logging
from datetime import datetime, timezone
import resend

from src.config import RESEND_API_KEY, SENDER_EMAIL, RECIPIENT_EMAIL

logger = logging.getLogger(__name__)

resend.api_key = RESEND_API_KEY

GROUP_LABELS = {
    "general": "General Small Business",
    "legal": "Legal",
    "healthcare": "Healthcare & Wellness",
    "realestate_finance": "Real Estate & Finance",
    "all": "Cross-Cutting (All Verticals)",
}


def build_email_html(insights: list[dict], crawl_stats: dict) -> str:
    """Build a styled HTML email from insights."""
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    total_posts = crawl_stats.get("posts_crawled", 0)
    subs_ok = len(crawl_stats.get("subreddits_succeeded", []))
    subs_fail = len(crawl_stats.get("subreddits_failed", []))

    sections_html = ""

    for insight in insights:
        group = insight.get("group", "unknown")
        label = GROUP_LABELS.get(group, group.title())
        count = insight.get("post_count", 0)

        # Themes
        themes_html = ""
        for t in insight.get("themes", []):
            themes_html += f"""
            <div style="margin-bottom:10px;padding:8px 12px;background:#f8fafc;border-left:3px solid #38BDF8;border-radius:4px;">
                <strong style="color:#0F2745;">{t.get('theme','')}</strong>
                <span style="color:#64748b;font-size:12px;"> ({t.get('frequency',0)} mentions)</span><br>
                <em style="color:#475569;font-size:13px;">"{t.get('example_quote','')}"</em>
            </div>"""

        # Phrases
        phrases_html = ""
        for i, p in enumerate(insight.get("phrases", []), 1):
            phrases_html += f'<li style="margin-bottom:4px;color:#334155;">{p}</li>'

        # Hooks
        hooks_html = ""
        for h in insight.get("hooks", []):
            hooks_html += f'<li style="margin-bottom:4px;color:#334155;font-weight:500;">{h}</li>'

        # Angles
        angles_html = ""
        for a in insight.get("angles", []):
            angles_html += f"""
            <div style="margin-bottom:8px;">
                <strong style="color:#0F2745;">{a.get('angle','')}</strong><br>
                <span style="color:#64748b;font-size:13px;">{a.get('rationale','')}</span>
            </div>"""

        sections_html += f"""
        <div style="margin-bottom:32px;">
            <h2 style="color:#0F2745;font-size:18px;margin-bottom:4px;border-bottom:2px solid #38BDF8;padding-bottom:6px;">
                {label}
                <span style="font-size:12px;color:#64748b;font-weight:400;"> ({count} posts analyzed)</span>
            </h2>

            <h3 style="color:#0F2745;font-size:14px;margin:16px 0 8px;">Pain Themes</h3>
            {themes_html}

            <h3 style="color:#0F2745;font-size:14px;margin:16px 0 8px;">Verbatim Phrases</h3>
            <ol style="padding-left:20px;font-size:13px;">{phrases_html}</ol>

            <h3 style="color:#0F2745;font-size:14px;margin:16px 0 8px;">High-Performing Hooks</h3>
            <ul style="padding-left:20px;font-size:13px;">{hooks_html}</ul>

            <h3 style="color:#0F2745;font-size:14px;margin:16px 0 8px;">Messaging Angles</h3>
            {angles_html}
        </div>"""

    failed_note = ""
    if subs_fail > 0:
        failed_subs = ", ".join(crawl_stats.get("subreddits_failed", []))
        failed_note = f'<div style="background:#fef3c7;padding:8px 12px;border-radius:4px;font-size:12px;color:#92400e;margin-top:8px;">Failed subreddits: {failed_subs}</div>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
        <div style="max-width:640px;margin:0 auto;padding:24px;">

            <!-- Header -->
            <div style="background:#0F2745;color:white;padding:20px 24px;border-radius:8px 8px 0 0;">
                <h1 style="margin:0;font-size:20px;">Spider Daily Brief</h1>
                <p style="margin:4px 0 0;font-size:13px;color:#94a3b8;">{today}</p>
            </div>

            <!-- Stats -->
            <div style="background:white;padding:16px 24px;border-bottom:1px solid #e2e8f0;display:flex;gap:24px;">
                <div style="font-size:12px;color:#64748b;">
                    <strong style="color:#0F2745;font-size:20px;">{total_posts}</strong><br>Posts Crawled
                </div>
                <div style="font-size:12px;color:#64748b;">
                    <strong style="color:#0F2745;font-size:20px;">{subs_ok}</strong><br>Subreddits
                </div>
                <div style="font-size:12px;color:#64748b;">
                    <strong style="color:#0F2745;font-size:20px;">{len(insights)}</strong><br>Insight Groups
                </div>
            </div>
            {failed_note}

            <!-- Insights -->
            <div style="background:white;padding:24px;border-radius:0 0 8px 8px;">
                {sections_html}
            </div>

            <!-- Footer -->
            <div style="text-align:center;padding:16px;font-size:11px;color:#94a3b8;">
                Generated by solosolutions-spider &middot; Raw data in Supabase
            </div>
        </div>
    </body>
    </html>"""

    return html


def send_email(html: str) -> bool:
    """Send the summary email via Resend."""
    today = datetime.now(timezone.utc).strftime("%b %d")

    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [RECIPIENT_EMAIL],
            "subject": f"Spider Brief — {today}",
            "html": html,
        })
        logger.info(f"Email sent to {RECIPIENT_EMAIL}")
        return True

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def send_daily_summary(insights: list[dict], crawl_stats: dict) -> bool:
    """Build and send the daily summary email."""
    if not insights:
        logger.warning("No insights to email — skipping")
        return True  # not a failure, just empty

    html = build_email_html(insights, crawl_stats)
    return send_email(html)
