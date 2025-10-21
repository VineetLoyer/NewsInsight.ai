# API Integration Guide

## Overview

The updated NewsInsight app now supports **real-time API fetching** for news articles. When you search for a topic, the app will:

1. **Try fetching from APIs first** (NewsAPI + Guardian) if API keys are configured
2. **Fall back to DynamoDB cache** if APIs don't have results or keys aren't set
3. **Show a loading spinner** while fetching

## Getting API Keys

### NewsAPI (Recommended)

1. Go to [https://newsapi.org](https://newsapi.org)
2. Click **"Get API Key"**
3. Sign up with email
4. Copy your API key from the dashboard

**Features:**
- Free tier: 100 requests/day
- 20,000 articles/month
- Search across 150+ news sources
- Excellent for technology, business, politics

### Guardian API (Optional)

1. Go to [https://open-platform.theguardian.com](https://open-platform.theguardian.com)
2. Click **"Register"** to create account
3. Generate API key from dashboard
4. Copy your API key

**Features:**
- Free tier: 500 requests/day
- Extensive archive going back 30+ years
- Very detailed articles
- Great for research

## Configuration

### Option 1: Environment Variables (Recommended)

Set environment variables before running the app:

**Windows PowerShell:**
```powershell
$env:NEWSAPI_KEY = "your-newsapi-key-here"
$env:GUARDIAN_KEY = "your-guardian-key-here"
$env:DEBUG_MODE = "true"  # For verbose logging
streamlit run app.py
```

**Windows CMD:**
```cmd
set NEWSAPI_KEY=your-newsapi-key-here
set GUARDIAN_KEY=your-guardian-key-here
set DEBUG_MODE=true
streamlit run app.py
```

**Linux/Mac (bash):**
```bash
export NEWSAPI_KEY="your-newsapi-key-here"
export GUARDIAN_KEY="your-guardian-key-here"
export DEBUG_MODE="true"
streamlit run app.py
```

### Option 2: .streamlit/secrets.toml (Local Development)

Create/edit `.streamlit/secrets.toml` in your workspace:

```toml
NEWSAPI_KEY = "your-newsapi-key-here"
GUARDIAN_KEY = "your-guardian-key-here"
DEBUG_MODE = "true"
```

Streamlit will automatically load these as environment variables.

### Option 3: .env File (with python-dotenv)

Create `.env` file in project root:

```
NEWSAPI_KEY=your-newsapi-key-here
GUARDIAN_KEY=your-guardian-key-here
DEBUG_MODE=true
```

Then in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Testing the Integration

Run the test script to verify everything works:

```bash
python test_api_integration.py
```

Expected output:
```
✅ news_fetcher imported successfully
✅ NEWSAPI_KEY set: abc123...
✅ GUARDIAN_KEY set: xyz789...
✅ Fetched 3 articles:
   [1] OpenAI Releases GPT-5...
   [2] Microsoft Invests in AI...
   ...
```

## How It Works

### Search Flow

```
User enters "technology" in search box
           ↓
   search_articles_ddb() called
           ↓
   Is topic provided + API keys available?
      ├─ YES → fetch_articles_for_topic()
      │          ├─ Try NewsAPI
      │          ├─ Try Guardian
      │          ├─ Deduplicate + sort by date
      │          └─ Format for display
      │          ↓
      │        Return fresh articles
      │
      └─ NO → Scan DynamoDB table
                └─ Filter by keyword
                └─ Return cached articles
```

### Key Features

✅ **Multi-source deduplication**: Articles from both APIs are deduplicated by URL
✅ **Smart fallback**: If API fails, falls back to DDB cache automatically
✅ **Rate limit handling**: Respects API rate limits and returns what's available
✅ **Debug logging**: Enable `DEBUG_MODE=true` to see all API calls
✅ **Loading UI**: Spinner shows while fetching (only when searching for a topic)

## Troubleshooting

### "No articles found yet" message

**Check 1: Are API keys set?**
```bash
python test_api_integration.py
```

If it says "⚠️  NEWSAPI_KEY not set", add them:
```powershell
$env:NEWSAPI_KEY = "your-key-here"
```

**Check 2: Are API keys valid?**
- NewsAPI: Log into [https://newsapi.org](https://newsapi.org) to verify
- Guardian: Log into [https://open-platform.theguardian.com](https://open-platform.theguardian.com) to verify
- Invalid/expired keys will silently fall back to DDB (if available)

**Check 3: Enable DEBUG_MODE**
```powershell
$env:DEBUG_MODE = "true"
streamlit run app.py
```

You'll see:
- 🔄 [Fetching from APIs for 'technology']
- ✅ [Got 5 articles from APIs]
- ⚠️ [API fetch error: ...] (if there's a problem)

### API Rate Limits

**NewsAPI:**
- Free tier: 100 requests/day
- Each search = 1 request
- If exceeded: Falls back to DDB cache

**Guardian:**
- Free tier: 500 requests/day
- Each search = 1 request

### Slow Searches

If searches are slow (5+ seconds):
1. Check internet connection
2. Set only NEWSAPI_KEY (faster than both)
3. Check `DEBUG_MODE=true` logs for specific API latency

### Getting Different Articles

Each search should ideally show different articles because:
1. APIs return fresh results (not cached)
2. Time-based sorting shows newest first
3. Deduplication removes duplicates between APIs

If you keep seeing the same articles:
- **With API keys**: API sources have limited inventory for that topic
- **Without API keys**: You're seeing DDB cache (search other keywords to test)

## Production Considerations

### Rate Limiting
- Consider caching API results for repeated searches
- Implement request throttling if needed
- Monitor API usage in dashboard

### Error Handling
- Current: Silent fallback to DDB
- Could add: Alerts for API failures
- Could add: Retry logic with exponential backoff

### Cost Management
- NewsAPI free tier: 100 requests/day (usually enough for 10-20 users)
- Guardian free tier: 500 requests/day (very generous)
- Premium tiers available if needed

### Scale
- Current architecture handles ~50 concurrent users
- For higher scale: Add caching layer (Redis/ElastiCache)
- Consider: DynamoDB cache + periodic Lambda refresh

## Advanced: Custom API Integration

Want to add another news source? Edit `news_fetcher.py`:

```python
def fetch_custom_api(query, api_key, page_size=10):
    """Fetch from your custom news source"""
    # Implement your API call here
    return [
        {
            "headline": "Article title",
            "url": "https://example.com/article",
            "date": datetime.now().isoformat(),
            "description": "Short description",
            "source": "CustomSource",
            "author": "Author Name"
        }
    ]

def fetch_articles_for_topic(...):
    # Add call to fetch_custom_api here
    custom_articles = fetch_custom_api(...)
    all_articles.extend(custom_articles)
```

## Summary

| Feature | Status | API Keys Required |
|---------|--------|------------------|
| Search articles by topic | ✅ Works | Yes |
| Fall back to DDB cache | ✅ Works | No |
| Real-time results | ✅ Works | Yes |
| Multi-source deduplication | ✅ Works | Yes |
| Debug logging | ✅ Works | Optional |
| Loading spinner | ✅ Works | N/A |

**Next**: Run `python test_api_integration.py` to verify, then `streamlit run app.py` to test!
