"""
news_fetcher.py - Real-time article fetching from public APIs
Used by app.py to fetch articles on-demand when users search for topics
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib

# NewsAPI
NEWSAPI_BASE = "https://newsapi.org/v2/everything"
NEWSAPI_KEY = "demo"  # Can be overridden via environment variable

# Guardian API
GUARDIAN_BASE = "https://content.guardianapis.com/search"
GUARDIAN_KEY = "demo"  # Can be overridden via environment variable

def fetch_newsapi(query: str, api_key: str = NEWSAPI_KEY, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch articles from NewsAPI.org
    
    Args:
        query: Search keyword (e.g., "artificial intelligence")
        api_key: NewsAPI key (get from https://newsapi.org)
        page_size: Number of articles to fetch (max 100)
    
    Returns:
        List of article dicts with: headline, url, date, description, source, author
    """
    try:
        if api_key == "demo":
            return []  # Demo key won't work
        
        params = {
            "q": query,
            "pageSize": str(min(page_size, 100)),
            "sortBy": "publishedAt",
            "language": "en"
        }
        
        qs = urllib.parse.urlencode(params)
        url = f"{NEWSAPI_BASE}?{qs}&apiKey={api_key}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "newsinsights-ai/0.2"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        
        articles = []
        for article in data.get("articles", []):
            if not article.get("title"):
                continue
            
            articles.append({
                "source": "newsapi",
                "headline": article.get("title", ""),
                "url": article.get("url", ""),
                "date": article.get("publishedAt", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "author": article.get("author", ""),
                "image": article.get("urlToImage", "")
            })
        
        return articles
    
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"NewsAPI error: Invalid API key. Get one at https://newsapi.org")
        elif e.code == 429:
            print(f"NewsAPI error: Rate limited. Try again later.")
        else:
            print(f"NewsAPI HTTP error: {e.code}")
        return []
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return []

def fetch_guardian(query: str, api_key: str = GUARDIAN_KEY, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch articles from The Guardian API
    
    Args:
        query: Search keyword
        api_key: Guardian API key (get from https://open-platform.theguardian.com)
        page_size: Number of articles (max 200)
    
    Returns:
        List of article dicts
    """
    try:
        if api_key == "demo":
            return []
        
        params = {
            "q": query,
            "page-size": str(min(page_size, 200)),
            "order-by": "newest",
            "show-fields": "headline,trailText,byline,thumbnail",
            "api-key": api_key
        }
        
        qs = urllib.parse.urlencode(params)
        url = f"{GUARDIAN_BASE}?{qs}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "newsinsights-ai/0.2"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        
        articles = []
        for result in data.get("response", {}).get("results", []):
            fields = result.get("fields", {}) or {}
            
            articles.append({
                "source": "guardian",
                "headline": fields.get("headline", "") or result.get("webTitle", ""),
                "url": result.get("webUrl", ""),
                "date": result.get("webPublicationDate", ""),
                "description": fields.get("trailText", ""),
                "content": "",
                "author": fields.get("byline", ""),
                "image": fields.get("thumbnail", "")
            })
        
        return articles
    
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"Guardian API error: Invalid API key. Get one at https://open-platform.theguardian.com")
        elif e.code == 429:
            print(f"Guardian API error: Rate limited. Try again later.")
        else:
            print(f"Guardian HTTP error: {e.code}")
        return []
    except Exception as e:
        print(f"Guardian API error: {e}")
        return []

def fetch_articles_for_topic(topic: str, 
                             newsapi_key: Optional[str] = None,
                             guardian_key: Optional[str] = None,
                             limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch articles for a given topic from multiple sources
    
    Args:
        topic: Search topic/keyword
        newsapi_key: Optional NewsAPI key override
        guardian_key: Optional Guardian API key override
        limit: Max articles to return
    
    Returns:
        Combined list of articles from all sources, sorted by date (newest first)
    """
    articles = []
    
    # Fetch from NewsAPI if key provided
    if newsapi_key:
        articles.extend(fetch_newsapi(topic, newsapi_key, page_size=limit))
    
    # Fetch from Guardian if key provided
    if guardian_key:
        articles.extend(fetch_guardian(topic, guardian_key, page_size=limit))
    
    # Sort by date (newest first)
    try:
        articles.sort(
            key=lambda x: datetime.fromisoformat(
                x.get("date", "").replace("Z", "+00:00")
            ) if x.get("date") else datetime.min,
            reverse=True
        )
    except Exception as e:
        print(f"Error sorting articles: {e}")
    
    # Remove duplicates (by URL)
    seen_urls = set()
    unique = []
    for article in articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)
    
    return unique[:limit]

def generate_article_id(url: str) -> str:
    """Generate consistent ID for article based on URL"""
    return hashlib.sha256(url.encode()).hexdigest()[:16]

def format_article_for_display(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format API article for Streamlit display
    
    Converts API response to standard DynamoDB schema
    """
    return {
        "id": generate_article_id(article.get("url", "")),
        "headline": article.get("headline", "Untitled"),
        "summary": article.get("description", ""),
        "date": article.get("date", ""),
        "source": article.get("source", "unknown"),
        "url": article.get("url", ""),
        "author": article.get("author", ""),
        "sentiment": "neutral",  # Will be set by LLM if available
        "entities": [],
        "image": article.get("image", "")
    }
