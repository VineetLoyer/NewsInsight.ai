import os
import json
import sys
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple

import boto3
import streamlit as st
import requests

# ---------- Config ----------
AWS_REGION      = os.getenv("AWS_REGION", "us-west-2")
DDB_TABLE       = os.getenv("DDB_TABLE", "news_metadata")
PROC_BUCKET     = os.getenv("PROC_BUCKET", "")  # e.g., newsinsights-processed-<acct>-<region>
MODEL_FAMILY    = os.getenv("MODEL_FAMILY", "anthropic").lower()  # "anthropic" | "amazon"
BEDROCK_MODELID = os.getenv("BEDROCK_MODEL_ID", "")  # Inference Profile ARN or modelId
DEBUG_MODE      = os.getenv("DEBUG_MODE", "false").lower() == "true"
NEWSAPI_KEY     = os.getenv("NEWSAPI_KEY")
GUARDIAN_KEY    = os.getenv("GUARDIAN_KEY")
RAW_BUCKET      = os.getenv("RAW_BUCKET")
PROCESSED_PREFIX = os.getenv("PROCESSED_PREFIX", "news-processed/")
RAW_PREFIX       = os.getenv("RAW_PREFIX", "news-raw/")

# More lenient startup for development
if DEBUG_MODE:
    st.warning("🔧 Running in DEBUG mode. Some AWS services may be unavailable.")
# ----------------------------

# AWS clients
try:
    session = boto3.Session(region_name=AWS_REGION)
    ddb     = session.resource("dynamodb")
    s3      = session.client("s3") if PROC_BUCKET else None
    bedrock = session.client("bedrock-runtime") if BEDROCK_MODELID else None
    table = ddb.Table(DDB_TABLE)
except Exception as e:
    st.error(f"AWS initialization failed: {e}")
    if not DEBUG_MODE:
        st.stop()

# ---------- Styles (NYT-inspired serif) ----------
st.set_page_config(
    page_title="NewsInsight — Daily Brief",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800;900&family=Crimson+Text:ital,wght@0,400;0,600;1,400&family=EB+Garamond:wght@400;500;600;700&display=swap');

:root {
  --headline-font: 'Playfair Display', 'EB Garamond', 'Georgia', 'Times New Roman', serif;
  --body-font: 'Crimson Text', 'Georgia', 'Times New Roman', serif;
  --accent-color: #1a1a1a;
  --text-color: #2c3e50;
  --border-color: #e5e7eb;
  --light-border: #f3f4f6;
  --positive-bg: #ecfdf5;
  --positive-text: #065f46;
  --positive-border: #10b981;
  --neutral-bg: #f8fafc;
  --neutral-text: #64748b;
  --neutral-border: #94a3b8;
  --negative-bg: #fef2f2;
  --negative-text: #dc2626;
  --negative-border: #ef4444;
  --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  --card-shadow-hover: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* Global Typography */
* {
  font-family: var(--body-font) !important;
  color: var(--text-color);
}

h1, h2, h3, h4, .headline {
  font-family: var(--headline-font) !important;
  color: var(--accent-color) !important;
  letter-spacing: -0.025em;
  line-height: 1.2;
  font-weight: 700;
}

h1 {
  font-size: 3.75rem;
  font-weight: 900;
  margin-bottom: 0.5rem;
  text-align: center;
  border-bottom: 4px double var(--accent-color);
  padding-bottom: 0.5rem;
}

h2 {
  font-size: 2.25rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  font-weight: 700;
}

h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

body {
  line-height: 1.7;
  font-size: 1.1rem;
}

/* Header Styling */
.main-header {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem 0;
  border-bottom: 2px solid var(--border-color);
}

.main-title {
  font-family: var(--headline-font) !important;
  font-size: 4rem !important;
  font-weight: 900 !important;
  color: var(--accent-color) !important;
  margin-bottom: 0.5rem !important;
  letter-spacing: -0.02em;
}

.main-subtitle {
  font-size: 1.25rem;
  color: #6b7280;
  font-style: italic;
  margin-top: 0.5rem;
}

/* Search Section */
.search-section {
  background: #fafafa;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  border: 1px solid var(--light-border);
}

.search-title {
  font-family: var(--headline-font) !important;
  font-size: 1.5rem !important;
  font-weight: 600 !important;
  margin-bottom: 1rem !important;
  color: var(--accent-color) !important;
}

/* Topic Suggestions */
.topic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}

.topic-button {
  background: white !important;
  border: 2px solid var(--border-color) !important;
  border-radius: 25px !important;
  padding: 0.5rem 1rem !important;
  font-size: 0.9rem !important;
  font-weight: 500 !important;
  color: var(--text-color) !important;
  transition: all 0.2s ease !important;
  cursor: pointer !important;
}

.topic-button:hover {
  border-color: var(--accent-color) !important;
  background: var(--accent-color) !important;
  color: white !important;
  transform: translateY(-1px);
}

/* News Cards */
.news-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 2rem;
  background: white;
  box-shadow: var(--card-shadow);
  margin-bottom: 2rem;
  transition: all 0.3s ease;
  position: relative;
}

