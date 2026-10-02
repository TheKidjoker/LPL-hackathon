# Roles

Find your name, do your first steps, then work down your checklist. Setup for everyone is in [`docs/DEV_SETUP.md`](docs/DEV_SETUP.md). The full inventory and reasoning are in [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md).

| Person | Role | You own |
|---|---|---|
| [Thomas](#thomas-ai-frontend-and-aws) | AI, Frontend, and AWS | `ai/`, `frontend/`, `infra/`, deploys |
| [Krish](#krish-case-logic-data-and-pitch) | Case Logic, Data, and Pitch | Write endpoints, `data/`, architecture diagram, deck and demo |
| [Kaylin](#kaylin-api-and-alerts) | API and Alerts | Request helpers, read endpoints, role filtering, alerts |

**Everyone:** run `python -m pytest` before every pull request. Search the code for `TODO(<your name>)` to find your stubs. Keep function signatures and [`docs/api.md`](docs/api.md) shapes unchanged unless the team agrees.

---

## Thomas: AI, Frontend, and AWS

You make Claude explain the scam, build the three screens people see, and keep everything deployed. You are the only person who runs `sam deploy`.

**Your files:** `ai/fraud_ai/` (all), `frontend/` (all), `infra/` (all)

**First steps**

1. Install the SAM CLI (`winget install -e --id Amazon.SAM-CLI`), then `cd infra`, `sam build`, `sam deploy`. If the account blocks IAM role creation, fix the template first, since everyone waits on the deploy
2. Post `ApiUrl` and the four table names from the deploy output in the team chat
3. Build `ai/fraud_ai/signals.py`, then the memo prompt in `ai/fraud_ai/prompts/memo.txt`, then `score.py` with `converse_json` (the Bedrock client already works)

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Stack deployed. Signals work |
| Fri 4 PM | API URL and table names shared. Views checked on mock data |
| Fri 8 PM | `score_withdrawal` returns a real Opus 5 memo. Hero scores high, normal accounts score low. Views pointed at the live API. Redeploying after every merge |
| Sat midnight | `doNotNotify` and `scam_check_chat` work. Scam-check chat screen, scam warning signs, emergency contact field, hold timer. Frontend on Amplify |
| Sat 6 AM | AI slide for the deck. Drive the app for the backup video |

**Stretch, after midnight:** Cognito logins, Bedrock Guardrails, Knowledge Base with FINRA rule text

**You need from others:** seed data from Krish (Fri 4 PM), merged code from everyone to deploy

**Others need from you:** live API URL and table names (Fri 4 PM), a real `score_withdrawal` for Krish (Fri 8 PM), a redeploy after each merge

---

## Krish: Case Logic, Data, and Pitch

You write the rules of a case and the fake data that tells the story, and you own the pitch and the architecture diagram.

**Your files:** `backend/common/db.py`, `case_state.py`, `audit.py`, `samples.py`, `backend/handlers/submit_withdrawal.py`, `post_response.py`, `post_decision.py`, `demo_reset.py`, `data/`, `scripts/seed_dynamodb.py`

**First steps**

1. Submit the categories by Fri 3 PM: Startup We'd Buy Tomorrow and Best Technical Execution
2. Write `data/accounts.json` and `data/transactions.json`: the hero (age 78, $180K to a new crypto payee), 3 normal accounts, 1 where the joint owner is the scammer, 1 with no advisor. Give every account 90 days of normal history
3. Build `db.py` first, since Kaylin's read endpoints use it

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Categories submitted. Hero and normal accounts in `data/` |
| Fri 4 PM | `db.py` done. Seed data loaded into the tables. `submit_withdrawal` saves a real Case using the AI stub |
| Fri 8 PM | `submit_withdrawal` uses Thomas's real scoring. `post_response` saves client and advisor answers. Every change writes an audit row |
| Sat midnight | `post_decision` (fraud team only) and `demo_reset` work. Demo script written. Architecture diagram done (start from [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)) |
| Sat 6 AM | Deck done. Backup video recorded |
| Sat 12 PM | Code ZIP and submission form uploaded |

**You need from others:** table names from Thomas (Fri 4 PM), real `score_withdrawal` from Thomas (Fri 8 PM), AI slide from Thomas and safety slide from Kaylin (Sat 6 AM)

**Others need from you:** `db.py` for Kaylin, seed data for everyone (Fri 4 PM)

---

## Kaylin: API and Alerts

You own the shared request code, the endpoints the views read, what each role is allowed to see, and who gets alerted.

**Your files:** `backend/common/http.py`, `roles.py`, `views.py`, `backend/handlers/list_cases.py`, `get_case.py`, `backend/notify.py`, tests for these in `tests/`

**First steps**

1. Read [`docs/api.md`](docs/api.md), especially "What each role sees in a Case". `views.py` already applies it. Make sure it matches
2. Write tests for role filtering: the client never sees the memo or advisor notes, the advisor never sees `doNotNotify` or the audit log
3. Switch `list_cases` and `get_case` from sample data to Krish's `db.py` as soon as it lands

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Role filtering tests written |
| Fri 4 PM | `list_cases` (held first, newest first) and `get_case` (404 when missing, audit rows for the fraud role) on real data |
| Fri 8 PM | `notify.py` alerts the client, advisor, emergency contact, and fraud team, skipping everyone in `doNotNotify`. Every endpoint checked against the live API after each redeploy |
| Sat midnight | One stretch item: SNS and SES alerts with no links, or EventBridge Scheduler to end holds |
| Sat 6 AM | Safety slide for the deck: role filtering, who gets alerted, audit log |

**Stretch, after midnight:** SNS and SES alerts, EventBridge hold expiry, Step Functions, CloudTrail and KMS. Add AWS resources to `infra/template.yaml` by pull request so Thomas can deploy them

**You need from others:** `db.py` from Krish (Fri 4 PM), live API URL from Thomas (Fri 4 PM)

**Others need from you:** working read endpoints for Thomas's views (Fri 4 PM)

---

## All three

- **Hour one:** confirm the product rules in [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md#product-rules-decide-in-hour-one-all-three) (hold at score 70+, 10 business days, only the fraud team releases)
- **Every 2 to 3 hours:** pull from main, merge your branch, tell Thomas to redeploy
- **Sat 10 AM:** Q&A prep together: the three safety rules, false positives, cost per case, why Bedrock
- **Sat 12:30 PM:** pitch
