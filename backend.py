#!/usr/bin/env python3
"""
FastAPI backend for NewsInsight React UI
Integrates with existing app.py functionality
"""

import os
import json
import sys
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from functools import lru_cache
import asyncio
import boto3
import requests

# Import content filtering
try:
    from content_filter import ContentFilter
except ImportError:
    ContentFilter = None
    print("⚠️ Content filtering not available - install content_filter.py")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ---------- Config (copied from app.py) ----------
# AWS_PROFILE not needed for Railway (uses direct credentials)
AWS_REGION      = os.getenv("AWS_REGION", "us-west-2")
DDB_TABLE       = os.getenv("DDB_TABLE", "news_metadata")
PROC_BUCKET     = os.getenv("PROC_BUCKET", "")
MODEL_FAMILY    = os.getenv("MODEL_FAMILY", "anthropic").lower()
BEDROCK_MODELID = os.getenv("BEDROCK_MODEL_ID", "")
DEBUG_MODE      = os.getenv("DEBUG_MODE", "false").lower() == "true"
NEWSAPI_KEY     = os.getenv("NEWSAPI_KEY")
GUARDIAN_KEY    = os.getenv("GUARDIAN_KEY")
RAW_BUCKET      = os.getenv("RAW_BUCKET")
PROCESSED_PREFIX = os.getenv("PROCESSED_PREFIX", "news-processed/")
RAW_PREFIX       = os.getenv("RAW_PREFIX", "news-raw/")

# AWS clients
try:
    # Use direct credentials for Railway, profile for local
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key and aws_secret_key:
        # Railway/production - use direct credentials
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=AWS_REGION
        )
        print("🔑 Using AWS credentials from environment variables")
    else:
        # Local development - use default profile
        session = boto3.Session(region_name=AWS_REGION)
        print("🔑 Using default AWS profile")
    ddb     = session.resource("dynamodb")
    s3      = session.client("s3") if PROC_BUCKET else None
    bedrock = session.client("bedrock-runtime") if BEDROCK_MODELID else None
    table = ddb.Table(DDB_TABLE) if DDB_TABLE else None
    print(f"✅ AWS initialized - Region: {AWS_REGION}, Table: {DDB_TABLE}")
    
    # Initialize content filter
    if ContentFilter:
        try:
            content_filter = ContentFilter(session)
            print("✅ Content filtering system initialized")
        except Exception as e:
            print(f"⚠️ Content filter initialization failed: {e}")
            content_filter = None
    else:
        content_filter = None
        
except Exception as e:
    print(f"⚠️ AWS initialization failed: {e}")
    if not DEBUG_MODE:
        table = None
        s3 = None
        bedrock = None
        content_filter = None

# ---------- Helper Functions (copied from app.py) ----------
def _to_dt(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        try:
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception:
            return None

def _teaser(text: str, limit: int = 180) -> str:
    if not text: 
        return ""
    t = text.strip().split("\n")[0]
    return t[:limit] + ("…" if len(t) > limit else "")

def _sentiment_bucket(overall: str) -> str:
    if not overall:
        return "neutral"
    
    overall = str(overall).lower().strip()
    
    # Handle various sentiment formats
    if any(word in overall for word in ["very_negative", "negative", "bad", "poor", "terrible", "awful"]):
        return "negative"
    if any(word in overall for word in ["very_positive", "positive", "good", "great", "excellent", "amazing"]):
        return "positive"
    if any(word in overall for word in ["neutral", "mixed", "balanced"]):
        return "neutral"
    
    # Default to neutral if unclear
    return "neutral"

def _normalize_date(date_str: Optional[str]) -> str:
    if not date_str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dt = _to_dt(date_str)
        if dt:
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _make_doc_id(article: Dict[str, Any]) -> str:
    base = article.get("url") or article.get("headline") or article.get("title") or str(article)
    return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:16]

# News API functions
def _fetch_from_newsapi(topic: str) -> List[Dict[str, Any]]:
    if not NEWSAPI_KEY:
        print("⚠️ NewsAPI key not configured")
        return []
    
    params = {
        "q": topic,
        "language": "en",
        "pageSize": 20,  # Increased from 10 to get more articles
        "sortBy": "publishedAt"
    }
    url = "https://newsapi.org/v2/everything"
    headers = {"X-API-Key": NEWSAPI_KEY}  # Fixed header format
    
    try:
        print(f"📡 Fetching from NewsAPI: {topic}")
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        articles = data.get("articles", [])
        print(f"📰 NewsAPI returned {len(articles)} articles")
        
        # Debug first article
        if articles:
            first = articles[0]
            print(f"   Sample: {first.get('title', 'No title')[:50]}...")
        
        return articles
    except Exception as e:
        print(f"❌ NewsAPI fetch failed: {e}")
        return []

