import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    print(f"📥 Incoming request: {request.method} {request.url}")
    print(f"📥 Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"📤 Response: {response.status_code} (took {process_time:.2f}s)")
    
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    print("🏠 Root endpoint called - Railway is reachable!")
    return {
        "message": "✅ Railway Backend Connected Successfully!", 
        "status": "ok", 
        "port": os.environ.get("PORT", "8000"),
        "timestamp": time.time(),
        "platform": "Railway",
        "environment": os.environ.get('RAILWAY_ENVIRONMENT', 'local')
    }

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.get("/api/articles/search")
def search():
    return [
        {
            "id": "railway-1",
            "headline": "🚀 Railway Backend is Live!",
            "summary": "The NewsInsight backend is now successfully running on Railway and responding to API calls from Vercel.",
            "source": "Railway",
            "date": "2024-10-21T12:00:00Z",
            "sentiment": "positive",
            "overall_sentiment": "positive",
            "_isRealData": True
        }
    ]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting on port {port}")
    print(f"🌍 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info",
        access_log=True
    )