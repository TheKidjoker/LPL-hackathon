"""POST /demo/reset. Owner: Kaylin.

Stub: returns ok. Replace with: delete every Case and Audit row, then reload
the seed data (share the loading code with scripts/seed_dynamodb.py).
"""

from common.http import api_handler, respond


@api_handler
def handler(event, context):
    # TODO(Kaylin): clear Cases and Audit, reload /data
    return respond({"ok": True, "accountsLoaded": 0})