def _fetch_from_guardian(topic: str) -> List[Dict[str, Any]]:
    if not GUARDIAN_KEY:
        return []
    params = {
        "order-by": "newest",
        "page-size": 20,  # Increased from 10 to get more articles
        "show-fields": "headline,trailText,bodyText,byline",
        "api-key": GUARDIAN_KEY,
        "q": topic
    }
    url = "https://content.guardianapis.com/search"
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("response", {}).get("results", [])
        out = []
        for item in results:
            fields = item.get("fields", {})
            out.append({
                "source": "guardian",
                "headline": fields.get("headline") or item.get("webTitle"),
                "url": item.get("webUrl"),
                "date": item.get("webPublicationDate"),
                "author": fields.get("byline"),
                "description": fields.get("trailText"),
                "content": fields.get("bodyText"),
            })
        return out
    except Exception as e:
        print(f"Guardian fetch failed: {e}")
        return []

# Core functions
# Smart caching system
_search_cache = {}
_cache_timestamp = datetime.utcnow()
_popular_topics = ["technology", "politics", "business", "science", "health", "economy", "AI", "climate", "market", "innovation"]

def clear_search_cache():
    """Clear the search cache when new articles are added"""
    global _search_cache, _cache_timestamp
    _search_cache = {}
    _cache_timestamp = datetime.utcnow()
    print("🗑️ Search cache cleared")

def get_cache_key(topic: str, limit: int) -> str:
    """Generate cache key for search results"""
    return f"{topic.lower().strip()}:{limit}"

def is_cache_valid(cache_entry: dict) -> bool:
    """Check if cache entry is still valid (24 hours)"""
    if not cache_entry:
        return False
    
    cache_time = datetime.fromisoformat(cache_entry.get('timestamp', ''))
    age_hours = (datetime.utcnow() - cache_time).total_seconds() / 3600
    return age_hours < 24  # Cache valid for 24 hours

def should_prefetch_topic(topic: str) -> bool:
    """Determine if topic should be prefetched"""
    if not topic:
        return False
    
    topic_lower = topic.lower().strip()
    
    # Always prefetch popular topics
    if topic_lower in _popular_topics:
        return True
    
    # Prefetch if topic contains popular keywords
    return any(popular in topic_lower for popular in _popular_topics)

def search_articles_ddb(topic: Optional[str] = None, limit: int = 6, use_cache: bool = True) -> List[Dict[str, Any]]:
    """Search articles in DynamoDB with smart caching"""
    if not table:
        print("⚠️ DynamoDB table not available")
        return []
    
    # Check cache first
    if use_cache and topic:
        cache_key = get_cache_key(topic, limit)
        cached_result = _search_cache.get(cache_key)
        
        if cached_result and is_cache_valid(cached_result):
            print(f"⚡ Cache hit for '{topic}' - returning {len(cached_result['articles'])} cached articles")
            return cached_result['articles']
        else:
            print(f"🔄 Cache miss for '{topic}' - fetching from database")
    
    try:
        items = []
        resp = table.scan(Limit=200)
        items.extend(resp.get("Items", []) or [])
        
        while "LastEvaluatedKey" in resp and len(items) < 500:
            resp = table.scan(Limit=200, ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []) or [])
        
        print(f"📊 Scanned {len(items)} items from DynamoDB")
        
        # Filter by topic if provided
        if topic and topic.strip():
            t_lower = topic.lower().strip()
            
            def match(item):
                summary = (item.get("summary") or "").lower()
                headline = (item.get("headline") or "").lower()
                source = (item.get("source") or "").lower()
                
                # Get entities if they exist
                entities_text = ""
                entities = item.get("entities", [])
                if isinstance(entities, list):
                    for entity in entities:
                        if isinstance(entity, dict):
                            entities_text += " " + (entity.get("text") or "").lower()
                        elif isinstance(entity, str):
                            entities_text += " " + entity.lower()
                
                # Combine all searchable text
                combined = f"{summary} {headline} {source} {entities_text}"
                
                # Try exact match first
                if t_lower in combined:
                    return True
                
                # Try word-by-word matching for multi-word queries
                topic_words = t_lower.split()
                if len(topic_words) > 1:
                    # Check if ANY word is present (more flexible)
                    matches = sum(1 for word in topic_words if word in combined)
                    # Require at least half the words to match
                    return matches >= len(topic_words) / 2
                
                # For single words, try partial matching
                return any(word in combined for word in [t_lower] + [t_lower[:-1], t_lower[:-2]] if len(word) > 3)
            
            filtered = [it for it in items if match(it)]
            print(f"🔍 Found {len(filtered)} items matching '{topic}'")
        else:
            filtered = items
        
        # Sort by date descending
        def key_fn(it):
            dt = _to_dt(it.get("date", ""))
            return dt or datetime.min
        
        filtered.sort(key=key_fn, reverse=True)
        result = filtered[:limit]
        
        # Cache the result if we have a topic
        if topic and use_cache:
            cache_key = get_cache_key(topic, limit)
            _search_cache[cache_key] = {
                'articles': result,
                'timestamp': datetime.utcnow().isoformat()
            }
            print(f"💾 Cached {len(result)} articles for '{topic}'")
        
        return result
    
    except Exception as e:
        print(f"❌ DDB scan error: {e}")
        return []

