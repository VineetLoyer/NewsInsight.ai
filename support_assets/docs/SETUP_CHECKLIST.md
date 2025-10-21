# NewsInsight.ai Setup Checklist

## ✅ Pre-Flight Checks

- [ ] Python 3.8+ installed (`python --version`)
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] Git (for cloning repo)

## 📦 Installation

- [ ] Clone repository: `git clone <repo-url> && cd NewsInsight.ai`
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate venv:
  - Windows: `.\venv\Scripts\activate`
  - Mac/Linux: `source venv/bin/activate`
- [ ] Install requirements: `pip install -r requirements.txt`

## 🔐 AWS Setup

### DynamoDB Table: `news_metadata`

```bash
aws dynamodb create-table \
  --table-name news_metadata \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-west-2
```

Expected schema:
- [ ] **Partition Key**: `id` (String)
- [ ] **Attributes**:
  - [ ] `headline` (String)
  - [ ] `summary` (String)
  - [ ] `date` (String, ISO 8601)
  - [ ] `source` (String)
  - [ ] `sentiment` (String, optional)
  - [ ] `verification_score` (Number, optional)
  - [ ] `entities` (List, optional)

### S3 Buckets (Optional)

- [ ] **Raw articles**: `newsinsights-raw-<acct>-<region>`
  ```bash
  aws s3 mb s3://newsinsights-raw-<acct>-<region> --region us-west-2
  ```

- [ ] **Processed articles**: `newsinsights-processed-<acct>-<region>`
  ```bash
  aws s3 mb s3://newsinsights-processed-<acct>-<region> --region us-west-2
  ```

### IAM Role / Permissions

Ensure your AWS identity (user/role) has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Scan",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/news_metadata*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::newsinsights-*/*",
        "arn:aws:s3:::newsinsights-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    }
  ]
}
```

## 🚀 Configuration

### Environment Variables

Set these before running the app:

**Windows PowerShell:**
```powershell
$env:AWS_REGION = "us-west-2"
$env:DDB_TABLE = "news_metadata"
$env:BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
$env:PROC_BUCKET = "newsinsights-processed-<acct>-<region>"
```

**Linux/Mac:**
```bash
export AWS_REGION="us-west-2"
export DDB_TABLE="news_metadata"
export BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
export PROC_BUCKET="newsinsights-processed-<acct>-<region>"
```

**Optional Debug Mode:**
```
export DEBUG_MODE="true"
```

## 📊 Data Population

Choose one method:

### Option 1: Insert Sample Data (Quick Testing)

```bash
# Activate venv first
python scripts/insert_sample_data.py insert
```

Then run the app:
```bash
streamlit run app.py
```

### Option 2: Run the Fetcher Lambda

If you have APIs configured:

```bash
# Set API keys in AWS Systems Manager Parameter Store
aws ssm put-parameter --name "/newsinsights/NEWSAPI_KEY" --value "your-key" --type "SecureString"
aws ssm put-parameter --name "/newsinsights/GUARDIAN_KEY" --value "your-key" --type "SecureString"

# Run locally or deploy as Lambda
python fetch_articles_lambda.py
```

### Option 3: Populate from External Source

Use your existing data pipeline to populate DynamoDB directly.

## 🧪 Verification

### Run Diagnostics

```bash
python scripts/diagnose.py
```

Should show:
- [ ] ✓ AWS credentials found
- [ ] ✓ Connected to DynamoDB table
- [ ] ✓ Found N articles (or ⚠ Table is empty)
- [ ] ✓ (Optional) S3 bucket accessible
- [ ] ✓ (Optional) Bedrock model available

### Check Sample Articles

```bash
python scripts/insert_sample_data.py list
```

Should show 6 sample articles with different sentiments.

## 🎯 First Run

1. **Terminal Window 1: Start Streamlit**
   ```bash
   # Make sure venv is activated
   streamlit run app.py
   ```

2. **Browser: Visit the app**
   - Open `http://localhost:8501`
   - Should see: "📰 NewsInsight — Daily Brief"

3. **Try Features:**
   - [ ] Search for a keyword (e.g., "technology")
   - [ ] Click a suggested topic button
   - [ ] View article cards with sentiment chips
   - [ ] Click "Original" link (if available)
   - [ ] Click "Explain" button
   - [ ] Expand "Chat About This Article"

## 🐛 Troubleshooting

If you see "No articles found yet":

1. **Run diagnostics:**
   ```bash
   python scripts/diagnose.py
   ```

2. **Check DDB table:**
   ```bash
   python scripts/insert_sample_data.py list
   ```

3. **Insert sample data:**
   ```bash
   python scripts/insert_sample_data.py insert
   ```

4. **Enable debug mode:**
   ```
   export DEBUG_MODE=true
   streamlit run app.py
   ```

5. **Check CloudWatch logs** (if using Lambda)

See `TROUBLESHOOTING.md` for more detailed help.

## 📋 Production Deployment

### Docker

Build and run:
```bash
docker build -t newsinsight .
docker run -e AWS_REGION=us-west-2 -e DDB_TABLE=news_metadata -p 8501:8501 newsinsight
```

### AWS ECS / AppRunner

1. [ ] Push Docker image to ECR
2. [ ] Create ECS task definition
3. [ ] Set environment variables via task definition
4. [ ] Create ECS service or AppRunner service
5. [ ] Configure load balancer (optional)

### Environment-Specific Configs

Create `.env` files per environment:

**`.env.dev`:**
```
AWS_REGION=us-west-2
DDB_TABLE=news_metadata_dev
DEBUG_MODE=true
```

**`.env.prod`:**
```
AWS_REGION=us-east-1
DDB_TABLE=news_metadata
DEBUG_MODE=false
```

Load with:
```bash
export $(cat .env.dev | xargs)
streamlit run app.py
```

## 📚 Next Steps

1. **Customize Topics**: Edit `suggested_topics` in `app.py`
2. **Add API Keys**: Configure NewsAPI and Guardian API
3. **Deploy Fetcher**: Set up Lambda for automatic article fetching
4. **Configure Processor**: Set up summarize Lambda for article processing
5. **Scale Search**: Add DynamoDB GSI for keyword queries
6. **Custom Branding**: Modify colors and fonts in CSS

## 🎓 Learning Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [AWS DynamoDB](https://docs.aws.amazon.com/dynamodb/)
- [AWS Bedrock](https://docs.aws.amazon.com/bedrock/)
- [NewsAPI](https://newsapi.org)
- [The Guardian API](https://open-platform.theguardian.com)

## 🆘 Getting Help

1. Enable `DEBUG_MODE=true` and check console output
2. Run `python scripts/diagnose.py` for system diagnostics
3. Check `TROUBLESHOOTING.md` for common issues
4. Review AWS CloudWatch logs
5. Check Streamlit logs: `streamlit logs`

## ✨ You're Ready!

Once all checkboxes above are complete, you should have:
- ✅ A fully functional NewsInsight app
- ✅ Sample articles displaying
- ✅ Search and filter working
- ✅ Explain & Chat features operational

Start exploring! 🚀
