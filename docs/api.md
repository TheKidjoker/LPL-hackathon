# API Contract

Every lane builds to this file. Change it only by pull request, and tell the team. The stubs in `backend/` and the mocks in `frontend/src/mock/` return exactly these shapes.

## Conventions

- JSON everywhere, with `camelCase` keys. The AI functions return the same keys, so handlers store their output as is.
- Every request sends the caller's role in an `X-Role` header: `client`, `advisor`, or `fraud`. Cognito replaces this later (stretch).
- Times are ISO 8601 in UTC (`2026-10-02T14:05:00Z`). Dates with no time are `YYYY-MM-DD`.
- Money is a plain number in US dollars (`180000`).
- Base URL comes from `sam deploy` output `ApiUrl`, for example `https://abc123.execute-api.us-east-1.amazonaws.com/Prod`.

## Data shapes

### Account

```json
{
  "accountId": "acc-1001",
  "clientName": "Margaret Ellis",
  "clientAge": 78,
  "accountOpened": "2004-03-15",
  "balance": 180000,
  "advisor": { "contactId": "adv-01", "name": "Daniel Reyes" },
  "emergencyContact": { "contactId": "ec-01", "name": "Susan Ellis", "relationship": "daughter" },
  "jointOwners": [],
  "knownPayees": [
    { "payeeId": "pay-100", "name": "First Harbor Bank checking", "type": "bank", "addedAt": "2011-06-01T00:00:00Z" }
  ]
}
```

- `advisor` is `null` for a client with no advisor. That client gets the scam-check chat instead.
- `jointOwners` items have the same shape as `emergencyContact`.
- `payee.type` is one of `bank`, `crypto_exchange`, `brokerage`, `individual`.

### Transaction

```json
{
  "transactionId": "txn-9001",
  "accountId": "acc-1001",
  "timestamp": "2026-10-02T14:05:00Z",
  "type": "withdrawal",
  "amount": 180000,
  "payee": { "payeeId": "pay-777", "name": "CoinVault Exchange", "type": "crypto_exchange", "addedAt": "2026-10-02T12:01:00Z" },
  "channel": "web",
  "clientNote": "Moving funds to a safe account as instructed by bank security."
}
```

- `type` is one of `withdrawal`, `deposit`, `transfer`.
- `channel` is one of `web`, `phone`, `branch`.
- History rows in the Transactions table use this same shape.

### Risk (output of `score_withdrawal`)

```json
{
  "score": 92,
  "level": "high",
  "signals": [
    { "name": "new_payee", "detail": "Payee added 2 hours before the request" },
    { "name": "full_liquidation", "detail": "Withdrawal is 100% of the account balance" },
    { "name": "senior_client", "detail": "Client is 78" },
    { "name": "first_crypto", "detail": "No crypto activity in 22 years" }
  ],
  "memo": "Margaret Ellis, 78, asked to send her full $180,000 balance to CoinVault Exchange, a crypto payee added two hours earlier...",
  "doNotNotify": []
}
```

- `score` is 0 to 100. `level` is `low` (under 40), `medium` (40 to 69), or `high` (70 and up).
- `signals[].name` values: `new_payee`, `full_liquidation`, `senior_client`, `first_crypto`, `unusual_timing`, `payee_added_recently`, plus any Claude adds.
- `doNotNotify` lists `contactId`s Claude thinks are involved in the scam.
- If Claude fails, the handler stores `score: null`, `level: "unknown"`, the rule signals, and the memo `"Automated review unavailable. Held for manual review."`, then holds the withdrawal.

### Response

```json
{
  "responseId": "resp-01",
  "role": "client",
  "kind": "deny",
  "text": "I did not request this. Someone called me.",
  "at": "2026-10-02T14:20:00Z"
}
```

