"""Run one Lambda handler on your machine, no Docker needed.

    python scripts/invoke_local.py submit_withdrawal
    python scripts/invoke_local.py get_case events/get_case.json

Uses events/<handler>.json by default. Real AWS calls (DynamoDB, Bedrock) use the
lpl-hackathon profile. Set the table env vars to the deployed names (from the
sam deploy outputs) once db.py is real.
"""

import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "ai")]
os.environ.setdefault("AWS_PROFILE", "lpl-hackathon")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("SEED_DATA_DIR", str(ROOT / "data"))  # /opt in Lambda, from the SeedDataLayer


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    name = sys.argv[1]
    event_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "events" / f"{name}.json"
    event = json.loads(event_path.read_text())

    handler = importlib.import_module(f"handlers.{name}").handler
    result = handler(event, None)
    print(f"status {result['statusCode']}")
    print(json.dumps(json.loads(result["body"]), indent=2))


if __name__ == "__main__":
    main()
