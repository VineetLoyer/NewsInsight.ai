# NewsInsight.ai — Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Prerequisites Check

```bash
# Check Python version (need 3.8+)
python --version

# Check AWS CLI
aws --version

# Verify AWS credentials
aws sts get-caller-identity
```

### Step 2: Install & Setup

```bash
# 1. Clone or cd into the repo
cd NewsInsight.ai

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate it
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

**For Windows PowerShell:**
```powershell
$env:AWS_REGION = "us-west-2"
$env:DDB_TABLE = "news_metadata"
$env:DEBUG_MODE = "true"
```

**For Mac/Linux:**
```bash
export AWS_REGION="us-west-2"
export DDB_TABLE="news_metadata"
export DEBUG_MODE="true"
```

### Step 4: Load Sample Data (No APIs needed!)

```bash
python scripts/insert_sample_data.py insert
```

This inserts 6 realistic sample articles. You should see:
```
✓ Inserted: OpenAI Announces GPT-5...
✓ Inserted: Federal Reserve Signals Pause...
✓ Inserted: European Parliament Approves AI...
✓ Inserted: Apple Announces iPhone 16...
✓ Inserted: Tesla Delivers Record...
✓ Inserted: Climate Summit Reaches...

✅ Successfully inserted 6/6 articles
```

### Step 5: Run the App

```bash
streamlit run app.py
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Step 6: Open in Browser

- Navigate to **http://localhost:8501**
- You should see the NYT-inspired layout with 3 sample articles
- Try clicking on a suggested topic or searching for a keyword

---

## ✨ Features to Try

### 1. **Search by Keyword**
- Type "technology" in the search box
- See articles filtered by keyword

### 2. **Click Suggested Topics**
- Use the sidebar buttons: Technology, Business, Politics, etc.
- Results update instantly

### 3. **View Article Details**
- Headline with sentiment chip (green/gray/red)
- Publication date and source
- Teaser text
- Entity tags (AI, Markets, etc.)

### 4. **Open Original Article**
- Click "🔗 Original" to open the source
- (Sample data has placeholder URLs)

### 5. **Get AI Explanation**
- Click "💡 Explain" button
- Claude analyzes the article in ~2 seconds
- Shows:
  - What happened
  - Why it matters
  - What to watch next

### 6. **Chat with Claude**
- Expand "💬 Chat About This Article"
- Ask questions about the article
- Examples:
  - "What does this mean for my business?"
  - "How does this compare to..."
  - "What are the risks?"
- Chat stays grounded in article context

---

## 🔧 Add Your Own Data

### Option A: Insert from CSV/JSON

Edit `scripts/insert_sample_data.py` with your articles:

```python
SAMPLE_ARTICLES = [
    {
        "id": "custom-001",
        "headline": "Your Article Title",
        "source": "your-source",
        "date": "2025-10-20T12:00:00Z",
        "summary": "Article summary...",
        "sentiment": "positive",
        "verification_score": 0.85,
        "entities": ["Tag1", "Tag2"]
    },
    # Add more articles...
]
```

Then:
```bash
python scripts/insert_sample_data.py insert
```

### Option B: Connect to Your API

Edit `fetch_articles_lambda.py` to add your news sources:

```python
def fetch_your_api(api_key: str, q: str):
    # Your custom fetcher
    return articles

# In handler():
articles += fetch_your_api(your_key)
```

### Option C: Import Existing Data

```python
import boto3

ddb = boto3.resource("dynamodb")
table = ddb.Table("news_metadata")

# Your existing articles
for article in your_articles:
    table.put_item(Item=article)
```

---

## 🎨 Customize the UI

### Change Colors

Edit the CSS in `app.py` (around line 45):

```python
:root {
  --accent-color: #1a1a1a;           # Main text color
  --positive-bg: #f1fdf3;             # Green sentiment background
  --positive-text: #0d5c0d;           # Green sentiment text
  --negative-bg: #fef3f3;             # Red sentiment background
  --negative-text: #a41e1e;           # Red sentiment text
}
```