.news-card:hover {
  box-shadow: var(--card-shadow-hover);
  transform: translateY(-2px);
}

.card-headline {
  font-family: var(--headline-font) !important;
  font-size: 1.75rem !important;
  line-height: 1.3 !important;
  margin-bottom: 0.75rem !important;
  color: var(--accent-color) !important;
  font-weight: 700 !important;
  letter-spacing: -0.01em;
}

.card-meta {
  color: #6b7280;
  font-size: 1rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--light-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card-teaser {
  font-size: 1.1rem;
  line-height: 1.7;
  color: var(--text-color);
  margin-bottom: 1.5rem;
  font-style: italic;
  text-align: justify;
}

/* Sentiment Chips */
.sentiment-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  margin-left: 0.5rem;
  border: 2px solid;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sentiment-positive {
  background: var(--positive-bg);
  color: var(--positive-text);
  border-color: var(--positive-border);
}

.sentiment-neutral {
  background: var(--neutral-bg);
  color: var(--neutral-text);
  border-color: var(--neutral-border);
}

.sentiment-negative {
  background: var(--negative-bg);
  color: var(--negative-text);
  border-color: var(--negative-border);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  min-width: 140px;
  padding: 0.75rem 1rem !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  transition: all 0.2s ease !important;
  border: 2px solid !important;
}

.btn-original {
  background: var(--accent-color) !important;
  color: white !important;
  border-color: var(--accent-color) !important;
}

.btn-original:hover {
  background: #374151 !important;
  border-color: #374151 !important;
}

.btn-explain {
  background: #3b82f6 !important;
  color: white !important;
  border-color: #3b82f6 !important;
}

.btn-explain:hover {
  background: #2563eb !important;
  border-color: #2563eb !important;
}

.btn-chat {
  background: #10b981 !important;
  color: white !important;
  border-color: #10b981 !important;
}

.btn-chat:hover {
  background: #059669 !important;
  border-color: #059669 !important;
}

/* Tags/Entities */
.tags-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--light-border);
}