def get_processed_doc(doc_id: str) -> Dict[str, Any]:
    """Fetch full processed document from S3"""
    try:
        if not s3 or not PROC_BUCKET:
            return {"summary": "", "url": "", "entities": [], "overall_sentiment": "neutral", "emotions": {}}

        key = f"{PROCESSED_PREFIX}{doc_id}.json"
        obj = s3.get_object(Bucket=PROC_BUCKET, Key=key)
        return json.loads(obj["Body"].read())
    except Exception as e:
        print(f"Could not fetch {doc_id} from S3: {e}")
        return {"summary": "", "url": "", "entities": [], "overall_sentiment": "neutral", "emotions": {}}

def bedrock_explain(text: str) -> str:
    """Detailed analysis using Bedrock"""
    if not bedrock or not BEDROCK_MODELID:
        return "⚠️ Bedrock model not configured. Set BEDROCK_MODEL_ID env var."
    
    try:
        if MODEL_FAMILY == "anthropic":
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 700,
                "messages": [{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": (
                            "Provide a crisp, structured analysis with:\n"
                            "1) **What happened** (2–3 bullets)\n"
                            "2) **Why it matters** (2–3 bullets)\n"
                            "3) **What to watch next** (2 bullets)\n\n"
                            f"ARTICLE CONTEXT:\n{text[:2000]}"
                        )
                    }]
                }]
            }
            resp = bedrock.invoke_model(modelId=BEDROCK_MODELID, body=json.dumps(body))
            payload = json.loads(resp["body"].read())
            chunks = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
            return "\n".join(chunks).strip()
        else:
            body = {
                "inputText": (
                    "Provide a crisp, structured analysis with:\n"
                    "1) What happened (2–3 bullets)\n"
                    "2) Why it matters (2–3 bullets)\n"
                    "3) What to watch next (2 bullets)\n\n"
                    f"ARTICLE CONTEXT:\n{text[:2000]}"
                ),
                "textGenerationConfig": {"maxTokenCount": 700, "temperature": 0.2, "topP": 0.9}
            }
            resp = bedrock.invoke_model(modelId=BEDROCK_MODELID, body=json.dumps(body))
            payload = json.loads(resp["body"].read())
            if payload.get("results"):
                return payload["results"][0].get("outputText", "").strip()
            return payload.get("outputText", "").strip()
    except Exception as e:
        return f"⚠️ Analysis failed: {str(e)[:100]}"

def bedrock_chat(context_text: str, user_msg: str, history: List[Dict[str, str]]) -> str:
    """Chat with article using Bedrock"""
    if not bedrock or not BEDROCK_MODELID:
        return "⚠️ Bedrock model not configured."
    
    try:
        if MODEL_FAMILY == "anthropic":
            msgs = []
            for turn in history:
                msgs.append({"role": "user", "content": [{"type": "text", "text": turn["user"]}]})
                msgs.append({"role": "assistant", "content": [{"type": "text", "text": turn["assistant"]}]})
            msgs.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"Answer concisely using only this article:\n\n{context_text[:2000]}\n\nQuestion: {user_msg}"
                }]
            })
            body = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 600, "messages": msgs}
            resp = bedrock.invoke_model(modelId=BEDROCK_MODELID, body=json.dumps(body))
            payload = json.loads(resp["body"].read())
            chunks = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
            return "\n".join(chunks).strip()
        else:
            prompt = (
                "Answer concisely using only this article content.\n\n"
                f"{context_text[:2000]}\n\nQuestion: {user_msg}"
            )
            body = {
                "inputText": prompt,
                "textGenerationConfig": {"maxTokenCount": 600, "temperature": 0.2, "topP": 0.9}
            }
            resp = bedrock.invoke_model(modelId=BEDROCK_MODELID, body=json.dumps(body))
            payload = json.loads(resp["body"].read())
            if payload.get("results"):
                return payload["results"][0].get("outputText", "").strip()
            return payload.get("outputText", "").strip()
    except Exception as e:
        return f"⚠️ Chat failed: {str(e)[:100]}"

