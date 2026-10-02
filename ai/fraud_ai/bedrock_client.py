"""One wrapper around the Bedrock Converse API. Owner: Thomas.

- Model IDs come from MODEL_ID and FALLBACK_MODEL_ID (set in infra/template.yaml).
- Opus 5 sends a reasoning block before its answer, so we read only blocks with "text".
- One retry on the main model, then one try on the fallback.
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

_client = None


def _bedrock():
    global _client
    if _client is None:
        _client = boto3.client(
            "bedrock-runtime",
            region_name=REGION,
            config=Config(read_timeout=25, retries={"max_attempts": 1}),
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
    for model_id in (MODEL_ID, MODEL_ID, FALLBACK_MODEL_ID):
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


def converse_json(prompt, system=None, max_tokens=2000):
    """Like converse, but parses the answer as a JSON object. Tolerates ```json fences."""
    text = converse(prompt, system=system, max_tokens=max_tokens)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object in Claude's answer: {text[:200]}")
    return json.loads(match.group(0))
