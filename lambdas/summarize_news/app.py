import os, json, boto3,re
from datetime import datetime, timezone
from decimal import Decimal

s3  = boto3.client("s3")
ssm = boto3.client("ssm")
bed = boto3.client("bedrock-runtime")

RAW_PREFIX = "news-raw/"
PROCESSED_PREFIX = "news-processed/"

ddb = boto3.resource("dynamodb")
TABLE_NAME=os.environ.get("TABLE_NAME","news_metadata")


def _get_param(name: str) -> str:
    return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]

def _get_obj(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read())

def _put_json(bucket, key, payload):
    s3.put_object(
        Bucket=bucket, Key=key,
        Body=json.dumps(payload, indent=2).encode("utf-8"),
        ContentType="application/json"
    )

def _summarize(model_id: str, text: str) -> str:
    """
    Supports:
      - Anthropic via model ID or inference profile ARN (set MODEL_FAMILY=anthropic)
      - Amazon Nova/Titan via model ID or inference profile ARN (set MODEL_FAMILY=amazon)
    """
    text = text or ""
    family = os.environ.get("MODEL_FAMILY", "").lower()

    if family == "anthropic":
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": f"Summarize the following news article in 3–5 concise bullet points:\n\n{text}"}]
            }]
        }
        resp = bed.invoke_model(modelId=model_id, body=json.dumps(body))
        payload = json.loads(resp["body"].read())
        out = []
        for b in payload.get("content", []):
            if b.get("type") == "text":
                out.append(b.get("text", ""))
        return ("\n".join(out)).strip() or json.dumps(payload)

    # default to Amazon Nova/Titan-style schema
    body = {
        "inputText": "Summarize the following news article in 3–5 concise bullet points.\n\n" + text,
        "textGenerationConfig": {"maxTokenCount": 512, "temperature": 0.3, "topP": 0.9}
    }
    resp = bed.invoke_model(modelId=model_id, body=json.dumps(body))
    payload = json.loads(resp["body"].read())
    if isinstance(payload, dict) and payload.get("results"):
        return payload["results"][0].get("outputText", "").strip() or json.dumps(payload)
    return (payload.get("outputText", "") or payload.get("generation", "") or json.dumps(payload)).strip()


# Prev working version before (extract metadata phase 2)
# def handler(event, context):
#     raw_bucket       = os.environ["RAW_BUCKET"]
#     processed_bucket = os.environ["PROCESSED_BUCKET"]
#     model_id         = _get_param(os.environ["BEDROCK_MODEL_ID_PARAM"])

#     for rec in event.get("Records", []):
#         key = rec["s3"]["object"]["key"]
#         if not key.startswith(RAW_PREFIX):
#             continue

#         article = _get_obj(raw_bucket, key)
#         text = article.get("content") or article.get("description") or article.get("headline") or ""
#         summary = _summarize(model_id, text)

#         # write processed JSON (summary + passthrough metadata)
#         doc_id = key.split("/")[-1].split(".")[0]
#         out = {
#             "id": doc_id,
#             "source": article.get("source","unknown"),
#             "headline": article.get("headline"),
#             "date": article.get("date"),   # keep as-is for now; DDB comes later
#             "summary": summary,
#             "ingested_at": datetime.now(timezone.utc).isoformat()
#         }
#         _put_json(processed_bucket, f"{PROCESSED_PREFIX}{doc_id}.json", out)

#     return {"status":"ok"}

# New version ~ Phase 2: extract metadata from extracted content

SYSTEM_JSON_INSTRUCTIONS = (
    "You are a structured information extractor. "
    "Return ONLY valid JSON, no markdown, with this exact schema: "
    "{"
    "\"summary\": string, "
    "\"sentiment\": one of [\"positive\",\"neutral\",\"negative\"], "
    "\"entities\": [ {\"type\": string, \"text\": string} ]"
    "}. "
    "Notes: keep summary to 3-5 bullets joined by \\n; "
    "entities should include people, orgs, locations, products, events if present; "
    "Do not add extra fields."
)

def _analyze_with_bedrock(model_id: str, model_family: str, text: str) -> dict:
    """Call Bedrock to produce JSON {summary, sentiment, entities[]}."""
    text = text or ""
    # Build request payload by family
    if model_family == "anthropic":
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 800,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_JSON_INSTRUCTIONS},
                        {"type": "text", "text": f"ARTICLE:\n{text}"}
                    ]
                }
            ]
        }
    else:  # amazon nova/titan style
        body = {
            "inputText": SYSTEM_JSON_INSTRUCTIONS + "\n\nARTICLE:\n" + text,
            "textGenerationConfig": {"maxTokenCount": 800, "temperature": 0.2, "topP": 0.9}
        }

    resp = bed.invoke_model(modelId=model_id, body=json.dumps(body))
    payload = json.loads(resp["body"].read())

    # Extract model text by family
    if model_family == "anthropic":
        chunks = []
        for blk in payload.get("content", []):
            if blk.get("type") == "text":
                chunks.append(blk.get("text", ""))
        model_text = "\n".join(chunks).strip()
    else:
        # Nova/Titan: results[0].outputText
        model_text = ""
        if isinstance(payload, dict):
            if payload.get("results"):
                model_text = (payload["results"][0].get("outputText") or "").strip()
            else:
                # Some variants may return outputText directly
                model_text = (payload.get("outputText") or payload.get("generation") or "").strip()

    # Clean to JSON (strip code fences if any)
    model_text = re.sub(r"^```(?:json)?|```$", "", model_text, flags=re.MULTILINE).strip()
    try:
        data = json.loads(model_text)
    except Exception:
        # Fallback minimal structure if model returned non-JSON
        data = {"summary": model_text[:1000], "sentiment": "neutral", "entities": []}

    # Normalize fields
    if not isinstance(data.get("entities"), list):
        data["entities"] = []
    if data.get("sentiment") not in ("positive", "neutral", "negative"):
        data["sentiment"] = "neutral"
    data["summary"] = (data.get("summary") or "").strip()

    return data

def handler(event, context):
    raw_bucket       = os.environ["RAW_BUCKET"]
    processed_bucket = os.environ["PROCESSED_BUCKET"]
    model_id         = _get_param(os.environ["BEDROCK_MODEL_ID_PARAM"])
    family           = os.environ.get("MODEL_FAMILY", "anthropic").lower()

    for rec in event.get("Records", []):
        key = rec["s3"]["object"]["key"]
        if not key.startswith(RAW_PREFIX):
            continue

        article = _get_obj(raw_bucket, key)
        # Pass-through fields from raw
        headline = article.get("headline")
        date     = article.get("date")
        text     = article.get("content") or article.get("description") or headline or ""

        analysis = _analyze_with_bedrock(model_id, family, text)

        # Compose processed record
        doc_id = key.split("/")[-1].split(".")[0]
        out = {
            "id": doc_id,
            "source": article.get("source", "unknown"),
            "headline": headline,
            "date": date,
            "summary": analysis.get("summary"),
            "sentiment": analysis.get("sentiment"),
            "entities": analysis.get("entities"),
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }

        _put_json(processed_bucket, f"{PROCESSED_PREFIX}{doc_id}.json", out)
        # inside handler(...) after you build `out` and write to S3:
        table = ddb.Table(TABLE_NAME)
        item = {
            "id": out["id"],
            "source": out.get("source","unknown"),
            "date": out.get("date"),
            "summary": out.get("summary",""),
            "sentiment": out.get("sentiment","neutral"),
            "verification_score": Decimal("0")
        }
        table.put_item(Item=item)
    return {"status": "ok"}