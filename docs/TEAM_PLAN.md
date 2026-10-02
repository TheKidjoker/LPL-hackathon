# Team Plan: Who Builds What

Three people, one owner for every piece. All three write backend code, split by file so nobody edits the same file. To change someone else's file, open a pull request and tag them. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how the pieces connect.

**Start with [`DEV_SETUP.md`](DEV_SETUP.md).** The repo already has a running skeleton: every endpoint, AI function, and view exists as a stub that returns the sample data from [`api.md`](api.md), and `python -m pytest` checks them all. Search for `TODO(<your name>)` to find your work.

| Person | Lane | In one line |
|---|---|---|
| **Thomas** | AI and Frontend | Everything Claude does, and everything the user sees |
| **Krish** | AWS and Platform | Everything deployed: infra, deploys, read endpoints, alerts, architecture diagram. The only person who runs `sam deploy` |
| **Kaylin** | Case Logic, Data, and Pitch | The rules of a case, the fake data that tells the story, and the deck and demo |

**Core** = needed for the demo, done by Sat midnight. **Stretch** = only after the core flow works.

## Everything this idea needs

### Product rules (decide in hour one, all three)

| Item | Decision to make | Owner |
|---|---|---|
| Hold threshold | Score of 70 or higher holds the withdrawal | Kaylin |
| Hold length | Up to 10 business days, per proposed FINRA Rule 2166 | Kaylin |
| Who can release | Fraud team only. Advisor can never release alone | Kaylin |
| Who gets alerted | Client, advisor, fraud team, minus anyone Claude flags as involved | Kaylin |
| How clients confirm | Inside the app only. Alerts never carry a link or a reply option | Kaylin |
| Claude fails or times out | Hold for manual review, never auto-release | Thomas |
| No advisor on the account | Claude scam-check chat replaces the advisor step | Thomas |

### AI (Thomas)

| Item | Core or stretch |
|---|---|
| Done: `ai/fraud_ai/bedrock_client.py`, one Converse wrapper with the model ID from config, `maxTokens` 2000, reads only the `text` block (Opus 5 sends reasoning first), retries once, falls back to Sonnet 5. Tested live | Core |
| `ai/fraud_ai/signals.py`: rule-based signals for new payee, full liquidation, age 65 or older, first-ever crypto, unusual timing, payee added within 24 hours | Core |
| `ai/fraud_ai/score.py`: `score_withdrawal(...)` returns score, level, signals, memo, `doNotNotify` as validated JSON | Core |
| `ai/fraud_ai/prompts/memo.txt`: about 120 words, plain English, names each signal, cites FINRA Rule 2165 and proposed Rule 2166, no investment advice | Core |
| Treat client and advisor text as data, never as instructions to Claude (prompt-injection guard) | Core |
| Eval script: run every scenario in `/data` and print score and level, so prompt changes can be checked in one command | Core |
| `doNotNotify`: flag a joint owner or emergency contact who looks involved | Core |
| `ai/fraud_ai/scam_chat.py`: `scam_check_chat(...)` asks "Did someone contact you first?" and "Were you told to keep this secret?", returns a risk update | Core |
| Done: AI stubs with the exact signatures, so Kaylin is never blocked | Core |
| Bedrock Guardrails on both calls: block investment advice and personal info | Stretch |
| Knowledge Base with FINRA rule text so memos quote the rule | Stretch |

### Frontend (Thomas)

| Item | Core or stretch |
|---|---|
| React app with a role switcher: Client, Advisor, Fraud team | Core |
| API client with the base URL in one config value, mock mode for working offline | Core |
| Client view: withdrawal form (the $180K crypto request pre-filled for the demo), "Reviewing..." state (about 7 seconds), "We paused a withdrawal to protect you" screen, confirm or deny, scam warning signs, emergency contact field | Core |
| Advisor view: alert banner, AI summary, notes box | Core |
| Fraud team view: case queue with held cases first, case detail with score, signals, memo, hold timer, client answer, advisor notes, audit timeline, release, extend, and escalate buttons | Core |
| Scam-check chat screen for clients with no advisor | Core |
| Loading and error states on every call | Core |
| "Reset demo" button that calls `POST /demo/reset` | Core |
| Our own product name and colors. Do not copy LPL's logo or branding | Core |
| Cognito login screens per role | Stretch |
| Mobile layout | Stretch |

### AWS and platform (Krish)

| Item | Core or stretch |
|---|---|
| Everyone has working credentials. Re-run `scripts/aws-login.ps1` when they expire | Core |
| `infra/template.yaml`: API Gateway with CORS, one Lambda per endpoint, Python 3.11, 30 second timeout | Core |
| DynamoDB tables: Accounts, Transactions, Cases (index on `status`), Audit | Core |
| Lambda layer that packages `ai/` so handlers can `from fraud_ai import ...` | Core |
| Environment variables: `MODEL_ID=us.anthropic.claude-opus-5`, `FALLBACK_MODEL_ID`, table names | Core |
| IAM: Lambdas can read and write only these tables and call `bedrock:InvokeModel` on Opus 5 and Sonnet 5 | Core |
| CloudWatch logs on, with no full memos or personal details written to logs | Core |
| First deploy and the live API URL posted by Fri 4 PM, redeploy after every merge | Core |
| Amplify hosting for the frontend from GitHub | Core |
| `backend/common/roles.py`: reads the caller's role from an `X-Role` header | Core |
| `backend/handlers/list_cases.py`: `GET /cases`, held first | Core |
| `backend/handlers/get_case.py`: `GET /cases/{id}`, each role sees only its fields (the client never sees the memo or advisor notes) | Core |
| `backend/notify.py`: in-app alerts on a held case, skipping everyone in `doNotNotify` | Core |
| Architecture diagram for the deck and submission, from the draft in `ARCHITECTURE.md` | Core |
| Cognito user pool with client, advisor, and fraud groups, plus an API authorizer replacing `X-Role` | Stretch |
| SNS and SES alerts with no links in them | Stretch |
| EventBridge Scheduler to end holds automatically | Stretch |
| Step Functions running the case flow | Stretch |
| CloudTrail and KMS for the security story | Stretch |

### Case logic (Kaylin)

| Item | Core or stretch |
|---|---|
| `backend/common/db.py`: `get_account`, `get_history(account_id, days=90)`, `put_case`, `update_case`, `list_cases_by_status`. Nobody calls DynamoDB directly | Core |
| `backend/common/case_state.py`: statuses and `can_move(from, to, role)` | Core |
| `backend/common/audit.py`: `write_audit(case_id, actor, action, detail)` on every change | Core |
| `backend/handlers/submit_withdrawal.py`: `POST /withdrawals`. Load account and history, call `score_withdrawal`, save `HELD` or `RELEASED`, set the hold end date, call `notify` | Core |
| `backend/handlers/post_response.py`: `POST /cases/{id}/responses`. Client confirms or denies, advisor adds notes, no-advisor clients go to `scam_check_chat` | Core |
| `backend/handlers/post_decision.py`: `POST /cases/{id}/decision`. Release, extend, or escalate, fraud team only | Core |
| `backend/handlers/demo_reset.py`: `POST /demo/reset` wipes cases and reloads seed data, so the demo can be run again | Core |
| Input checks on every handler, with clear error messages | Core |
| `events/*.json`: a sample request per handler, used by `scripts/invoke_local.py` and the tests | Core |

### Data (Kaylin)

| Item | Core or stretch |
|---|---|
| Hero scenario: age 78, 22-year account, $180K full liquidation to a crypto exchange payee added 2 hours ago, client says a "bank security officer" called | Core |
| 90 days of normal-looking transaction history behind each account, so "unusual" means something | Core |
| 3 normal accounts that should not be flagged (house down payment, regular monthly transfer, small withdrawal) | Core |
| One account where the joint owner is the scammer, to show `doNotNotify` | Core |
| One account with no advisor, to show the scam-check chat | Core |
| `scripts/seed_dynamodb.py`: loads `/data` into the tables | Core |
| Romance scam and fake tech support scenarios | Stretch |
| All names and numbers fake. No real people or real account numbers | Core |

### Pitch and submission (Kaylin, with everyone)

| Item | Owner | When |
|---|---|---|
| Submit categories: Startup We'd Buy Tomorrow and Best Technical Execution | Kaylin | Fri 3 PM |
| Demo script: the $180K hero through all three views, then the no-advisor and joint-owner cases if time allows | Kaylin | Sat midnight |
| Deck: problem, why now (Rule 2166), demo, architecture, three safety rules, why LPL buys it | Kaylin | Sat 6 AM |
| Architecture slide | Krish | Sat 6 AM |
| AI slide: how Claude scores and explains, what it never does | Thomas | Sat 6 AM |
| Backup demo video | Kaylin records, Thomas drives the app | Sat 6 AM |
| Q&A prep: the three safety rules, false positives, cost per case, why Bedrock | All | Sat 10 AM |
| Code ZIP and submission form | Krish | Sat 12 PM |

