# NewsInsight React UI - Complete Setup Guide

## 🎯 Current Status

✅ **Backend Server**: Running on http://localhost:8000  
✅ **Frontend Server**: Running on http://localhost:3002  
✅ **AWS Connection**: Connected to DynamoDB table `news_metadata`  
⚠️ **Database**: Empty (no articles yet)  
❌ **News APIs**: Not configured  
❌ **Bedrock**: Not configured  

## 🔧 Next Steps to Get Real Data

### Step 1: Configure News API Keys (Required for fetching articles)

#### Option A: NewsAPI (Recommended)
1. Go to https://newsapi.org/register
2. Sign up for a free account (60 requests/day)
3. Get your API key
4. Add it to `.env` file:
   ```
   NEWSAPI_KEY=your_newsapi_key_here
   ```

#### Option B: Guardian API (Alternative/Additional)
1. Go to https://open-platform.theguardian.com/access/
2. Register for a free developer key
3. Get your API key
4. Add it to `.env` file:
   ```
   GUARDIAN_KEY=your_guardian_key_here
   ```

### Step 2: Configure AWS Bedrock (Optional - for AI analysis)

1. Ensure you have AWS CLI configured:
   ```bash
   aws configure
   ```

2. Enable Bedrock model access in AWS Console:
   - Go to AWS Bedrock console
   - Request access to Claude models
   - Note your model ID

3. Add to `.env` file:
   ```
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   ```

### Step 3: Restart Backend Server

After configuring API keys:
```bash
# Stop the current backend (Ctrl+C)
# Then restart:
venv\Scripts\activate
python backend.py
```

### Step 4: Bootstrap Your Database

1. Open http://localhost:3002 in your browser
2. You'll see an empty state with a "Fetch Sample Articles" button
3. Click the button to populate your database with sample articles
4. Or search for specific topics (e.g., "technology", "AI", "politics")

## 🎯 What Each Configuration Enables

| Configuration | What It Does |
|---------------|--------------|
| **NewsAPI Key** | Fetches real news articles from 70,000+ sources |
| **Guardian Key** | Fetches articles from The Guardian newspaper |
| **Bedrock Model** | Enables AI-powered article analysis and chat |
| **S3 Buckets** | Stores processed article data (optional) |

## 🚀 Testing Your Setup

### Test 1: Check System Status
```bash
curl http://localhost:8000/api/status
```

### Test 2: Search for Articles (will auto-fetch if APIs configured)
```bash
curl "http://localhost:8000/api/articles/search?query=technology&limit=3"
```

### Test 3: Bootstrap Database
```bash
curl -X POST http://localhost:8000/api/articles/bootstrap
```

## 🎨 Frontend Features (Already Working)

✅ **Modern React UI** with newspaper-style design  
✅ **Responsive layout** for mobile and desktop  
✅ **Search functionality** with trending topics  
✅ **Article cards** with sentiment analysis  
✅ **Clickable tags** for topic exploration  
✅ **Statistics dashboard**  
✅ **Loading states** and error handling  

## 🔍 Troubleshooting

### Backend Issues
- **Port 8000 in use**: Change PORT in .env file
- **AWS errors**: Check `aws configure` and credentials
- **Import errors**: Ensure virtual environment is activated

### Frontend Issues
- **Port 3002 in use**: The app will auto-select another port
- **API connection failed**: Check if backend is running on port 8000
- **Mock data showing**: Configure news API keys and restart backend

### Database Issues
- **Empty results**: Click "Fetch Sample Articles" or configure API keys
- **DynamoDB errors**: Check AWS credentials and table permissions

## 📊 Expected Behavior

### With API Keys Configured:
1. **Search "technology"** → Fetches real articles from NewsAPI/Guardian
2. **Click "Explain"** → Uses Bedrock for AI analysis (if configured)
3. **Click "Chat"** → Interactive Q&A about articles (if Bedrock configured)
4. **Click tags** → Searches for related articles

### Without API Keys:
1. **Empty database** → Shows bootstrap button
2. **Search queries** → Returns empty results
3. **Mock data fallback** → Only in case of network errors

## 🎉 Success Indicators

You'll know everything is working when:

✅ **Homepage loads** with articles (not empty state)  
✅ **Search works** and returns real articles  
✅ **Sentiment analysis** shows on article cards  
✅ **Tags are clickable** and trigger new searches  
✅ **Statistics show** article counts and sentiment distribution  
✅ **AI features work** (if Bedrock configured)  

## 🔄 Quick Start Commands

```bash
# 1. Start backend (in one terminal)
venv\Scripts\activate
python backend.py

# 2. Start frontend (in another terminal)
npm start

# 3. Open browser
# http://localhost:3002

# 4. Configure API keys in .env file
# 5. Restart backend
# 6. Click "Fetch Sample Articles" or search for topics
```

## 📞 Need Help?

The React UI is fully functional and much better than the Streamlit version:
- ✅ **Clean, readable design** with proper typography
- ✅ **Intuitive navigation** and search
- ✅ **Mobile responsive** layout
- ✅ **Professional appearance** like a real news website
- ✅ **Fast performance** with smooth animations

The only thing needed now is to configure the news API keys to get real data instead of the empty database!