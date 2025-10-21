# 📚 NewsInsight.ai — Documentation Index

Welcome! Here's a guide to navigate all the documentation and get started quickly.

## 🚀 Start Here (Choose Your Path)

### **Path 1: Quick Start (5 minutes)**
👉 Read: [`QUICKSTART.md`](QUICKSTART.md)

- Setup in 5 minutes
- Load sample data
- Try all features
- No APIs needed

**Perfect for:** Local development, testing, demos

---

### **Path 2: Full Setup (30 minutes)**
👉 Read: [`SETUP_CHECKLIST.md`](SETUP_CHECKLIST.md)

- Complete installation steps
- AWS infrastructure setup
- Environment configuration
- Verification steps

**Perfect for:** First-time setup, production deployment

---

### **Path 3: Troubleshooting (As needed)**
👉 Read: [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)

- Common issues & solutions
- Diagnostic tools
- AWS service checks
- Performance tips

**Perfect for:** When something doesn't work

---

## 📖 Reference Guides

### **Features & Usage**
📄 [`README_UI_GUIDE.md`](README_UI_GUIDE.md)

- Feature overview
- Configuration reference
- Deployment options
- UI customization

### **Technical Architecture**
📄 [`ARCHITECTURE.md`](ARCHITECTURE.md)

- System diagrams
- Component details
- Data flow
- Performance tuning
- Scaling strategies

### **What We Built**
📄 [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md)

- What problems we solved
- Before/after comparison
- Key improvements
- Testing checklist

---

## 🛠️ Helper Scripts

| Script | Purpose | Usage |
|---|---|---|
| `start.sh` / `start.bat` | Launch app | `./start.sh` or `start.bat` |
| `scripts/diagnose.py` | Health check | `python scripts/diagnose.py` |
| `scripts/insert_sample_data.py` | Load test data | `python scripts/insert_sample_data.py insert` |

---

## 📋 Quick Reference

### Environment Variables
```bash
AWS_REGION           # AWS region (default: us-west-2)
DDB_TABLE           # DynamoDB table (default: news_metadata)
PROC_BUCKET         # S3 bucket for processed docs (optional)
BEDROCK_MODEL_ID    # Claude model ID (optional)
MODEL_FAMILY        # anthropic or amazon (default: anthropic)
DEBUG_MODE          # true/false for debug logs (default: false)
```

### Common Commands

```bash
# Install
pip install -r requirements.txt

# Load sample data
python scripts/insert_sample_data.py insert

# Check system health
python scripts/diagnose.py

# Run app
streamlit run app.py

# View articles in DDB
python scripts/insert_sample_data.py list

# Clear database (⚠️ caution!)
python scripts/insert_sample_data.py clear
```

---

## 🎯 Feature Overview

### Search & Explore
- 🔍 Keyword search in articles
- 📌 Suggested topic buttons
- 🗞️ Top 3 results per query

### Article Display
- 📰 NYT-inspired serif typography
- 💚 Sentiment indicators (green/gray/red)
- 🏷️ Auto-extracted entity tags
- 📅 Publication date & source

### AI Features
- 💡 Explain: Deep analysis via Claude
- 💬 Chat: Ask questions about article
- 🔗 Open Original: Link to source

### Developer Experience
- 🔧 DEBUG_MODE for visibility
- 📊 Diagnostic tools included
- 📚 5 comprehensive guides
- 🧪 Sample data for testing

---

## 💡 Common Tasks

### "I want to get started immediately"
```bash
python scripts/insert_sample_data.py insert
streamlit run app.py
```
→ Then open http://localhost:8501

### "I'm getting 'No articles found yet'"
```bash
python scripts/diagnose.py
```
→ Follow the suggestions shown

### "I want to understand the architecture"
→ Read [`ARCHITECTURE.md`](ARCHITECTURE.md)

### "I want to add my own data"
→ See "Add Your Own Data" in [`QUICKSTART.md`](QUICKSTART.md)

### "I want to deploy to production"
→ See "Deployment Options" in [`README_UI_GUIDE.md`](README_UI_GUIDE.md)

### "I want to customize the styling"
→ See "Customize the UI" in [`QUICKSTART.md`](QUICKSTART.md)

---

## 📊 Documentation Map

