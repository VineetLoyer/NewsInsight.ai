#!/usr/bin/env python3
import argparse, json, os, sys
from datetime import datetime
import boto3

def parse_args():
    ap = argparse.ArgumentParser(description="Verify NewsInsight ingestion loop")
    ap.add_argument("--table", default="news_metadata", help="DynamoDB table name")
    ap.add_argument("--proc-bucket", required=True, help="Processed S3 bucket name")
    ap.add_argument("--limit", type=int, default=5, help="How many recent items to show")
    ap.add_argument("--id", help="If provided, fetch this specific id's S3 processed JSON")
    return ap.parse_args()

def get_ddb_items(table_name, limit):
    ddb = boto3.resource("dynamodb")
    table = ddb.Table(table_name)
    # For demo simplicity, SCAN then sort by date desc (sufficient for small test volumes)
    resp = table.scan()
    items = resp.get("Items", [])
    # Normalize date for sort
    def key_fn(it):
        # date like '2025-10-18T22:34:07Z'
        try:
            return datetime.strptime(it.get("date","1970-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return datetime.min
    items.sort(key=key_fn, reverse=True)
    return items[:limit]

def get_processed_json(proc_bucket, doc_id):
    s3 = boto3.client("s3")
    key = f"news-processed/{doc_id}.json"
    obj = s3.get_object(Bucket=proc_bucket, Key=key)
    return json.loads(obj["Body"].read())

def main():
    args = parse_args()
    print(f"Table: {args.table}")
    print(f"Processed bucket: {args.proc_bucket}\n")

    if args.id:
        doc = get_processed_json(args.proc_bucket, args.id)
        print(f"# Processed doc {args.id}")
        print(json.dumps(doc, indent=2))
        return

    items = get_ddb_items(args.table, args.limit)
    if not items:
        print("No items found in DynamoDB.")
        return

    print(f"# Latest {len(items)} items in DynamoDB")
    for i, it in enumerate(items, 1):
        line = (
            f"{i:02d}. id={it.get('id')}  src={it.get('source')}  "
            f"date={it.get('date')}  senti={it.get('sentiment')}"
        )
        print(line)

    # Also fetch the first one's processed JSON from S3
    first = items[0]
    doc = get_processed_json(args.proc_bucket, first["id"])
    print("\n# Sample processed JSON from S3")
    print(json.dumps(doc, indent=2))

if __name__ == "__main__":
    sys.exit(main())
