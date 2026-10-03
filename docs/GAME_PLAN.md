# Second Look: Team Game Plan

Oct 2, 2026 · @Thomas

## The idea in one paragraph

We are building Second Look, an AI pause that catches scams where a client is tricked into moving their own money. When a risky withdrawal comes in, the system pauses it, has Claude explain in plain English why it looks like fraud, and alerts three people at once: the client, their financial advisor, and LPL's fraud team. Each one weighs in, and the fraud team makes the final call.

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

Judges score "right service for the right reason," so everyone should be able to explain this table. **Only claim what is live.** The full picture is in [`ARCHITECTURE.md`](ARCHITECTURE.md).

| Service | Status | What it does in our app | Why this one |
|---|---|---|---|
| Bedrock (Claude) | Live | Juno: Opus 5 scores the risk, writes the memo, runs the scam-check chat, answers clients' "Is this a scam?" questions, and answers staff questions. Hedges to Sonnet 5 if Opus is slow | Managed AI, data stays in our AWS account. Approved models are listed in [`AWS_SETUP.md`](AWS_SETUP.md#5-calling-claude) |
| Bedrock Guardrails | Live | Two guardrails: one refuses investment-advice questions to Juno, one masks identity and account numbers in everything the AI writes | Compliance enforced by the platform, not only by prompts |
| EventBridge Scheduler | Live | Every 15 minutes, escalates holds that passed their end date with no decision (never releases) | Exact timing with no server running |
| Lambda | Live | 10 functions: every endpoint plus hold expiry. Layers carry the AI code and seed data | Pay only when a request comes in |
| DynamoDB | Live | Accounts, transactions, cases, audit log | Fast, serverless storage |
| API Gateway | Live | Front door between the app and backend | Secure, managed API |
| KMS and CloudTrail | Live | One customer-managed key encrypts every table and the trail logs. CloudTrail records every API call and every table read and write | Security and audit trail, built in from the first deploy |
| Amplify | Live | Hosts the frontend at https://main.d1s6iogq4h15rg.amplifyapp.com (manual deploy with `scripts/deploy_frontend.py`, not auto-deploy from GitHub) | Managed static hosting with HTTPS |
| Cognito | In progress | Real logins for client, advisor, and fraud roles, replacing the `X-Role` header | Role comes from a verified identity |
| Step Functions | Not built | Would run the case as a visible workflow | Stretch |
| SNS and SES | Not built | Would deliver alerts by text and email. Alerts are in-app today | Stretch |
| Bedrock Knowledge Base | Not built | Would hold FINRA rule text so memos quote it | Stretch |

**Skip:** SageMaker (too slow to train) and Amazon Fraud Detector (likely closed to new customers).

## Who does what and how we use GitHub

We split work by folder so nobody edits the same files. For checklists and handoffs, see [`TEAM_PLAN.md`](TEAM_PLAN.md). For the architecture diagram, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

| Person | Folders | Owns |
|---|---|---|
| Thomas | `/ai`, `/frontend`, `/infra` | Everything Claude does (Bedrock client, scoring, memo, scam-check chat, Guardrails), all three app views, and all AWS setup (SAM template, IAM, tables, Amplify, Cognito). The only person who runs `sam deploy` |
| Kaylin | `/backend`, `/data` | Every API endpoint, DynamoDB helpers, case statuses, audit log, role filtering, alerts, seed data and loader |
| Krish | `/docs` (deck and demo) | Architecture diagram, category submission, deck, demo script, backup video, extra scam scenarios, submission form. Nothing on the critical path |

Thomas and Kaylin write the code. The file-by-file split is in [`TEAM_PLAN.md`](TEAM_PLAN.md#backend-file-map).

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
| Fri 3:00 PM | Submit categories: Best Technical Execution and Biggest Business Impact (Best Use of AWS is automatic) |
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
