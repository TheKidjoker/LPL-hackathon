# Team Plan: Who Builds What

Three people, four jobs. Each person owns their folders. If you need to change someone else's folder, open a pull request and tag them.

| Person | Owns | Folders |
|---|---|---|
| **1. Backend and AWS** | API, database, workflow, deploys. The only person who runs `sam deploy` | `/backend`, `/infra` |
| **2. AI and Data** | Claude prompts, risk scoring, fake accounts and scam scenarios, Guardrails | `/ai`, `/data` |
| **3. Frontend and Pitch** | The app with three role views, hosting, deck, demo video | `/frontend`, `/docs` (deck and demo script) |

Write your name next to a number before you start:

- Person 1:
- Person 2:
- Person 3:

## Hour one: everyone together

1. **AWS access.** Everyone runs `.\scripts\aws-login.ps1` and the checks in [`AWS_SETUP.md`](AWS_SETUP.md).
2. **Fill in [`api.md`](api.md).** Agree on the data shapes (Account, Transaction, Case, Response) and about five endpoints:
   - `POST /withdrawals`: submit a withdrawal and get a risk decision
   - `GET /cases` and `GET /cases/{id}`: fraud team list and one case
   - `POST /cases/{id}/responses`: client or advisor answer
   - `POST /cases/{id}/decision`: fraud team releases, extends, or escalates
3. **Merge `api.md`.** After this, change it only by pull request, and tell the team.

## Person 1: Backend and AWS

**By Fri 4 PM: a fake request flows through the deployed API**

- [ ] SAM template in `/infra` with API Gateway, Lambda, and DynamoDB tables (Accounts, Transactions, Cases)
- [ ] One Lambda per endpoint in `api.md`, at first returning stored or mock data
- [ ] Deploy and share the API URL in the team chat

**By Fri 8 PM: the real memo comes back from the API**

- [ ] `POST /withdrawals` calls Person 2's scoring and memo function and saves the Case
- [ ] Load Person 2's seed data into DynamoDB

**By Sat midnight: full flow**

- [ ] Responses and decision endpoints update the Case and write an audit log entry
- [ ] Safety rule enforced in code: an advisor cannot release a hold

**Stretch, only after midnight:** Step Functions for the case flow, EventBridge hold timers, SNS and SES alerts, Cognito logins.

## Person 2: AI and Data

**By Fri 4 PM: test data exists**

- [ ] `/data` JSON with the hero scenario (age 78, $180K full liquidation to a crypto exchange payee added hours ago) plus 2 or 3 normal accounts that should not be flagged
- [ ] Share the file so Persons 1 and 3 can use it right away

**By Fri 8 PM: Claude writes a real memo**

- [ ] Function in `/ai` that takes an account and a transaction, calls Opus 5 (`us.anthropic.claude-opus-5`), and returns `{ score, signals[], memo }` as JSON
- [ ] The memo is about 120 words, names the risk signals, and cites FINRA Rule 2165 and proposed Rule 2166
- [ ] Check it on every scenario: the scam scores high and normal accounts score low

**By Sat midnight**

- [ ] Hand Person 1 a function they can import into the Lambda
- [ ] Rule for "never alert a suspected scammer": if a joint owner or the emergency contact looks involved, flag it in the output

**Stretch:** Bedrock Guardrails (block investment advice and personal info), a Knowledge Base with FINRA rule text, the in-app scam check for clients without an advisor.

## Person 3: Frontend and Pitch

**By Fri 4 PM: three views on mock data**

- [ ] One app with a role switcher: Client, Advisor, Fraud team
- [ ] Each view reads mock JSON shaped exactly like `api.md`

**By Fri 8 PM: wired to the real API**

- [ ] Switch mock data to Person 1's API URL
- [ ] The fraud team view shows the Claude memo, risk signals, and a hold timer

**By Sat midnight: full flow on screen**

- [ ] Client can confirm or deny. Advisor can add notes. Fraud team can release, extend, or escalate
- [ ] Hosted on Amplify from GitHub

**Pitch, starting Sat midnight:**

- [ ] Deck, demo script, and a backup demo video recorded by 6 AM
- [ ] Practice the three safety rules and the "AI co-pilot for LPL's fraud investigators" line

## Handoffs

| From | To | What | When |
|---|---|---|---|
| Everyone | Everyone | Merged `api.md` | End of hour one |
| Person 2 | Persons 1 and 3 | Seed data JSON | Fri 4 PM |
| Person 1 | Person 3 | Live API URL | Fri 4 PM |
| Person 2 | Person 1 | Scoring and memo function | Fri 8 PM |
| Persons 1 and 2 | Person 3 | Working demo for the video | Sat 6 AM |

## Rules

- Work on a branch named after your role (`backend/...`, `ai/...`, `frontend/...`). Open a small pull request and get one teammate to look.
- Pull from main before starting something new, and merge every 2 to 3 hours.
- Never commit AWS keys. Keep the model ID in one config value.
- Protect the core flow first: flag, memo, alerts, fraud team decision. Stretch items wait until midnight.
