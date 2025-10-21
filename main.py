#!/usr/bin/env python3
"""
FastAPI backend for NewsInsight React UI
Full functionality with AWS integration
"""

import os
import json
import sys
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from functools import lru_cache
import asyncio
import boto3
import requests
import time

# Import content filtering
from content_filter import ContentFilter

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------- Config ----------
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

# AWS clients - handle missing credentials gracefully
table = None
s3 = None
bedrock = None

try:
    # Check for AWS credentials
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if aws_access_key and aws_secret_key:
        # Use direct credentials (Railway/production)
        print("🔑 Using AWS credentials from environment variables")
        print(f"🔑 Access Key: {aws_access_key[:8]}...")
        print(f"🔑 Region: {AWS_REGION}")
        
        # Create session with explicit credentials (no profile needed)
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=AWS_REGION
        )
        
        # Initialize AWS services
        ddb = session.resource("dynamodb")
        s3 = session.client("s3") if PROC_BUCKET else None
        bedrock = session.client("bedrock-runtime") if BEDROCK_MODELID else None
        
        # Test DynamoDB connection
        if DDB_TABLE:
            table = ddb.Table(DDB_TABLE)
            # Test table access
            table.load()
            print(f"✅ DynamoDB table '{DDB_TABLE}' accessible")
        else:
            table = None
            print("⚠️ DDB_TABLE not configured")
            
        print(f"✅ AWS services initialized successfully")
        print(f"   - S3 Bucket: {PROC_BUCKET}")
        print(f"   - Bedrock Model: {BEDROCK_MODELID}")
        
        # Initialize content filter
        try:
            content_filter = ContentFilter(session)
            print("✅ Content filtering system initialized")
        except Exception as e:
            print(f"⚠️ Content filter initialization failed: {e}")
            content_filter = None
        
    else:
        print("⚠️ AWS credentials not found - running in demo mode")
        print(f"   AWS_ACCESS_KEY_ID: {'✅' if aws_access_key else '❌'}")
        print(f"   AWS_SECRET_ACCESS_KEY: {'✅' if aws_secret_key else '❌'}")
        session = None
        content_filter = None
    
