#!/usr/bin/env python3
"""
Content Quality Filtering System for NewsInsight
Multi-layer filtering to ensure high-quality news content
"""

import os
import re
import json
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

class ContentFilter:
    def __init__(self, session: boto3.Session):
        self.ddb = session.resource("dynamodb")
        self.blacklist_table = self.ddb.Table("content_blacklist")
        
        # Content quality thresholds
        self.MIN_WORDS = 200
        self.MAX_WORDS = 10000
        self.MIN_QUALITY_SCORE = 70
        
        # Known low-quality indicators
        self.SPAM_KEYWORDS = [
            "click here", "limited time", "act now", "free trial",
            "make money", "work from home", "get rich", "miracle cure"
        ]
        
        self.AD_INDICATORS = [
            "sponsored", "advertisement", "promoted", "paid content",
            "affiliate", "partner content", "brand story"
        ]

    def preprocess_filter(self, article: Dict) -> Tuple[bool, str]:
        """
        Layer 1: Basic preprocessing filters
        Returns: (should_process, rejection_reason)
        """
        
        # Age filter (check first - fastest)
        is_recent, age_reason = self._check_article_age(article)
        if not is_recent:
            return False, age_reason
        
        # Extract text content
        content = self._get_article_text(article)
        word_count = len(content.split()) if content else 0
        
        # Word count filter
        if word_count < self.MIN_WORDS:
            return False, f"Too short: {word_count} words (min: {self.MIN_WORDS})"
        
        if word_count > self.MAX_WORDS:
            return False, f"Too long: {word_count} words (max: {self.MAX_WORDS})"
        
        # Source blacklist check
        source = article.get("source", "").lower()
        if self._is_blacklisted("source", source):
            return False, f"Blacklisted source: {source}"
        
        # Domain blacklist check
        url = article.get("url", "")
        domain = self._extract_domain(url)
        if domain and self._is_blacklisted("domain", domain):
            return False, f"Blacklisted domain: {domain}"
        
        # Basic spam detection
        title = article.get("headline", "").lower()
        if any(spam in title for spam in self.SPAM_KEYWORDS):
            return False, "Contains spam keywords"
        
        return True, "Passed preprocessing"

    def ai_classify_content(self, article: Dict, bedrock_client) -> Dict:
        """
        Layer 2: AI-powered content classification
        Returns classification results with quality score
        """
        
        content = self._get_article_text(article)
        
        # Enhanced prompt for content classification
        classification_prompt = f"""
        Analyze this article and provide a JSON response with content classification:
        
        {{
            "category": "news_article|advertisement|opinion_piece|press_release|clickbait|duplicate|low_quality|spam",
            "quality_score": 0-100,
            "credibility_indicators": {{
                "has_sources": true/false,
                "has_quotes": true/false,
                "factual_tone": true/false,
                "proper_attribution": true/false
            }},
            "content_flags": [
                "promotional_language",
                "sensationalized_headline", 
                "missing_attribution",
                "poor_grammar",
                "duplicate_content"
            ],
            "recommendation": "accept|review|reject",
            "reasoning": "Brief explanation of classification"
        }}
        
        Article Title: {article.get('headline', '')}
        Article Content: {content[:2000]}
        Source: {article.get('source', '')}
        """
        
        try:
            # Call Bedrock for classification
            response = self._call_bedrock_classification(bedrock_client, classification_prompt)
            return json.loads(response)
        except Exception as e:
            print(f"AI classification failed: {e}")
            return {
                "category": "unknown",
                "quality_score": 50,
                "recommendation": "review",
                "reasoning": f"Classification failed: {e}"
            }

    def should_store_article(self, classification: Dict) -> Tuple[str, str]:
        """
        Determine storage destination based on classification
        Returns: (storage_location, reason)
        """
        
        quality_score = classification.get("quality_score", 0)
        category = classification.get("category", "unknown")
        recommendation = classification.get("recommendation", "review")
        
        # High quality - store in main database
        if quality_score >= 70 and category == "news_article" and recommendation == "accept":
            return "news_metadata", "High quality news article"
        
        # Medium quality - queue for review
        elif quality_score >= 50 and recommendation in ["accept", "review"]:
            return "content_review_queue", "Needs human review"
        
        # Low quality - reject but keep for analysis
        else:
            return "content_rejected", f"Low quality: {classification.get('reasoning', 'Unknown')}"

    def add_to_blacklist(self, item_type: str, value: str, reason: str = ""):
        """Add item to blacklist"""
        try:
            self.blacklist_table.put_item(
                Item={
                    "type": item_type,
                    "value": value.lower(),
                    "reason": reason,
                    "added_date": datetime.utcnow().isoformat(),
                    "added_by": "system"
                }
            )
            print(f"✅ Added to blacklist: {item_type}={value}")
        except Exception as e:
            print(f"❌ Failed to add to blacklist: {e}")

    def _is_blacklisted(self, item_type: str, value: str) -> bool:
        """Check if item is blacklisted"""
        try:
            response = self.blacklist_table.get_item(
                Key={"type": item_type, "value": value.lower()}
            )
            return "Item" in response
        except Exception as e:
            print(f"Blacklist check failed: {e}")
            return False

    def _get_article_text(self, article: Dict) -> str:
        """Extract text content from article"""
        content_fields = ["content", "description", "summary", "headline", "title"]
        text_parts = []
        
        for field in content_fields:
            if article.get(field):
                text_parts.append(str(article[field]))
        
        return " ".join(text_parts)

    def _check_article_age(self, article: Dict) -> Tuple[bool, str]:
        """
        Check if article is within acceptable age limit (2 days)
        Returns: (is_recent, reason)
        """
        MAX_AGE_DAYS = 2
        
        # Get article date
        article_date_str = article.get("date") or article.get("publishedAt") or article.get("webPublicationDate")
        
        if not article_date_str:
            return False, "No publication date found"
        
        try:
            # Parse article date (handle multiple formats)
            article_date = self._parse_article_date(article_date_str)
            if not article_date:
                return False, f"Invalid date format: {article_date_str}"
            
            # Calculate age
            now = datetime.utcnow()
            age_delta = now - article_date
            age_days = age_delta.total_seconds() / (24 * 3600)
            
            if age_days > MAX_AGE_DAYS:
                return False, f"Too old: {age_days:.1f} days (max: {MAX_AGE_DAYS} days)"
            
            return True, f"Recent: {age_days:.1f} days old"
            
        except Exception as e:
            return False, f"Date parsing error: {e}"
    
    def _parse_article_date(self, date_str: str) -> Optional[datetime]:
        """Parse article date from various formats"""
        if not date_str:
            return None
        
        # Common date formats from news APIs
        date_formats = [
            "%Y-%m-%dT%H:%M:%SZ",           # 2024-10-21T14:30:00Z (ISO format)
            "%Y-%m-%dT%H:%M:%S.%fZ",        # 2024-10-21T14:30:00.123Z (with microseconds)
            "%Y-%m-%dT%H:%M:%S%z",          # 2024-10-21T14:30:00+00:00 (with timezone)
            "%Y-%m-%d %H:%M:%S",            # 2024-10-21 14:30:00
            "%Y-%m-%d",                     # 2024-10-21
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try parsing with dateutil as fallback
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            # Convert to UTC if timezone-aware
            if parsed_date.tzinfo:
                parsed_date = parsed_date.utctimetuple()
                parsed_date = datetime(*parsed_date[:6])
            return parsed_date
        except:
            pass
        
        return None

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            import re
            match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            return match.group(1) if match else None
        except:
            return None

    def _call_bedrock_classification(self, bedrock_client, prompt: str) -> str:
        """Call Bedrock for content classification"""
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }]
        }
        
        model_id = os.getenv("BEDROCK_MODEL_ID")
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

