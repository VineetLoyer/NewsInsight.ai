# NewsInsight Content Filtering Implementation Guide

## 🎯 Implementation Steps

### Phase 1: Local Setup & Testing

#### Step 1: Install Dependencies
```bash
pip install boto3 python-dateutil
```

#### Step 2: Setup AWS Infrastructure
```bash
# This creates all DynamoDB tables and S3 buckets
python setup_aws_infrastructure.py
```

**What this creates:**
- DynamoDB Tables:
  - `news_metadata` (main articles)
  - `content_blacklist` (filtering rules)
  - `content_review_queue` (pending review)
- S3 Buckets:
  - `newsinsights-processed-{account}-{region}`
  - `newsinsights-raw-{account}-{region}`
- Initial blacklist data

#### Step 3: Test Everything Locally
```bash
# Run comprehensive tests
python test_content_filtering.py
```

**Tests include:**
- AWS connectivity
- Content filtering logic
- Blacklist functionality
- Age filtering
- API endpoints

#### Step 4: Start Local Backend
```bash
# Start FastAPI server locally
python main.py
```

#### Step 5: Test Frontend Integration
- Open your Vercel frontend
- Test search functionality
- Verify age filtering works
- Check content quality

### Phase 2: Production Deployment

#### Step 6: Update Railway Environment Variables
Add these to Railway (if not already present):
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-west-2
DDB_TABLE=news_metadata
PROC_BUCKET=newsinsights-processed-{account}-{region}
RAW_BUCKET=newsinsights-raw-{account}-{region}
BEDROCK_MODEL_ID=your_model_arn
NEWSAPI_KEY=your_key
GUARDIAN_KEY=your_key
```

#### Step 7: Deploy to Railway
```bash
git add .
git commit -m "Add content filtering system with age filtering"
git push origin main
```

#### Step 8: Verify Production
- Check Railway logs for successful startup
- Test API endpoints via Vercel frontend
- Monitor filtering statistics

## 🔧 Configuration Options

### Age Filter Settings
```python
# In main.py search function
max_age_days = 2  # Default: 2 days
max_age_days = 1  # Breaking news mode
max_age_days = 7  # Weekly analysis
```

### Content Filter Thresholds
```python
# In content_filter.py
MIN_WORDS = 200      # Minimum article length
MAX_WORDS = 10000    # Maximum article length
MAX_AGE_DAYS = 2     # Age filter threshold
```

### Blacklist Management
```python
# Add new blacklisted source
content_filter.add_to_blacklist("source", "spam-news.com", "Low quality")

# Add blacklisted keyword
content_filter.add_to_blacklist("keyword", "buy now", "Promotional")
```

## 📊 Monitoring & Maintenance

### Daily Tasks
- Check content quality statistics
- Review rejected articles (if needed)
- Monitor API usage and costs

### Weekly Tasks
- Clean up old articles (30+ days)
- Review and update blacklist
- Analyze filtering effectiveness

### Monthly Tasks
- Optimize filtering thresholds
- Review AWS costs
- Update content categories

## 🚨 Troubleshooting

### Common Issues

#### AWS Connection Failed
```bash
# Check credentials
aws sts get-caller-identity

# Check region
echo $AWS_REGION
```

#### DynamoDB Table Not Found
```bash
# Re-run setup
python setup_aws_infrastructure.py
```

#### Content Filter Not Working
```bash
# Run tests
python test_content_filtering.py
```

#### Railway Deployment Issues
- Check Railway logs for errors
- Verify environment variables
- Ensure all dependencies in requirements.txt

## 📈 Expected Results

### Content Quality Improvement
- **Before**: Mixed quality articles, ads, old content
- **After**: High-quality, recent, legitimate news only

### Performance Metrics
- **Filtering Speed**: <100ms per article
- **Acceptance Rate**: ~50% (varies by topic)
- **User Satisfaction**: Significantly improved

### Cost Optimization
- **AI Processing**: 50% reduction in Bedrock calls
- **Storage**: Automatic cleanup of old content
- **Bandwidth**: Smaller, higher-quality result sets

## 🎯 Success Criteria

✅ All tests pass locally
✅ Railway deployment successful
✅ Frontend shows only recent, high-quality articles
✅ Age filtering works (1-2 day articles only)
✅ Blacklist prevents spam/ads
✅ Performance remains fast (<2s response time)
✅ AWS costs remain reasonable

## 🚀 Future Enhancements

### Phase 3: Advanced Features
- Machine learning-based quality scoring
- User feedback integration
- Automated blacklist updates
- Real-time content monitoring
- Advanced analytics dashboard

### Phase 4: Scale Optimization
- Elasticsearch for better search
- Redis caching layer
- CDN for article content
- Multi-region deployment