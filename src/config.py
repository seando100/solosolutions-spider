import os
from dotenv import load_dotenv

load_dotenv()

# --- External services ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]

# Brave Search is the data source. Reddit closed unauthenticated .json access,
# so every request the old crawler made returns a 403 HTML page.
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
BRAVE_RESULTS_PER_QUERY = 20
BRAVE_REQUEST_DELAY = 1.1  # Brave's free tier allows roughly one query per second

# --- Email ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "Research <research@example.com>")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")

# --- Reddit ---
# Reddit asks crawlers to identify themselves and give a contact address.
USER_AGENT = f"SoloSolutionsSpider/1.0 (market-research; contact: {os.environ.get('CRAWLER_CONTACT', 'unset')})"
REQUEST_DELAY = 4.0  # seconds between Reddit search requests
COMMENT_DELAY = 6.0  # seconds between comment fetches (Reddit is stricter here)
SEARCH_RESULTS_PER_QUERY = 50  # fewer per search, more targeted
TOP_COMMENTS_PER_POST = 5
MAX_POSTS_FOR_COMMENTS = 30  # only fetch comments for top N posts by score

# --- Search keywords (the real value — finding pain points directly) ---
SEARCH_KEYWORDS = [
    # Sean's keywords
    "sole business owner everyday challenges",
    "solopreneur",
    "small business and AI",
    "small business challenges with AI",
    # Pain-point keywords aligned to SoloSolutionsAI
    "missed calls clients",
    "too many hats small business",
    "client follow up",
    "losing leads",
    "answering phones",
]

# --- Subreddits to search within ---
SUBREDDIT_GROUPS = {
    "general": ["smallbusiness", "Entrepreneur", "freelance", "solopreneur"],
    "legal": ["lawfirm", "lawyers"],
    "healthcare": ["veterinary", "therapists", "insurance"],
    "realestate_finance": ["realtors", "accounting"],
}
ALL_SUBREDDITS = [s for group in SUBREDDIT_GROUPS.values() for s in group]

# --- OpenAI ---
OPENAI_MODEL = "gpt-4o"
MAX_BODY_CHARS = 500  # truncate post body for token management