# Pre-defined blacklists to get started
INITIAL_BLACKLIST = {
    "sources": [
        "buzzfeed", "clickhole", "theonion", "babylonbee",  # Satire/entertainment
        "infowars", "breitbart", "naturalnews",  # Low credibility
        "taboola", "outbrain", "revcontent"  # Ad networks
    ],
    "domains": [
        "ads.yahoo.com", "googleads.com", "doubleclick.net",
        "facebook.com/tr", "analytics.google.com"
    ],
    "keywords": [
        "sponsored content", "paid promotion", "advertisement",
        "affiliate link", "click here to buy"
    ]
}

def setup_blacklist_table(session: boto3.Session):
    """Create and populate initial blacklist table"""
    
    ddb = session.resource("dynamodb")
    
    # Create table if it doesn't exist
    try:
        table = ddb.create_table(
            TableName="content_blacklist",
            KeySchema=[
                {"AttributeName": "type", "KeyType": "HASH"},
                {"AttributeName": "value", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "type", "AttributeType": "S"},
                {"AttributeName": "value", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Wait for table to be created
        table.wait_until_exists()
        print("✅ Created content_blacklist table")
        
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print("✅ content_blacklist table already exists")
        else:
            print(f"❌ Failed to create blacklist table: {e}")
            return
    
    # Populate with initial blacklist
    content_filter = ContentFilter(session)
    
    for source in INITIAL_BLACKLIST["sources"]:
        content_filter.add_to_blacklist("source", source, "Low credibility/satire")
    
    for domain in INITIAL_BLACKLIST["domains"]:
        content_filter.add_to_blacklist("domain", domain, "Ad network")
    
    for keyword in INITIAL_BLACKLIST["keywords"]:
        content_filter.add_to_blacklist("keyword", keyword, "Promotional content")

if __name__ == "__main__":
    # Test the content filter
    import boto3
    
    session = boto3.Session(region_name="us-west-2")
    setup_blacklist_table(session)

def ingest_topic_with_filtering(topic: str, content_filter: ContentFilter, bedrock_client) -> Dict[str, int]:
    """Enhanced ingestion with comprehensive content filtering"""
    
    stats = {
        "fetched": 0,
        "age_rejected": 0,        # Articles older than 2 days
        "word_count_rejected": 0,
        "blacklist_rejected": 0,
        "spam_rejected": 0,
        "ai_rejected": 0,
        "processed": 0,
        "stored": 0
    }
    
    # Fetch raw articles from APIs
    articles = fetch_articles_from_apis(topic)  # Your existing function
    stats["fetched"] = len(articles)
    
    print(f"📥 Processing {len(articles)} articles for topic: {topic}")
    
    for i, article in enumerate(articles):
        print(f"📄 Processing article {i+1}/{len(articles)}: {article.get('headline', 'No title')[:50]}...")
        
        # Layer 1: Preprocessing filters
        should_process, reason = content_filter.preprocess_filter(article)
        if not should_process:
            # Categorize rejection reason
            if "Too old" in reason or "days" in reason:
                stats["age_rejected"] += 1
            elif "Too short" in reason or "Too long" in reason:
                stats["word_count_rejected"] += 1
            elif "Blacklisted" in reason:
                stats["blacklist_rejected"] += 1
            elif "spam" in reason.lower():
                stats["spam_rejected"] += 1
            
            print(f"   🚫 L1 Reject: {reason}")
            continue
        
        # Layer 2: AI legitimacy check
        ai_classification = content_filter.ai_classify_content(article, bedrock_client)
        if ai_classification.get("category") != "news_article":
            stats["ai_rejected"] += 1
            print(f"   🤖 L2 Reject: {ai_classification.get('reasoning', 'Not legitimate news')}")
            continue
        
        # Process legitimate, recent article
        stats["processed"] += 1
        print(f"   ✅ Processing legitimate article")
        
        # Your existing sentiment analysis and storage
        # text = get_article_text(article)
        # analysis = analyze_with_bedrock(text)
        # doc_id = store_processed_article(article, analysis)
        # if doc_id:
        #     stats["stored"] += 1
    
    # Print summary
    print(f"\n📊 Ingestion Summary for '{topic}':")
    print(f"   📥 Fetched: {stats['fetched']}")
    print(f"   🕒 Age rejected: {stats['age_rejected']} ({stats['age_rejected']/stats['fetched']*100:.1f}%)")
    print(f"   📝 Word count rejected: {stats['word_count_rejected']}")
    print(f"   🚫 Blacklist rejected: {stats['blacklist_rejected']}")
    print(f"   🗑️ Spam rejected: {stats['spam_rejected']}")
    print(f"   🤖 AI rejected: {stats['ai_rejected']}")
    print(f"   ✅ Processed: {stats['processed']}")
    print(f"   💾 Stored: {stats['stored']}")
    
    return stats