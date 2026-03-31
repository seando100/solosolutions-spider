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
REQUEST_DELAY = 2.0  # seconds between Reddit requests
SEARCH_RESULTS_PER_QUERY = 100
TOP_COMMENTS_PER_POST = 5
MIN_SCORE_FOR_COMMENTS = 3
MIN_COMMENTS_FOR_FETCH = 2

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
