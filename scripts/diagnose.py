#!/usr/bin/env python3
"""
Quick diagnostic script to troubleshoot NewsInsight.ai setup
"""

import os
import sys
import json
from datetime import datetime

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
END = "\033[0m"

def check_env_vars():
    """Check if required environment variables are set"""
    print(f"\n{BLUE}=== Environment Variables ==={END}")
    
    required = {
        "AWS_REGION": "us-west-2",
        "DDB_TABLE": "news_metadata",
        "BEDROCK_MODEL_ID": "",
        "PROC_BUCKET": "",
        "DEBUG_MODE": "false"
    }
    
    for var, default in required.items():
        value = os.getenv(var, default)
        status = f"{GREEN}✓{END}" if value else f"{YELLOW}⚠{END}"
        print(f"{status} {var:20} = {value or '(not set)'}")

def check_aws_credentials():
    """Check if AWS credentials are available"""
    print(f"\n{BLUE}=== AWS Credentials ==={END}")
    
    try:
        import boto3
        client = boto3.client("sts")
        identity = client.get_caller_identity()
        print(f"{GREEN}✓{END} AWS credentials found")
        print(f"  Account: {identity['Account']}")
        print(f"  User: {identity['Arn']}")
    except Exception as e:
        print(f"{RED}✗{END} AWS credentials not found: {e}")

def check_ddb_connection():
    """Check connection to DynamoDB"""
    print(f"\n{BLUE}=== DynamoDB Connection ==={END}")
    
    try:
        import boto3
        region = os.getenv("AWS_REGION", "us-west-2")
        table_name = os.getenv("DDB_TABLE", "news_metadata")
        
        ddb = boto3.resource("dynamodb", region_name=region)
        table = ddb.Table(table_name)
        
        # Try a simple scan
        response = table.scan(Limit=1)
        print(f"{GREEN}✓{END} Connected to DynamoDB table: {table_name}")
        
        # Count items
        response = table.scan(Select="COUNT")
        count = response.get("Count", 0)
        print(f"  Items in table: {count}")
        
        if count == 0:
            print(f"  {YELLOW}⚠ Table is empty! Run the fetcher Lambda.{END}")
        
        return count
    except Exception as e:
        print(f"{RED}✗{END} DynamoDB error: {e}")
        return 0

def check_sample_articles(limit=5):
    """Fetch and display sample articles"""
    print(f"\n{BLUE}=== Sample Articles ==={END}")
    
    try:
        import boto3
        region = os.getenv("AWS_REGION", "us-west-2")
        table_name = os.getenv("DDB_TABLE", "news_metadata")
        
        ddb = boto3.resource("dynamodb", region_name=region)
        table = ddb.Table(table_name)
        
        response = table.scan(Limit=limit)
        items = response.get("Items", [])
        
        if not items:
            print(f"{YELLOW}⚠ No articles found in DDB{END}")
            return
        
        print(f"{GREEN}✓{END} Found {len(items)} sample articles:")
        for idx, item in enumerate(items, 1):
            headline = item.get("headline", "N/A")[:60]
            source = item.get("source", "unknown")
            date = item.get("date", "unknown")[:10]
            sentiment = item.get("sentiment", "neutral")
            
            print(f"\n  [{idx}] {headline}...")
            print(f"      Source: {source} | Date: {date} | Sentiment: {sentiment}")
    
    except Exception as e:
        print(f"{RED}✗{END} Error fetching articles: {e}")

def check_s3_bucket():
    """Check S3 bucket for processed documents"""
    print(f"\n{BLUE}=== S3 Processed Bucket ==={END}")
    
    bucket = os.getenv("PROC_BUCKET", "")
    if not bucket:
        print(f"{YELLOW}⚠ PROC_BUCKET not set{END}")
        return
    
    try:
        import boto3
        region = os.getenv("AWS_REGION", "us-west-2")
        
        s3 = boto3.client("s3", region_name=region)
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix="news-processed/",
            MaxKeys=5
        )
        
        items = response.get("Contents", [])
        if items:
            print(f"{GREEN}✓{END} Found {len(items)} processed documents in S3")
            for item in items:
                print(f"  - {item['Key']}")
        else:
            print(f"{YELLOW}⚠ No processed documents found in S3{END}")
    
    except Exception as e:
        print(f"{RED}✗{END} S3 error: {e}")

def check_bedrock_model():
    """Check Bedrock model availability"""
    print(f"\n{BLUE}=== Bedrock Model ==={END}")
    
    model_id = os.getenv("BEDROCK_MODEL_ID", "")
    if not model_id:
        print(f"{YELLOW}⚠ BEDROCK_MODEL_ID not set{END}")
        return
    
    try:
        import boto3
        region = os.getenv("AWS_REGION", "us-west-2")
        
        client = boto3.client("bedrock-runtime", region_name=region)
        
        # Try a simple invoke with empty input
        try:
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]
                })
            )
            print(f"{GREEN}✓{END} Bedrock model is available: {model_id}")
        except client.exceptions.ResourceNotFoundException:
            print(f"{RED}✗{END} Model not found or not accessible: {model_id}")
        except Exception as e:
            if "ValidationException" in str(type(e)):
                print(f"{GREEN}✓{END} Model exists (validation error is OK): {model_id}")
            else:
                raise
    
    except Exception as e:
        print(f"{RED}✗{END} Bedrock error: {e}")

def main():
    print(f"\n{BLUE}{'='*50}")
    print(f"NewsInsight.ai Diagnostic Tool")
    print(f"{'='*50}{END}")
    
    check_env_vars()
    check_aws_credentials()
    count = check_ddb_connection()
    
    if count > 0:
        check_sample_articles()
    
    check_s3_bucket()
    check_bedrock_model()
    
    print(f"\n{BLUE}=== Summary ==={END}")
    print(f"Run the app with: {GREEN}DEBUG_MODE=true streamlit run app.py{END}")
    print(f"See {YELLOW}TROUBLESHOOTING.md{END} for more help.\n")

if __name__ == "__main__":
    main()
