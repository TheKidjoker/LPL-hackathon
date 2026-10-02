# Fraud Speed Bump: Team Game Plan

Oct 2, 2026 · @Thomas

## The idea in one paragraph

We are building an AI "speed bump" that catches scams where a client is tricked into moving their own money. When a risky withdrawal comes in, the system pauses it, has Claude explain in plain English why it looks like fraud, and alerts three people at once: the client, their financial advisor, and LPL's fraud team. Each one weighs in, and the fraud team makes the final call.

**Why it fits the prompt:** the prompt asks for a compliant, AI-powered startup that helps advisors, investors, or the teams that support them. We help all three, and compliance is the whole point of the product.

## The problem and why LPL would buy it

Scammers now use AI voice clones and fake websites to trick people, often seniors, into sending their own money away. Every security check passes because the real client is logging in. LPL has no public AI tool for this.

What LPL has today, from our research:

- **Cyber monitoring** for hacking and account takeovers (LPL cybersecurity).
- **A Cyber Fraud Guarantee** that does not cover money the client moves themselves. That is exactly our gap.
- **A human Senior Investor Protection team** that investigates elder exploitation by hand.
- **Cyan**, LPL's new AI agent, which focuses on advisor workflows, not fraud (Latitude announcement).

**Why now:** FINRA's proposed Rule 2166 would let firms pause a suspicious transaction for any client, not just seniors, for up to 10 business days (Federal Register, Sept 2026). LPL commented on these rules and pushed to rename "trusted contact" to "emergency contact" so more clients name one (LPL comment letter). We are building the tool for a rule LPL helped shape.

**How we say it:** "We built the AI co-pilot for LPL's fraud investigators." Never say "LPL has no fraud detection."

## How it works

1. A client asks to withdraw $180K to a brand new crypto exchange.
2. The system scores the risk using account history: new payee, full liquidation, unusual timing, client age.
3. If it looks risky, the withdrawal is paused and Claude writes a short memo explaining why, citing the FINRA rule.
4. The client, advisor, and fraud team are all alerted at the same time.
5. Each one responds, and the fraud team releases, extends, or escalates the hold.

| Who | What they see | What they can do |
|---|---|---|
| Client | "We paused a withdrawal to protect you. Did you request this?" plus scam warning signs | Confirm or deny, name an Emergency Contact |
| Advisor | Alert that their client has a held withdrawal, with the AI summary | Log what they know ("she's buying a house" or "this isn't like her") |
| Fraud team | Full case: memo, risk signals, client answer, advisor notes, timer, audit log | Make the final decision |

**Clients without an advisor:** instead of the advisor step, Claude runs a short in-app scam check ("Did someone contact you first? Were you told to keep this secret?"). Build this last.

**Three safety rules judges will ask about:**

- The advisor cannot release a hold alone. Sometimes the advisor is the fraud.
- Never alert a suspected scammer. If the AI thinks a joint owner or the emergency contact is involved, skip notifying them.
- Clients confirm inside the app only, never by replying to a text or clicking an email link. Otherwise scammers copy our alerts.

## AWS services and why we use each

Judges score "right service for the right reason," so everyone should be able to explain this table.

| Service | What it does in our app | Why this one |
|---|---|---|
| Bedrock (Claude) | Opus 5 scores the risk, writes the memo, and runs the scam-check chat | Managed AI, data stays in our AWS account. Approved models are listed in [`AWS_SETUP.md`](AWS_SETUP.md#5-calling-claude) |
| Bedrock Guardrails | Blocks investment advice and personal info leaks | Compliance built in |
| Bedrock Knowledge Base | Holds FINRA rule text so memos cite real rules | Answers grounded in regulation |
| Step Functions | Runs the case: flag, review, hold, notify, release | Every step visible and auditable |
| EventBridge Scheduler | Fires notice deadlines and hold expiry | Exact timers with no server running |
| Lambda | Scoring logic and API code | Pay only when a request comes in |
| DynamoDB | Accounts, transactions, cases, responses | Fast, serverless storage |
| API Gateway | Front door between the app and backend | Secure, managed API |
| Cognito | Logins with client, advisor, and fraud roles | Each role sees only its own view |
| SNS and SES | Sends alerts to all three parties | Reliable fan-out messaging |
| KMS and CloudTrail | Encryption and a log of who did what | Security and audit trail |
| Amplify | Hosts the frontend from GitHub | Auto-deploys on every push |

**Skip:** SageMaker (too slow to train) and Amazon Fraud Detector (likely closed to new customers).

## Who does what and how we use GitHub

We split work by folder so nobody edits the same files. For checklists and handoffs, see [`TEAM_PLAN.md`](TEAM_PLAN.md).

| Person | Folders | Owns |
|---|---|---|
| Thomas | `/backend`, `/infra`, `/ai` | Lambda, DynamoDB, Step Functions, API, Opus 5 scoring and memo, Guardrails. The only person who runs `sam deploy` |
| Kaylin | `/frontend`, `/data`, `/docs` | One app with three role views, Amplify hosting, fake accounts and scam scenarios, deck, demo script, video |

**Rules for the repo:**

- In hour one, agree on the data shapes and endpoints in [`/docs/api.md`](api.md). Then everyone builds to that.
- Nobody pushes straight to main. Work on a branch, open a small pull request, get one teammate to look, then merge.
- Pull from main before starting anything new, and merge every 2 to 3 hours.
- Never commit AWS keys. Put `.env` in `.gitignore`.
- Everyone uses the same AWS account and the same region.

## Timeline, deliverables, and pitch

All times Eastern. Build done by 6 AM Saturday. Hard deadline is noon Saturday.

| When | What |
|---|---|
| Fri 12:30 PM | AWS setup session. Confirm Bedrock and Claude access first. **Done:** Sonnet 5 call works via `us.anthropic.claude-sonnet-5` ([`AWS_SETUP.md`](AWS_SETUP.md#5-calling-claude)) |
| Fri 3:00 PM | Submit categories: Startup We'd Buy Tomorrow and Best Technical Execution |
| Fri 4:00 PM | Checkpoint: a fake request flows through the deployed API |
| Fri 8:00 PM | Checkpoint: the real AI memo shows on the dashboard |
| Sat 12:00 AM | Checkpoint: full flow works across all three views. Polish only after this |
| Sat 6:00 AM | Build frozen. Record backup demo video |
| Sat 12:00 PM | Deck, code ZIP, and submission form uploaded |
| Sat 12:30 PM | 5 minute pitch plus 5 minute Q&A |

**Required to submit:** deck on the LPL template, working demo, code ZIP, submission form. Also add the backup video and an architecture diagram.

**Pitch (5 minutes):** 30 seconds on Margaret's story, 30 seconds on the problem and Rule 2166, 2.5 minutes of live demo with three windows lighting up at once, 1 minute on AWS and safety, 30 seconds on why LPL should buy us.

**Biggest risks:**

- **Doing too much.** Core flow first: flag, memo, alerts, fraud decision. The self-directed scam check and extras come last.
- **AI that looks fake.** Make Claude's reasoning visible in the memo, not just simple if-statements.
- **"Doesn't LPL already have this?"** Answer: their tools target hacking. We target scams where the client moves the money, plus the Rule 2166 workflow, and we can plug into Cyan.
