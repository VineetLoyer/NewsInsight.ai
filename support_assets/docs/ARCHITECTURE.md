# NewsInsight.ai — Technical Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    NEWSINSIGHT.AI PLATFORM                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              STREAMLIT UI (app.py)                       │  │
│  │  - NYT-inspired typography (EB Garamond, Lora)          │  │
│  │  - Search + suggested topics                            │  │
│  │  - Article cards with sentiment                         │  │
│  │  - Explain (Claude analysis)                            │  │
│  │  - Chat (article-grounded Q&A)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                  ↓                 ↓                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  DynamoDB       │  │  S3 (Docs)   │  │  Bedrock     │       │
│  │  (Metadata)     │  │ (Processed)  │  │ (LLM Model)  │       │
│  │                 │  │              │  │              │       │
│  │ - headline      │  │ - summaries  │  │ Claude 3.5   │       │
│  │ - summary       │  │ - entities   │  │ (or Amazon)  │       │
│  │ - date          │  │ - url        │  │              │       │
│  │ - source        │  │ - sentiment  │  │              │       │
│  │ - sentiment     │  │              │  │              │       │
│  │ - entities      │  │              │  │              │       │
│  └─────────────────┘  └──────────────┘  └──────────────┘       │
│           ↑                                                      │
│  ┌────────────────────────────────────────────────────┐        │
│  │   ARTICLE PROCESSING PIPELINE                      │        │
│  │   (Lambda-based, external to UI)                   │        │
│  │                                                    │        │
│  │  fetch_articles_lambda.py                         │        │
│  │  ├─ NewsAPI (topheadlines, everything)            │        │
│  │  ├─ The Guardian API (search)                     │        │
│  │  └─ → S3:news-raw/ + DDB raw items               │        │
│  │                                                    │        │
│  │  ↓                                                │        │
│  │                                                    │        │
│  │  summarize_news/app.py (Lambda)                   │        │
│  │  ├─ Fetch raw from S3                            │        │
│  │  ├─ Summarize + sentiment analysis               │        │
│  │  ├─ Extract entities                             │        │
│  │  └─ → S3:news-processed/ + DDB metadata          │        │
│  │                                                    │        │
│  │  ↓                                                │        │
│  │                                                    │        │
│  │  agent/newsinsights_agent.py (optional)          │        │
│  │  ├─ Query DDB for topic matches                  │        │
│  │  ├─ Bedrock: primary reasoning                   │        │
│  │  ├─ Web search: external evidence                │        │
│  │  ├─ Bedrock: cross-verification                 │        │
│  │  └─ → DDB:agent_trace                           │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
│  ┌────────────────────────────────────────────────────┐        │
│  │   HELPER SCRIPTS                                   │        │
│  │                                                    │        │
│  │  scripts/diagnose.py         - System diagnostics │        │
│  │  scripts/insert_sample_data.py - Load test data   │        │
│  │                                                    │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Streamlit UI (`app.py`)

**Responsibilities:**
- Display articles in cards with NYT-inspired design
- Handle search and topic filtering
- Render sentiment chips
- Manage Explain and Chat interactions
- Session state management

**Key Functions:**
- `search_articles_ddb()` — Scan DDB + keyword filter
- `get_processed_doc()` — Fetch full doc from S3
- `bedrock_explain()` — Generate detailed analysis
- `bedrock_chat()` — Interactive Q&A grounded in article

**Dependencies:**
- `boto3` — AWS SDK
- `streamlit` — UI framework
- `python-dateutil` — Date parsing

**Performance:**
- Search results: 60s cache
- Processed docs: 120s cache
- DDB scan limit: 500 items

### 2. DynamoDB Schema

**Table: `news_metadata`**

| Attribute | Type | Key | Required | Example |
|---|---|---|---|---|
| `id` | String | HASH | ✓ | `article-001` |
| `headline` | String | — | ✓ | `"OpenAI Announces GPT-5"` |
| `summary` | String | — | ✓ | `"OpenAI has announced..."` |
| `date` | String | — | ✓ | `"2025-10-20T12:00:00Z"` |
| `source` | String | — | ✓ | `"techcrunch"` |
| `sentiment` | String | — | — | `"positive"` |
| `verification_score` | Number | — | — | `0.95` |
| `entities` | List | — | — | `["OpenAI", "AI"]` |
| `url` | String | — | — | `"https://..."` |

