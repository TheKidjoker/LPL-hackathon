# Team Plan: Who Builds What

Three people, three lanes. Each person owns their folders and the interface they hand to the others. To change someone else's folder, open a pull request and tag them. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for how the pieces connect.

| Person | Lane | Folders | Hands to the others |
|---|---|---|---|
| **Thomas** | Frontend and Pitch | `/frontend`, `/docs` (deck, demo script) | The app, the deck, the demo video |
| **Krish** | Backend and AWS | `/backend`, `/infra` | Live API URL that matches `api.md`. The only person who runs `sam deploy` |
| **Kaylin** | AI and Data | `/ai`, `/data` | `score_withdrawal` and `scam_check_chat` functions, seed data JSON |

## The two interfaces everyone builds to

Agree on both in hour one. After that, change them only by pull request.

**1. The API (Thomas and Krish).** Fill in [`api.md`](api.md) with the data shapes (Account, Transaction, Case, Response) and these endpoints:

| Endpoint | Who calls it | Does |
|---|---|---|
| `POST /withdrawals` | Client view | Submit a withdrawal. Returns the Case with risk score, status, and memo |
| `GET /cases` | Fraud team view | List cases, held first |
| `GET /cases/{id}` | All three views | One case. Each role sees only its fields |
| `POST /cases/{id}/responses` | Client and advisor views | Client confirms or denies. Advisor adds notes. No-advisor clients get a chat reply |
| `POST /cases/{id}/decision` | Fraud team view | Release, extend, or escalate. Rejected for any role except `fraud` |

**2. The AI functions (Krish and Kaylin).** Python in `/ai`, imported by Krish's Lambdas:

```python
score_withdrawal(account: dict, transaction: dict, history: list[dict]) -> dict
# returns {"score": 0-100, "level": "low"|"medium"|"high",
#          "signals": [{"name": str, "detail": str}],
#          "memo": str, "do_not_notify": [contact_id, ...]}

scam_check_chat(case: dict, messages: list[dict]) -> dict
# returns {"reply": str, "risk_update": int | None, "done": bool}
```

Until the real functions land, Kaylin commits stubs with these exact signatures that return fixed sample output, so Krish is never blocked.

## Hour one: all three together

- [ ] Everyone runs `.\scripts\aws-login.ps1` and the checks in [`AWS_SETUP.md`](AWS_SETUP.md)
- [ ] Fill in and merge `api.md`
- [ ] Agree on the two AI function signatures above
- [ ] Kaylin commits the AI stubs. Krish creates the SAM project. Thomas creates the frontend app

## Thomas: Frontend and Pitch

**Goal:** one app, three role views, that tells the scam story clearly in a 5 minute demo.

**By Fri 4 PM: three views on mock data**

- [ ] React app in `/frontend` with a role switcher: Client, Advisor, Fraud team
- [ ] Mock JSON in the exact shapes from `api.md`, kept in one file so it is easy to swap out
- [ ] Client view: withdrawal form with the $180K crypto request pre-filled for the demo
- [ ] Fraud team view: case list, held cases first

**By Fri 8 PM: wired to Krish's API**

- [ ] Swap mock data for the live API URL, kept in one config value
- [ ] Case detail page: risk score, signals list, Claude memo, hold timer
- [ ] "Reviewing..." state while the withdrawal is scored (takes about 7 seconds)

**By Sat midnight: full flow on screen**

- [ ] Client: "We paused a withdrawal to protect you. Did you request this?" with confirm or deny, scam warning signs, and a field to name an emergency contact
- [ ] Advisor: alert banner, the AI summary, and a notes box
- [ ] Fraud team: client answer, advisor notes, audit log, and release, extend, or escalate buttons
- [ ] Hosted on Amplify from GitHub

**Pitch, from Sat midnight (Krish and Kaylin join after the build freezes):**

- [ ] Architecture diagram for the deck and submission: how Claude on Bedrock connects to each AWS service. Start from the draft in `ARCHITECTURE.md`, and check it with Krish and Kaylin
- [ ] Deck: problem, demo, architecture diagram, the three safety rules, why LPL buys it
- [ ] Demo script that walks the $180K scenario through all three views
- [ ] Backup demo video recorded by 6 AM

