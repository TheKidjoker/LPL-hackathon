# Architecture

Second Look pauses risky withdrawals, has **Juno** (our AI co-pilot, built on Claude via Amazon Bedrock) explain why in plain English, and brings the client, their advisor, and the fraud team into one case. Everything runs serverless in one AWS account in `us-east-1`, deployed as one SAM stack (`fraud-speed-bump`).

Live API: `https://x9ku6sdgu3.execute-api.us-east-1.amazonaws.com/Prod`

## System diagram

```mermaid
flowchart LR
    subgraph Users["People"]
        C[Client]
        A[Advisor]
        F[Fraud team]
    end

    subgraph Web["Frontend (React + Vite)"]
        UI["Three role views<br/>polls every 4s"]
    end

    subgraph API["API Gateway + Lambda (Python 3.11)"]
        SUB[POST /withdrawals]
        READ["GET /cases<br/>GET /cases/{id}<br/>GET /cases/{id}/context"]
        RESP[POST /cases/{id}/responses]
        DEC[POST /cases/{id}/decision]
        ASK[POST /cases/{id}/assistant]
        CHECK[POST /scam-check]
        RESET[POST /demo/reset]
    end

    subgraph AI["Juno (ai/fraud_ai, Lambda layer)"]
        SIG[Rule signals]
        SCORE[score_withdrawal]
        CHAT[scam_check_chat]
        ASSIST[assistant.ask]
        CONTACT[check_contact]
    end

    subgraph Bedrock["Amazon Bedrock"]
        OPUS["Claude Opus 5<br/>hedged to Sonnet 5"]
        GQ[Guardrail: questions]
        GO[Guardrail: output masking]
    end

    subgraph Data["Data and security"]
        DDB[("DynamoDB<br/>Accounts, Transactions,<br/>Cases, Audit")]
        KMS[KMS key]
        CT[CloudTrail]
    end

    SCHED[EventBridge Scheduler<br/>every 15 min] --> EXP[hold_expiry Lambda]

    C & A & F --> UI --> API
    SUB --> SIG --> SCORE
    RESP --> CHAT
    ASK --> GQ --> ASSIST
    CHECK --> CONTACT
    SCORE & CHAT & ASSIST & CONTACT --> OPUS --> GO
    API --> DDB
    EXP --> DDB
    KMS -. encrypts .-> DDB
    KMS -. encrypts .-> CT
    DDB -. every read and write .-> CT
```

## Before a withdrawal: "Is this a scam?"

A client describes a call, text, or email in the app. `POST /scam-check` sends Juno the description plus only the client's first name, age, and advisor's name (to catch someone impersonating the advisor). Juno returns a verdict, the scam pattern, a reply, and next steps. The handler saves the check to the account's `contactLog` in DynamoDB, one entry per conversation, so it shows up in the staff views and in the scoring of any later withdrawal. If Claude fails, the client gets fixed safety advice instead of an error.

## What happens on one withdrawal

1. **Client submits** in the app. `POST /withdrawals` loads the account and 90 days of history from DynamoDB.
2. **Saved as HELD first.** The case is written as HELD with a "manual review" placeholder *before* the AI runs, so a timeout can never lose a withdrawal.
3. **Rule signals.** Seven deterministic checks run in Python: new payee, payee added within 24 hours, 90%+ of the balance, client 65 or older, first crypto transfer, outside 7 AM to 9 PM Eastern, and 5x the largest past withdrawal.
4. **Juno scores it.** Claude Opus 5 reads the account summary, history, signals, the client's note, the firm's contact log, and the advisor's CRM notes (all text treated as untrusted evidence). It returns a 0 to 100 score, up to 4 extra signals, a roughly 80-word memo, and `doNotNotify`: contacts who appear to be part of the scam. The memo cites FINRA Rule 2165 for clients 65 and older, the firm's fraud policy for younger clients, and proposed Rule 2166 only as "proposed".
5. **Guardrail on output.** The memo passes through a Bedrock Guardrail that masks SSNs, card, bank account, and routing numbers.
6. **Decision.** A score of 70 or higher, or unknown because the AI failed, means HELD until 10 business days out (5:00 PM ET). Anything lower is RELEASED.
7. **Alerts.** The client, advisor, emergency contact, and fraud team are alerted in the app. Anyone in `doNotNotify` is skipped. For example, the joint-owner nephew in the Harold Brooks scenario is never told.
8. **Everyone weighs in.** The client answers "Did you request this?" and can add an emergency contact. Clients with no advisor take Juno's scam-check chat. Advisors add notes. Each view refreshes every 4 seconds.
9. **Fraud team decides:** release (needs a written reason), extend (10 more business days, once), or escalate. Advisors can never release.
10. **Hold expiry.** Every 15 minutes, EventBridge Scheduler runs `hold_expiry`. Holds past their end date with no decision are **escalated, never released**.

