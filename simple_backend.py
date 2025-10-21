#!/usr/bin/env python3
"""
Simplified backend for Railway deployment
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="NewsInsight API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://news-insight-ai-tawny.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check
@app.get("/")
async def root():
    return {"message": "NewsInsight API is running", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is working"}

# Mock articles endpoint
@app.get("/api/articles/search")
async def search_articles():
    mock_articles = [
        {
            "id": "test-1",
            "headline": "Railway Backend is Now Working!",
            "summary": "The NewsInsight backend has been successfully deployed to Railway and is responding to API calls.",
            "source": "NewsInsight",
            "date": "2024-10-21T12:00:00Z",
            "url": "https://railway.app",
            "sentiment": "positive",
            "overall_sentiment": "positive",
            "entities": [{"text": "Railway", "type": "platform"}],
            "emotions": {"joy": "high", "trust": "high"},
            "_isRealData": True
        }
    ]
    return mock_articles

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting simplified NewsInsight API on port {port}")
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )