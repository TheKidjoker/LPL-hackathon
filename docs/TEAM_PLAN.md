# Team Plan: Who Builds What

Three people, one owner for every piece. All three write backend code, split by file so nobody edits the same file. To change someone else's file, open a pull request and tag them. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how the pieces connect. The short version per person is [`ROLES.md`](../ROLES.md).

**Start with [`DEV_SETUP.md`](DEV_SETUP.md).** The repo already has a running skeleton: every endpoint, AI function, and view exists as a stub that returns the sample data from [`api.md`](api.md), and `python -m pytest` checks them all. Search for `TODO(<your name>)` to find your work.

| Person | Lane | In one line |
|---|---|---|
| **Thomas** | AI, Frontend, and AWS | Everything Claude does, everything the user sees, and everything deployed. The only person who runs `sam deploy` |
| **Krish** | Case Logic, Data, and Pitch | The rules of a case, the fake data that tells the story, the architecture diagram, and the deck and demo |
| **Kaylin** | API and Alerts | The request helpers, the endpoints the views read, what each role can see, and who gets alerted |

**Core** = needed for the demo, done by Sat midnight. **Stretch** = only after the core flow works.

## Everything this idea needs

### Product rules (decide in hour one, all three)

| Item | Decision to make | Owner |
|---|---|---|
| Hold threshold | Score of 70 or higher holds the withdrawal | Krish |
| Hold length | Up to 10 business days, per proposed FINRA Rule 2166 | Krish |
| Who can release | Fraud team only. Advisor can never release alone | Krish |
| Who gets alerted | Client, advisor, fraud team, minus anyone Claude flags as involved | Kaylin |
| How clients confirm | Inside the app only. Alerts never carry a link or a reply option | Kaylin |
| Claude fails or times out | Hold for manual review, never auto-release | Thomas |
| No advisor on the account | Claude scam-check chat replaces the advisor step | Thomas |

### AI (Thomas)

| Item | Core or stretch |
|---|---|
| Done: `ai/fraud_ai/bedrock_client.py`, one Converse wrapper with the model ID from config, `maxTokens` 2000, reads only the `text` block (Opus 5 sends reasoning first), retries once, falls back to Sonnet 5. Tested live | Core |
| Done: AI stubs with the exact signatures, so Krish is never blocked | Core |
| `ai/fraud_ai/signals.py`: rule-based signals for new payee, full liquidation, age 65 or older, first-ever crypto, unusual timing, payee added within 24 hours | Core |
| `ai/fraud_ai/score.py`: `score_withdrawal(...)` returns score, level, signals, memo, `doNotNotify` as validated JSON | Core |
| `ai/fraud_ai/prompts/memo.txt`: about 120 words, plain English, names each signal, cites FINRA Rule 2165 and proposed Rule 2166, no investment advice | Core |
| Treat client and advisor text as data, never as instructions to Claude (prompt-injection guard) | Core |
| Eval script: run every scenario in `/data` and print score and level, so prompt changes can be checked in one command | Core |
| `doNotNotify`: flag a joint owner or emergency contact who looks involved | Core |
| `ai/fraud_ai/scam_chat.py`: `scam_check_chat(...)` asks "Did someone contact you first?" and "Were you told to keep this secret?", returns a risk update | Core |
| Bedrock Guardrails on both calls: block investment advice and personal info | Stretch |
| Knowledge Base with FINRA rule text so memos quote the rule | Stretch |

### Frontend (Thomas)

| Item | Core or stretch |
|---|---|
| Done: React app with a role switcher, API client with mock mode, three working views on mock data, "Reset demo" button | Core |
| Client view: scam warning signs, emergency contact field, polished "We paused a withdrawal to protect you" screen | Core |
| Advisor view: alert banner styling, only this advisor's clients | Core |
| Fraud team view: hold countdown timer, audit timeline | Core |
| Scam-check chat screen for clients with no advisor | Core |
| Loading and error states on every call | Core |
| Our own product name and colors. Do not copy LPL's logo or branding | Core |
| Cognito login screens per role | Stretch |
| Mobile layout | Stretch |

