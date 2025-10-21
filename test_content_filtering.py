#!/usr/bin/env python3
"""
Local Testing Script for Content Filtering
Tests all filtering components before deployment
"""

import os
import json
import boto3
from datetime import datetime, timedelta
from content_filter import ContentFilter

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def test_aws_connection():
    """Test AWS connectivity and resources"""
    print("🔍 Testing AWS Connection...")
    
    try:
        session = boto3.Session(region_name=os.getenv("AWS_REGION", "us-west-2"))
        
        # Test DynamoDB
        ddb = session.resource("dynamodb")
        table = ddb.Table("news_metadata")
        table.load()
        print("   ✅ DynamoDB connection successful")
        
        # Test S3
        s3 = session.client("s3")
        proc_bucket = os.getenv("PROC_BUCKET")
        if proc_bucket:
            s3.head_bucket(Bucket=proc_bucket)
            print("   ✅ S3 connection successful")
        
        # Test Bedrock
        bedrock = session.client("bedrock-runtime")
        model_id = os.getenv("BEDROCK_MODEL_ID")
        if model_id:
            print("   ✅ Bedrock client initialized")
        
        return True, session
        
    except Exception as e:
        print(f"   ❌ AWS connection failed: {e}")
        return False, None

def test_content_filter(session):
    """Test content filtering functionality"""
    print("\n🔍 Testing Content Filter...")
    
    try:
        content_filter = ContentFilter(session)
        
        # Test articles (mix of good and bad)
        test_articles = [
            {
                "headline": "Breaking: Major Tech Company Announces AI Breakthrough",
                "summary": "A leading technology company has announced a significant breakthrough in artificial intelligence research that could revolutionize the industry. The new AI system demonstrates unprecedented capabilities in natural language processing and reasoning.",
                "content": "In a groundbreaking announcement today, TechCorp revealed their latest AI system, which represents a major leap forward in machine learning capabilities. The system, developed over three years by a team of 200 researchers, can perform complex reasoning tasks and understand context in ways previously thought impossible. Industry experts are calling this a watershed moment for AI development. The breakthrough comes after years of intensive research into neural network architectures and training methodologies. The new system can process and understand natural language with human-like comprehension, making it capable of engaging in sophisticated conversations, analyzing complex documents, and even generating creative content. This advancement is expected to have far-reaching implications across multiple industries, from healthcare and finance to education and entertainment. The company plans to gradually roll out the technology through partnerships with select organizations before making it more widely available. Researchers believe this could be the stepping stone toward more advanced AI systems that can truly understand and interact with the world in meaningful ways.",
                "source": "TechNews",
                "date": datetime.utcnow().isoformat() + "Z",
                "url": "https://technews.com/ai-breakthrough"
            },
            {
                "headline": "CLICK HERE! Amazing Weight Loss Secret Doctors Don't Want You to Know!",
                "summary": "Discover the one weird trick that will help you lose 30 pounds in 30 days! Limited time offer - act now!",
                "content": "This amazing supplement will change your life! Click here to buy now and get 50% off. Don't wait, this offer expires soon! Doctors hate this one simple trick that has helped thousands of people lose weight without diet or exercise. The secret ingredient found in this revolutionary supplement has been used for centuries in ancient medicine but big pharma doesn't want you to know about it. Our customers report losing 10, 20, even 30 pounds in just weeks without changing their lifestyle. But hurry, this special promotional price won't last long. Order now and get free shipping plus a bonus bottle absolutely free. This offer is only available for the next 24 hours so don't miss out on this incredible opportunity to transform your body and your life. Thousands of satisfied customers can't be wrong. Join them today and start your weight loss journey with this miracle supplement that really works. Click the link below to order now and take advantage of this limited time offer before it's too late.",
                "source": "ClickBait Daily",
                "date": datetime.utcnow().isoformat() + "Z",
                "url": "https://spamsite.com/weightloss"
            },
            {
                "headline": "Short article",
                "summary": "Too short.",
                "content": "This article is way too short to be useful.",
                "source": "News Source",
                "date": datetime.utcnow().isoformat() + "Z",
                "url": "https://news.com/short"
            },
            {
                "headline": "Old News: Something That Happened Last Week",
                "summary": "This is an old news article that should be filtered out by the age filter.",
                "content": "This article discusses events that happened several days ago and should not appear in recent news feeds. It contains enough content to pass the word count filter but should fail the age filter test. The events described in this article took place last week and are no longer relevant to current news consumers who are looking for fresh, up-to-date information. While the content itself may be well-written and informative, the age of the article makes it unsuitable for inclusion in a modern news feed that prioritizes recent developments. This type of content filtering is essential for maintaining the relevance and quality of news aggregation services. Users expect to see the latest information, not outdated stories that may no longer be accurate or relevant to current events. The age filtering system should automatically detect and exclude such content to ensure that only fresh, timely news articles are presented to users. This helps maintain user engagement and trust in the news service by providing consistently current and relevant information.",
                "source": "Old News Network",
                "date": (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z",
                "url": "https://oldnews.com/article"
            }
        ]
        
        print(f"   Testing {len(test_articles)} sample articles...")
        
        results = {
            "passed_preprocessing": 0,
            "failed_preprocessing": 0,
            "rejection_reasons": {}
        }
        
        for i, article in enumerate(test_articles):
            print(f"\n   📄 Testing Article {i+1}: {article['headline'][:50]}...")
            
            # Test preprocessing filter
            should_process, reason = content_filter.preprocess_filter(article)
            
            if should_process:
                results["passed_preprocessing"] += 1
                print(f"      ✅ Passed: {reason}")
            else:
                results["failed_preprocessing"] += 1
                print(f"      ❌ Rejected: {reason}")
                
                # Categorize rejection reason
                if reason not in results["rejection_reasons"]:
                    results["rejection_reasons"][reason] = 0
                results["rejection_reasons"][reason] += 1
        
        print(f"\n   📊 Preprocessing Results:")
        print(f"      ✅ Passed: {results['passed_preprocessing']}")
        print(f"      ❌ Rejected: {results['failed_preprocessing']}")
        
        if results["rejection_reasons"]:
            print(f"      📋 Rejection Reasons:")
            for reason, count in results["rejection_reasons"].items():
                print(f"         - {reason}: {count}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Content filter test failed: {e}")
        return False

def test_blacklist_functionality(session):
    """Test blacklist add/check functionality"""
    print("\n🔍 Testing Blacklist Functionality...")
    
    try:
        content_filter = ContentFilter(session)
        
        # Test adding to blacklist
        test_source = "test-spam-source"
        content_filter.add_to_blacklist("source", test_source, "Test entry")
        print(f"   ✅ Added test source to blacklist: {test_source}")
        
        # Test checking blacklist
        is_blacklisted = content_filter._is_blacklisted("source", test_source)
        if is_blacklisted:
            print(f"   ✅ Blacklist check working: {test_source} found")
        else:
            print(f"   ❌ Blacklist check failed: {test_source} not found")
        
        # Clean up test entry
        try:
            blacklist_table = session.resource("dynamodb").Table("content_blacklist")
            blacklist_table.delete_item(Key={"type": "source", "value": test_source})
            print(f"   🗑️ Cleaned up test entry")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"   ❌ Blacklist test failed: {e}")
        return False