## Backend file map

Python 3.11 for every Lambda. One owner per file.

| File | Owner |
|---|---|
| `infra/template.yaml` | Krish |
| `backend/common/roles.py` | Krish |
| `backend/handlers/list_cases.py`, `get_case.py` | Krish |
| `backend/notify.py` | Krish |
| `backend/common/db.py`, `case_state.py`, `audit.py` | Kaylin |
| `backend/handlers/submit_withdrawal.py`, `post_response.py`, `post_decision.py`, `demo_reset.py` | Kaylin |
| `scripts/seed_dynamodb.py`, `/data` | Kaylin |
| `ai/` (all of it) | Thomas |
| `frontend/` (all of it) | Thomas |
| `events/*.json` | Owner of the matching handler |

## Shared contracts

Agree on these in hour one. After that, change them only by pull request, and tell the team.

**DynamoDB tables** (Krish defines them, Kaylin's `db.py` reads and writes them):

| Table | Key | Holds |
|---|---|---|
| Accounts | `accountId` | Client name, age, account age, advisor, emergency contact, joint owners |
| Transactions | `accountId` + `timestamp` | Past transactions, used as history for scoring |
| Cases | `caseId`, plus an index on `status` | The withdrawal, risk result, memo, status, responses, hold end date |
| Audit | `caseId` + `timestamp` | Every action: who, what, when |

**Case statuses** (Kaylin's `case_state.py`):

| From | Allowed moves | Who can make it |
|---|---|---|
| New withdrawal | `HELD` (score 70 or higher) or `RELEASED` | System |
| `HELD` | `RELEASED`, `EXTENDED`, `ESCALATED` | Fraud team only |
| `EXTENDED` | `RELEASED`, `ESCALATED` | Fraud team only |

**AI functions** (Thomas writes them, Kaylin's handlers call them):

```python
score_withdrawal(account: dict, transaction: dict, history: list[dict]) -> dict
# returns {"score": 0-100, "level": "low"|"medium"|"high",
#          "signals": [{"name": str, "detail": str}],
#          "memo": str, "doNotNotify": [contact_id, ...]}

scam_check_chat(case: dict, messages: list[dict]) -> dict
# returns {"reply": str, "riskUpdate": int | None, "done": bool}
```

**API** in [`api.md`](api.md): data shapes for Account, Transaction, Case, and Response, plus `POST /withdrawals`, `GET /cases`, `GET /cases/{id}`, `POST /cases/{id}/responses`, `POST /cases/{id}/decision`, and `POST /demo/reset`.

## Timeline by person

| Checkpoint | Thomas: AI and Frontend | Krish: AWS and Platform | Kaylin: Case Logic, Data, Pitch |
|---|---|---|---|
| Hour one | AI stubs committed. Empty React app | SAM project created. SAM CLI on all three machines | Product rules written down. `db.py` and `case_state.py` shapes agreed |
| Fri 3 PM | Signals and Bedrock client working locally | Tables and stub Lambdas deployed | Categories submitted. Hero and normal accounts in `/data` |
| Fri 4 PM | Three views on mock data | Live API URL posted | Seed data loaded. Submit flow working on AI stubs |
| Fri 8 PM | Real memo from Opus 5, eval passes. Views wired to the live API | Read endpoints with role filtering. Redeploys after each merge | Submit flow on real scoring. Responses endpoint |
| Sat midnight | Scam-check chat and `doNotNotify`. Full flow on screen | Alerts skip flagged contacts. Amplify hosting. Architecture diagram | Decision endpoint, demo reset, joint-owner and no-advisor accounts. Demo script |
| Sat 6 AM | AI slide. Drive the backup video | Architecture slide | Deck done. Backup video recorded |
| Sat 12 PM | Q&A prep | Code ZIP and submission form | Q&A prep |

## Rules

- Work on a branch named after your lane (`ai/...`, `frontend/...`, `infra/...`, `backend/...`). Open a small pull request and get one teammate to look.
- Pull from main before starting something new, and merge every 2 to 3 hours. Tell Krish when to redeploy.
- Never commit AWS keys. Keep the model ID and API URL in one config value each.
- Protect the core flow first: flag, memo, alerts, fraud team decision. Stretch items wait until midnight.