### AWS (Thomas)

| Item | Core or stretch |
|---|---|
| Everyone has working credentials. Re-run `scripts/aws-login.ps1` when they expire | Core |
| Done: `infra/template.yaml` with API Gateway (CORS), one Lambda per endpoint, Python 3.11, 30 second timeout, the four tables, the `ai/` layer, IAM for the tables and Bedrock. Passes `cfn-lint` | Core |
| First `sam deploy`. If the account blocks IAM role creation, change the template right away | Core |
| Post `ApiUrl` and the four table names in the team chat by Fri 4 PM | Core |
| Redeploy after every merge that touches `backend/`, `ai/`, or `infra/` | Core |
| CloudWatch logs on, with no full memos or personal details written to logs | Core |
| Amplify hosting for the frontend from GitHub | Core |
| Cognito user pool with client, advisor, and fraud groups, plus an API authorizer replacing `X-Role` | Stretch |

### API and alerts (Kaylin)

| Item | Core or stretch |
|---|---|
| Done: `backend/common/http.py` (responses, errors, body parsing), `roles.py` (`X-Role` check), `views.py` (what each role sees). Own and maintain them | Core |
| `backend/handlers/list_cases.py`: `GET /cases` from `db.list_cases_by_status`, held first, newest first | Core |
| `backend/handlers/get_case.py`: `GET /cases/{id}` from `db.get_case`, 404 when missing, audit rows added for the fraud role | Core |
| `backend/notify.py`: in-app alerts on a held case, including the emergency contact, skipping everyone in `doNotNotify` | Core |
| Tests in `tests/` for role filtering and `doNotNotify` | Core |
| Help Thomas check each deploy: run every endpoint against the live API after a redeploy | Core |
| SNS and SES alerts with no links in them (add the resources to the template by pull request) | Stretch |
| EventBridge Scheduler to end holds automatically | Stretch |
| Step Functions running the case flow | Stretch |
| CloudTrail and KMS for the security story | Stretch |

### Case logic (Krish)

| Item | Core or stretch |
|---|---|
| `backend/common/db.py`: `get_account`, `get_history(account_id, days=90)`, `put_case`, `get_case`, `update_case`, `list_cases_by_status`. Nobody calls DynamoDB directly | Core |
| Done: `backend/common/case_state.py` statuses, hold rules, and `can_move(from, to, role)`. Own and maintain it | Core |
| `backend/common/audit.py`: `write_audit(case_id, actor, action, detail)` and `list_audit(case_id)` | Core |
| `backend/handlers/submit_withdrawal.py`: `POST /withdrawals`. Load account and history, call `score_withdrawal`, save `HELD` or `RELEASED`, set the hold end date, call `notify` | Core |
| `backend/handlers/post_response.py`: `POST /cases/{id}/responses`. Client confirms or denies, advisor adds notes, no-advisor clients go to `scam_check_chat` | Core |
| `backend/handlers/post_decision.py`: `POST /cases/{id}/decision`. Release, extend, or escalate, fraud team only | Core |
| `backend/handlers/demo_reset.py`: `POST /demo/reset` wipes cases and reloads seed data, so the demo can be run again | Core |
| `events/*.json`: keep a sample request per handler, used by `scripts/invoke_local.py` and the tests | Core |

### Data (Krish)

| Item | Core or stretch |
|---|---|
| Hero scenario: age 78, 22-year account, $180K full liquidation to a crypto exchange payee added 2 hours ago, client says a "bank security officer" called | Core |
| 90 days of normal-looking transaction history behind each account, so "unusual" means something | Core |
| 3 normal accounts that should not be flagged (house down payment, regular monthly transfer, small withdrawal) | Core |
| One account where the joint owner is the scammer, to show `doNotNotify` | Core |
| One account with no advisor, to show the scam-check chat | Core |
| `scripts/seed_dynamodb.py`: loads `/data` into the tables | Core |
| All names and numbers fake. No real people or real account numbers | Core |
| Romance scam and fake tech support scenarios | Stretch |

