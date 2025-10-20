# agent/newsinsights_agent.py

from __future__ import annotations
import json, os, time, uuid, logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
import requests

# ---------- Config ----------
DEFAULT_REGION = os.getenv("AWS_REGION", "us-west-2")
METADATA_TABLE = os.getenv("METADATA_TABLE", "news_metadata")
TRACE_TABLE    = os.getenv("TRACE_TABLE", "agent_trace")
SSM_MODEL_PARAM = os.getenv("BEDROCK_MODEL_ID_PARAM", "/newsinsights/BEDROCK_MODEL_ID")  # inference profile ARN
WEB_SEARCH_PROVIDER = os.getenv("WEB_SEARCH_PROVIDER", "tavily")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
HTTP_TIMEOUT = (5, 25)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("NewsInsightsAgent")

# ---------- Data Contracts ----------
@dataclass
class InternalRecord:
    id: str
    source: str
    date: str
    summary: str
    sentiment: Optional[str] = None
    verification_score: Optional[float] = None

@dataclass
class EvidenceItem:
    title: str
    url: str
    published_at: Optional[str]
    source: Optional[str]
    snippet: Optional[str]

@dataclass
class AgentOutput:
    topic: str
    summary: str
    confidence: float
    bias: str
    verdict: str
    top_articles: List[Dict[str, Any]]
    external_evidence: List[Dict[str, Any]]
    run_id: str

# ---------- Utils ----------
def _short(s: str, n: int = 7000) -> str:
    return s if len(s) <= n else s[: n - 3] + "..."

def _retryable(fn, retries: int = 3, backoff: float = 1.6):
    def w(*a, **kw):
        delay = 0.8
        last = None
        for _ in range(retries):
            try: return fn(*a, **kw)
            except Exception as e:
                last = e; log.warning("Retryable error: %s", e); time.sleep(delay); delay *= backoff
        raise last
    return w