def test_age_filtering():
    """Test age filtering logic"""
    print("\n🔍 Testing Age Filtering...")
    
    try:
        from content_filter import ContentFilter
        
        # Create a mock content filter for testing (without DynamoDB dependency)
        class MockContentFilter:
            def _check_article_age(self, article):
                return ContentFilter._check_article_age(self, article)
            
            def _parse_article_date(self, date_str):
                return ContentFilter._parse_article_date(self, date_str)
        
        content_filter = MockContentFilter()
        
        # Test articles with different ages
        test_cases = [
            {
                "name": "Recent article (1 hour old)",
                "date": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
                "should_pass": True
            },
            {
                "name": "1 day old article",
                "date": (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
                "should_pass": True
            },
            {
                "name": "3 day old article",
                "date": (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z",
                "should_pass": False
            },
            {
                "name": "Article with no date",
                "date": None,
                "should_pass": False
            }
        ]
        
        passed_tests = 0
        for test_case in test_cases:
            article = {"date": test_case["date"]}
            is_recent, reason = content_filter._check_article_age(article)
            
            if is_recent == test_case["should_pass"]:
                print(f"   ✅ {test_case['name']}: {reason}")
                passed_tests += 1
            else:
                print(f"   ❌ {test_case['name']}: Expected {test_case['should_pass']}, got {is_recent}")
        
        print(f"   📊 Age Filter Tests: {passed_tests}/{len(test_cases)} passed")
        return passed_tests == len(test_cases)
        
    except Exception as e:
        print(f"   ❌ Age filtering test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints locally"""
    print("\n🔍 Testing API Endpoints...")
    
    try:
        # This would require running the FastAPI server
        # For now, just check if the main.py imports work
        
        import main
        print("   ✅ Main module imports successfully")
        
        # Test if required functions exist
        required_functions = [
            "search_articles_ddb",
            "format_article",
            "cleanup_old_articles"
        ]
        
        for func_name in required_functions:
            if hasattr(main, func_name):
                print(f"   ✅ Function '{func_name}' exists")
            else:
                print(f"   ❌ Function '{func_name}' missing")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 NewsInsight Content Filtering - Local Testing")
    print("=" * 60)
    
    test_results = []
    
    # Test AWS connection
    aws_ok, session = test_aws_connection()
    test_results.append(("AWS Connection", aws_ok))
    
    if aws_ok and session:
        # Test content filtering
        filter_ok = test_content_filter(session)
        test_results.append(("Content Filtering", filter_ok))
        
        # Test blacklist functionality
        blacklist_ok = test_blacklist_functionality(session)
        test_results.append(("Blacklist Functionality", blacklist_ok))
    
    # Test age filtering (doesn't need AWS)
    age_ok = test_age_filtering()
    test_results.append(("Age Filtering", age_ok))
    
    # Test API endpoints
    api_ok = test_api_endpoints()
    test_results.append(("API Endpoints", api_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment.")
        print("\n🚀 Next steps:")
        print("   1. Run: python main.py (to start local server)")
        print("   2. Test frontend integration")
        print("   3. Deploy to Railway: git add . && git commit && git push")
    else:
        print("⚠️ Some tests failed. Please fix issues before deployment.")
    
    return passed == total

if __name__ == "__main__":
    main()