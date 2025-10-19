import os, json, time, hashlib, urllib.request, urllib.parse, boto3
from datetime import datetime, timezone

s3  = boto3.client("s3")
ssm = boto3.client("ssm")

RAW_PREFIX = "news-raw/"

def _get_param(name: str) -> str:
    """Retrieve API keys from AWS SSM Parameter Store."""
    return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]

def _put_json(bucket, key, payload):
    """Upload JSON object to S3."""
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json"
    )

# ---------- API Fetchers ----------

# --- NewsAPI (supports top-headlines or everything) ---
def fetch_newsapi(api_key: str, q: str | None = None, from_iso: str | None = None, page_size: int = 20):
    if q:
        base = "https://newsapi.org/v2/everything"
        params = {"q": q, "pageSize": str(page_size)}
        if from_iso: params["from"] = from_iso  # e.g., "2025-10-18"
        params["sortBy"] = "publishedAt"
    else:
        base = "https://newsapi.org/v2/top-headlines"
        params = {"language": "en", "country": "us", "pageSize": str(page_size)}
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{base}?{qs}&apiKey={api_key}", headers={"User-Agent":"newsinsights-ai/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for a in data.get("articles", []):
        out.append({
            "source": "newsapi",
            "headline": a.get("title"),
            "url": a.get("url"),
            "date": a.get("publishedAt"),
            "author": a.get("author"),
            "description": a.get("description"),
            "content": a.get("content"),
        })
    return out

# --- The Guardian (supports query + pagination) ---
def fetch_guardian(api_key: str, q: str | None = None, page: int = 1, page_size: int = 20):
    base = "https://content.guardianapis.com/search"
    params = {
        "order-by": "newest",
        "page-size": str(page_size),
        "page": str(page),
        "show-fields": "headline,trailText,body",
        "api-key": api_key,
    }
    if q: params["q"] = q
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{base}?{qs}", headers={"User-Agent":"newsinsights-ai/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    out = []
    for r in data.get("response", {}).get("results", []):
        f = r.get("fields", {}) or {}
        out.append({
            "source": "guardian",
            "headline": f.get("headline"),
            "url": r.get("webUrl"),
            "date": r.get("webPublicationDate"),
            "author": None,
            "description": f.get("trailText"),
            "content": f.get("body"),
        })
    return out


# ---------- Main Handler ----------

def handler(event, context):
    bucket = os.environ["RAW_BUCKET"]
    newsapi_key  = _get_param(os.environ["NEWSAPI_PARAM"])
    guardian_key = _get_param(os.environ["GUARDIAN_PARAM"])

    articles = []

    # Fetch from both APIs
    try:
        articles += fetch_newsapi(newsapi_key)
    except Exception as e:
        print("NewsAPI error:", e)

    try:
        articles += fetch_guardian(guardian_key)
    except Exception as e:
        print("Guardian API error:", e)

    if not articles:
        return {"status": "no_articles"}

    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Save each article as separate JSON
    for a in articles:
        base = (a.get("url") or a.get("headline") or str(time.time())).encode("utf-8")
        doc_id = hashlib.sha256(base).hexdigest()[:16]
        key = f"{RAW_PREFIX}{now}/{doc_id}.json"
        _put_json(bucket, key, a)

    return {"status": "ok", "count": len(articles)}
