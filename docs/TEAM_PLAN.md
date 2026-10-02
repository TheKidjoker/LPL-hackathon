# Team Plan: Who Builds What

Two people. Each owns their folders. If you need to change the other person's folder, open a pull request and tag them.

| Person | Owns | Folders |
|---|---|---|
| **Thomas: Backend, AWS, and AI** | API, database, workflow, deploys, Claude scoring and memo, Guardrails. The only person who runs `sam deploy` | `/backend`, `/infra`, `/ai` |
| **Kaylin: Frontend, Data, and Pitch** | The app with three role views, hosting, fake accounts and scam scenarios, deck, demo video | `/frontend`, `/data`, `/docs` (deck and demo script) |

Thomas owns both backend and AI, so the Claude call lives right inside the Lambda with no handoff between people.

## Hour one: together

1. **AWS access.** Both run `.\scripts\aws-login.ps1` and the checks in [`AWS_SETUP.md`](AWS_SETUP.md). Kaylin needs it for Amplify hosting.
2. **Fill in [`api.md`](api.md).** Agree on the data shapes (Account, Transaction, Case, Response) and about five endpoints:
   - `POST /withdrawals`: submit a withdrawal and get a risk decision
   - `GET /cases` and `GET /cases/{id}`: fraud team list and one case
   - `POST /cases/{id}/responses`: client or advisor answer
   - `POST /cases/{id}/decision`: fraud team releases, extends, or escalates
3. **Merge `api.md`.** After this, change it only by pull request, and tell the other person.

## Thomas: Backend, AWS, and AI

**By Fri 4 PM: a fake request flows through the deployed API**

- [ ] SAM template in `/infra` with API Gateway, Lambda, and DynamoDB tables (Accounts, Transactions, Cases)
- [ ] One Lambda per endpoint in `api.md`, at first returning mock data
- [ ] Deploy and send Kaylin the API URL

**By Fri 8 PM: the real memo comes back from the API**

- [ ] Function in `/ai` that takes an account and a transaction, calls Opus 5 (`us.anthropic.claude-opus-5`), and returns `{ score, signals[], memo }` as JSON
- [ ] The memo is about 120 words, names the risk signals, and cites FINRA Rule 2165 and proposed Rule 2166
- [ ] `POST /withdrawals` calls it and saves the Case
- [ ] Load Kaylin's seed data into DynamoDB. Check that the scam scores high and the normal accounts score low

**By Sat midnight: full flow**

- [ ] Responses and decision endpoints update the Case and write an audit log entry
- [ ] Safety rules in code: an advisor cannot release a hold, and a suspected scammer (joint owner or emergency contact) is never alerted

**Stretch, only after midnight:** Step Functions for the case flow, EventBridge hold timers, SNS and SES alerts, Cognito logins, Bedrock Guardrails, a Knowledge Base with FINRA rule text, the in-app scam check for clients without an advisor.

## Kaylin: Frontend, Data, and Pitch

**By Fri 4 PM: test data and three views on mock data**

- [ ] `/data` JSON with the hero scenario (age 78, $180K full liquidation to a crypto exchange payee added hours ago) plus 2 or 3 normal accounts that should not be flagged. Send it to Thomas first, since it unblocks the memo work
- [ ] One app with a role switcher: Client, Advisor, Fraud team
- [ ] Each view reads mock JSON shaped exactly like `api.md`

**By Fri 8 PM: wired to the real API**

- [ ] Switch from mock data to Thomas's API URL
- [ ] The fraud team view shows the Claude memo, risk signals, and a hold timer

**By Sat midnight: full flow on screen**

- [ ] Client can confirm or deny. Advisor can add notes. Fraud team can release, extend, or escalate
- [ ] Hosted on Amplify from GitHub

**Pitch, starting Sat midnight (Thomas joins once the build is frozen):**

- [ ] Deck, demo script, and a backup demo video recorded by 6 AM
- [ ] Both practice the three safety rules and the "AI co-pilot for LPL's fraud investigators" line

## Handoffs

| From | To | What | When |
|---|---|---|---|
| Both | Both | Merged `api.md` | End of hour one |
| Kaylin | Thomas | Seed data JSON | As early as possible, by Fri 4 PM |
| Thomas | Kaylin | Live API URL | Fri 4 PM |
| Thomas | Kaylin | Working demo for the video | Sat 6 AM |

## Rules

- Work on a branch named after your area (`backend/...`, `ai/...`, `frontend/...`). Open a small pull request and get the other person to look.
- Pull from main before starting something new, and merge every 2 to 3 hours.
- Never commit AWS keys. Keep the model ID in one config value.
- Protect the core flow first: flag, memo, alerts, fraud team decision. Stretch items wait until midnight.
