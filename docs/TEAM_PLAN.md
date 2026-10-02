# Team Plan: Who Builds What

Three people. Each person owns their lane, and all three build parts of the backend. Backend work is split by file, so nobody edits the same file. To change someone else's file, open a pull request and tag them. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how the pieces connect.

| Person | Own lane | Backend share |
|---|---|---|
| **Thomas** | All frontend and all AWS setup: the app, SAM template, IAM, Amplify, Cognito, deploys. Also the pitch | Read endpoints the views use: `GET /cases`, `GET /cases/{id}` |
| **Krish** | Case logic | Submit, responses, and decision endpoints, case states, audit log, alerts |
| **Kaylin** | AI and data | Bedrock client, risk scoring, memo, scam-check chat, seed data loader |

Thomas is the only person who runs `sam deploy`. Krish and Kaylin test locally with `sam local invoke`, then merge, and Thomas deploys.

## Backend file map

Language: Python 3.12 for every Lambda. One owner per file.

| File | Owner | What it does |
|---|---|---|
| `infra/template.yaml` | Thomas | SAM template: API Gateway, every Lambda, DynamoDB tables, IAM, environment variables |
| `backend/common/db.py` | Krish | Read and write helpers for all four tables. Everyone imports these, nobody calls DynamoDB directly |
| `backend/common/case_state.py` | Krish | Case statuses and which moves are allowed |
| `backend/common/audit.py` | Krish | `write_audit(case_id, actor, action, detail)` |
| `backend/common/roles.py` | Thomas | Reads the caller's role. An `X-Role` header for now, Cognito later |
| `backend/handlers/submit_withdrawal.py` | Krish | `POST /withdrawals` |
| `backend/handlers/post_response.py` | Krish | `POST /cases/{id}/responses` |
| `backend/handlers/post_decision.py` | Krish | `POST /cases/{id}/decision` |
| `backend/notify.py` | Krish | Sends alerts and skips everyone in `do_not_notify` |
| `backend/handlers/list_cases.py` | Thomas | `GET /cases` |
| `backend/handlers/get_case.py` | Thomas | `GET /cases/{id}`, showing each role only its fields |
| `ai/bedrock_client.py` | Kaylin | One Converse call wrapper: model ID from config, retry, Sonnet 5 fallback, JSON parsing |
| `ai/signals.py` | Kaylin | Rule-based risk signals |
| `ai/score.py` | Kaylin | `score_withdrawal(...)` |
| `ai/scam_chat.py` | Kaylin | `scam_check_chat(...)` |
| `ai/prompts/` | Kaylin | Prompt text files, kept out of the code |
| `scripts/seed_dynamodb.py` | Kaylin | Loads `/data` JSON into the tables |
| `events/*.json` | Each owner | Sample requests for `sam local invoke`, one per handler |

## Shared contracts

Agree on these in hour one. After that, change them only by pull request, and tell the team.

