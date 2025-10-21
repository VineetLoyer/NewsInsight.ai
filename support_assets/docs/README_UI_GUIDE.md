# NewsInsight.ai — AI-Powered News Analytics

**Verified News Insights & Deep Analysis** with Bedrock-powered explanations and chat.

## ✨ Features

- 📰 **Curated News Insights**: Scan 3 top-verified articles per topic
- 🔍 **Smart Search**: Keyword-based filtering across articles
- 💡 **AI Explanations**: Bedrock-powered deep analysis of articles
- 💬 **Interactive Chat**: Ask questions grounded in article context
- 🎨 **NYT-Inspired Design**: Classic serif typography and clean card layout
- 📊 **Sentiment Analysis**: Visual sentiment indicators for each article
- 🔗 **Source Attribution**: Direct links to original articles

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **AWS Account** with:
  - DynamoDB (table: `news_metadata`)
  - S3 (optional, for processed articles)
  - Bedrock (optional, for Explain & Chat features)
  - IAM credentials configured

### Installation

1. **Clone the repo**
   ```bash
   cd NewsInsight.ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**

   **Windows PowerShell:**
   ```powershell
   $env:AWS_REGION = "us-west-2"
   $env:DDB_TABLE = "news_metadata"
   $env:BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
   ```

   **Linux/Mac:**
   ```bash
   export AWS_REGION=us-west-2
   export DDB_TABLE=news_metadata
   export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**
   - Navigate to `http://localhost:8501`

## 📋 Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `us-west-2` | AWS region for DynamoDB & Bedrock |
| `DDB_TABLE` | `news_metadata` | DynamoDB table containing articles |
| `PROC_BUCKET` | *(optional)* | S3 bucket for processed articles |
| `BEDROCK_MODEL_ID` | *(optional)* | Bedrock model for Explain & Chat |
| `MODEL_FAMILY` | `anthropic` | Model type: `anthropic` or `amazon` |
| `DEBUG_MODE` | `false` | Enable debug logging (set to `true`) |

## 🔧 Components

### `app.py` — Main Streamlit App
- Search interface with suggested topics
- Article card display with sentiment
- Explain & Chat buttons
- NYT-inspired styling

### `fetch_articles_lambda.py` — Article Fetcher
- Fetches articles from NewsAPI & The Guardian
- Stores raw articles in S3
- Can be deployed as AWS Lambda

### `agent/newsinsights_agent.py` — Reasoning Agent
- Queries processed articles from DDB
- Uses Bedrock for reasoning & fact-checking
- External web search for verification
- Saves traces to DynamoDB

### `summarize_news/app.py` — Lambda Processor
- Processes raw articles
- Generates summaries & sentiment
- Stores processed docs in S3
- Writes metadata to DynamoDB

## 🐛 Troubleshooting

### Problem: "No articles found yet"

**Quick diagnostic:**
```bash
python scripts/diagnose.py
```

**Manual check:**
1. Ensure DynamoDB table exists and has articles
2. Run the fetcher Lambda or test script
3. Enable `DEBUG_MODE=true` to see detailed logs
4. See `TROUBLESHOOTING.md` for detailed guide

### Problem: Explain/Chat buttons not working

1. Set `BEDROCK_MODEL_ID` environment variable
2. Ensure IAM role has `bedrock:InvokeModel` permission
3. Verify Bedrock is available in your region

### Problem: Original article links not showing

1. Ensure `PROC_BUCKET` is set (optional)
2. Check S3 bucket exists and has processed documents
3. Articles without URLs will show a disabled link button

## 📊 Data Flow

```
NewsAPI / Guardian APIs
        ↓
fetch_articles_lambda.py (stores raw → S3 + DDB)
        ↓
summarize_news/app.py (processes → S3 + DDB metadata)
        ↓
agent/newsinsights_agent.py (reasoning → DDB trace)
        ↓
app.py (Streamlit UI - displays + chat)
```

## 🎨 UI Design

- **Typography**: EB Garamond (headlines), Lora (body) — inspired by NYT
- **Color Scheme**: Newspaper-neutral with sentiment indicators
- **Layout**: Wide cards with expandable sections
- **Interactions**: Copy-paste keywords, click suggested topics, expand explanations

## 🤖 Bedrock Models

Supports both Claude and Amazon models:

**Anthropic:**
```
anthropic.claude-3-sonnet-20240229-v1:0
anthropic.claude-3-opus-20240229-v1:0
```

**Amazon:**
```
amazon.nova-pro-v1:0
```

Set `MODEL_FAMILY` environment variable accordingly.

## 🚀 Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### AWS ECS / AppRunner
- Package as Docker image
- Set environment variables via secrets manager
- Mount IAM role with DDB/Bedrock permissions

### AWS Lambda (for fetcher/processor)
- See `fetch_articles_lambda.py` and `summarize_news/app.py`
- Deploy with appropriate IAM role and environment variables

## 📝 Example Usage

### Search for Technology News
1. Enter "AI regulation" in search box
2. View top 3 articles with sentiment chips
3. Click "Explain" for deep analysis
4. Use "Chat" to ask follow-up questions

### Use Suggested Topics
1. Click buttons in sidebar: Politics, Technology, Business, etc.
2. Results auto-update with articles matching that topic
3. All features (explain, chat, original link) available

### Chat with Claude
1. Click "Chat About This Article"
2. Ask questions like:
   - "What does this mean for my business?"
   - "How is this different from last month?"
   - "What are the risks here?"
3. Chat stays grounded in article context

## 📊 Performance Notes

- Caching: Search results cached for 60s, processed docs for 120s
- Limit: DDB scan limited to 500 items to prevent timeouts
- For larger datasets (>10K): Consider adding DDB GSI or switching to ElasticSearch

## 🔐 Security

- AWS credentials: Use IAM roles (don't hardcode keys)
- Bedrock: Model invocations use AWS authentication
- S3: All buckets accessed via IAM permissions
- DDB: Fine-grained table access via IAM policies

## 📖 Documentation

- **Main app**: See `app.py` for UI flow
- **Fetcher**: See `fetch_articles_lambda.py` for API integrations
- **Agent**: See `agent/newsinsights_agent.py` for reasoning pipeline
- **Troubleshooting**: See `TROUBLESHOOTING.md` for common issues

## 🤝 Contributing

1. Test locally with `DEBUG_MODE=true`
2. Run diagnostics: `python scripts/diagnose.py`
3. Check for errors: See CloudWatch logs
4. Submit issues/PRs with context from debug logs

## 📜 License

(Add your license here)

## 💬 Support

- Enable `DEBUG_MODE=true` for detailed logs
- Run `python scripts/diagnose.py` for system diagnostics
- Check `TROUBLESHOOTING.md` for common issues
- Review AWS CloudWatch logs for service errors
