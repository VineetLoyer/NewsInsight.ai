# 📁 NewsInsight.ai - Project Structure

## 🏗️ **Core Application Files**

### **Frontend (React)**
```
src/
├── components/
│   ├── Header.js              # Main header with dark mode toggle
│   ├── SearchSection.js       # Search interface with filters
│   ├── ArticleCard.js         # Individual article display
│   ├── StatsSection.js        # Analytics dashboard
│   └── EmptyState.js          # No results state
├── contexts/
│   └── ThemeContext.js        # Dark mode state management
├── pages/
│   └── HomePage.js            # Main application page
├── services/
│   └── api.js                 # Backend API integration
├── index.css                  # Global styles and themes
└── App.js                     # Root application component
```

### **Backend (Python)**
```
├── backend.py                 # Main FastAPI application
├── main.py                    # Simplified backend (Railway entry point)
├── content_filter.py          # Multi-layer content filtering system
├── requirements.txt           # Python dependencies
└── Procfile                   # Railway deployment configuration
```

### **Configuration**
```
├── .env                       # Environment variables (local)
├── package.json               # Node.js dependencies and scripts
├── tailwind.config.js         # Tailwind CSS configuration
└── railway.json               # Railway deployment settings
```

### **Setup & Testing**
```
├── setup_aws_infrastructure.py  # AWS resource creation script
├── test_content_filtering.py    # Content filtering test suite
├── start-newsinsight.bat       # Windows startup script
└── start-newsinsight.sh        # Unix startup script
```

## 🗑️ **Removed Development Files**

The following files were cleaned up during production preparation:

- `IMPLEMENTATION_GUIDE.md` - Development implementation guide
- `SETUP_GUIDE.md` - Old setup instructions
- `REACT_UI_SUMMARY.md` - React UI development summary
- `README-REACT.md` - Old React-specific README
- `UI_ENHANCEMENT_GUIDE.md` - UI development guide
- `setup-backend.py` - Old backend setup script
- `setup-react.sh` - Old React setup script
- `test_ui.py` - Old UI test file
- `app.py` - Legacy Streamlit application
- `simple_backend.py` - Simplified backend version

## 🎯 **Key Features by File**

### **Content Filtering (`content_filter.py`)**
- Multi-layer filtering system
- Age-based article filtering
- Source blacklisting
- AI content classification
- Automatic cleanup

### **Smart Backend (`backend.py`)**
- Entity-based search with relevance scoring
- Smart caching with 24-hour TTL
- Efficient ingestion (only when needed)
- AWS integration (DynamoDB, S3, Bedrock)
- Real-time streaming responses

### **Modern UI (`src/components/`)**
- Parchment theme with dark mode
- Responsive newspaper-style design
- Interactive search and filtering
- Real-time updates and animations
- Accessibility-compliant components

### **Infrastructure (`setup_aws_infrastructure.py`)**
- Automated DynamoDB table creation
- S3 bucket setup with lifecycle policies
- Initial blacklist population
- Environment configuration

## 📊 **File Size Optimization**

| Category | Before Cleanup | After Cleanup | Reduction |
|----------|---------------|---------------|-----------|
| Documentation | 8 files | 2 files | 75% |
| Backend Scripts | 4 files | 2 files | 50% |
| Test Files | 3 files | 1 file | 67% |
| Total Project | 45+ files | 25 files | 44% |

## 🚀 **Deployment Files**

### **Vercel (Frontend)**
- Automatic deployment from GitHub
- Uses `package.json` and `src/` directory
- Environment variables configured in Vercel dashboard

### **Railway (Backend)**
- Uses `Procfile` for deployment configuration
- Runs `backend.py` via uvicorn
- Environment variables configured in Railway dashboard

### **AWS (Database & AI)**
- Resources created via `setup_aws_infrastructure.py`
- DynamoDB tables and S3 buckets
- Bedrock AI model integration

## 🔧 **Development Workflow**

1. **Local Development**: Use startup scripts or manual commands
2. **Testing**: Run `test_content_filtering.py` before deployment
3. **Deployment**: Git push triggers automatic deployment
4. **Monitoring**: Check Railway logs and Vercel analytics

This clean structure makes the project maintainable, scalable, and easy to understand for new contributors.