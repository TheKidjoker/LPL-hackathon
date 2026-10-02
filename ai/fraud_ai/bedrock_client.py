"""One wrapper around the Bedrock Converse API. Owner: Thomas.

- Model IDs come from MODEL_ID and FALLBACK_MODEL_ID (set in infra/template.yaml).
- Opus 5 sends a reasoning block before its answer, so we read only blocks with "text".
- One try on the main model, then one on the fallback, each capped at 13 seconds, so a
  request always finishes inside API Gateway's 29-second limit.
"""

import json
import logging
import os
import re

import boto3
from botocore.config import Config

logger = logging.getLogger()

MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-opus-5")
FALLBACK_MODEL_ID = os.environ.get("FALLBACK_MODEL_ID", "us.anthropic.claude-sonnet-5")
REGION = os.environ.get("AWS_REGION", "us-east-1")
# Bedrock Guardrails from infra/template.yaml. Unset locally, in which case both checks are no-ops.
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "")  # masks identity and account numbers in AI output
GUARDRAIL_VERSION = os.environ.get("GUARDRAIL_VERSION", "DRAFT")
QUESTION_GUARDRAIL_ID = os.environ.get("QUESTION_GUARDRAIL_ID", "")  # refuses investment-advice questions
QUESTION_GUARDRAIL_VERSION = os.environ.get("QUESTION_GUARDRAIL_VERSION", "DRAFT")

_client = None


def _bedrock():
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-runtime",
            region_name=REGION,
            config=Config(read_timeout=13, connect_timeout=3, retries={"max_attempts": 1, "mode": "standard"}),
        )
    return _client


def converse(prompt, system=None, max_tokens=2000):
    """Send one user message and return Claude's text answer."""
    request = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    if system:
        request["system"] = [{"text": system}]

    last_error = None
    for model_id in (MODEL_ID, FALLBACK_MODEL_ID):
        try:
            resp = _bedrock().converse(modelId=model_id, **request)
            blocks = resp["output"]["message"]["content"]
            text = "".join(b["text"] for b in blocks if "text" in b).strip()
            if text:
                return text
            last_error = RuntimeError(f"{model_id} returned no text (stopReason={resp.get('stopReason')})")
        except Exception as e:
            last_error = e
        logger.warning("Bedrock call to %s failed: %s", model_id, last_error)
    raise last_error


def guard_output(text):
    """Mask identity and account numbers in text the AI wrote, before anyone sees it.

    Only masking runs on output. Blocking by topic would also block memos that describe
    an investment scam, which are exactly the cases we need to explain. If the guardrail
    call itself fails, the text passes through and the failure is logged, so a guardrail
    outage never blocks a fraud hold.
    """
    if not GUARDRAIL_ID or not text:
        return text
    try:
        resp = _bedrock().apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source="OUTPUT",
            content=[{"text": {"text": text}}],
        )
    except Exception as e:
        logger.warning("Guardrail check failed, passing text through: %s", e)
        return text
    if resp.get("action") != "GUARDRAIL_INTERVENED":
        return text
    logger.info("Guardrail intervened: %s", json.dumps(resp.get("assessments", []), default=str)[:500])
    outputs = resp.get("outputs") or []
    return "".join(o.get("text", "") for o in outputs).strip() or text


def blocked_question(text):
    """Return the refusal message if a staff question asks for investment advice, else None.

    Runs before any model call, on the question only (never on case data or client answers,
    which often describe investment pitches as evidence). Fails open if the guardrail is down.
    """
    if not QUESTION_GUARDRAIL_ID or not text:
        return None
    try:
        resp = _bedrock().apply_guardrail(
            guardrailIdentifier=QUESTION_GUARDRAIL_ID,
            guardrailVersion=QUESTION_GUARDRAIL_VERSION,
            source="INPUT",
            content=[{"text": {"text": text}}],
        )
    except Exception as e:
        logger.warning("Question guardrail check failed, allowing the question: %s", e)
        return None
    if resp.get("action") != "GUARDRAIL_INTERVENED":
        return None
    return "".join(o.get("text", "") for o in resp.get("outputs") or []).strip() or "Juno can't give investment advice."


def converse_json(prompt, system=None, max_tokens=2000):
    """Like converse, but parses the answer as a JSON object. Tolerates ```json fences."""
    text = converse(prompt, system=system, max_tokens=max_tokens)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object in Claude's answer: {text[:200]}")
    return json.loads(match.group(0))
