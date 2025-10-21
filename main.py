#!/usr/bin/env python3
"""
FastAPI backend for NewsInsight React UI
Full functionality with AWS integration
"""

import os
import json
import sys
import hashlib
from datetime import datetime
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
        
    else:
        print("⚠️ AWS credentials not found - running in demo mode")
        print(f"   AWS_ACCESS_KEY_ID: {'✅' if aws_access_key else '❌'}")
        print(f"   AWS_SECRET_ACCESS_KEY: {'✅' if aws_secret_key else '❌'}")
        session = None
    
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

def search_articles_ddb(topic: Optional[str] = None, limit: int = 6) -> List[Dict[str, Any]]:
    """Search articles in DynamoDB"""
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
        
        # Filter by topic if provided
        if topic and topic.strip():
            t_lower = topic.lower().strip()
            
            def match(item):
                summary = (item.get("summary") or "").lower()
                headline = (item.get("headline") or "").lower()
                source = (item.get("source") or "").lower()
                combined = f"{summary} {headline} {source}"
                return t_lower in combined
            
            filtered = [it for it in items if match(it)]
            print(f"🔍 Found {len(filtered)} items matching '{topic}'")
        else:
            filtered = items
        
        # Sort by date descending
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
    limit: int = Query(6, description="Number of articles to return")
):
    """Search for articles"""
    try:
        print(f"🔍 Searching for: '{query}' (limit: {limit})")
        
        # Search in DynamoDB
        raw_articles = search_articles_ddb(query, limit)
        
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