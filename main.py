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
AWS_PROFILE     = os.getenv("AWS_PROFILE", "default")
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
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    ddb     = session.resource("dynamodb")
    s3      = session.client("s3") if PROC_BUCKET else None
    bedrock = session.client("bedrock-runtime") if BEDROCK_MODELID else None
    table = ddb.Table(DDB_TABLE) if DDB_TABLE else None
    print(f"✅ AWS initialized - Profile: {AWS_PROFILE}, Region: {AWS_REGION}, Table: {DDB_TABLE}")
except Exception as e:
    print(f"⚠️ AWS initialization failed: {e}")
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

def search_articles_ddb(topic: Optional[str] = None, limit: int = 6) -> List[Dict[str, Any]]:
    """Search articles in DynamoDB"""
    if not table:
        print("⚠️ DynamoDB table not available")
        return []
    
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