```
🚀 Getting Started
├── QUICKSTART.md           ← 5-minute setup
├── SETUP_CHECKLIST.md      ← Complete checklist
└── TROUBLESHOOTING.md      ← Common issues

📖 Reference
├── README_UI_GUIDE.md      ← Features & config
├── ARCHITECTURE.md         ← Technical details
└── IMPLEMENTATION_SUMMARY.md ← What we built

🛠️ Tools
├── start.sh / start.bat    ← Launch script
├── scripts/diagnose.py     ← Health check
└── scripts/insert_sample_data.py ← Load data

📁 Code
├── app.py                  ← Main UI
├── fetch_articles_lambda.py ← Article fetcher
├── agent/                  ← Reasoning agent
└── lambdas/                ← Processors
```

---

## 🎓 Learning Paths

### **For First-Time Users**
1. [`QUICKSTART.md`](QUICKSTART.md) — Get running in 5 min
2. Try all UI features
3. [`README_UI_GUIDE.md`](README_UI_GUIDE.md) — Understand features
4. [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — Know how to debug

### **For Developers**
1. [`ARCHITECTURE.md`](ARCHITECTURE.md) — Understand system design
2. [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) — See what changed
3. `app.py` — Review code
4. [`SETUP_CHECKLIST.md`](SETUP_CHECKLIST.md) — Full deployment

### **For DevOps/SRE**
1. [`ARCHITECTURE.md`](ARCHITECTURE.md) — Deployment architectures
2. [`README_UI_GUIDE.md`](README_UI_GUIDE.md) — Deployment options
3. [`SETUP_CHECKLIST.md`](SETUP_CHECKLIST.md) — Infrastructure setup
4. `start.sh` / `start.bat` — Automation scripts

### **For Data Scientists**
1. [`ARCHITECTURE.md`](ARCHITECTURE.md) — Data flow section
2. `fetch_articles_lambda.py` — Data ingestion
3. `agent/newsinsights_agent.py` — AI reasoning
4. `lambdas/summarize_news/app.py` — Processing pipeline

---

## ✅ Implementation Status

| Feature | Status | Doc | Code |
|---|---|---|---|
| Streamlit UI | ✅ Complete | README_UI_GUIDE.md | app.py |
| Search & Filter | ✅ Complete | QUICKSTART.md | app.py |
| Sample Data | ✅ Complete | QUICKSTART.md | scripts/insert_sample_data.py |
| Explain (AI) | ✅ Complete | README_UI_GUIDE.md | app.py |
| Chat (AI) | ✅ Complete | README_UI_GUIDE.md | app.py |
| Debug Mode | ✅ Complete | TROUBLESHOOTING.md | app.py |
| Diagnostics | ✅ Complete | QUICKSTART.md | scripts/diagnose.py |
| Documentation | ✅ Complete | (all .md files) | — |

---

## 🆘 Getting Help

### **Step 1: Check the right guide**
- "No articles found" → [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
- "How do I customize?" → [`QUICKSTART.md`](QUICKSTART.md)
- "How does it work?" → [`ARCHITECTURE.md`](ARCHITECTURE.md)

### **Step 2: Run diagnostics**
```bash
python scripts/diagnose.py
```

### **Step 3: Enable debug mode**
```bash
export DEBUG_MODE=true
streamlit run app.py
```

### **Step 4: Check logs**
- Streamlit: Browser console (F12)
- Python: Terminal output
- AWS: CloudWatch logs

---

## 🚀 Next Steps

1. **Pick a path above** (Quick Start / Full Setup / Troubleshooting)
2. **Follow the guide** — Each has step-by-step instructions
3. **Try the features** — Experiment with search, explain, chat
4. **Customize** — Update colors, fonts, topics
5. **Deploy** — Follow deployment section in README_UI_GUIDE.md

---

## 📞 Quick Links

| Resource | Link |
|---|---|
| **Quick Start** | [`QUICKSTART.md`](QUICKSTART.md) |
| **Full Setup** | [`SETUP_CHECKLIST.md`](SETUP_CHECKLIST.md) |
| **Troubleshooting** | [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) |
| **Features** | [`README_UI_GUIDE.md`](README_UI_GUIDE.md) |
| **Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| **What We Built** | [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) |

---

**Ready to start?** 👉 **Open [`QUICKSTART.md`](QUICKSTART.md) now!**

```bash
# Or run the app immediately:
python scripts/insert_sample_data.py insert
streamlit run app.py
```

Enjoy exploring NewsInsight.ai! 🎉📰