def _fetch_articles_from_apis(topic: str) -> List[Dict[str, Any]]:
    """Fetch articles from news APIs"""
    articles: List[Dict[str, Any]] = []
    if not topic:
        return articles
    
    newsapi_articles = _fetch_from_newsapi(topic)
    guardian_articles = _fetch_from_guardian(topic)
    
    print(f"📰 NewsAPI returned {len(newsapi_articles)} articles")
    print(f"📰 Guardian returned {len(guardian_articles)} articles")
    
    articles.extend(newsapi_articles)
    articles.extend(guardian_articles)

    normalized: List[Dict[str, Any]] = []
    for i, art in enumerate(articles):
        headline = art.get("title") or art.get("headline")
        if not headline:
            print(f"⚠️ Skipping article {i+1}: no headline")
            continue
            
        # Debug the article structure
        print(f"📄 Processing article {i+1}: {headline[:50]}...")
        
        normalized_article = {
            "id": _make_doc_id(art),
            "headline": headline,
            "summary": art.get("description") or art.get("summary") or "",
            "content": art.get("content") or art.get("body") or art.get("bodyText") or "",
            "source": (art.get("source") or {}).get("name") if isinstance(art.get("source"), dict) else str(art.get("source", "Unknown")),
            "date": _normalize_date(art.get("publishedAt") or art.get("date")),
            "url": art.get("url") or "",
            "author": art.get("author") or (art.get("fields", {}) if isinstance(art.get("fields"), dict) else {}).get("byline") or "",
        }
        
        print(f"   ✅ Normalized: headline='{normalized_article['headline'][:30]}...', source='{normalized_article['source']}'")
        normalized.append(normalized_article)
        
    print(f"✅ Normalized {len(normalized)} articles total")
    return normalized

def _analyze_with_bedrock_local(text: str) -> Dict[str, Any]:
    """Analyze article with Bedrock"""
    fallback_summary = (text or "")[:400] + ("…" if text and len(text) > 400 else "")
    default_payload = {
        "overall_sentiment": "neutral",
        "sentiment": "neutral",
        "emotions": {},
        "summary": fallback_summary,
        "entities": []
    }

    if not bedrock or not BEDROCK_MODELID:
        return default_payload

    SYSTEM_JSON_INSTRUCTIONS = (
        "You are an expert analyst producing NRC-style emotion insights. "
        "Return ONLY strict JSON (no markdown) with this schema: "
        "{"
        "\"overall_sentiment\": one of [\"very_negative\",\"negative\",\"neutral\",\"positive\",\"very_positive\"], "
        "\"emotions\": {"
        "\"anger\": level, "
        "\"anticipation\": level, "
        "\"disgust\": level, "
        "\"fear\": level, "
        "\"joy\": level, "
        "\"sadness\": level, "
        "\"surprise\": level, "
        "\"trust\": level "
        "}, "
        "\"entities\": [ {\"type\": string, \"text\": string} ], "
        "\"summary\": string"
        "}. "
        "Each level must be one of [\"high\",\"medium\",\"low\",\"none\"]. "
        "Keep summary to 3-5 concise bullet sentences joined by \\n describing key takeaways and emotion drivers. "
        "overall_sentiment reflects the dominant tone on a red (very_negative) to green (very_positive) continuum; neutral is white. "
        "If unsure, use \"neutral\" and \"none\". Do not add extra fields."
    )

    payload: Dict[str, Any]
    if MODEL_FAMILY == "anthropic":
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 600,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_JSON_INSTRUCTIONS},
                        {"type": "text", "text": f"ARTICLE:\n{text}"}
                    ]
                }
            ]
        }
    else:
        payload = {
            "inputText": SYSTEM_JSON_INSTRUCTIONS + "\n\nARTICLE:\n" + text,
            "textGenerationConfig": {"maxTokenCount": 600, "temperature": 0.2, "topP": 0.9}
        }

    try:
        resp = bedrock.invoke_model(modelId=BEDROCK_MODELID, body=json.dumps(payload))
        body = json.loads(resp["body"].read())
        if MODEL_FAMILY == "anthropic":
            chunks = [blk.get("text", "") for blk in body.get("content", []) if blk.get("type") == "text"]
            model_text = "\n".join(chunks)
        else:
            model_text = ""
            if isinstance(body, dict):
                if body.get("results"):
                    model_text = body["results"][0].get("outputText", "")
                else:
                    model_text = body.get("outputText", "") or body.get("generation", "")
        model_text = model_text.strip().strip("`")
        try:
            data = json.loads(model_text)
        except Exception:
            data = default_payload.copy()
            data["summary"] = model_text
    except Exception as e:
        print(f"Bedrock analysis failed: {e}")
        data = default_payload.copy()

    overall = (data.get("overall_sentiment") or data.get("sentiment") or "neutral").lower()
    if overall not in ["very_negative", "negative", "neutral", "positive", "very_positive"]:
        overall = "neutral"
    data["overall_sentiment"] = overall
    data["sentiment"] = _sentiment_bucket(overall)

    if not isinstance(data.get("entities"), list):
        data["entities"] = []
    if not data.get("summary"):
        data["summary"] = fallback_summary
    return data