Every step writes a row to the Audit table, and CloudTrail records the underlying AWS calls.

## AWS services

| Service | What it does here | Why this one |
|---|---|---|
| **Amazon Bedrock: Claude Opus 5** (Sonnet 5 fallback) | Risk score and memo, scam-check chat, "Is this a scam?" check, Juno assistant | Strong reasoning on messy human context; data stays in our AWS account |
| **Bedrock Guardrails** (2) | Refuses investment-advice questions to Juno; masks identity and account numbers in all AI output | Compliance enforced by the platform, not only by prompts |
| **AWS Lambda** (10 functions, 2 layers) | Every endpoint, plus scheduled hold expiry. Layers: `ai/` code, `data/` seed files | Pay per request, no servers to run |
| **Amazon API Gateway** | REST front door with CORS | Managed, secure entry point |
| **AWS Amplify Hosting** | Serves the React app over HTTPS at https://main.d1s6iogq4h15rg.amplifyapp.com (manual deploy, `scripts/deploy_frontend.py`) | Managed static hosting, no servers |
| **Amazon DynamoDB** (4 tables) | Accounts, Transactions, Cases (with a `StatusIndex`), Audit | Fast serverless storage; strongly consistent reads for cases |
| **EventBridge Scheduler** | Runs `hold_expiry` every 15 minutes | Exact timing with no server running |
| **AWS KMS** | One customer-managed key, rotation on, encrypts all tables and the CloudTrail logs | Encryption we control |
| **AWS CloudTrail** | Logs every API call and every table read and write, with log file validation, to a KMS-encrypted S3 bucket | Tamper-evident record of who did what |
| **Amazon CloudWatch** | Lambda logs, including guardrail interventions and model fallbacks | Debugging and evidence |
| **AWS IAM** | One least-privilege role: these tables, these models, these guardrails, this key | Nothing more than the app needs |

Not deployed: Cognito logins (built in PR #14; the app uses an `X-Role` header today). Not built (stretch): SNS/SES delivery, Step Functions, a Bedrock Knowledge Base.

## Safety rules, and where each is enforced

| Rule | Enforced in |
|---|---|
| Only the fraud team can release, extend, or escalate | `post_decision.py` checks the role; `case_state.MOVES` lists the allowed moves (409 otherwise) |
| Never alert a suspected scammer | Juno returns `doNotNotify`; `notify.py` skips those contacts; the fraud view shows them as "not alerted: may be involved" |
| Clients confirm only inside the app | Alerts carry no links or reply options |
| A suspect withdrawal never leaves on its own | Saved as HELD before scoring; AI failure means a manual-review hold; expired holds escalate instead of releasing |
| Each role sees only its own fields | `views.py`: clients never see the memo, scores, or notes; advisors never see `doNotNotify` or the audit trail |
| Juno never gives investment advice | Question guardrail refuses before any model call; prompts forbid it |
| Juno never tells a client to move money or share a code | `contact_check.py` and `scam_chat.py` prompts; it only points to the statement number or the advisor |
| Every AI consultation is on the record | Each Juno question writes an `ASSISTANT_QUESTION` audit row |
| Two reviewers can't overwrite each other | Decisions save only if the status is unchanged (`if_status`), else 409 |

## Code map

| Path | What |
|---|---|
| `frontend/` | React app: `views/` (Client, Advisor, Fraud team, `ContactCheck.jsx` for "Is this a scam?"), `components/` (Juno panel, signal groups, client history, alerts, polling, toasts), `mock/` (offline data) |
| `backend/handlers/` | One Lambda per endpoint (including `scam_check.py`), plus `hold_expiry.py` |
| `backend/common/` | `db.py` (DynamoDB), `audit.py`, `case_state.py` (statuses and allowed moves), `views.py` (role filtering), `roles.py`, `http.py` |
| `backend/notify.py` | Who gets alerted |
| `ai/fraud_ai/` | `signals.py`, `score.py`, `scam_chat.py`, `contact_check.py`, `assistant.py`, `bedrock_client.py`, `prompts/memo.txt` |
| `ai/eval/run_eval.py` | Live eval of every demo scenario |
| `infra/template.yaml` | The whole stack |
| `data/` | 10 seed accounts with contact logs and advisor notes, 90 days of transactions, 6 demo scenarios, 4 pre-seeded cases and their audit rows. See [`DATA.md`](DATA.md) |
| `scripts/` | Login, local handler runner, seed loader, scenario measurement |
| `tests/` | 106 tests: contract, handlers, AI, guardrails, hold expiry, time budget, scam check |

More detail: [`PRODUCT.md`](PRODUCT.md) (every screen), [`AI.md`](AI.md) (how Juno works), [`DATA.md`](DATA.md) (seed data), [`api.md`](api.md) (every endpoint), [`OPERATIONS.md`](OPERATIONS.md) (deploy and run the demo).
