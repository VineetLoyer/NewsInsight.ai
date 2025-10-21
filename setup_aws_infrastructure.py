#!/usr/bin/env python3
"""
AWS Infrastructure Setup for NewsInsight
Creates DynamoDB tables, S3 buckets, and sets up content filtering
"""

import os
import json
import boto3
import time
from datetime import datetime
from botocore.exceptions import ClientError

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class AWSInfrastructureSetup:
    def __init__(self):
        self.aws_region = os.getenv("AWS_REGION", "us-west-2")
        self.account_id = None
        
        # Initialize AWS clients
        try:
            self.session = boto3.Session(region_name=self.aws_region)
            self.ddb = self.session.resource("dynamodb")
            self.s3 = self.session.client("s3")
            self.sts = self.session.client("sts")
            
            # Get account ID
            identity = self.sts.get_caller_identity()
            self.account_id = identity["Account"]
            print(f"✅ AWS Session initialized - Account: {self.account_id}, Region: {self.aws_region}")
            
        except Exception as e:
            print(f"❌ AWS initialization failed: {e}")
            raise

    def create_dynamodb_tables(self):
        """Create all required DynamoDB tables"""
        
        tables_config = [
            {
                "name": "news_metadata",
                "description": "Main news articles storage",
                "key_schema": [
                    {"AttributeName": "id", "KeyType": "HASH"}
                ],
                "attribute_definitions": [
                    {"AttributeName": "id", "AttributeType": "S"}
                ],
                "global_secondary_indexes": [
                    {
                        "IndexName": "source-date-index",
                        "KeySchema": [
                            {"AttributeName": "source", "KeyType": "HASH"},
                            {"AttributeName": "date", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ],
                "additional_attributes": [
                    {"AttributeName": "source", "AttributeType": "S"},
                    {"AttributeName": "date", "AttributeType": "S"}
                ]
            },
            {
                "name": "content_blacklist",
                "description": "Content filtering blacklist",
                "key_schema": [
                    {"AttributeName": "type", "KeyType": "HASH"},
                    {"AttributeName": "value", "KeyType": "RANGE"}
                ],
                "attribute_definitions": [
                    {"AttributeName": "type", "AttributeType": "S"},
                    {"AttributeName": "value", "AttributeType": "S"}
                ]
            },
            {
                "name": "content_review_queue",
                "description": "Articles pending manual review",
                "key_schema": [
                    {"AttributeName": "id", "KeyType": "HASH"}
                ],
                "attribute_definitions": [
                    {"AttributeName": "id", "AttributeType": "S"}
                ]
            }
        ]
        
        created_tables = []
        
        for table_config in tables_config:
            table_name = table_config["name"]
            
            try:
                # Check if table exists
                existing_table = self.ddb.Table(table_name)
                existing_table.load()
                print(f"✅ Table '{table_name}' already exists")
                created_tables.append(table_name)
                continue
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceNotFoundException':
                    print(f"❌ Error checking table '{table_name}': {e}")
                    continue
            
            # Create table
            print(f"🔨 Creating table '{table_name}'...")
            
            create_params = {
                "TableName": table_name,
                "KeySchema": table_config["key_schema"],
                "AttributeDefinitions": table_config["attribute_definitions"],
                "BillingMode": "PAY_PER_REQUEST"
            }
            
            # Add additional attributes for GSI
            if "additional_attributes" in table_config:
                create_params["AttributeDefinitions"].extend(table_config["additional_attributes"])
            
            # Add Global Secondary Indexes
            if "global_secondary_indexes" in table_config:
                create_params["GlobalSecondaryIndexes"] = []
                for gsi in table_config["global_secondary_indexes"]:
                    gsi_config = {
                        "IndexName": gsi["IndexName"],
                        "KeySchema": gsi["KeySchema"],
                        "Projection": gsi["Projection"]
                    }
                    create_params["GlobalSecondaryIndexes"].append(gsi_config)
            
            try:
                table = self.ddb.create_table(**create_params)
                print(f"   ⏳ Waiting for table '{table_name}' to be created...")
                table.wait_until_exists()
                print(f"   ✅ Table '{table_name}' created successfully")
                created_tables.append(table_name)
                
            except Exception as e:
                print(f"   ❌ Failed to create table '{table_name}': {e}")
        
        return created_tables

    def create_s3_buckets(self):
        """Create S3 buckets for article storage"""
        
        bucket_configs = [
            {
                "name": f"newsinsights-processed-{self.account_id}-{self.aws_region}",
                "description": "Processed articles storage"
            },
            {
                "name": f"newsinsights-raw-{self.account_id}-{self.aws_region}",
                "description": "Raw articles backup"
            }
        ]
        
        created_buckets = []
        
        for bucket_config in bucket_configs:
            bucket_name = bucket_config["name"]
            
            try:
                # Check if bucket exists
                self.s3.head_bucket(Bucket=bucket_name)
                print(f"✅ Bucket '{bucket_name}' already exists")
                created_buckets.append(bucket_name)
                continue
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code != '404':
                    print(f"❌ Error checking bucket '{bucket_name}': {e}")
                    continue
            
            # Create bucket
            print(f"🪣 Creating S3 bucket '{bucket_name}'...")
            
            try:
                if self.aws_region == "us-east-1":
                    # us-east-1 doesn't need LocationConstraint
                    self.s3.create_bucket(Bucket=bucket_name)
                else:
                    self.s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                    )
                
                # Set bucket versioning
                self.s3.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                # Set lifecycle policy to delete old versions
                lifecycle_config = {
                    'Rules': [
                        {
                            'ID': 'DeleteOldVersions',
                            'Status': 'Enabled',
                            'NoncurrentVersionExpiration': {'NoncurrentDays': 30}
                        }
                    ]
                }
                
                self.s3.put_bucket_lifecycle_configuration(
                    Bucket=bucket_name,
                    LifecycleConfiguration=lifecycle_config
                )
                
                print(f"   ✅ Bucket '{bucket_name}' created successfully")
                created_buckets.append(bucket_name)
                
            except Exception as e:
                print(f"   ❌ Failed to create bucket '{bucket_name}': {e}")
        
        return created_buckets

    def setup_content_blacklist(self):
        """Populate initial content blacklist"""
        
        try:
            blacklist_table = self.ddb.Table("content_blacklist")
            
            # Initial blacklist data
            initial_blacklist = [
                # Low credibility sources
                {"type": "source", "value": "buzzfeed", "reason": "Entertainment/clickbait"},
                {"type": "source", "value": "clickhole", "reason": "Satire"},
                {"type": "source", "value": "theonion", "reason": "Satire"},
                {"type": "source", "value": "babylonbee", "reason": "Satire"},
                {"type": "source", "value": "infowars", "reason": "Low credibility"},
                {"type": "source", "value": "naturalnews", "reason": "Low credibility"},
                
                # Ad networks and promotional domains
                {"type": "domain", "value": "ads.yahoo.com", "reason": "Ad network"},
                {"type": "domain", "value": "googleads.com", "reason": "Ad network"},
                {"type": "domain", "value": "doubleclick.net", "reason": "Ad network"},
                {"type": "domain", "value": "taboola.com", "reason": "Content recommendation ads"},
                {"type": "domain", "value": "outbrain.com", "reason": "Content recommendation ads"},
                
                # Spam keywords
                {"type": "keyword", "value": "sponsored content", "reason": "Promotional"},
                {"type": "keyword", "value": "paid promotion", "reason": "Promotional"},
                {"type": "keyword", "value": "affiliate link", "reason": "Promotional"},
                {"type": "keyword", "value": "click here to buy", "reason": "Promotional"},
                {"type": "keyword", "value": "limited time offer", "reason": "Promotional"},
            ]
            
            print("📝 Setting up initial content blacklist...")
            
            added_count = 0
            for item in initial_blacklist:
                try:
                    # Check if item already exists
                    response = blacklist_table.get_item(
                        Key={"type": item["type"], "value": item["value"]}
                    )
                    
                    if "Item" not in response:
                        # Add timestamp
                        item["added_date"] = datetime.utcnow().isoformat()
                        item["added_by"] = "setup_script"
                        
                        blacklist_table.put_item(Item=item)
                        added_count += 1
                        
                except Exception as e:
                    print(f"   ⚠️ Failed to add blacklist item {item}: {e}")
            
            print(f"   ✅ Added {added_count} items to content blacklist")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup content blacklist: {e}")
            return False

    def update_env_file(self, created_buckets):
        """Update .env file with created resource names"""
        
        if not created_buckets:
            print("⚠️ No buckets created, skipping .env update")
            return
        
        try:
            # Read current .env file
            env_updates = {}
            
            if created_buckets:
                processed_bucket = next((b for b in created_buckets if "processed" in b), None)
                raw_bucket = next((b for b in created_buckets if "raw" in b), None)
                
                if processed_bucket:
                    env_updates["PROC_BUCKET"] = processed_bucket
                if raw_bucket:
                    env_updates["RAW_BUCKET"] = raw_bucket
            
            if env_updates:
                print("📝 Updating .env file with new resource names...")
                
                # Read existing .env
                env_lines = []
                if os.path.exists(".env"):
                    with open(".env", "r") as f:
                        env_lines = f.readlines()
                
                # Update or add new values
                updated_keys = set()
                for i, line in enumerate(env_lines):
                    for key, value in env_updates.items():
                        if line.startswith(f"{key}="):
                            env_lines[i] = f"{key}={value}\n"
                            updated_keys.add(key)
                            break
                
                # Add new keys that weren't found
                for key, value in env_updates.items():
                    if key not in updated_keys:
                        env_lines.append(f"{key}={value}\n")
                
                # Write back to .env
                with open(".env", "w") as f:
                    f.writelines(env_lines)
                
                print(f"   ✅ Updated .env with: {', '.join(env_updates.keys())}")
            
        except Exception as e:
            print(f"❌ Failed to update .env file: {e}")

    def run_setup(self):
        """Run complete infrastructure setup"""
        
        print("🚀 Starting AWS Infrastructure Setup for NewsInsight")
        print("=" * 60)
        
        # Create DynamoDB tables
        print("\n📊 Setting up DynamoDB tables...")
        created_tables = self.create_dynamodb_tables()
        
        # Create S3 buckets
        print("\n🪣 Setting up S3 buckets...")
        created_buckets = self.create_s3_buckets()
        
        # Setup content blacklist
        if "content_blacklist" in created_tables:
            print("\n🚫 Setting up content blacklist...")
            self.setup_content_blacklist()
        
        # Update .env file
        print("\n📝 Updating configuration...")
        self.update_env_file(created_buckets)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ AWS Infrastructure Setup Complete!")
        print(f"📊 DynamoDB Tables: {len(created_tables)} created/verified")
        print(f"🪣 S3 Buckets: {len(created_buckets)} created/verified")
        print(f"🌍 Region: {self.aws_region}")
        print(f"👤 Account: {self.account_id}")
        
        if created_tables:
            print(f"\nDynamoDB Tables:")
            for table in created_tables:
                print(f"   - {table}")
        
        if created_buckets:
            print(f"\nS3 Buckets:")
            for bucket in created_buckets:
                print(f"   - {bucket}")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Test locally: python test_content_filtering.py")
        print(f"   2. Run backend: python main.py")
        print(f"   3. Deploy to Railway after testing")

def main():
    """Main setup function"""
    try:
        setup = AWSInfrastructureSetup()
        setup.run_setup()
        
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("Please check your AWS credentials and try again")

if __name__ == "__main__":
    main()