- Client `kind`: `confirm`, `deny`, `emergency_contact`, `chat`. Advisor `kind`: `note`.
- `chat` responses also carry `chatReply` (Claude's answer) and `done` (true when the scam check is finished).

### Case

```json
{
  "caseId": "case-0001",
  "accountId": "acc-1001",
  "clientName": "Margaret Ellis",
  "createdAt": "2026-10-02T14:05:00Z",
  "status": "HELD",
  "transaction": { "...": "Transaction" },
  "risk": { "...": "Risk" },
  "holdEndsAt": "2026-10-16",
  "notified": ["client", "adv-01", "fraud-team"],
  "responses": [],
  "decision": null,
  "audit": [
    { "timestamp": "2026-10-02T14:05:07Z", "actor": "system", "action": "HELD", "detail": "Risk score 92" }
  ]
}
```

- `status` is one of `HELD`, `RELEASED`, `EXTENDED`, `ESCALATED`.
- `holdEndsAt` is 10 business days after `createdAt`. `null` when released.
- `decision` is `null` until the fraud team acts, then `{ "action": "release", "by": "fraud", "at": "...", "note": "..." }`.

### What each role sees in a Case

| Field | client | advisor | fraud |
|---|---|---|---|
| `caseId`, `status`, `createdAt`, `transaction`, `holdEndsAt`, `decision` | Yes | Yes | Yes |
| `clientName`, `accountId`, `notified` | No | Yes | Yes |
| `risk` (score, signals, memo) | No | Yes, without `doNotNotify` | Yes |
| `responses` | Only the client's own | All | All |
| `audit` | No | No | Yes |

`backend/common/views.py` applies this table. Every handler that returns a Case passes it through `case_for_role`.

### CaseSummary (items in `GET /cases`)

```json
{
  "caseId": "case-0001",
  "clientName": "Margaret Ellis",
  "amount": 180000,
  "payeeName": "CoinVault Exchange",
  "status": "HELD",
  "score": 92,
  "level": "high",
  "createdAt": "2026-10-02T14:05:00Z",
  "holdEndsAt": "2026-10-16"
}
```

### Error

```json
{ "error": { "code": "forbidden", "message": "Only the fraud team can release a hold." } }
```

| Status | `code` | When |
|---|---|---|
| 400 | `bad_request` | Missing or invalid field, bad JSON |
| 403 | `forbidden` | Missing `X-Role`, or the role cannot do this |
| 404 | `not_found` | Unknown `caseId` or `accountId` |
| 409 | `invalid_move` | The status change is not allowed from the current status |
| 500 | `server_error` | Anything else. Details go to CloudWatch, not the response |

## Endpoints

| Method and path | Roles | Owner |
|---|---|---|
| `POST /withdrawals` | client | Krish |
| `GET /cases` | advisor, fraud | Kaylin |
| `GET /cases/{caseId}` | client, advisor, fraud | Kaylin |
| `POST /cases/{caseId}/responses` | client, advisor | Krish |
| `POST /cases/{caseId}/decision` | fraud | Krish |
| `POST /demo/reset` | any | Krish |

### `POST /withdrawals`

Request:

```json
{
  "accountId": "acc-1001",
  "amount": 180000,
  "payee": { "name": "CoinVault Exchange", "type": "crypto_exchange", "addedAt": "2026-10-02T12:01:00Z" },
  "channel": "web",
  "clientNote": "Moving funds to a safe account as instructed by bank security."
}
```

Response `201`: the new Case, as the client sees it. Takes about 7 seconds while Claude scores it.

### `GET /cases`

Query: `status` (optional, for example `?status=HELD`). Response `200`:

```json
{ "cases": [ { "...": "CaseSummary" } ] }
```

Held cases first, newest first within each status.

### `GET /cases/{caseId}`

Response `200`: the Case, filtered for the caller's role.

### `POST /cases/{caseId}/responses`

Request:

```json
{ "kind": "deny", "text": "I did not request this. Someone called me." }
```

Response `200`: the updated Case, filtered for the caller's role. For `kind: "chat"`, the new Response in `responses` carries `chatReply` and `done`.

### `POST /cases/{caseId}/decision`

Request:

```json
{ "action": "release", "note": "Client confirmed in person at the branch." }
```

- `action` is `release`, `extend`, or `escalate`. The Case moves to `RELEASED`, `EXTENDED`, or `ESCALATED`.
- Any role but `fraud` gets `403`. A move not allowed from the current status gets `409`.

Response `200`: the updated Case.

### `POST /demo/reset`

No body. Deletes all Cases and Audit rows, reloads the seed data. Response `200`:

```json
{ "ok": true, "accountsLoaded": 6 }
```
