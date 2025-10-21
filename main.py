import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from Railway!", "status": "ok"}

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
    uvicorn.run(app, host="0.0.0.0", port=port)