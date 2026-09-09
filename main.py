import logging
import sys

from src.brave_source import crawl_all
from src.analyzer import analyze_all
from src.emailer import send_daily_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=== SoloSolutions Spider — starting daily pipeline ===")

    # Step 1: Crawl Reddit
    logger.info("Step 1/3: Searching (Brave)...")
    crawl_stats = crawl_all()
    logger.info(f"Crawl complete: {crawl_stats['posts_crawled']} posts, "
                f"{len(crawl_stats.get('searches_succeeded', []))} searches OK, "
                f"{len(crawl_stats.get('searches_failed', []))} failed")

    # A run that collects nothing is a FAILURE, not a quiet no-op. Exiting zero
    # here is what hid Reddit's 403s for seven weeks: Task Scheduler saw success
    # every morning while nothing was being stored.
    if crawl_stats["posts_crawled"] == 0:
        logger.error(
            "Collected 0 results from %d queries. Treating this as a failure.",
            len(crawl_stats.get("searches_failed", [])),
        )
        sys.exit(2)

    # Step 2: Analyze
    logger.info("Step 2/3: Analyzing with OpenAI...")
    insights = analyze_all()
    logger.info(f"Analysis complete: {len(insights)} insight groups")

    # Step 3: Email summary
    logger.info("Step 3/3: Sending daily summary...")
    success = send_daily_summary(insights, crawl_stats)

    if not success:
        logger.error("Email send failed")
        sys.exit(1)

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
