# Roles

Find your name, do your first steps, then work down your checklist. Setup for everyone is in [`docs/DEV_SETUP.md`](docs/DEV_SETUP.md). The full inventory and reasoning are in [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md).

| Person | Role | You own |
|---|---|---|
| [Thomas](#thomas-ai-and-frontend) | AI and Frontend | `ai/`, `frontend/` |
| [Krish](#krish-aws-and-platform) | AWS and Platform | `infra/`, read endpoints, alerts, deploys |
| [Kaylin](#kaylin-case-logic-data-and-pitch) | Case Logic, Data, and Pitch | Write endpoints, `data/`, deck and demo |

**Everyone:** run `python -m pytest` before every pull request. Search the code for `TODO(<your name>)` to find your stubs. Keep function signatures and [`docs/api.md`](docs/api.md) shapes unchanged unless the team agrees.

---

## Thomas: AI and Frontend

You make Claude explain the scam, and you build the three screens people see.

**Your files:** `ai/fraud_ai/` (all), `frontend/` (all)

**First steps**

1. `cd frontend`, `npm install`, `npm run dev`. Click through all three views on mock data
2. Build `ai/fraud_ai/signals.py`: new payee, full liquidation, age 65+, first crypto, unusual timing, payee added within 24 hours
3. Write the memo prompt in `ai/fraud_ai/prompts/memo.txt`, then build `score.py` with `converse_json` (the Bedrock client already works)

**Checklist**

| By | Done when |
|---|---|
| Fri 4 PM | Signals work. Three views look right on mock data |
| Fri 8 PM | `score_withdrawal` returns a real Opus 5 memo. Hero scores high, normal accounts score low. Views pointed at Krish's live API |
| Sat midnight | `doNotNotify` works. `scam_check_chat` works. Scam-check chat screen. Scam warning signs and emergency contact on the client view. Hold timer on the fraud view |
| Sat 6 AM | AI slide for the deck. Drive the app for the backup video |

**You need from others:** seed data from Kaylin (Fri 4 PM), live API URL from Krish (Fri 4 PM)

**Others need from you:** a real `score_withdrawal` for Kaylin (Fri 8 PM)

---

## Krish: AWS and Platform

You get everything deployed and keep it running. You are the only person who runs `sam deploy`.

**Your files:** `infra/`, `backend/common/http.py`, `roles.py`, `views.py`, `backend/handlers/list_cases.py`, `get_case.py`, `backend/notify.py`

**First steps**

1. Install the SAM CLI: `winget install -e --id Amazon.SAM-CLI`
2. `cd infra`, `sam build`, `sam deploy`. If the account blocks IAM role creation, tell the team right away
3. Post `ApiUrl` and the four table names from the deploy output in the team chat

**Checklist**

| By | Done when |
|---|---|
| Fri 4 PM | Stack deployed. API URL and table names shared |
| Fri 8 PM | `list_cases` and `get_case` read real data through Kaylin's `db.py`. Redeploying after every merge |
| Sat midnight | `notify.py` skips everyone in `doNotNotify`. Frontend hosted on Amplify. Architecture diagram done (start from [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)) |
| Sat 6 AM | Architecture slide |
| Sat 12 PM | Code ZIP and submission form uploaded |

**Stretch, after midnight:** Cognito logins, SNS and SES alerts, EventBridge hold timers, Step Functions, CloudTrail and KMS

**You need from others:** `db.py` from Kaylin, merged code from everyone to deploy

**Others need from you:** live API URL and table names (Fri 4 PM), a redeploy after each merge

---

## Kaylin: Case Logic, Data, and Pitch

You write the rules of a case, the fake data that tells the story, and the pitch.

**Your files:** `backend/common/db.py`, `case_state.py`, `audit.py`, `backend/handlers/submit_withdrawal.py`, `post_response.py`, `post_decision.py`, `demo_reset.py`, `data/`, `scripts/seed_dynamodb.py`

**First steps**

1. Submit the categories by Fri 3 PM: Startup We'd Buy Tomorrow and Best Technical Execution
2. Write `data/accounts.json` and `data/transactions.json`: the hero (age 78, $180K to a new crypto payee), 3 normal accounts, 1 where the joint owner is the scammer, 1 with no advisor. Give every account 90 days of normal history
3. Build `db.py` so Krish's read endpoints can use it

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Categories submitted |
| Fri 4 PM | Seed data loaded into Krish's tables. `submit_withdrawal` saves a real Case using the AI stub |
| Fri 8 PM | `submit_withdrawal` uses Thomas's real scoring. `post_response` saves client and advisor answers. Every change writes an audit row |
| Sat midnight | `post_decision` (fraud team only) and `demo_reset` work. Demo script written |
| Sat 6 AM | Deck done. Backup video recorded |

**You need from others:** table names from Krish (Fri 4 PM), real `score_withdrawal` from Thomas (Fri 8 PM)

**Others need from you:** `db.py` for Krish, seed data for everyone (Fri 4 PM)

---

## All three

- **Hour one:** confirm the product rules in [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md#product-rules-decide-in-hour-one-all-three) (hold at score 70+, 10 business days, only the fraud team releases)
- **Every 2 to 3 hours:** pull from main, merge your branch, tell Krish to redeploy
- **Sat 10 AM:** Q&A prep together: the three safety rules, false positives, cost per case, why Bedrock
- **Sat 12:30 PM:** pitch