**Stretch:** Cognito logins per role, the scam-check chat screen for no-advisor clients, mobile layout.

## Krish: Backend and AWS

**Goal:** a deployed API that stores cases and calls Kaylin's functions.

**By Fri 4 PM: a fake request flows through the deployed API**

- [ ] SAM template in `/infra`: API Gateway, Lambdas, and DynamoDB tables (Accounts, Transactions, Cases, Audit)
- [ ] One Lambda per endpoint, returning mock data in the `api.md` shapes
- [ ] IAM role for the Lambdas with `bedrock:InvokeModel` on Opus 5 and Sonnet 5
- [ ] Deploy and post the API URL in the team chat

**By Fri 8 PM: the real memo comes back**

- [ ] `POST /withdrawals` loads the account and history, calls `score_withdrawal`, and saves the Case as `HELD` (score 70 or higher) or `RELEASED`
- [ ] Load Kaylin's seed data into DynamoDB
- [ ] Lambda timeout of 30 seconds or more so the Claude call never gets cut off

**By Sat midnight: full flow**

- [ ] Responses and decision endpoints update the Case and write an Audit row every time
- [ ] Decision endpoint rejects any role except `fraud`
- [ ] Notifications skip every contact in `do_not_notify`
- [ ] No-advisor responses call `scam_check_chat`

**Stretch:** Step Functions for the case flow, EventBridge Scheduler for hold expiry, SNS and SES alerts, Cognito authorizer on the API, CloudTrail and KMS.

## Kaylin: AI and Data

**Goal:** Claude explains clearly why a withdrawal looks like a scam, and stays quiet on normal ones.

**By Fri 4 PM: data and stubs**

- [ ] AI stubs in `/ai` with the exact signatures above, returning fixed sample output
- [ ] Seed data in `/data`: the hero scenario (age 78, 22-year account, $180K full liquidation to a crypto exchange payee added 2 hours ago, client says a "bank security officer" called) plus 3 normal accounts that should not be flagged. Send it to Krish and Thomas
- [ ] Rule-based signals in Python: new payee, full liquidation, client age 65 or older, first-ever crypto, unusual timing

**By Fri 8 PM: the real memo**

- [ ] `score_withdrawal` calls Opus 5 (`us.anthropic.claude-opus-5`) through the Bedrock Converse API with the signals and history, and returns the JSON above
- [ ] Prompt rules: about 120 words, plain English, names each signal, cites FINRA Rule 2165 and proposed Rule 2166, never gives investment advice
- [ ] Ask for JSON only, and parse the reply that has `text` (Opus 5 returns a reasoning block first). Set `maxTokens` to 2000
- [ ] Test on every scenario: the hero scores high, the normal accounts score low

**By Sat midnight**

- [ ] `do_not_notify`: Claude flags a joint owner or emergency contact who looks involved
- [ ] `scam_check_chat`: asks "Did someone contact you first?" and "Were you told to keep this secret?", then returns a risk update
- [ ] 2 more scam scenarios for the demo (romance scam, fake tech support)

**Stretch:** Bedrock Guardrails on both calls (block investment advice and personal info), Knowledge Base with FINRA rule text so memos quote the rule.

## Handoffs

| From | To | What | When |
|---|---|---|---|
| All | All | Merged `api.md` and AI signatures | End of hour one |
| Kaylin | Krish | AI stubs | End of hour one |
| Kaylin | Krish and Thomas | Seed data JSON | Fri 4 PM |
| Krish | Thomas | Live API URL | Fri 4 PM |
| Kaylin | Krish | Real `score_withdrawal` | Fri 8 PM |
| Krish and Kaylin | Thomas | Working full flow for the video | Sat 6 AM |

## Rules

- Work on a branch named after your lane (`frontend/...`, `backend/...`, `ai/...`). Open a small pull request and get one teammate to look.
- Pull from main before starting something new, and merge every 2 to 3 hours.
- Never commit AWS keys. Keep the model ID and API URL in one config value each.
- Protect the core flow first: flag, memo, alerts, fraud team decision. Stretch items wait until midnight.
