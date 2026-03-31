import os
from dotenv import load_dotenv

load_dotenv()

# --- External services ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]

# --- Email ---
SENDER_EMAIL = "SoloSolutionsAI Research <intake@sololawyerai.com>"
RECIPIENT_EMAIL = "sean@solosolutionsai.com"

# --- Reddit ---
USER_AGENT = "SoloSolutionsSpider/1.0 (market-research; contact: sean@solosolutionsai.com)"
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