### Pitch and submission (Krish, with everyone)

| Item | Owner | When |
|---|---|---|
| Submit categories: Startup We'd Buy Tomorrow and Best Technical Execution | Krish | Fri 3 PM |
| Architecture diagram, from the draft in [`ARCHITECTURE.md`](ARCHITECTURE.md) | Krish | Sat midnight |
| Demo script: the $180K hero through all three views, then the no-advisor and joint-owner cases if time allows | Krish | Sat midnight |
| Deck: problem, why now (Rule 2166), demo, architecture, three safety rules, why LPL buys it | Krish | Sat 6 AM |
| AI slide: how Claude scores and explains, what it never does | Thomas | Sat 6 AM |
| Safety slide: role filtering, who gets alerted, audit log | Kaylin | Sat 6 AM |
| Backup demo video | Krish records, Thomas drives the app | Sat 6 AM |
| Q&A prep: the three safety rules, false positives, cost per case, why Bedrock | All | Sat 10 AM |
| Code ZIP and submission form | Krish | Sat 12 PM |

## Backend file map

Python 3.11 for every Lambda. One owner per file.

| File | Owner |
|---|---|
| `infra/template.yaml`, `infra/samconfig.toml` | Thomas |
| `ai/` (all of it) | Thomas |
| `frontend/` (all of it) | Thomas |
| `backend/common/http.py`, `roles.py`, `views.py` | Kaylin |
| `backend/handlers/list_cases.py`, `get_case.py` | Kaylin |
| `backend/notify.py` | Kaylin |
| `backend/common/db.py`, `case_state.py`, `audit.py`, `samples.py` | Krish |
| `backend/handlers/submit_withdrawal.py`, `post_response.py`, `post_decision.py`, `demo_reset.py` | Krish |
| `scripts/seed_dynamodb.py`, `/data` | Krish |
| `events/*.json` | Owner of the matching handler |

## Shared contracts

Change these only by pull request, and tell the team.

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

**AI functions** (Thomas writes them, Krish's handlers call them):

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

| Checkpoint | Thomas: AI, Frontend, AWS | Krish: Case Logic, Data, Pitch | Kaylin: API and Alerts |
|---|---|---|---|
| Hour one | SAM CLI installed. First `sam deploy` started | Product rules confirmed. `db.py` started | Read the contract in `api.md`. `list_cases` and `get_case` planned against `db.py` |
| Fri 3 PM | Stack deployed. Signals working locally | Categories submitted. Hero and normal accounts in `/data` | Tests for role filtering |
| Fri 4 PM | API URL and table names posted. Views checked on mock data | Seed data loaded. `db.py` done. Submit flow working on AI stubs | `list_cases` and `get_case` on real data |
| Fri 8 PM | Real memo from Opus 5, eval passes. Views wired to the live API | Submit flow on real scoring. Responses endpoint. Audit rows | `notify.py` with `doNotNotify`. Every endpoint checked on the live API |
| Sat midnight | Scam-check chat. Full flow on screen. Amplify hosting | Decision endpoint, demo reset, joint-owner and no-advisor accounts. Demo script. Architecture diagram | Stretch: SNS and SES alerts or EventBridge hold expiry |
| Sat 6 AM | AI slide. Drive the backup video | Deck done. Backup video recorded | Safety slide |
| Sat 12 PM | Q&A prep | Code ZIP and submission form | Q&A prep |

## Rules

- Work on a branch named after your lane (`ai/...`, `frontend/...`, `infra/...`, `backend/...`). Open a small pull request and get one teammate to look.
- Pull from main before starting something new, and merge every 2 to 3 hours. Tell Thomas when to redeploy.
- Never commit AWS keys. Keep the model ID and API URL in one config value each.
- Protect the core flow first: flag, memo, alerts, fraud team decision. Stretch items wait until midnight.
