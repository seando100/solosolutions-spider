# SoloSolutions Spider

Market research crawler for SoloSolutionsAI. Crawls Reddit for small business pain points, analyzes with GPT-4o, emails daily brief.

## Architecture

```
GitHub Actions (daily 6am ET)
  -> crawler.py (Reddit public JSON feeds)
  -> spider_raw_posts (Supabase)
  -> analyzer.py (OpenAI GPT-4o)
  -> spider_insights (Supabase)
  -> emailer.py (Resend)
  -> sean@solosolutionsai.com
```

## Subreddits

- **General:** smallbusiness, Entrepreneur, freelance, solopreneur
- **Legal:** lawfirm, lawyers
- **Healthcare:** veterinary, therapists, insurance
- **Real Estate/Finance:** realtors, accounting

## Local Development

```bash
cp .env.example .env
# Fill in your keys
pip install -r requirements.txt
python main.py
```

## Manual Trigger

Go to GitHub Actions tab and click "Run workflow" on Daily Reddit Crawl.
