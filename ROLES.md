# Roles

Find your name, do your first steps, then work down your checklist. Setup for everyone is in [`docs/DEV_SETUP.md`](docs/DEV_SETUP.md). The full inventory is in [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md).

| Person | Role | You own |
|---|---|---|
| [Thomas](#thomas-ai-frontend-and-aws) | AI, Frontend, and AWS | `ai/`, `frontend/`, `infra/`, deploys |
| [Kaylin](#kaylin-backend-and-data) | Backend and Data | Every API endpoint, DynamoDB code, `data/` |
| [Krish](#krish-pitch-and-demo) | Pitch and Demo | Deck, demo script, architecture diagram, submission |

**Stack:** DynamoDB for every table. One KMS key encrypts all tables and the CloudTrail logs. CloudTrail records every API call and every table read and write. All three are in `infra/template.yaml` and go live on the first deploy.

**Everyone:** run `python -m pytest` before every pull request. Search the code for `TODO(<your name>)` to find your stubs. Keep function signatures and [`docs/api.md`](docs/api.md) shapes unchanged unless the team agrees.

---

## Thomas: AI, Frontend, and AWS

You make Claude explain the scam, build the three screens people see, and keep everything deployed. You are the only person who runs `sam deploy`.

**Your files:** `ai/fraud_ai/` (all), `frontend/` (all), `infra/` (all)

**First steps**

1. Install the SAM CLI (`winget install -e --id Amazon.SAM-CLI`), then `cd infra`, `sam build`, `sam deploy`. If the account blocks creating IAM roles, KMS keys, or trails, fix the template first, since everyone waits on the deploy
2. Post `ApiUrl` and the four table names from the deploy output in the team chat
3. Build `ai/fraud_ai/signals.py`, then the memo prompt in `ai/fraud_ai/prompts/memo.txt`, then `score.py` with `converse_json` (the Bedrock client already works)

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Stack deployed: tables encrypted with KMS, CloudTrail logging. Signals work |
| Fri 4 PM | API URL and table names shared. Views checked on mock data |
| Fri 8 PM | `score_withdrawal` returns a real Opus 5 memo. Hero scores high, normal accounts score low. Views pointed at the live API. Redeploying after every merge |
| Sat midnight | `doNotNotify` and `scam_check_chat` work. Scam-check chat screen, scam warning signs, emergency contact field, hold timer. Frontend on Amplify |
| Sat 6 AM | AI and AWS slide for the deck. Drive the app for the backup video |

**Stretch, after midnight:** Cognito logins, Bedrock Guardrails, SNS and SES alerts, EventBridge hold timers

**You need from others:** seed data from Kaylin (Fri 4 PM), merged code from Kaylin to deploy

**Others need from you:** live API URL and table names (Fri 4 PM), a real `score_withdrawal` for Kaylin (Fri 8 PM), a redeploy after each merge

---

## Kaylin: Backend and Data

You build every API endpoint, everything that reads and writes DynamoDB, and the fake data that tells the story.

**Your files:** everything in `backend/`, `data/`, `scripts/seed_dynamodb.py`, `events/`, `tests/`

**First steps**

1. Write `data/accounts.json` and `data/transactions.json`: the hero (age 78, $180K to a new crypto payee), 3 normal accounts, 1 where the joint owner is the scammer, 1 with no advisor. Give every account 90 days of normal history
2. Build `backend/common/db.py` (DynamoDB returns numbers as `Decimal`, convert them) and `audit.py`
3. Once Thomas deploys, load the data with `scripts/seed_dynamodb.py`, then switch `submit_withdrawal` from sample data to real data

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Hero and normal accounts in `data/`. `db.py` working |
| Fri 4 PM | Seed data loaded. `submit_withdrawal` saves a real Case using the AI stub. `list_cases` and `get_case` read real data |
| Fri 8 PM | `submit_withdrawal` uses Thomas's real scoring. `post_response` saves client and advisor answers. Every change writes an audit row |
| Sat midnight | `post_decision` (fraud team only) and `demo_reset` work. `notify.py` skips everyone in `doNotNotify`. Joint-owner and no-advisor accounts work end to end |
| Sat 6 AM | Help Krish with the safety slide: role filtering, who gets alerted, audit log, encryption |

**You need from others:** table names from Thomas (Fri 4 PM), real `score_withdrawal` from Thomas (Fri 8 PM)

**Others need from you:** seed data (Fri 4 PM), working endpoints for Thomas's views (Fri 4 PM), merged code for Thomas to deploy

---

## Krish: Pitch and Demo

You own everything the judges see besides the app. Nothing in the build waits on you, so work at your own pace and check in every few hours.

**Your files:** the deck, `docs/DEMO_SCRIPT.md`, the architecture diagram

**First steps**

1. Submit the categories by Fri 3 PM: Startup We'd Buy Tomorrow and Best Technical Execution
2. Read [`docs/GAME_PLAN.md`](docs/GAME_PLAN.md) and start the deck on the LPL template
3. Turn [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) into a clean architecture diagram. Show DynamoDB, KMS, and CloudTrail

**Checklist**

| By | Done when |
|---|---|
| Fri 3 PM | Categories submitted |
| Fri 8 PM | Architecture diagram done. Deck outline: problem, why now (Rule 2166), demo, architecture, safety rules, why LPL buys it |
| Sat midnight | Demo script in `docs/DEMO_SCRIPT.md`: the $180K hero through all three views, then the joint-owner and no-advisor cases |
| Sat 6 AM | Deck done. Backup video recorded with Thomas driving the app |
| Sat 12 PM | Code ZIP and submission form uploaded |

**Stretch:** write 2 more scam scenarios (romance scam, fake tech support) as JSON for Kaylin to load

**You need from others:** AI and AWS slide from Thomas, safety slide input from Kaylin (Sat 6 AM)

---

## All three

- **Hour one:** confirm the product rules in [`docs/TEAM_PLAN.md`](docs/TEAM_PLAN.md#product-rules-decide-in-hour-one-all-three) (hold at score 70+, 10 business days, only the fraud team releases)
- **Every 2 to 3 hours:** pull from main, merge your branch, tell Thomas to redeploy
- **Sat 10 AM:** Q&A prep together: the three safety rules, false positives, cost per case, why Bedrock, how data is encrypted
- **Sat 12:30 PM:** pitch
