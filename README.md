# SoloSolutions Spider

Market research crawler. Reads Reddit for small business pain points, analyses them with
GPT-4o, stores the findings, and emails a daily brief. Runs unattended on GitHub Actions.

Built because market research is a job nobody does consistently by hand. A crawler does it
every morning at six whether or not anyone remembers to ask.

## Architecture

```
GitHub Actions (daily 6am ET)
  -> crawler.py (Reddit public JSON feeds)
  -> spider_raw_posts (Supabase)
  -> analyzer.py (OpenAI GPT-4o)
  -> spider_insights (Supabase)
  -> emailer.py (Resend)
  -> your inbox (RECIPIENT_EMAIL)
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