except Exception as e:
    print(f"⚠️ AWS initialization failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    print("   Running in demo mode")
    table = None
    s3 = None
    bedrock = None

# FastAPI app
app = FastAPI(
    title="NewsInsight API",
    description="AI-powered news analysis backend",
    version="1.0.0"
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"📥 {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"📤 {response.status_code} (took {process_time:.2f}s)")
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://news-insight-ai-tawny.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def _to_dt(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        try:
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        except Exception:
            return None

def _sentiment_bucket(overall: str) -> str:
    if not overall:
        return "neutral"
    
    overall = str(overall).lower().strip()
    
    if any(word in overall for word in ["very_negative", "negative", "bad", "poor"]):
        return "negative"
    if any(word in overall for word in ["very_positive", "positive", "good", "great"]):
        return "positive"
    
    return "neutral"

def get_demo_articles() -> List[Dict[str, Any]]:
    """Return demo articles when AWS is not available"""
    return [
        {
            "id": "demo-1",
            "headline": "🚀 Railway Backend Connected Successfully!",
            "summary": "The NewsInsight backend is now running on Railway with full AWS integration capabilities. Add your AWS credentials to enable real news data.",
            "source": "NewsInsight",
            "date": "2024-10-21T12:00:00Z",
            "overall_sentiment": "positive",
            "sentiment": "positive",
            "entities": [{"text": "Railway", "type": "platform"}, {"text": "AWS", "type": "technology"}],
            "emotions": {"joy": "high", "anticipation": "medium", "trust": "high"},
            "url": "https://railway.app"
        },
        {
            "id": "demo-2", 
            "headline": "Add AWS Credentials to Enable Real News Data",
            "summary": "To fetch real news articles, add your AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) and API keys (NEWSAPI_KEY, GUARDIAN_KEY) to Railway environment variables.",
            "source": "Setup Guide",
            "date": "2024-10-21T11:00:00Z",
            "overall_sentiment": "neutral",
            "sentiment": "neutral",
            "entities": [{"text": "AWS", "type": "technology"}, {"text": "API Keys", "type": "configuration"}],
            "emotions": {"anticipation": "medium", "trust": "medium"},
            "url": "https://railway.app/project/settings"
        }
    ]

def search_articles_ddb(topic: Optional[str] = None, limit: int = 6, max_age_days: int = 2) -> List[Dict[str, Any]]:
    """Search articles in DynamoDB with age filtering"""
    if not table:
        print("⚠️ DynamoDB table not available - returning demo articles")
        demo_articles = get_demo_articles()
        if topic:
            # Simple filtering for demo
            topic_lower = topic.lower()
            filtered = [art for art in demo_articles if topic_lower in art['headline'].lower() or topic_lower in art['summary'].lower()]
            return filtered[:limit] if filtered else demo_articles[:limit]
        return demo_articles[:limit]
    
    try:
        items = []
        resp = table.scan(Limit=200)
        items.extend(resp.get("Items", []) or [])
        
        while "LastEvaluatedKey" in resp and len(items) < 500:
            resp = table.scan(Limit=200, ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []) or [])
        
        print(f"📊 Scanned {len(items)} items from DynamoDB")
        
        # Calculate cutoff date for age filtering
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        print(f"🕒 Age filter: showing articles newer than {cutoff_date.strftime('%Y-%m-%d %H:%M')} UTC")
        
        # Filter by age first (most restrictive)
        recent_items = []
        old_count = 0
        
        for item in items:
            article_date = _to_dt(item.get("date", ""))
            if article_date and article_date >= cutoff_date:
                recent_items.append(item)
            else:
                old_count += 1
        
        print(f"📅 Age filtering: {len(recent_items)} recent articles, {old_count} old articles filtered out")
        
        # Filter by topic if provided
        if topic and topic.strip():
            t_lower = topic.lower().strip()
            
            def match(item):
                summary = (item.get("summary") or "").lower()
                headline = (item.get("headline") or "").lower()
                source = (item.get("source") or "").lower()
                combined = f"{summary} {headline} {source}"
                return t_lower in combined
            
            filtered = [it for it in recent_items if match(it)]
            print(f"🔍 Found {len(filtered)} recent items matching '{topic}'")
        else:
            filtered = recent_items
        
        # Sort by date descending (newest first)
        def key_fn(it):
            dt = _to_dt(it.get("date", ""))
            return dt or datetime.min
        
        filtered.sort(key=key_fn, reverse=True)
        return filtered[:limit]
    
    except Exception as e:
        print(f"❌ DDB scan error: {e}")
        return []

def format_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Format article data for frontend consumption"""
    def convert_decimal(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return obj
    
    formatted = {}
    for key, value in article.items():
        if isinstance(value, dict):
            formatted[key] = {k: convert_decimal(v) for k, v in value.items()}
        else:
            formatted[key] = convert_decimal(value)
    
    # Ensure required fields
    formatted.setdefault('id', formatted.get('id', 'unknown'))
    formatted.setdefault('headline', formatted.get('headline', 'Untitled'))
    formatted.setdefault('summary', formatted.get('summary', ''))
    formatted.setdefault('source', formatted.get('source', 'Unknown'))
    formatted.setdefault('date', formatted.get('date', datetime.utcnow().isoformat()))
    formatted.setdefault('url', formatted.get('url', ''))
    
    # Fix sentiment
    overall_sentiment = formatted.get('overall_sentiment', 'neutral')
    formatted['overall_sentiment'] = overall_sentiment
    formatted['sentiment'] = _sentiment_bucket(overall_sentiment)
    
    formatted.setdefault('entities', formatted.get('entities', []))
    formatted.setdefault('emotions', formatted.get('emotions', {}))
    
    return formatted

# API Routes
@app.get("/")
async def root():
    return {"message": "NewsInsight API", "status": "ok", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/health")
async def health_api():
    return {"status": "healthy"}

@app.get("/api/articles/search")
async def search_articles(
    query: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(6, description="Number of articles to return"),
    max_age_days: int = Query(2, description="Maximum age of articles in days")
):
    """Search for articles"""
    try:
        print(f"🔍 Searching for: '{query}' (limit: {limit})")
        
        # Search in DynamoDB with age filtering
        raw_articles = search_articles_ddb(query, limit, max_age_days)
        
        if not raw_articles:
            print("📰 No articles found in database")
            return []
        
        # Format articles for frontend
        articles = [format_article(art) for art in raw_articles]
        
        print(f"✅ Returning {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/blacklist")
async def add_to_blacklist(
    item_type: str = Query(..., description="Type: source, domain, or keyword"),
    value: str = Query(..., description="Value to blacklist"),
    reason: str = Query("", description="Reason for blacklisting")
):
    """Add item to content blacklist"""
    try:
        if not content_filter:
            raise HTTPException(status_code=503, detail="Content filtering not available")
        
        content_filter.add_to_blacklist(item_type, value, reason)
        return {"message": f"Added {item_type}='{value}' to blacklist", "success": True}
        
    except Exception as e:
        print(f"❌ Blacklist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/quality-stats")
async def get_quality_stats():
    """Get content quality statistics"""
    try:
        # This would query your quality metrics
        # For now, return mock data
        return {
            "total_processed": 1250,
            "high_quality": 892,
            "medium_quality": 234,
            "rejected": 124,
            "blacklisted_sources": 15,
            "quality_distribution": {
                "90-100": 445,
                "70-89": 447,
                "50-69": 234,
                "30-49": 89,
                "0-29": 35
            }
        }
        
    except Exception as e:
        print(f"❌ Quality stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Debug Railway environment
    railway_port = os.environ.get("PORT")
    print(f"🔌 Railway PORT env var: {railway_port}")
    
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting NewsInsight API on port {port}")
    print(f"🌍 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    print(f"🗄️ DynamoDB Table: {DDB_TABLE}")
    print(f"🤖 Bedrock Model: {BEDROCK_MODELID}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )

# Background cleanup functions
def cleanup_old_articles(max_age_days: int = 30) -> Dict[str, int]:
    """Remove articles older than specified days"""
    if not table:
        return {"error": "DynamoDB not available"}
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        print(f"🗑️ Cleaning up articles older than {cutoff_date.strftime('%Y-%m-%d %H:%M')} UTC")
        
        # Scan for old articles
        resp = table.scan()
        items = resp.get("Items", [])
        
        old_articles = []
        for item in items:
            article_date = _to_dt(item.get("date", ""))
            if not article_date or article_date < cutoff_date:
                old_articles.append(item)
        
        # Delete old articles
        deleted_count = 0
        for article in old_articles:
            try:
                table.delete_item(Key={"id": article["id"]})
                deleted_count += 1
                
                # Also delete from S3 if available
                if s3 and PROC_BUCKET:
                    s3_key = f"{PROCESSED_PREFIX}{article['id']}.json"
                    s3.delete_object(Bucket=PROC_BUCKET, Key=s3_key)
                    
            except Exception as e:
                print(f"Failed to delete article {article.get('id', 'unknown')}: {e}")
        
        print(f"✅ Cleanup complete: {deleted_count} old articles removed")
        return {
            "total_scanned": len(items),
            "old_articles_found": len(old_articles),
            "deleted": deleted_count
        }
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return {"error": str(e)}

@app.post("/api/admin/cleanup")
async def cleanup_articles(max_age_days: int = Query(30, description="Maximum age in days")):
    """Admin endpoint to cleanup old articles"""
    try:
        result = cleanup_old_articles(max_age_days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles/age-stats")
async def get_age_statistics():
    """Get article age distribution statistics"""
    try:
        if not table:
            return {"error": "DynamoDB not available"}
        
        # Scan all articles
        resp = table.scan()
        items = resp.get("Items", [])
        
        now = datetime.utcnow()
        age_buckets = {
            "0-1_days": 0,
            "1-2_days": 0,
            "2-7_days": 0,
            "7-30_days": 0,
            "30+_days": 0,
            "no_date": 0
        }
        
        for item in items:
            article_date = _to_dt(item.get("date", ""))
            if not article_date:
                age_buckets["no_date"] += 1
                continue
            
            age_days = (now - article_date).total_seconds() / (24 * 3600)
            
            if age_days <= 1:
                age_buckets["0-1_days"] += 1
            elif age_days <= 2:
                age_buckets["1-2_days"] += 1
            elif age_days <= 7:
                age_buckets["2-7_days"] += 1
            elif age_days <= 30:
                age_buckets["7-30_days"] += 1
            else:
                age_buckets["30+_days"] += 1
        
        return {
            "total_articles": len(items),
            "age_distribution": age_buckets,
            "recommended_cleanup": age_buckets["30+_days"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Art
icle ingestion with filtering
def fetch_and_filter_articles(topic: str) -> Dict[str, Any]:
    """Fetch articles from APIs and apply content filtering"""
    
    if not content_filter:
        return {"error": "Content filtering not available"}
    
    try:
        # Mock article fetching (replace with your actual API calls)
        print(f"📥 Fetching articles for topic: {topic}")
        
        # This would be your actual API calls to NewsAPI and Guardian
        raw_articles = []  # Replace with actual API calls
        
        stats = {
            "fetched": len(raw_articles),
            "age_rejected": 0,
            "content_rejected": 0,
            "processed": 0,
            "stored": 0
        }
        
        for article in raw_articles:
            # Layer 1: Basic filtering
            should_process, reason = content_filter.preprocess_filter(article)
            if not should_process:
                if "old" in reason.lower():
                    stats["age_rejected"] += 1
                else:
                    stats["content_rejected"] += 1
                print(f"🚫 Rejected: {reason}")
                continue
            
            # Layer 2: AI legitimacy check (if needed)
            # For now, assume all articles that pass Layer 1 are legitimate
            
            # Process article (your existing sentiment analysis)
            stats["processed"] += 1
            # Store article (your existing storage logic)
            stats["stored"] += 1
        
        return stats
        
    except Exception as e:
        print(f"❌ Article ingestion failed: {e}")
        return {"error": str(e)}

@app.post("/api/articles/ingest")
async def ingest_articles(
    topic: str = Query(..., description="Topic to ingest articles for")
):
    """Ingest new articles with content filtering"""
    try:
        result = fetch_and_filter_articles(topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))