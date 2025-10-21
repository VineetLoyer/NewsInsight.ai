# NewsInsight — Troubleshooting Guide

## Issue: "No articles found yet. Try a different keyword or run the fetcher"

This error means the DynamoDB `news_metadata` table is either empty or the search isn't matching your query. Here's how to diagnose and fix it:

### Step 1: Enable Debug Mode

Set the environment variable before running the app:

**Windows PowerShell:**
```powershell
$env:DEBUG_MODE = "true"
streamlit run app.py
```

**Linux/Mac:**
```bash
export DEBUG_MODE=true
streamlit run app.py
```

With DEBUG_MODE enabled, you'll see:
- How many items were scanned from DDB
- How many matched your search query
- Any S3 fetch errors

---

## Step 2: Check if Articles Exist in DDB

Run this quick Python script to verify:

```python
import boto3

# Configure
AWS_REGION = "us-west-2"  # Change if needed
DDB_TABLE = "news_metadata"  # Change if needed

# Scan the table
ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = ddb.Table(DDB_TABLE)

response = table.scan(Limit=10)
items = response.get("Items", [])

print(f"Total items found: {len(items)}")
for item in items:
    print(f"  - {item.get('headline', 'No headline')} [{item.get('source', 'unknown')}]")

if len(items) == 0:
    print("\n⚠️ DynamoDB table is empty! Run the fetcher Lambda first.")
```

**Save as:** `scripts/check_ddb.py`

**Run it:**
```bash
python scripts/check_ddb.py
```

---

## Step 3: Verify the Fetcher Lambda is Running

The `fetch_articles_lambda.py` must have run successfully to populate the table.

### Check CloudWatch Logs:
1. Go to AWS CloudWatch
2. Search for the Lambda function log group
3. Look for recent execution logs
4. Check for errors (especially API key issues)

### Manual Test of the Fetcher:

Create a test file:

```python
# scripts/test_fetcher.py
import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__) + "/..")

# Mock environment (adjust to your setup)
os.environ["RAW_BUCKET"] = "newsinsights-raw-<acct>-<region>"
os.environ["DDB_TABLE"] = "news_metadata"

from fetch_articles_lambda import handler

# Mock AWS event/context
event = {}
context = None

result = handler(event, context)
print(json.dumps(result, indent=2))
```

---

## Step 4: Ensure Environment Variables Are Set

The app requires these environment variables (or they use defaults):

| Variable | Default | Purpose |
|----------|---------|---------|
| `AWS_REGION` | `us-west-2` | AWS region |
| `DDB_TABLE` | `news_metadata` | DynamoDB table name |
| `PROC_BUCKET` | *(empty)* | S3 bucket for processed articles |
| `BEDROCK_MODEL_ID` | *(empty)* | Bedrock model for Explain & Chat |
| `MODEL_FAMILY` | `anthropic` | Model type (`anthropic` or `amazon`) |
| `DEBUG_MODE` | `false` | Enable debug logging |

### Set them locally:

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

---

## Step 5: Check AWS Credentials

Ensure your AWS credentials are properly configured:

```bash
aws sts get-caller-identity
```

If this fails, configure AWS credentials:

```bash
aws configure
```

---

## Step 6: Verify DDB Schema

Check that your table has the right attributes:

```python
import boto3

ddb = boto3.client("dynamodb", region_name="us-west-2")
response = ddb.describe_table(TableName="news_metadata")

print("Table Status:", response["Table"]["TableStatus"])
print("Key Schema:", response["Table"]["KeySchema"])
print("Attributes:")
for attr in response["Table"]["AttributeDefinitions"]:
    print(f"  - {attr['AttributeName']} ({attr['AttributeType']})")
```

**Expected attributes (at minimum):**
- `id` (String, Partition Key)
- `headline` (String)
- `summary` (String)
- `date` (String, ISO 8601 format)
- `source` (String)
- `sentiment` (String, optional)

---

## Step 7: Check S3 Processed Documents

If articles exist in DDB but don't render properly, check S3:

```python
import boto3

s3 = boto3.client("s3", region_name="us-west-2")
bucket = "newsinsights-processed-<acct>-<region>"

try:
    response = s3.list_objects_v2(Bucket=bucket, Prefix="news-processed/", MaxKeys=10)
    items = response.get("Contents", [])
    print(f"Found {len(items)} processed documents in S3")
    for item in items:
        print(f"  - {item['Key']}")
except Exception as e:
    print(f"S3 error: {e}")
```

---

## Step 8: Run the Full Agent

If everything above checks out, try running the agent:

```python
# scripts/test_agent.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__) + "/..")

os.environ["AWS_REGION"] = "us-west-2"
os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"

from agent.newsinsights_agent import NewsInsightsAgent

agent = NewsInsightsAgent()
result = agent.run("technology")

print(f"Summary: {result.summary}")
print(f"Verdict: {result.verdict}")
print(f"Confidence: {result.confidence}")
print(f"Top articles: {len(result.top_articles)}")
```

---

## Common Issues & Fixes

### Issue: "No articles found" even after running fetcher

**Cause:** Articles aren't being written to the `news_metadata` table.

**Fix:**
1. Check that the fetcher Lambda has the right DynamoDB permissions
2. Check the Lambda logs for write errors
3. Manually insert a test article:
   ```python
   table.put_item(Item={
       "id": "test-001",
       "headline": "Test Article",
       "summary": "This is a test",
       "date": "2025-10-20T12:00:00Z",
       "source": "test"
   })
   ```

### Issue: Bedrock Explain/Chat not working

**Cause:** Bedrock model not configured or insufficient permissions.

**Fix:**
1. Set `BEDROCK_MODEL_ID` environment variable
2. Ensure IAM role has `bedrock:InvokeModel` permission
3. Check that the model is available in your region

### Issue: S3 fetch fails (URL not showing)

**Cause:** S3 bucket doesn't exist or permissions are missing.

**Fix:**
1. Create the bucket: `aws s3 mb s3://newsinsights-processed-<acct>-<region>`
2. Ensure Lambda has `s3:GetObject` permission
3. Disable the S3 fetch gracefully by leaving `PROC_BUCKET` empty

---

## Performance Tips

For large datasets (>10K articles):

1. **Add a GSI on `date`** for faster sorting
2. **Add a GSI on `entities` or tags** for keyword search
3. **Switch to ElasticSearch/OpenSearch** instead of DDB Scan
4. **Cache search results** with a longer TTL (already done with `@st.cache_data`)

---

## Need Help?

1. Run with `DEBUG_MODE=true` to see detailed logs
2. Check AWS CloudWatch logs
3. Verify environment variables with: `env | grep -E 'AWS|BEDROCK|DDB'`
4. Test individual components (fetcher, agent) in isolation