.tags-label {
  font-size: 0.9rem;
  color: #6b7280;
  margin-bottom: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tag {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  margin: 0.25rem 0.5rem 0.25rem 0;
  font-size: 0.85rem;
  background: white;
  color: var(--text-color);
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.tag:hover {
  background: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
  transform: translateY(-1px);
}

/* Emotion Badges */
.emotion-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  margin: 0.125rem 0.25rem 0.125rem 0;
  border: 1px solid;
  font-weight: 500;
  text-transform: capitalize;
}

.emotion-level-high {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

.emotion-level-medium {
  background: #fef3c7;
  color: #92400e;
  border-color: #fcd34d;
}

.emotion-level-low {
  background: #dcfce7;
  color: #166534;
  border-color: #86efac;
}

.emotion-level-none {
  background: #f8fafc;
  color: #475569;
  border-color: #cbd5e1;
}

/* Expanders */
.stExpander {
  border: 1px solid var(--border-color) !important;
  border-radius: 8px !important;
  margin-top: 1rem !important;
}

/* Responsive Design */
@media (max-width: 768px) {
  .main-title {
    font-size: 2.5rem !important;
  }
  
  .card-headline {
    font-size: 1.5rem !important;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .action-btn {
    min-width: auto;
  }
}

/* Custom Streamlit Overrides */
.stButton > button {
  font-family: var(--body-font) !important;
}

.stTextInput > div > div > input {
  font-family: var(--body-font) !important;
  font-size: 1.1rem !important;
  padding: 0.75rem !important;
  border-radius: 8px !important;
}

/* Links */
a {
  color: var(--accent-color);
  text-decoration: none;
  border-bottom: 1px solid var(--accent-color);
  transition: all 0.2s ease;
}

a:hover {
  color: #374151;
  border-bottom-color: #374151;
}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
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

def _sentiment_chip(sent: str) -> str:
    sent = (sent or "neutral").lower().strip()
    style = _SENTIMENT_STYLES.get(sent, _SENTIMENT_STYLES["neutral"])
    return (
        f'<span class="sentiment-chip" '
        f'style="background:{style["bg"]};color:{style["fg"]};">'
        f'{style["label"]}</span>'
    )


_SENTIMENT_STYLES = {
    "very_negative": {"label": "Very Negative", "bg": "#7f1d1d", "fg": "#fef2f2"},
    "negative": {"label": "Negative", "bg": "#fca5a5", "fg": "#7f1d1d"},
    "neutral": {"label": "Neutral", "bg": "#ffffff", "fg": "#1f2937"},
    "positive": {"label": "Positive", "bg": "#bbf7d0", "fg": "#14532d"},
    "very_positive": {"label": "Very Positive", "bg": "#047857", "fg": "#ecfdf5"},
}

NRC_EMOTIONS = [
    "anger",
    "anticipation",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "surprise",
    "trust",
]

EMOTION_LEVELS = {"high", "medium", "low", "none"}

DEFAULT_EMOTIONS = {emotion: "none" for emotion in NRC_EMOTIONS}


def _sentiment_bucket(overall: str) -> str:
    overall = (overall or "neutral").lower()
    if overall in ("very_negative", "negative"):
        return "negative"
    if overall in ("very_positive", "positive"):
        return "positive"
    return "neutral"


def _set_topic(value: str) -> None:
    """Update the shared topic search box via callbacks."""
    st.session_state["topic_input"] = value

def _normalize_date(date_str: Optional[str]) -> str:
    if not date_str:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dt = _to_dt(date_str)
        if dt:
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Attempt generic ISO parse
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _make_doc_id(article: Dict[str, Any]) -> str:
    base = article.get("url") or article.get("headline") or article.get("title") or str(article)
    return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:16]

def _fetch_from_newsapi(topic: str) -> List[Dict[str, Any]]:
    if not NEWSAPI_KEY:
        return []
    params = {
        "q": topic,
        "language": "en",
        "pageSize": 10,
        "sortBy": "publishedAt"
    }
    url = "https://newsapi.org/v2/everything"
    headers = {"Authorization": NEWSAPI_KEY}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data.get("articles", [])
    except Exception as e:
        if DEBUG_MODE:
            st.warning(f"[DEBUG] NewsAPI fetch failed: {e}")
        return []

def _fetch_from_guardian(topic: str) -> List[Dict[str, Any]]:
    if not GUARDIAN_KEY:
        return []
    params = {
        "order-by": "newest",
        "page-size": 10,
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
        if DEBUG_MODE:
            st.warning(f"[DEBUG] Guardian fetch failed: {e}")
        return []

def _fetch_articles_from_apis(topic: str) -> List[Dict[str, Any]]:
    articles: List[Dict[str, Any]] = []
    if not topic:
        return articles
    articles.extend(_fetch_from_newsapi(topic))
    articles.extend(_fetch_from_guardian(topic))

    normalized: List[Dict[str, Any]] = []
    for art in articles:
        headline = art.get("title") or art.get("headline")
        if not headline:
            continue
        normalized.append({
            "id": _make_doc_id(art),
            "headline": headline,
            "summary": art.get("description") or art.get("summary"),
            "content": art.get("content") or art.get("body") or art.get("bodyText"),
            "source": (art.get("source") or {}).get("name") if isinstance(art.get("source"), dict) else art.get("source", ""),
            "date": _normalize_date(art.get("publishedAt") or art.get("date")),
            "url": art.get("url"),
            "author": art.get("author") or (art.get("fields", {}) if isinstance(art.get("fields"), dict) else {}).get("byline"),
        })
    return normalized

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

def _analyze_with_bedrock_local(text: str) -> Dict[str, Any]:
    fallback_summary = (text or "")[:400] + ("…" if text and len(text) > 400 else "")
    default_payload = {
        "overall_sentiment": "neutral",
        "sentiment": "neutral",
        "emotions": DEFAULT_EMOTIONS.copy(),
        "summary": fallback_summary,
        "entities": []
    }

    if not bedrock or not BEDROCK_MODELID:
        return default_payload

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
        if DEBUG_MODE:
            st.warning(f"[DEBUG] Bedrock analysis failed: {e}")
        data = default_payload.copy()

    overall = (data.get("overall_sentiment") or data.get("sentiment") or "neutral").lower()
    if overall not in _SENTIMENT_STYLES:
        overall = "neutral"
    data["overall_sentiment"] = overall
    data["sentiment"] = _sentiment_bucket(overall)

    emotions_raw = data.get("emotions") or {}
    sanitized = DEFAULT_EMOTIONS.copy()
    if isinstance(emotions_raw, dict):
        for emotion in NRC_EMOTIONS:
            level = emotions_raw.get(emotion, "none")
            if isinstance(level, str):
                lvl = level.lower()
                sanitized[emotion] = lvl if lvl in EMOTION_LEVELS else "none"
            else:
                sanitized[emotion] = "none"
    data["emotions"] = sanitized

    if not isinstance(data.get("entities"), list):
        data["entities"] = []
    if not data.get("summary"):
        data["summary"] = fallback_summary
    return data

def _store_processed_article(article: Dict[str, Any], analysis: Dict[str, Any]) -> Optional[str]:
    doc_id = article.get("id") or _make_doc_id(article)
    if not doc_id:
        return None
    # Write to S3 processed bucket if available
    processed_payload = {
        "id": doc_id,
        "headline": article.get("headline"),
        "summary": analysis.get("summary") or article.get("summary"),
        "sentiment": analysis.get("sentiment", "neutral"),
        "overall_sentiment": analysis.get("overall_sentiment", "neutral"),
        "emotions": analysis.get("emotions", DEFAULT_EMOTIONS.copy()),
        "entities": analysis.get("entities", []),
        "url": article.get("url"),
        "source": article.get("source", "unknown"),
        "date": article.get("date"),
        "ingested_at": datetime.utcnow().isoformat()
    }

    processed_payload["sentiment"] = _sentiment_bucket(processed_payload.get("overall_sentiment"))

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
            if DEBUG_MODE:
                st.warning(f"[DEBUG] Failed to write processed doc to S3: {e}")

    # Optionally store raw article for completeness
    if s3 and RAW_BUCKET:
        try:
            raw_key = f"{RAW_PREFIX}{doc_id}.json"
            s3.put_object(
                Bucket=RAW_BUCKET,
                Key=raw_key,
                Body=json.dumps(article, indent=2).encode("utf-8"),
                ContentType="application/json"
            )
        except Exception:
            pass

    # Write to DynamoDB
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
        table.put_item(Item=item)
    except Exception as e:
        if DEBUG_MODE:
            st.warning(f"[DEBUG] Failed to write item to DynamoDB: {e}")
        return None

    return doc_id

def ingest_topic(topic: str) -> Tuple[int, int]:
    articles = _fetch_articles_from_apis(topic)
    if not articles:
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
            # Warm cache: store in session state for immediate use
            st.session_state[f"analysis-{doc_id}"] = analysis.get("summary")
    return processed, stored

@st.cache_data(show_spinner=False, ttl=60)
def search_articles_ddb(topic: Optional[str] = None, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Improved search: DDB scan + keyword matching on summary/headline.
    Falls back to recent articles if no keyword match.
    """
    try:
        # Scan table
        items = []
        resp = table.scan(Limit=200)
        items.extend(resp.get("Items", []) or [])
        
        # Continue scanning if more items
        while "LastEvaluatedKey" in resp:
            resp = table.scan(Limit=200, ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []) or [])
            if len(items) > 500:  # Safety limit
                break
        
        if DEBUG_MODE:
            st.write(f"[DEBUG] Total items scanned from DDB: {len(items)}")
        
        # Filter by topic if provided
        if topic and topic.strip():
            t_lower = topic.lower().strip()
            def match(item):
                summary = (item.get("summary") or "").lower()
                headline = (item.get("headline") or "").lower()
                combined = f"{summary} {headline}"
                return t_lower in combined
            
            filtered = [it for it in items if match(it)]
            if DEBUG_MODE:
                st.write(f"[DEBUG] Items matching '{topic}': {len(filtered)}")
        else:
            filtered = items
        
        # Sort by date descending
        def key_fn(it):
            dt = _to_dt(it.get("date", ""))
            return dt or datetime.min
        
        filtered.sort(key=key_fn, reverse=True)
        
        return filtered[:limit]
    
    except Exception as e:
        st.error(f"DDB scan error: {e}")
        if DEBUG_MODE:
            st.write(f"[DEBUG] Exception: {e}")
        return []

@st.cache_data(show_spinner=False, ttl=120)
def get_processed_doc(doc_id: str) -> Dict[str, Any]:
    """
    Fetch full processed document from S3.
    Falls back to minimal data if unavailable.
    """
    try:
        if not s3 or not PROC_BUCKET:
            return {"summary": "", "url": "", "entities": [], "overall_sentiment": "neutral", "emotions": DEFAULT_EMOTIONS.copy()}

        key = f"{PROCESSED_PREFIX}{doc_id}.json"
        obj = s3.get_object(Bucket=PROC_BUCKET, Key=key)
        return json.loads(obj["Body"].read())
    except Exception as e:
        if DEBUG_MODE:
            st.warning(f"Could not fetch {doc_id} from S3: {e}")
        return {"summary": "", "url": "", "entities": [], "overall_sentiment": "neutral", "emotions": DEFAULT_EMOTIONS.copy()}

def bedrock_explain(text: str) -> str:
    """
    Detailed analysis for the Explain button.
    """
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
    """
    Lightweight chat grounded in a single article.
    """
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

# ---------- UI ----------
# Header with classic newspaper styling
st.markdown("""
<div class="main-header">
  <div class="main-title">📰 NewsInsight</div>
  <div class="main-subtitle">Verified News Insights & Deep Analysis</div>
  <div style="font-size: 0.9rem; color: #9ca3af; margin-top: 0.5rem;">
    AI-Powered News Intelligence • Real-time Analysis • Sentiment & Emotion Tracking
  </div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""

# Main search section (moved to main area for better UX)
st.markdown("""
<div class="search-section">
  <div class="search-title">🔍 Search News & Analysis</div>
</div>
""", unsafe_allow_html=True)

# Search input
col1, col2 = st.columns([3, 1])
with col1:
    st.text_input(
        "",
        placeholder="Search for topics like 'AI regulation', 'climate change', 'market trends'...",
        help="Enter keywords to find relevant articles, or leave empty to see latest news",
        key="topic_input",
        label_visibility="collapsed"
    )

with col2:
    search_clicked = st.button("🔍 Search", use_container_width=True, type="primary")

# Suggested topics section
st.markdown("### 📌 Trending Topics")
st.markdown("Click on any topic below to explore related articles:")

suggested_topics = [
    "Politics", "Technology", "Business", "Markets", 
    "Science", "World", "Climate", "AI", "Healthcare", 
    "Economy", "Sports", "Entertainment"
]

# Create a more visually appealing topic grid
cols = st.columns(4)
for i, topic in enumerate(suggested_topics):
    with cols[i % 4]:
        if st.button(
            topic,
            key=f"topic-{topic}",
            use_container_width=True,
            on_click=_set_topic,
            args=(topic,)
        ):
            pass

st.divider()

# Sidebar for additional controls
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    
    # Article limit selector
    article_limit = st.selectbox(
        "Articles to show",
        options=[3, 5, 10, 15],
        index=0,
        help="Number of articles to display"
    )
    
    # Sentiment filter
    sentiment_filter = st.selectbox(
        "Filter by sentiment",
        options=["All", "Positive", "Neutral", "Negative"],
        index=0,
        help="Filter articles by sentiment analysis"
    )
    
    st.divider()
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    if st.button("📰 Latest News", use_container_width=True):
        st.session_state["topic_input"] = ""
        st.rerun()
    
    if st.button("🔥 Trending Now", use_container_width=True):
        st.session_state["topic_input"] = "trending"
        st.rerun()
    
    st.divider()
    
    if DEBUG_MODE:
        st.info(f"**Debug Info:**\n- Region: {AWS_REGION}\n- Table: {DDB_TABLE}\n- Model: {BEDROCK_MODELID or 'Not set'}")

# Search and display results
topic = st.session_state.get("topic_input", "")
topic_suffix = f' for "{topic}"' if topic else ''

# Dynamic title based on search
if topic:
    st.markdown(f"## 🗞️ News Analysis{topic_suffix}")
    st.markdown(f"*Found insights related to your search*")
else:
    st.markdown("## 🗞️ Latest Verified News Insights")
    st.markdown("*Real-time analysis of breaking news and trending topics*")

results = search_articles_ddb(topic, limit=article_limit)
ingestion_notice: Optional[Tuple[str, str]] = None

if topic and topic.strip() and not results:
    if not (NEWSAPI_KEY or GUARDIAN_KEY):
        ingestion_notice = (
            "warning",
            "Configure NEWSAPI_KEY or GUARDIAN_KEY to fetch fresh coverage for this topic."
        )
    else:
        with st.spinner(f"Fetching latest coverage for '{topic}'…"):
            processed, stored = ingest_topic(topic)
        search_articles_ddb.clear()
        get_processed_doc.clear()
        results = search_articles_ddb(topic, limit=3)

        if stored > 0:
            ingestion_notice = (
                "success",
                f"Fetched {processed} articles and added {stored} new insights from live sources."
            )
        elif processed > 0:
            ingestion_notice = (
                "info",
                "Fetched fresh articles, but they were already present in DynamoDB."
            )
        else:
            ingestion_notice = (
                "warning",
                "No fresh articles were available from the news APIs right now."
            )

if ingestion_notice:
    level, message = ingestion_notice
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.info(message)

# Show loading state
if search_clicked or topic:
    with st.spinner("🔍 Searching for relevant articles..."):
        pass

if not results:
    # Enhanced empty state
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; background: #f8fafc; border-radius: 12px; margin: 2rem 0;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📰</div>
        <h3 style="color: #374151; margin-bottom: 1rem;">No articles found</h3>
        <p style="color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem;">
            We couldn't find any articles matching your search criteria.
        </p>
        <div style="background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #e5e7eb;">
            <p style="font-weight: 600; margin-bottom: 1rem;">Try these suggestions:</p>
            <ul style="text-align: left; color: #6b7280;">
                <li>Use different or broader keywords</li>
                <li>Check the trending topics above</li>
                <li>Clear your search to see latest articles</li>
                <li>Try searching for general topics like "technology" or "politics"</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if DEBUG_MODE:
        with st.expander("🔧 Debug Information"):
            st.write("**Troubleshooting:**")
            st.write("- Ensure DDB_TABLE is set and accessible")
            st.write("- Verify articles exist in the news_metadata table")
            st.write("- Check fetch_articles_lambda.py is running")
            st.write(f"- Current search term: '{topic}'")
            st.write(f"- Article limit: {article_limit}")
            st.write(f"- Sentiment filter: {sentiment_filter}")
else:
    # Apply sentiment filtering and count results
    filtered_results = []
    for article in results:
        overall_sentiment = (
            article.get("overall_sentiment") or 
            article.get("sentiment") or 
            "neutral"
        )
        
        # Apply sentiment filter
        if sentiment_filter != "All":
            sentiment_bucket = _sentiment_bucket(overall_sentiment)
            if sentiment_filter.lower() != sentiment_bucket:
                continue
        
        filtered_results.append(article)
    
    # Show results summary with quick stats
    if filtered_results:
        filter_text = f" (filtered by {sentiment_filter} sentiment)" if sentiment_filter != "All" else ""
        
        # Calculate sentiment distribution
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for article in filtered_results:
            sentiment = _sentiment_bucket(article.get("overall_sentiment") or article.get("sentiment") or "neutral")
            sentiment_counts[sentiment] += 1
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Articles", len(filtered_results))
        with col2:
            st.metric("😊 Positive", sentiment_counts["positive"])
        with col3:
            st.metric("😐 Neutral", sentiment_counts["neutral"])
        with col4:
            st.metric("😟 Negative", sentiment_counts["negative"])
        
        st.markdown("---")
    
    for idx, article in enumerate(filtered_results, 1):
        doc_id = article.get("id", f"unknown-{idx}")
        headline = article.get("headline", "Untitled")
        date = article.get("date", "Unknown date")
        source = article.get("source", "Unknown source")
        summary = article.get("summary", "")
        
        # Try to get full processed doc
        doc = get_processed_doc(doc_id)
        teaser = _teaser(doc.get("summary") or summary or "No summary available")
        url = doc.get("url") or article.get("url", "")
        entities = (doc.get("entities") if isinstance(doc, dict) else None) or article.get("entities", [])
        if not isinstance(entities, list):
            entities = []

        overall_sentiment = (
            (doc.get("overall_sentiment") if isinstance(doc, dict) else None)
            or article.get("overall_sentiment")
            or article.get("sentiment")
            or "neutral"
        )

        emotions_map = {}
        if isinstance(doc, dict):
            emotions_map = doc.get("emotions") or {}
        if not emotions_map and isinstance(article.get("emotions"), dict):
            emotions_map = article["emotions"]
        
        # Render card
        st.markdown('<div class="news-card">', unsafe_allow_html=True)
        
        # Headline
        st.markdown(
            f'<div class="card-headline">{headline}</div>',
            unsafe_allow_html=True
        )
        
        # Meta information with sentiment
        formatted_date = date
        if date and date != "Unknown date":
            try:
                dt = _to_dt(date)
                if dt:
                    formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
            except:
                pass
        
        st.markdown(
            f'<div class="card-meta">'
            f'<span>📅 {formatted_date}</span> • '
            f'<span><strong>📰 {source}</strong></span>'
            f'{_sentiment_chip(overall_sentiment)}'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Teaser/Summary
        st.markdown(
            f'<div class="card-teaser">"{teaser}"</div>',
            unsafe_allow_html=True
        )
        
        # Action buttons - enhanced design
        st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if url:
                st.link_button(
                    "🔗 Original Article", 
                    url, 
                    use_container_width=True,
                    help="Read the full article from the original source"
                )
            else:
                st.button(
                    "🔗 Original Article",
                    key=f"orig-disabled-{doc_id}",
                    disabled=True,
                    use_container_width=True,
                    help="Original article link not available"
                )
        
        with col2:
            explain_key = f"explain-{doc_id}"
            if st.button(
                "💡 Explain in Detail", 
                key=explain_key, 
                use_container_width=True,
                help="Get AI-powered detailed analysis and insights"
            ):
                with st.spinner("🤖 Generating detailed analysis..."):
                    analysis = bedrock_explain(doc.get("summary") or summary)
                    st.session_state[f"analysis-{doc_id}"] = analysis
                    st.rerun()
        
        with col3:
            chat_key = f"chat-toggle-{doc_id}"
            if st.button(
                "💬 Chat with Article", 
                key=chat_key, 
                use_container_width=True,
                help="Ask questions about this article"
            ):
                # Toggle chat visibility
                chat_state_key = f"show_chat_{doc_id}"
                st.session_state[chat_state_key] = not st.session_state.get(chat_state_key, False)
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tags/Entities section - enhanced design
        if entities:
            labels = []
            for e in entities[:8]:  # Show more tags
                label = e.get("text") if isinstance(e, dict) else e
                label = (label or "").strip()
                if label and len(label) > 2:  # Filter out very short tags
                    labels.append(label)

            if labels:
                st.markdown(
                    '<div class="tags-section">'
                    '<div class="tags-label">🏷️ Related Topics</div>',
                    unsafe_allow_html=True
                )
                
                # Create clickable tags
                tag_cols = st.columns(min(4, len(labels)))
                for idx, label in enumerate(labels):
                    with tag_cols[idx % len(tag_cols)]:
                        if st.button(
                            f"#{label}",
                            key=f"entity-{doc_id}-{idx}",
                            use_container_width=True,
                            on_click=_set_topic,
                            args=(label,),
                            help=f"Search for articles about {label}"
                        ):
                            pass
                
                st.markdown('</div>', unsafe_allow_html=True)

        # Emotion analysis section
        emotion_badges = []
        if isinstance(emotions_map, dict):
            for emotion in NRC_EMOTIONS:
                level = emotions_map.get(emotion, "none")
                if not isinstance(level, str):
                    continue
                level_norm = level.lower()
                if level_norm not in EMOTION_LEVELS or level_norm == "none":
                    continue
                emotion_badges.append(
                    f'<span class="emotion-badge emotion-level-{level_norm}">{emotion} • {level_norm}</span>'
                )
        
        if emotion_badges:
            st.markdown(
                '<div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--light-border);">'
                '<div class="tags-label">🎭 Emotional Tone Analysis</div>'
                + " ".join(emotion_badges)
                + "</div>",
                unsafe_allow_html=True
            )
        
        # Detailed analysis section
        analysis = st.session_state.get(f"analysis-{doc_id}")
        if analysis:
            st.markdown("---")
            st.markdown("### 📊 Detailed Analysis")
            st.markdown(analysis)
            st.markdown("---")
        
        # Chat section - only show if toggled
        chat_state_key = f"show_chat_{doc_id}"
        if st.session_state.get(chat_state_key, False):
            st.markdown("---")
            st.markdown("### 💬 Chat About This Article")
            
            chat_key = f"chat-{doc_id}"
            
            if chat_key not in st.session_state:
                st.session_state[chat_key] = []
            
            # Chat history
            if st.session_state[chat_key]:
                st.markdown("**Conversation History:**")
                for i, turn in enumerate(st.session_state[chat_key]):
                    with st.container():
                        st.markdown(f"**🙋 You:** {turn['user']}")
                        st.markdown(f"**🤖 AI:** {turn['assistant']}")
                        if i < len(st.session_state[chat_key]) - 1:
                            st.divider()
                st.markdown("---")
            
            # Chat input
            st.markdown("**Ask a question about this article:**")
            chat_cols = st.columns([4, 1])
            
            with chat_cols[0]:
                user_msg = st.text_input(
                    "",
                    key=f"chat_input_{doc_id}",
                    placeholder="e.g., What are the implications? Who is affected? What happens next?",
                    label_visibility="collapsed"
                )
            
            with chat_cols[1]:
                send_btn = st.button("💬 Send", key=f"send-{doc_id}", use_container_width=True, type="primary")
            
            if send_btn and user_msg.strip():
                with st.spinner("🤖 AI is analyzing and responding..."):
                    answer = bedrock_chat(
                        doc.get("summary") or summary,
                        user_msg,
                        st.session_state[chat_key]
                    )
                    st.session_state[chat_key].append({
                        "user": user_msg,
                        "assistant": answer
                    })
                    # Clear the input
                    st.session_state[f"chat_input_{doc_id}"] = ""
                    st.rerun()
            
            # Close chat button
            if st.button("❌ Close Chat", key=f"close_chat_{doc_id}"):
                st.session_state[chat_state_key] = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("")  # spacing

# Footer section
if results:
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #6b7280; font-style: italic;">
        <p>📰 <strong>NewsInsight</strong> • Powered by AI • Real-time Analysis</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">
            Sentiment analysis, emotion detection, and intelligent insights for informed decision-making
        </p>
    </div>
    """, unsafe_allow_html=True)