**DynamoDB tables** (Thomas defines them in the template, Krish's `db.py` reads and writes them):

| Table | Key | Holds |
|---|---|---|
| Accounts | `accountId` | Client name, age, account age, advisor, emergency contact, joint owners |
| Transactions | `accountId` + `timestamp` | Past transactions, used as history for scoring |
| Cases | `caseId`, plus an index on `status` | The withdrawal, risk result, memo, status, responses, hold end date |
| Audit | `caseId` + `timestamp` | Every action: who, what, when |

**Case statuses** (Krish's `case_state.py`):

| From | Allowed moves | Who can make it |
|---|---|---|
| New withdrawal | `HELD` (score 70 or higher) or `RELEASED` | System |
| `HELD` | `RELEASED`, `EXTENDED`, `ESCALATED` | Fraud team only |
| `EXTENDED` | `RELEASED`, `ESCALATED` | Fraud team only |

**AI functions** (Kaylin writes them, Krish's handlers call them):

```python
score_withdrawal(account: dict, transaction: dict, history: list[dict]) -> dict
# returns {"score": 0-100, "level": "low"|"medium"|"high",
#          "signals": [{"name": str, "detail": str}],
#          "memo": str, "do_not_notify": [contact_id, ...]}

scam_check_chat(case: dict, messages: list[dict]) -> dict
# returns {"reply": str, "risk_update": int | None, "done": bool}
```

**API** in [`api.md`](api.md): data shapes for Account, Transaction, Case, and Response, plus the five endpoints in the file map.

## Hour one: all three together

- [ ] Everyone runs `.\scripts\aws-login.ps1` and the checks in [`AWS_SETUP.md`](AWS_SETUP.md), and installs the SAM CLI
- [ ] Fill in and merge `api.md`, the table keys, and the AI signatures above
- [ ] Thomas: create the SAM project and an empty React app
- [ ] Krish: `db.py` and `case_state.py` with the shapes above
- [ ] Kaylin: AI stubs with the exact signatures, returning fixed sample output, so Krish is never blocked

## Thomas: Frontend, AWS, and Pitch

**By Fri 4 PM: stub API deployed, three views on mock data**

AWS:

- [ ] `infra/template.yaml` with API Gateway (CORS on), the four DynamoDB tables, and one Lambda per endpoint
- [ ] Lambda settings: Python 3.12, 30 second timeout, environment variables `MODEL_ID=us.anthropic.claude-opus-5` and the table names
- [ ] IAM: Lambdas can read and write the tables and call `bedrock:InvokeModel` on Opus 5 and Sonnet 5
- [ ] Package `/ai` so the Lambdas can import it (a Lambda layer)
- [ ] First `sam deploy`, then post the API URL in the team chat

Frontend:

- [ ] React app in `/frontend` with a role switcher: Client, Advisor, Fraud team
- [ ] Mock JSON in the exact `api.md` shapes, in one file so it is easy to swap out
- [ ] Client view: withdrawal form with the $180K crypto request pre-filled for the demo

Backend:

- [ ] `list_cases.py` and `get_case.py` returning mock data, then real data once `db.py` lands
- [ ] `roles.py` reading the `X-Role` header

**By Fri 8 PM: wired to the live API**

- [ ] Swap mock data for the live API URL, kept in one config value
- [ ] Case detail page: risk score, signals, Claude memo, hold timer
- [ ] "Reviewing..." state while a withdrawal is scored (about 7 seconds)
- [ ] `get_case.py` filters by role: the client never sees the memo or advisor notes, and the advisor never sees the fraud team's decision controls
- [ ] Redeploy whenever Krish or Kaylin merges

**By Sat midnight: full flow on screen and hosted**

- [ ] Client: "We paused a withdrawal to protect you. Did you request this?" with confirm or deny, scam warning signs, and an emergency contact field
- [ ] Advisor: alert banner, AI summary, notes box
- [ ] Fraud team: client answer, advisor notes, audit log, and release, extend, or escalate buttons
- [ ] Hosted on Amplify from GitHub

**Pitch, from Sat midnight (Krish and Kaylin join once the build freezes):**

- [ ] Architecture diagram for the deck and submission. Start from the draft in `ARCHITECTURE.md`
- [ ] Deck: problem, demo, architecture diagram, the three safety rules, why LPL buys it
- [ ] Demo script for the $180K scenario through all three views, and a backup video by 6 AM

**Stretch:** Cognito logins with an API authorizer (replaces the `X-Role` header), CloudTrail and KMS, mobile layout.

## Krish: Case Logic

**By Fri 4 PM: the case flow works locally on stubs**

- [ ] `db.py`: `get_account`, `get_history(account_id, days=90)`, `put_case`, `update_case`, `list_cases_by_status`
- [ ] `case_state.py`: statuses and a `can_move(from, to, role)` check
- [ ] `audit.py`: `write_audit(...)`
- [ ] `submit_withdrawal.py` calls the AI stub and saves a Case. Test with `sam local invoke` and `events/submit_withdrawal.json`

**By Fri 8 PM: real scoring end to end**

- [ ] `submit_withdrawal.py` with the real `score_withdrawal`: load the account and 90 days of history, score it, save `HELD` (70 or higher) or `RELEASED`, store the memo, write an Audit row
- [ ] If Claude fails or times out, hold the withdrawal for manual review rather than releasing it

**By Sat midnight: full flow**

- [ ] `post_response.py`: the client confirms or denies, the advisor adds notes. A client with no advisor gets a reply from `scam_check_chat`. Each response writes an Audit row
- [ ] `post_decision.py`: release, extend, or escalate. Uses `can_move`, so only the fraud team can release
- [ ] `notify.py`: on `HELD`, alert the client, advisor, and fraud team, skipping every contact in `do_not_notify`. Logging the alert is enough for the core build
- [ ] Hold end date set to 10 business days out, saved on the Case

**Stretch:** real alerts through SNS and SES, EventBridge Scheduler to end holds automatically, Step Functions to run the case flow.

## Kaylin: AI and Data

**By Fri 4 PM: data, stubs, and signals**

- [ ] AI stubs in `/ai` with the exact signatures above (hour one)
- [ ] Seed data in `/data`: the hero scenario (age 78, 22-year account, $180K full liquidation to a crypto exchange payee added 2 hours ago, client says a "bank security officer" called) plus 3 normal accounts that should not be flagged
- [ ] `signals.py`: new payee, full liquidation, client age 65 or older, first-ever crypto, unusual timing
- [ ] `scripts/seed_dynamodb.py` loads the data once Thomas's tables are deployed

**By Fri 8 PM: the real memo**

- [ ] `bedrock_client.py`: one Converse call using `MODEL_ID`, `maxTokens` 2000, reads only the block with `text` (Opus 5 sends a reasoning block first), retries once, falls back to `us.anthropic.claude-sonnet-5`
- [ ] `score.py`: sends signals and history, asks for JSON only, and validates the reply before returning it
- [ ] Prompt in `ai/prompts/`: about 120 words, plain English, names each signal, cites FINRA Rule 2165 and proposed Rule 2166, never gives investment advice
- [ ] Test every scenario: the hero scores high, the normal accounts score low

**By Sat midnight**

- [ ] `do_not_notify`: Claude flags a joint owner or emergency contact who looks involved
- [ ] `scam_chat.py`: asks "Did someone contact you first?" and "Were you told to keep this secret?", then returns a risk update
- [ ] 2 more scam scenarios for the demo (romance scam, fake tech support)

**Stretch:** Bedrock Guardrails on both calls (block investment advice and personal info), a Knowledge Base with FINRA rule text so memos quote the rule.

## Handoffs

| From | To | What | When |
|---|---|---|---|
| All | All | Merged `api.md`, table keys, AI signatures | End of hour one |
| Kaylin | Krish | AI stubs | End of hour one |
| Krish | Thomas and Kaylin | `db.py` helpers | Fri 2 PM |
| Thomas | All | Deployed tables and the live API URL | Fri 4 PM |
| Kaylin | All | Seed data loaded into DynamoDB | Fri 4 PM |
| Kaylin | Krish | Real `score_withdrawal` | Fri 8 PM |
| Krish and Kaylin | Thomas | Working full flow for the video | Sat 6 AM |

## Rules

- Work on a branch named after your lane (`frontend/...`, `infra/...`, `backend/...`, `ai/...`). Open a small pull request and get one teammate to look.
- Pull from main before starting something new, and merge every 2 to 3 hours. Tell Thomas when to redeploy.
- Never commit AWS keys. Keep the model ID and API URL in one config value each.
- Protect the core flow first: flag, memo, alerts, fraud team decision. Stretch items wait until midnight.