### Change Fonts

Update the Google Fonts import (line 38):

```python
@import url('https://fonts.googleapis.com/css2?family=YOUR_FONT:wght@400;700&display=swap');
```

### Change Suggested Topics

Edit line ~300:

```python
suggested_topics = ["Your", "Topics", "Here"]
```

---

## 🐛 Debugging

### Enable Debug Mode

```powershell
$env:DEBUG_MODE = "true"
streamlit run app.py
```

You'll see:
- Number of articles scanned from DDB
- Number of articles matching your search
- Any S3/Bedrock errors

### Run Diagnostics

```bash
python scripts/diagnose.py
```

Shows:
- ✓/✗ Environment variables
- ✓/✗ AWS credentials
- ✓/✗ DDB connection
- ✓/✗ Sample articles
- ✓/✗ Bedrock model

### Check Article Count

```bash
python scripts/insert_sample_data.py list
```

Shows all articles currently in DDB.

### Clear & Restart

```bash
python scripts/insert_sample_data.py clear
python scripts/insert_sample_data.py insert
streamlit run app.py
```

---

## ⚡ Performance Tips

### For Local Development
- Use `DEBUG_MODE=true` to see what's happening
- Cache results are set to 60s (search) / 120s (docs)
- Refresh browser to see new data

### For Production
- Set `DEBUG_MODE=false`
- Increase cache TTL for less frequent queries
- Use Streamlit Cloud or Docker
- Add DynamoDB GSI for faster searches

---

## 🚀 Next Steps

1. **Add Real Data**: Set up fetcher Lambda with NewsAPI/Guardian keys
2. **Configure Bedrock**: Get a Bedrock model and set `BEDROCK_MODEL_ID`
3. **Custom Styling**: Update colors, fonts, and layout
4. **Deploy**: Use Docker or AWS ECS/AppRunner
5. **Monitor**: Set up CloudWatch dashboards

---

## 📚 File Guide

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI (start here) |
| `fetch_articles_lambda.py` | News API fetcher |
| `agent/newsinsights_agent.py` | AI reasoning engine |
| `summarize_news/app.py` | Article processor Lambda |
| `scripts/diagnose.py` | System diagnostics |
| `scripts/insert_sample_data.py` | Load test data |

---

## 🆘 Common Issues

### "No articles found yet"
```bash
python scripts/insert_sample_data.py insert
```

### Explain/Chat not working
Set `BEDROCK_MODEL_ID` environment variable

### Search not filtering
Enable `DEBUG_MODE=true` to see what's happening

### Streamlit not starting
```bash
pip install --upgrade streamlit
streamlit run app.py --logger.level=debug
```

---

## 💡 Tips & Tricks

### Use PowerShell Profile (Windows)

Add to your PowerShell profile (`$PROFILE`):
```powershell
function newsinsight {
    cd C:\Users\vinee\NewsInsight.ai
    $env:AWS_REGION = "us-west-2"
    $env:DDB_TABLE = "news_metadata"
    $env:DEBUG_MODE = "true"
    streamlit run app.py
}
```

Then just run: `newsinsight`

### Quick Restart

```bash
# Stop current app: Ctrl+C
# Reload: Press 'r' in terminal or Ctrl+Shift+R in browser
```

### Share with Team

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
# Access from: http://<your-ip>:8501
```

---

## 🎉 You're All Set!

You now have a fully functional AI-powered news analytics platform. Next:

1. Try all the features
2. Add your own articles
3. Customize the styling
4. Share with your team
5. Deploy to production

**Questions?** Check:
- `README_UI_GUIDE.md` — Detailed features
- `TROUBLESHOOTING.md` — Common issues
- `SETUP_CHECKLIST.md` — Full setup guide

**Happy analyzing!** 📰✨