**Indexes:**
- Primary: `id`
- (Optional) GSI on `date` for sorting
- (Optional) GSI on `entities` for faceted search

### 3. Article Flow

```
NewsAPI / Guardian API
    ↓ (raw articles JSON)
S3: news-raw/{timestamp}/{doc_id}.json
    ↓ (async processor)
Lambda: summarize_news/app.py
    ├─ Extract text → Bedrock summarization
    ├─ Sentiment analysis
    ├─ Entity extraction
    └─ Structured output
    ↓
S3: news-processed/{doc_id}.json
    ↓
DynamoDB: news_metadata
    ├─ headline
    ├─ summary
    ├─ sentiment
    ├─ date
    └─ entities
    ↓
Streamlit app.py (reads metadata)
    ├─ Search/filter articles
    ├─ Display in UI
    └─ Link to S3 processed docs for full details
```

### 4. Bedrock Integration

**Models Supported:**

```
Anthropic (preferred):
  - claude-3-opus-20240229-v1:0    (larger, slower)
  - claude-3-sonnet-20240229-v1:0  (balanced)
  - claude-3-haiku-20240307-v1:0   (fast, small)

Amazon:
  - amazon.nova-pro-v1:0
```

**Usage:**

```python
# Explain feature
bedrock.invoke_model(
    modelId=BEDROCK_MODEL_ID,
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 700,
        "messages": [{
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }]
    })
)

# Chat feature (same, but with conversation history)
```

**Prompts:**

- **Explain**: Generate 3-part analysis (What happened, Why it matters, What to watch)
- **Chat**: Answer questions grounded only in article context

### 5. Styling Architecture

**Fonts:**
- Headlines: EB Garamond (serif, 400/500/700/800 weights)
- Body: Lora (serif, 400/500/600/700 weights)
- Fallback: Georgia, Times New Roman

**Color System:**
```
Accent:        #1a1a1a (dark gray)
Text:          #2c3e50 (medium gray)
Border:        #d9d9d9 (light gray)

Sentiment:
  Positive:    #f1fdf3 bg / #0d5c0d text (green)
  Neutral:     #f9f9f9 bg / #5a5a5a text (gray)
  Negative:    #fef3f3 bg / #a41e1e text (red)
```

**Card Layout:**
```
┌─ Card ──────────────────────────────┐
│ Headline + [Sentiment Chip]         │
│ ────────────────────────────────────│
│ Date · Source                       │
│ ────────────────────────────────────│
│ Teaser text...                      │
│ ────────────────────────────────────│
│ [Open] [Explain] [Tags...]          │
│                                     │
│ ▼ Detailed Analysis                 │
│ ▼ Chat About This Article           │
└─────────────────────────────────────┘
```

## Deployment Architectures

### Development (Local)

```
[Laptop]
├─ Python venv
├─ Streamlit dev server
├─ Local AWS credentials
├─ (optional) Local DDB emulator
└─ Connects to AWS via boto3
```

### Small Scale (AWS)

```
[Streamlit Cloud / AppRunner]
├─ Docker image with app.py
├─ IAM role with DDB/Bedrock permissions
├─ Environment variables from secrets
└─ Direct to AWS services
```

### Medium Scale (Containerized)

```
[ECS / Kubernetes]
├─ Docker container (Streamlit + dependencies)
├─ CloudFront CDN (optional)
├─ ALB / NLB for load balancing
├─ Auto-scaling group
├─ Secrets manager for API keys
└─ CloudWatch for monitoring
```

### Large Scale (Microservices)

```
[Frontend]
├─ React SPA (static)
├─ CloudFront CDN
└─ API Gateway

[Backend API]
├─ Lambda / FastAPI
├─ API Gateway
└─ Services (DDB, Bedrock, etc)

[Processing Pipeline]
├─ EventBridge rules
├─ SQS queue
├─ Lambda processors
└─ S3 + DDB storage

[Data Warehouse]
├─ S3 Data Lake
├─ Glue ETL
└─ Athena / QuickSight
```

## Environment Variables Reference

