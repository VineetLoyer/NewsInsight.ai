#!/usr/bin/env python3
"""
Insert sample articles into DynamoDB for testing.
Useful for local development without running the full fetcher pipeline.
"""

import os
import boto3
from datetime import datetime, timedelta
import json

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
DDB_TABLE = os.getenv("DDB_TABLE", "news_metadata")

# Sample articles (based on typical news structure)
SAMPLE_ARTICLES = [
    {
        "id": "article-001",
        "headline": "OpenAI Announces GPT-5 with Advanced Reasoning Capabilities",
        "source": "techcrunch",
        "date": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
        "summary": "OpenAI has announced GPT-5, their latest language model featuring advanced reasoning capabilities. The model demonstrates improved performance on complex reasoning tasks and shows 40% better accuracy on benchmark tests compared to GPT-4. The release marks a significant milestone in AI development.",
        "sentiment": "positive",
        "verification_score": 0.95,
        "entities": ["OpenAI", "GPT-5", "AI", "Language Model"]
    },
    {
        "id": "article-002",
        "headline": "Federal Reserve Signals Pause in Interest Rate Hikes",
        "source": "bloomberg",
        "date": (datetime.utcnow() - timedelta(hours=4)).isoformat() + "Z",
        "summary": "The Federal Reserve Chair indicated during a press conference that the central bank may pause its rate hike campaign. This comes after inflation data shows some moderation, though it remains above the Fed's 2% target. Market indices surged on the news, with the S&P 500 closing up 2.1%.",
        "sentiment": "neutral",
        "verification_score": 0.88,
        "entities": ["Federal Reserve", "Interest Rates", "Inflation", "Markets"]
    },
    {
        "id": "article-003",
        "headline": "European Parliament Approves AI Regulation Framework",
        "source": "euractiv",
        "date": (datetime.utcnow() - timedelta(hours=6)).isoformat() + "Z",
        "summary": "The European Parliament has passed the AI Act, establishing a comprehensive regulatory framework for artificial intelligence. The law includes provisions for high-risk AI systems, transparency requirements, and penalties for non-compliance. Industry groups expressed mixed reactions to the stringent regulations.",
        "sentiment": "neutral",
        "verification_score": 0.92,
        "entities": ["EU", "AI Regulation", "European Parliament", "Policy"]
    },
    {
        "id": "article-004",
        "headline": "Apple Announces iPhone 16 with Advanced AI Features",
        "source": "apple_press",
        "date": (datetime.utcnow() - timedelta(hours=8)).isoformat() + "Z",
        "summary": "Apple unveiled the iPhone 16 with on-device AI capabilities powered by the new A18 chip. New features include advanced photo editing, real-time language translation, and intelligent summarization. The company emphasized privacy with on-device processing rather than cloud computation.",
        "sentiment": "positive",
        "verification_score": 0.96,
        "entities": ["Apple", "iPhone 16", "AI", "Technology"]
    },
    {
        "id": "article-005",
        "headline": "Tesla Delivers Record Quarterly Vehicle Sales",
        "source": "reuters",
        "date": (datetime.utcnow() - timedelta(hours=10)).isoformat() + "Z",
        "summary": "Tesla reported record quarterly vehicle deliveries, exceeding analyst expectations by 12%. The company delivered 1.81 million vehicles in Q3 2024, driven by strong demand for the new Cybertruck model. CEO Elon Musk attributed the success to manufacturing efficiency improvements.",
        "sentiment": "positive",
        "verification_score": 0.94,
        "entities": ["Tesla", "Earnings", "Vehicles", "Cybertruck"]
    },
    {
        "id": "article-006",
        "headline": "Climate Summit Reaches Agreement on Carbon Credits",
        "source": "un_dispatch",
        "date": (datetime.utcnow() - timedelta(hours=12)).isoformat() + "Z",
        "summary": "World leaders at COP29 agreed on a framework for international carbon credit trading. The deal establishes mechanisms for countries to buy and sell carbon offsets, with the goal of accelerating global decarbonization efforts. Environmental groups praised the agreement but called for stricter enforcement.",
        "sentiment": "positive",
        "verification_score": 0.85,
        "entities": ["Climate", "Carbon Credits", "COP29", "Sustainability"]
    }
]

def insert_sample_data():
    """Insert sample articles into DynamoDB"""
    try:
        # Connect to DynamoDB
        ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = ddb.Table(DDB_TABLE)
        
        print(f"🔄 Connecting to DynamoDB table: {DDB_TABLE} (region: {AWS_REGION})")
        
        # Insert each article
        inserted = 0
        for article in SAMPLE_ARTICLES:
            try:
                table.put_item(Item=article)
                inserted += 1
                print(f"✓ Inserted: {article['headline'][:60]}...")
            except Exception as e:
                print(f"✗ Failed to insert {article['id']}: {e}")
        
        print(f"\n✅ Successfully inserted {inserted}/{len(SAMPLE_ARTICLES)} articles")
        
        # Verify insertion
        response = table.scan(Select="COUNT")
        total_count = response.get("Count", 0)
        print(f"📊 Table now contains {total_count} articles total")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_articles(limit=10):
    """List articles in the table"""
    try:
        ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = ddb.Table(DDB_TABLE)
        
        response = table.scan(Limit=limit)
        items = response.get("Items", [])
        
        print(f"\n📰 Articles in {DDB_TABLE}:\n")
        for idx, item in enumerate(items, 1):
            headline = item.get("headline", "N/A")[:70]
            source = item.get("source", "unknown")
            sentiment = item.get("sentiment", "neutral")
            date = item.get("date", "N/A")[:10]
            
            print(f"{idx:2}. {headline}")
            print(f"    Source: {source:15} | Sentiment: {sentiment:8} | Date: {date}")
        
        if not items:
            print("  (No articles found)")
            
    except Exception as e:
        print(f"Error: {e}")

def clear_table():
    """Clear all items from the table (use with caution!)"""
    try:
        ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = ddb.Table(DDB_TABLE)
        
        response = table.scan(ProjectionExpression="id")
        items = response.get("Items", [])
        
        if not items:
            print("Table is already empty")
            return
        
        print(f"⚠️  About to delete {len(items)} items from {DDB_TABLE}")
        confirm = input("Type 'yes' to confirm: ")
        
        if confirm.lower() != "yes":
            print("❌ Cancelled")
            return
        
        # Delete all items
        deleted = 0
        with table.batch_writer(batch_size=25) as batch:
            for item in items:
                batch.delete_item(Key={"id": item["id"]})
                deleted += 1
        
        print(f"✅ Deleted {deleted} items")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "insert":
            insert_sample_data()
        elif command == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            list_articles(limit)
        elif command == "clear":
            clear_table()
        else:
            print("Usage: python scripts/insert_sample_data.py [insert|list|clear]")
    else:
        print("📝 Sample Data Loader for NewsInsight.ai\n")
        print("Usage:")
        print("  python scripts/insert_sample_data.py insert   # Insert 6 sample articles")
        print("  python scripts/insert_sample_data.py list     # List articles in table")
        print("  python scripts/insert_sample_data.py list 20  # List 20 articles")
        print("  python scripts/insert_sample_data.py clear    # Delete all articles (⚠️ caution!)")
        print("\nExample:")
        print("  python scripts/insert_sample_data.py insert")
        print("  streamlit run app.py")
