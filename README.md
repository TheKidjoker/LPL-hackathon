# Second Look

**An AI pause for scams where clients are tricked into moving their own money.** When a risky withdrawal comes in, Second Look holds it, has **Juno** (our AI co-pilot, Claude on Amazon Bedrock) explain in plain English why it looks like fraud, and brings the client, their advisor, and the fraud team into one case. Only the fraud team can release it.

Built for the 2026 LPL Financial University Hackathon. **Deadline: Saturday 12:00 PM ET** (deck, code ZIP, submission form).

| | |
|---|---|
| **Live app** | https://secondlook-lpl.vercel.app (short link) → https://main.d1s6iogq4h15rg.amplifyapp.com |
| **Live API** | https://x9ku6sdgu3.execute-api.us-east-1.amazonaws.com/Prod |
| **Measured** | 9/9 scams held · 0 false positives · 10.9s average to a decision and memo · about 3¢ per withdrawal |

## What it does

- **Scores every withdrawal.** Seven rule checks plus Claude Opus 5's reasoning over 90 days of history give a 0 to 100 risk score, the signals behind it, and a memo citing FINRA Rule 2165 and proposed Rule 2166.
- **Holds risky ones safely.** A case is saved as held *before* the AI runs, and if the AI fails, it stays held for a person.
- **Never tips off the scammer.** Juno flags contacts who look involved (like a joint owner directing the transfer), and they are left out of the alerts.
- **Three role views, live.** The client confirms or denies and can add an emergency contact. The advisor adds notes. The fraud team sees everything and releases, extends, or escalates. Each role sees only what it should.
- **Ask Juno.** The fraud team and advisors can ask questions about a case. Answers come only from the case data, and every question is logged.
- **"Is this a scam?"** Before any money moves, a client can describe a call, text, or email and Juno says whether it looks like a scam and what to do. The check is saved to the client's contact log, so staff see it and a later withdrawal is scored with it.
- **The firm's memory.** Juno scores with the contact log (calls, emails, people asking about the client) and the advisor's CRM notes, and the staff views show that history next to the case.
- **Scam-check chat** for clients with no advisor.
- **Compliance built in:** Bedrock Guardrails refuse investment-advice requests and mask identity and account numbers; KMS encryption; CloudTrail on every table read and write; an audit row for every action; holds that reach their end date are escalated automatically, never released.

## Docs

| Doc | For |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Every feature, screen by screen, for each role; how FINRA rules are cited |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, request flow, AWS services and why, safety rules, code map |
| [docs/AI.md](docs/AI.md) | How Juno scores, chats, and answers; guardrails; prompt-injection defense; time budget; eval |
| [docs/IMPACT.md](docs/IMPACT.md) | The problem in sourced numbers, measured results, cost per case |
| [docs/RESULTS.md](docs/RESULTS.md) | Raw measured results, 3 runs × 6 scenarios on the live API |
| [docs/api.md](docs/api.md) | Every endpoint and data shape |
| [docs/DATA.md](docs/DATA.md) | The seed accounts, demo scenarios, pre-seeded cases, contact log and advisor notes |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Deploy, run locally, reset and run the demo, troubleshooting |
| [docs/DEV_SETUP.md](docs/DEV_SETUP.md) | Install, tests, and the repo layout |
| [docs/AWS_SETUP.md](docs/AWS_SETUP.md) | AWS login and which Claude models work |
| [docs/TEAM_PLAN.md](docs/TEAM_PLAN.md) | Who built what |
| [docs/GAME_PLAN.md](docs/GAME_PLAN.md) | The idea, timeline, and pitch |
| [docs/HACKATHON_CONTEXT.md](docs/HACKATHON_CONTEXT.md) | Rules, deliverables, judging |

## Quick start

```powershell
python -m venv .venv; .\.venv\Scripts\activate; pip install -r requirements-dev.txt
python -m pytest                     # all tests, no AWS needed
cd frontend; npm install; npm run dev  # http://localhost:5173 on mock data
```

To use the live API locally, put `VITE_API_URL=<live API>` in `frontend/.env.local`. Deploys: see [OPERATIONS.md](docs/OPERATIONS.md).

## Team

| Person | Built |
|---|---|
| Thomas | Juno (all AI), the frontend, all AWS infrastructure and deploys |
| Kaylin | The backend case logic, DynamoDB layer, audit log, seed data generator, measurement script |
| Krish | Deck, demo script, architecture diagram, submission |

Work on a branch and open a pull request. Don't push straight to main.