# ---------- Agent ----------
class NewsInsightsAgent:
    """
    Phase-1 integrated agent:
      1) Read internal processed items from DynamoDB: news_metadata
      2) Bedrock (via SSM inference profile) reasoning on internal summaries
      3) External web search for corroboration
      4) Cross-verify via second Bedrock call
      5) Persist full reasoning trace to DynamoDB: agent_trace
    """

    def __init__(self, region: str = DEFAULT_REGION):
        self.region = region
        self._ddb = boto3.resource("dynamodb", region_name=self.region)
        self._tbl_meta  = self._ddb.Table(METADATA_TABLE)
        self._tbl_trace = self._ddb.Table(TRACE_TABLE)

        self._ssm = boto3.client("ssm", region_name=self.region)
        self._model_id = self._resolve_bedrock_model_id()

        self._bedrock_rt = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            config=Config(retries={"max_attempts": 3, "mode": "adaptive"})
        )

        log.info("Agent ready (region=%s, model=%s, meta=%s, trace=%s)",
                 self.region, self._model_id, METADATA_TABLE, TRACE_TABLE)

    # ----- Public API -----
    def run(self, topic: str) -> AgentOutput:
        run_id = str(uuid.uuid4())
        trace: Dict[str, Any] = {"run_id": run_id, "topic": topic,
                                 "timestamps": {"started_at": int(time.time())}, "steps": []}

        internal = self._query_news_metadata(topic, trace)
        summary, verdict, bias, conf = self._primary_reasoning(topic, internal, trace)
        evidence = self._external_evidence(topic, trace)
        final_verdict, final_conf, final_bias = self._cross_verify(topic, internal, evidence, verdict, trace)

        out = AgentOutput(
            topic=topic, summary=summary or "(no internal summary available)",
            confidence=float(final_conf), bias=final_bias or bias or "unknown",
            verdict=final_verdict or verdict or "Insufficient evidence",
            top_articles=[asdict(r) for r in internal],
            external_evidence=[asdict(e) for e in evidence],
            run_id=run_id
        )

        trace["timestamps"]["ended_at"] = int(time.time())
        trace["output"] = asdict(out)
        self._persist_trace(trace)
        return out

    # ----- Step 1: DynamoDB -> news_metadata -----
    @_retryable
    def _query_news_metadata(self, topic: str, trace: Dict[str, Any]) -> List[InternalRecord]:
        """
        Your Day-1 schema: id, source, date, summary, sentiment, verification_score.
        We don't have a GSI in the snapshot, so we do a constrained Scan and filter in-code.
        (If you later add a GSI on a 'topic' or 'entities' field, switch to .query for efficiency.)
        """
        step = {"name": "query_news_metadata", "topic": topic}
        items: List[Dict[str, Any]] = []
        try:
            resp = self._tbl_meta.scan(Limit=200)
            items.extend(resp.get("Items", []))
            while "LastEvaluatedKey" in resp and len(items) < 600:
                resp = self._tbl_meta.scan(
                    Limit=200, ExclusiveStartKey=resp["LastEvaluatedKey"]
                )
                items.extend(resp.get("Items", []))

            topic_l = topic.lower()
            def keep(d: Dict[str, Any]) -> bool:
                s = (d.get("summary") or "")
                # lightweight keyword match on processed summaries
                return topic_l in s.lower()

            matched = [d for d in items if keep(d)]
            matched = sorted(matched, key=lambda d: d.get("date", ""), reverse=True)[:15]

            recs = [InternalRecord(
                        id=str(d.get("id")),
                        source=str(d.get("source", "")),
                        date=str(d.get("date", "")),
                        summary=str(d.get("summary", "")),
                        sentiment=d.get("sentiment"),
                        verification_score=float(d.get("verification_score", 0.0)) if d.get("verification_score") is not None else None
                    ) for d in matched]

            step["response"] = {"count": len(recs)}
            trace["steps"].append(step)
            return recs

        except (ClientError, BotoCoreError) as e:
            step["error"] = str(e); trace["steps"].append(step); log.exception("DDB scan failed")
            return []

    # ----- Step 2: Bedrock Primary -----
    @_retryable
    def _primary_reasoning(self, topic: str, recs: List[InternalRecord], trace: Dict[str, Any]) -> Tuple[str, str, str, float]:
        step = {"name": "primary_reasoning", "model": self._model_id}
        try:
            bullets = "\n".join(
                f"- [{r.date}] {r.source}: {r.summary}" + (f" (sentiment={r.sentiment})" if r.sentiment else "")
                for r in recs[:10]
            ) or "(no internal items matched)"

            prompt = f"""
You are an impartial news analyst. Use ONLY the internal processed summaries below.

Topic: "{topic}"

Internal items:
{_short(bullets, 7000)}

Tasks:
1) Write a neutral 4–6 sentence synthesis of key facts.
2) Give a one-line 'verdict' on overall factual consistency (e.g., "Mostly consistent", "Conflicting reports", "Insufficient evidence").
3) Provide a confidence score in [0.0, 1.0].
4) Note any observable bias in sources (e.g., "mostly wire-service", "mixed outlets", "regional skew").

Return strict JSON with keys: summary, verdict, confidence, bias.
""".strip()

            body = {
                "modelId": self._model_id,
                "contentType": "application/json",
                "accept": "application/json",
                "inputText": prompt
            }
            resp = self._bedrock_rt.invoke_model(body=json.dumps(body))
            payload = json.loads(resp["body"].read())
            text = payload.get("outputText") or payload.get("results", [{}])[0].get("outputText", "")

            parsed = self._extract_json(text)
            summary = (parsed.get("summary") or "").strip()
            verdict = (parsed.get("verdict") or "Insufficient evidence").strip()
            conf = float(parsed.get("confidence", 0.5))
            bias = (parsed.get("bias") or "unknown").strip()

            step["response"] = {"verdict": verdict, "confidence": conf, "bias": bias, "summary_len": len(summary)}
            trace["steps"].append(step)
            return summary, verdict, bias, conf

        except Exception as e:
            step["error"] = str(e); trace["steps"].append(step); log.exception("Primary reasoning failed")
            return "", "Insufficient evidence", "unknown", 0.45

    # ----- Step 3: External Evidence -----
    @_retryable
    def _external_evidence(self, topic: str, trace: Dict[str, Any]) -> List[EvidenceItem]:
        step = {"name": "external_evidence", "provider": WEB_SEARCH_PROVIDER, "q": topic}
        try:
            res: List[EvidenceItem] = []
            if WEB_SEARCH_PROVIDER == "tavily":
                if not TAVILY_API_KEY: raise RuntimeError("Missing TAVILY_API_KEY")
                r = requests.post("https://api.tavily.com/search",
                                  json={"api_key": TAVILY_API_KEY, "query": topic, "max_results": 6},
                                  timeout=HTTP_TIMEOUT)
                r.raise_for_status()
                data = r.json()
                for it in data.get("results", [])[:6]:
                    res.append(EvidenceItem(
                        title=it.get("title",""), url=it.get("url",""),
                        published_at=it.get("published_date"), source=it.get("source"),
                        snippet=it.get("content")
                    ))
            elif WEB_SEARCH_PROVIDER == "serpapi":
                if not SERPAPI_API_KEY: raise RuntimeError("Missing SERPAPI_API_KEY")
                r = requests.get("https://serpapi.com/search.json",
                                 params={"q": topic, "engine": "google", "api_key": SERPAPI_API_KEY},
                                 timeout=HTTP_TIMEOUT)
                r.raise_for_status()
                data = r.json()
                for it in (data.get("news_results") or data.get("organic_results") or [])[:6]:
                    res.append(EvidenceItem(
                        title=it.get("title",""), url=it.get("link",""),
                        published_at=it.get("date"), source=it.get("source"),
                        snippet=it.get("snippet")
                    ))
            else:
                raise RuntimeError("Unsupported WEB_SEARCH_PROVIDER")

            step["response"] = {"count": len(res)}
            trace["steps"].append(step)
            return res

        except Exception as e:
            step["error"] = str(e); trace["steps"].append(step); log.exception("External evidence failed")
            return []

    # ----- Step 4: Cross-Verify -----
    @_retryable
    def _cross_verify(self, topic: str, recs: List[InternalRecord], ev: List[EvidenceItem],
                      primary_verdict: str, trace: Dict[str, Any]) -> Tuple[str, float, str]:
        step = {"name": "cross_verify", "model": self._model_id}
        try:
            internal = "\n".join(f"- [{r.date}] {r.source}: {r.summary}" for r in recs[:8]) or "(none)"
            external = "\n".join(f"- {e.title} ({e.source}, {e.published_at}) :: {e.snippet or ''} <{e.url}>"
                                 for e in ev[:8]) or "(none)"

            prompt = f"""
You are an adversarial fact-checker.

Topic: "{topic}"

Internal corpus:
{_short(internal, 6000)}

External evidence:
{_short(external, 6000)}

Primary internal verdict: "{primary_verdict}"

Tasks:
1) Say SUPPORTS / PARTIALLY SUPPORTS / CONTRADICTS for the internal verdict.
2) Provide a final one-sentence verdict integrating both sources.
3) Updated confidence in [0.0, 1.0].
4) Brief bias note comparing internal vs external.

Return JSON: {{"support":"...", "verdict":"...", "confidence":0.0, "bias":"..."}}.
""".strip()

            resp = self._bedrock_rt.invoke_model(body=json.dumps({
                "modelId": self._model_id,
                "contentType": "application/json",
                "accept": "application/json",
                "inputText": prompt
            }))
            payload = json.loads(resp["body"].read())
            text = payload.get("outputText") or payload.get("results", [{}])[0].get("outputText", "")

            parsed = self._extract_json(text)
            support = (parsed.get("support") or "PARTIALLY SUPPORTS").upper()
            verdict = parsed.get("verdict", primary_verdict)
            conf = float(parsed.get("confidence", 0.55))
            bias = parsed.get("bias", "mixed")

            if support == "SUPPORTS":       conf = min(1.0, conf + 0.1)
            elif support == "CONTRADICTS":  conf = max(0.0, conf - 0.1)

            step["response"] = {"support": support, "verdict": verdict, "confidence": conf, "bias": bias}
            trace["steps"].append(step)
            return verdict, conf, bias

        except Exception as e:
            step["error"] = str(e); trace["steps"].append(step); log.exception("Cross-verify failed")
            return primary_verdict, 0.5, "unknown"

    # ----- Step 5: Trace -----
    @_retryable
    def _persist_trace(self, trace: Dict[str, Any]) -> None:
        try:
            self._tbl_trace.put_item(Item={
                "run_id": trace["run_id"], "topic": trace["topic"],
                "timestamps": trace.get("timestamps", {}),
                "steps": trace.get("steps", []),
                "output": trace.get("output", {})
            })
        except (ClientError, BotoCoreError) as e:
            log.exception("Trace persist failed: %s", e)

    # ----- Helpers -----
    def _resolve_bedrock_model_id(self) -> str:
        """Reads the Bedrock Inference Profile / modelId from SSM as per Phase-1."""
        try:
            p = self._ssm.get_parameter(Name=SSM_MODEL_PARAM, WithDecryption=False)
            mid = p["Parameter"]["Value"]
            if not mid:
                raise RuntimeError("Empty BEDROCK model id in SSM")
            return mid
        except Exception as e:
            log.error("Unable to read %s: %s", SSM_MODEL_PARAM, e)
            raise

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        try: return json.loads(text.strip())
        except Exception: pass
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1 and e > s:
            try: return json.loads(text[s:e+1])
            except Exception: return {}
        return {}

if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "global tech layoffs"
    agent = NewsInsightsAgent()
    print(json.dumps(asdict(agent.run(topic)), indent=2))