def _store_processed_article(article: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[str]:
    """Store processed article in DynamoDB and S3"""
    doc_id = article.get("id") or _make_doc_id(article)
    if not doc_id:
        return None
    
    processed_payload = {
        "id": doc_id,
        "headline": article.get("headline"),
        "summary": analysis.get("summary") or article.get("summary"),
        "sentiment": analysis.get("sentiment", "neutral"),
        "overall_sentiment": analysis.get("overall_sentiment", "neutral"),
        "emotions": analysis.get("emotions", {}),
        "entities": analysis.get("entities", []),
        "url": article.get("url"),
        "source": article.get("source", "unknown"),
        "date": article.get("date"),
        "ingested_at": datetime.utcnow().isoformat()
    }

    processed_payload["sentiment"] = _sentiment_bucket(processed_payload.get("overall_sentiment"))

    # Write to S3 if available
    if s3 and PROC_BUCKET:
        try:
            key = f"{PROCESSED_PREFIX}{doc_id}.json"
            s3.put_object(
                Bucket=PROC_BUCKET,
                Key=key,
                Body=json.dumps(processed_payload, indent=2).encode("utf-8"),
                ContentType="application/json"
            )
        except Exception as e:
            print(f"Failed to write processed doc to S3: {e}")

    # Write to DynamoDB
    if not table:
        print("⚠️ DynamoDB table not available")
        return None
        
    try:
        item = {
            "id": doc_id,
            "source": processed_payload.get("source") or "unknown",
            "date": processed_payload.get("date"),
            "headline": processed_payload.get("headline") or article.get("headline") or article.get("title") or "",
            "summary": processed_payload.get("summary") or "",
            "sentiment": processed_payload.get("sentiment") or "neutral",
            "overall_sentiment": processed_payload.get("overall_sentiment") or "neutral",
            "url": processed_payload.get("url") or article.get("url") or "",
            "verification_score": Decimal("0")
        }
        if processed_payload.get("emotions"):
            item["emotions"] = processed_payload["emotions"]
        if processed_payload.get("entities"):
            item["entities"] = processed_payload["entities"]
        
        table.put_item(Item=item)
        print(f"✅ Stored article: {doc_id}")
        
        # Clear search cache since we added a new article
        clear_search_cache()
    except Exception as e:
        print(f"Failed to write item to DynamoDB: {e}")
        return None

    return doc_id

def ingest_topic(topic: str) -> Tuple[int, int]:
    """Ingest new articles for a topic"""
    print(f"📥 Starting ingestion for topic: {topic}")
    
    # Try the original topic first
    articles = _fetch_articles_from_apis(topic)
    
    # If we didn't get many articles, try some variations
    if len(articles) < 10:
        print(f"🔄 Only got {len(articles)} articles for '{topic}', trying variations...")
        
        # Generate topic variations
        variations = []
        if ' ' in topic:
            # Try individual words
            words = topic.split()
            variations.extend(words)
        
        # Try related terms
        topic_lower = topic.lower()
        if 'market' in topic_lower:
            variations.extend(['finance', 'economy', 'trading', 'stocks'])
        elif 'tech' in topic_lower or 'ai' in topic_lower:
            variations.extend(['artificial intelligence', 'machine learning', 'innovation'])
        elif 'health' in topic_lower:
            variations.extend(['medicine', 'medical', 'healthcare'])
        
        # Fetch articles for variations
        for variation in variations[:2]:  # Limit to 2 variations to avoid too many API calls
            if variation != topic:
                print(f"🔍 Trying variation: {variation}")
                variation_articles = _fetch_articles_from_apis(variation)
                articles.extend(variation_articles)
                if len(articles) >= 15:  # Stop if we have enough
                    break
    
    if not articles:
        print("❌ No articles found from APIs")
        return 0, 0

    processed = 0
    stored = 0
    for art in articles:
        processed += 1
        text = art.get("content") or art.get("summary") or art.get("headline") or ""
        analysis = _analyze_with_bedrock_local(text)
        doc_id = _store_processed_article(art, analysis)
        if doc_id:
            stored += 1
    
    print(f"✅ Ingestion complete: {processed} processed, {stored} stored")
    return processed, stored

# FastAPI app
app = FastAPI(
    title="NewsInsight API",
    description="AI-powered news analysis backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:3002", 
        "http://127.0.0.1:3002",
        "http://localhost:3003", 
        "http://127.0.0.1:3003",
        # Production - Vercel domains
        "https://news-insight-ai-tawny.vercel.app",  # Your main Vercel domain
        "https://news-insight-ai-tawny-git-main.vercel.app",  # Git branch deployments
        "https://*.vercel.app",  # Allow all Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SearchResponse(BaseModel):
    articles: List[Dict[str, Any]]
    total: int

class ExplainRequest(BaseModel):
    article_id: str
    content: str

class ExplainResponse(BaseModel):
    explanation: str

class ChatRequest(BaseModel):
    article_id: str
    content: str
    message: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str

class IngestRequest(BaseModel):
    topic: str

class IngestResponse(BaseModel):
    processed: int
    stored: int
    message: str

# Helper functions
def format_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Format article data for frontend consumption"""
    # Handle Decimal types from DynamoDB
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    # Convert all Decimal values
    formatted = {}
    for key, value in article.items():
        if isinstance(value, dict):
            formatted[key] = {k: convert_decimal(v) for k, v in value.items()}
        else:
            formatted[key] = convert_decimal(value)
    
    # Ensure required fields exist
    formatted.setdefault('id', formatted.get('id', 'unknown'))
    formatted.setdefault('headline', formatted.get('headline', 'Untitled'))
    formatted.setdefault('summary', formatted.get('summary', ''))
    formatted.setdefault('source', formatted.get('source', 'Unknown'))
    formatted.setdefault('date', formatted.get('date', datetime.utcnow().isoformat()))
    formatted.setdefault('url', formatted.get('url', ''))
    
    # Fix sentiment handling
    overall_sentiment = formatted.get('overall_sentiment', 'neutral')
    formatted['overall_sentiment'] = overall_sentiment
    formatted['sentiment'] = _sentiment_bucket(overall_sentiment)
    
    formatted.setdefault('entities', formatted.get('entities', []))
    formatted.setdefault('emotions', formatted.get('emotions', {}))
    
    # Debug sentiment
    print(f"📊 Article {formatted['id']}: overall_sentiment='{overall_sentiment}' -> sentiment='{formatted['sentiment']}')")
    
    # Add teaser if not present
    if not formatted.get('teaser'):
        formatted['teaser'] = _teaser(formatted['summary'], 180)
    
    return formatted

# API Routes
@app.get("/")
async def root():
    return {"message": "NewsInsight API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/articles/refresh")
async def refresh_articles():
    """Clear cache and refresh article search"""
    clear_search_cache()
    return {"message": "Article cache cleared", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/articles/debug")
async def debug_articles(limit: int = Query(10, description="Number of recent articles to show")):
    """Debug endpoint to see recent articles"""
    if not table:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Get recent articles
        resp = table.scan(Limit=limit)
        items = resp.get("Items", [])
        
        # Sort by date
        def key_fn(it):
            dt = _to_dt(it.get("date", ""))
            return dt or datetime.min
        
        items.sort(key=key_fn, reverse=True)
        
        # Format for debugging
        debug_items = []
        for item in items:
            debug_items.append({
                "id": item.get("id"),
                "headline": item.get("headline", "")[:100],
                "summary": item.get("summary", "")[:100],
                "source": item.get("source"),
                "date": item.get("date"),
                "sentiment": item.get("sentiment"),
                "entities_count": len(item.get("entities", []))
            })
        
        return {
            "total_scanned": len(items),
            "articles": debug_items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

@app.get("/api/status")
async def system_status():
    """Check system configuration status"""
    status = {
        "aws": {
            "region": AWS_REGION,
            "dynamodb_table": DDB_TABLE,
            "dynamodb_connected": table is not None,
            "s3_bucket": PROC_BUCKET or "Not configured",
            "s3_connected": s3 is not None,
        },
        "bedrock": {
            "model_family": MODEL_FAMILY,
            "model_id": BEDROCK_MODELID or "Not configured",
            "connected": bedrock is not None,
        },
        "news_apis": {
            "newsapi_configured": bool(NEWSAPI_KEY),
            "guardian_configured": bool(GUARDIAN_KEY),
        },
        "debug_mode": DEBUG_MODE
    }
    
    # Count articles in database
    if table:
        try:
            resp = table.scan(Select='COUNT')
            status["database"] = {
                "article_count": resp.get('Count', 0),
                "status": "connected"
            }
        except Exception as e:
            status["database"] = {
                "article_count": 0,
                "status": f"error: {str(e)}"
            }
    else:
        status["database"] = {
            "article_count": 0,
            "status": "not configured"
        }
    
    return status

@app.post("/api/articles/bootstrap")
async def bootstrap_articles():
    """Bootstrap the database with some initial articles"""
    if not (NEWSAPI_KEY or GUARDIAN_KEY):
        raise HTTPException(status_code=400, detail="No news API keys configured")
    
    default_topics = ["technology", "politics", "business", "science", "world"]
    total_processed = 0
    total_stored = 0
    
    for topic in default_topics:
        try:
            processed, stored = ingest_topic(topic)
            total_processed += processed
            total_stored += stored
        except Exception as e:
            print(f"Failed to ingest {topic}: {e}")
    
    return {
        "message": f"Bootstrap complete: {total_processed} processed, {total_stored} stored",
        "processed": total_processed,
        "stored": total_stored,
        "topics": default_topics
    }

@app.post("/api/articles/prefetch")
async def prefetch_popular_topics():
    """Prefetch and cache popular topics for faster searches"""
    prefetched = []
    
    for topic in _popular_topics:
        try:
            # Search and cache the results
            articles = search_articles_ddb(topic, 6, use_cache=True)
            prefetched.append({
                "topic": topic,
                "cached_articles": len(articles)
            })
            print(f"✅ Prefetched {len(articles)} articles for '{topic}'")
        except Exception as e:
            print(f"❌ Failed to prefetch '{topic}': {e}")
    
    return {
        "message": f"Prefetched {len(prefetched)} popular topics",
        "topics": prefetched,
        "cache_size": len(_search_cache)
    }

@app.get("/api/articles/search")
async def search_articles(
    query: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(6, ge=1, le=50, description="Number of articles to return"),
    auto_ingest: bool = Query(True, description="Auto-ingest if no articles found")
):
    """Search for articles with smart caching"""
    try:
        # Use existing search function with caching
        articles = search_articles_ddb(query, limit, use_cache=True)
        
        # If we don't have enough articles and we have a query, try to ingest more
        if len(articles) < limit and query and auto_ingest and (NEWSAPI_KEY or GUARDIAN_KEY):
            articles_needed = limit - len(articles)
            print(f"🔄 Found {len(articles)} articles for '{query}', need {articles_needed} more. Attempting to ingest...")
            
            # Try multiple ingestion attempts to get enough articles
            max_attempts = 2  # Reduced from 3 to speed up
            attempt = 1
            
            while len(articles) < limit and attempt <= max_attempts:
                print(f"📥 Ingestion attempt {attempt}/{max_attempts}")
                processed, stored = ingest_topic(query)
                
                if stored > 0:
                    # Clear any caching and search again after ingestion
                    import time
                    time.sleep(1)  # Reduced from 2 seconds
                    articles = search_articles_ddb(query, limit, use_cache=False)  # Skip cache for fresh results
                    print(f"✅ After ingestion attempt {attempt}: found {len(articles)} articles")
                    
                    if len(articles) >= limit:
                        break
                else:
                    print(f"⚠️ No new articles stored in attempt {attempt}")
                    break
                
                attempt += 1
            
            # If still not enough articles, try a broader search
            if len(articles) < limit:
                print(f"🔍 Still need more articles. Trying broader search...")
                all_articles = search_articles_ddb(None, 100, use_cache=False)
                
                # Filter for articles that might match the query
                query_words = query.lower().split()
                matching_articles = []
                
                for art in all_articles:
                    # Skip articles we already have
                    if any(existing.get('id') == art.get('id') for existing in articles):
                        continue
                        
                    text_to_search = (art.get('headline', '') + ' ' + art.get('summary', '') + ' ' + art.get('source', '')).lower()
                    if any(word in text_to_search for word in query_words):
                        matching_articles.append(art)
                
                # Add the additional matching articles
                additional_needed = limit - len(articles)
                articles.extend(matching_articles[:additional_needed])
                print(f"✅ Broader search added {len(matching_articles[:additional_needed])} more articles. Total: {len(articles)}")
        
        # Format articles for frontend
        formatted_articles = [format_article(article) for article in articles]
        
        return formatted_articles
        
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/articles/search-stream")
async def search_articles_stream(
    query: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(6, ge=1, le=50, description="Number of articles to return")
):
    """Stream articles as they are found and processed"""
    
    async def generate_stream():
        try:
            # First, return existing articles immediately
            existing_articles = search_articles_ddb(query, limit, use_cache=True)
            
            if existing_articles:
                yield f"data: {json.dumps({'type': 'existing', 'articles': [format_article(art) for art in existing_articles], 'count': len(existing_articles)})}\n\n"
            
            # If we need more articles, start ingestion
            if len(existing_articles) < limit and query and (NEWSAPI_KEY or GUARDIAN_KEY):
                yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(existing_articles)} existing articles, fetching more...'})}\n\n"
                
                # Start ingestion process
                yield f"data: {json.dumps({'type': 'status', 'message': 'Fetching from news APIs...'})}\n\n"
                
                # Fetch articles from APIs
                new_articles = _fetch_articles_from_apis(query)
                
                if new_articles:
                    yield f"data: {json.dumps({'type': 'status', 'message': f'Processing {len(new_articles)} new articles...'})}\n\n"
                    
                    # Process articles one by one and stream them
                    processed_count = 0
                    for i, art in enumerate(new_articles):
                        if processed_count >= (limit - len(existing_articles)):
                            break
                            
                        # Analyze article
                        text = art.get("content") or art.get("summary") or art.get("headline") or ""
                        analysis = _analyze_with_bedrock_local(text)
                        
                        # Store article
                        doc_id = _store_processed_article(art, analysis)
                        
                        if doc_id:
                            # Get the stored article and format it
                            stored_articles = search_articles_ddb(None, 1, use_cache=False)  # Get the latest article
                            if stored_articles:
                                latest_article = stored_articles[0]
                                if latest_article.get('id') == doc_id:
                                    formatted_article = format_article(latest_article)
                                    yield f"data: {json.dumps({'type': 'new_article', 'article': formatted_article, 'progress': i+1, 'total': len(new_articles)})}\n\n"
                                    processed_count += 1
                
                yield f"data: {json.dumps({'type': 'complete', 'message': f'Processing complete. Found {len(existing_articles) + processed_count} total articles.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'complete', 'message': f'Search complete. Found {len(existing_articles)} articles.'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.post("/api/articles/explain", response_model=ExplainResponse)
async def explain_article(request: ExplainRequest):
    """Generate detailed explanation for an article"""
    try:
        explanation = bedrock_explain(request.content)
        return ExplainResponse(explanation=explanation)
        
    except Exception as e:
        print(f"Explain error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/articles/chat", response_model=ChatResponse)
async def chat_with_article(request: ChatRequest):
    """Chat about an article"""
    try:
        # Convert history format
        history_formatted = []
        for msg in request.history:
            if msg.get('type') == 'user':
                history_formatted.append({'user': msg['content'], 'assistant': ''})
            elif msg.get('type') == 'assistant' and history_formatted:
                history_formatted[-1]['assistant'] = msg['content']
        
        response = bedrock_chat(request.content, request.message, history_formatted)
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/api/articles/ingest", response_model=IngestResponse)
async def ingest_articles(request: IngestRequest):
    """Ingest new articles for a topic"""
    try:
        processed, stored = ingest_topic(request.topic)
        
        if stored > 0:
            message = f"Successfully processed {processed} articles and stored {stored} new insights"
        elif processed > 0:
            message = f"Processed {processed} articles but they were already in the database"
        else:
            message = "No new articles were found for this topic"
            
        return IngestResponse(
            processed=processed,
            stored=stored,
            message=message
        )
        
    except Exception as e:
        print(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    """Get detailed article information"""
    try:
        doc = get_processed_doc(article_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return format_article(doc)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get article error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve article: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Not found", "detail": str(exc)}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting NewsInsight API server on port {port}")
    print("Frontend should be available at: http://localhost:3000")
    print(f"API docs available at: http://localhost:{port}/docs")
    
    # Railway deployment configuration
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
    
    uvicorn.run(
        "backend:app",
        host="0.0.0.0",
        port=port,
        reload=not is_railway,  # Disable reload in production
        log_level="info"
    )