| Variable | Default | Type | Used By |
|---|---|---|---|
| `AWS_REGION` | `us-west-2` | String | boto3 clients |
| `DDB_TABLE` | `news_metadata` | String | app.py search |
| `PROC_BUCKET` | *(empty)* | String | app.py doc fetch |
| `BEDROCK_MODEL_ID` | *(empty)* | String | explain/chat |
| `MODEL_FAMILY` | `anthropic` | String | bedrock invoke |
| `DEBUG_MODE` | `false` | Boolean | all logging |
| `RAW_BUCKET` | *(env only)* | String | fetcher Lambda |
| `NEWSAPI_PARAM` | *(env only)* | String | fetcher Lambda |
| `GUARDIAN_PARAM` | *(env only)* | String | fetcher Lambda |

## API Integration Points

### News APIs

**NewsAPI.org:**
- Endpoint: `https://newsapi.org/v2/everything`
- Auth: API key query param
- Rate: 500 req/day (free), 1000 (paid)

**The Guardian:**
- Endpoint: `https://content.guardianapis.com/search`
- Auth: API key query param
- Rate: 100 req/second

### AWS Services Used

| Service | Operations | Cost |
|---|---|---|
| DynamoDB | Scan, GetItem, PutItem, Query | Pay-per-request or provisioned |
| S3 | GetObject, PutObject, ListObjects | $0.023/GB stored, $0.0004/1K requests |
| Bedrock | InvokeModel | $0.003 (input), $0.015 (output) per 1K tokens |
| Lambda | (if deployed) | $0.20 per 1M invocations |

## Security Considerations

### Authentication
- AWS IAM roles (preferred over keys)
- API keys stored in AWS Secrets Manager
- No credentials in code

### Data
- S3 bucket encryption (default AES-256)
- DDB encryption (default enabled)
- SSL/TLS for all API calls

### Access Control
- Minimal IAM permissions (DDB scan, S3 get, Bedrock invoke)
- No public bucket access
- VPC endpoints (optional, for production)

## Monitoring & Logging

### CloudWatch
- Lambda execution logs
- DynamoDB metrics (scan count, throttling)
- Bedrock API calls (via CloudTrail)

### Streamlit
- Server logs in `.streamlit/logs/`
- User interactions visible in browser console
- Session state in `st.write(st.session_state)`

### Application
- `DEBUG_MODE=true` for verbose logging
- `scripts/diagnose.py` for health check
- Article count: `python scripts/insert_sample_data.py list`

## Performance Optimization

### Query Performance
| Scenario | Current | Optimized |
|---|---|---|
| Search 500 items | ~500ms DDB scan | ~50ms with GSI |
| Fetch doc from S3 | ~100ms | ~20ms with CloudFront |
| Bedrock invoke | ~2-3s | ~2s (model dependent) |

**Improvements:**
1. Add DynamoDB GSI on `date` and `entities`
2. Cache frequently accessed docs in S3 CloudFront
3. Use Bedrock batch processing (if available)
4. Implement ElasticSearch for full-text search

### Caching Strategy
```python
@st.cache_data(ttl=60)        # Search results
def search_articles_ddb():...

@st.cache_data(ttl=120)       # Processed docs
def get_processed_doc():...
```

Invalidation: Automatic after TTL or manual `st.cache_data.clear()`

## Scaling Considerations

### User Load
- 1-10 concurrent: Single Streamlit instance
- 10-100 concurrent: Streamlit Cloud (auto-scaling)
- 100+ concurrent: Custom backend API + static frontend

### Data Volume
- <1K articles: Current DDB scan approach
- 1K-100K: Add GSI indexes
- 100K+: Migrate to ElasticSearch / Opensearch

### Cost Optimization
- Batch write articles during off-peak
- Use S3 lifecycle policies for old docs
- Bedrock: Use cheaper models (haiku) for high volume

## Testing Strategy

```bash
# Unit tests (add pytest)
pytest tests/

# Integration tests (with DDB/Bedrock)
pytest tests/integration/

# Load tests (simulate users)
locust -f locustfile.py

# Diagnostics
python scripts/diagnose.py
```

## Future Enhancements

1. **Real-time Updates**: WebSockets + Streamlit updates
2. **User Personalization**: User preferences in DDB
3. **Multi-language**: i18n support
4. **Mobile**: React Native companion app
5. **Advanced Search**: Full-text search with ElasticSearch
6. **Trending Analysis**: Time-series data + visualization
7. **Fact-checking**: Integration with external fact-check APIs
8. **Export**: PDF/CSV export of articles
