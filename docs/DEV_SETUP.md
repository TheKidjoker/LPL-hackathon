# Dev Setup

Everyone does sections 1 and 2. Then go to your lane's section. Total setup is about 15 minutes.

## 1. Tools

| Tool | Who | Install (Windows) | Check |
|---|---|---|---|
| Git | All | `winget install -e --id Git.Git` | `git --version` |
| Python 3.11 | All | `winget install -e --id Python.Python.3.11` | `python --version` |
| Node 20 or newer | Thomas | `winget install -e --id OpenJS.NodeJS.LTS` | `node --version` |
| AWS CLI | All | See [`AWS_SETUP.md`](AWS_SETUP.md) | `aws --version` |
| SAM CLI | Thomas | `winget install -e --id Amazon.SAM-CLI` | `sam --version` |

Docker is not needed. We test handlers as plain Python (section 2), not with `sam local`.

Lambdas run Python 3.11, so use 3.11 locally too. `sam build` fails if your Python does not match the runtime.

## 2. Repo and tests (all)

```powershell
git clone https://github.com/TheKidjoker/LPL-hackathon.git
cd LPL-hackathon
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest
```

All tests should pass. They call every handler with the sample requests in `events/` and check the shapes in [`api.md`](api.md). Run them before every pull request.

Run one handler and see its output:

```powershell
python scripts/invoke_local.py submit_withdrawal
python scripts/invoke_local.py get_case events/get_case.json
```

Then log in to AWS (see [`AWS_SETUP.md`](AWS_SETUP.md)). Scripts default to the `lpl-hackathon` profile.

## 3. Repo layout

| Path | Owner | What |
|---|---|---|
| `frontend/` | Thomas | React app (Vite, JavaScript). `src/api.js` is every API call |
| `ai/fraud_ai/` | Thomas | `score_withdrawal`, `scam_check_chat`, Bedrock client, prompts. Deployed as a Lambda layer |
| `infra/` | Thomas | SAM template and deploy config |
| `backend/common/http.py`, `roles.py`, `views.py` | Kaylin | Request helpers, role check, what each role sees |
| `backend/handlers/list_cases.py`, `get_case.py`, `backend/notify.py` | Kaylin | Read endpoints and alerts |
| `backend/common/db.py`, `case_state.py`, `audit.py` | Krish | Tables, statuses, audit log |
| `backend/handlers/submit_withdrawal.py`, `post_response.py`, `post_decision.py`, `demo_reset.py` | Krish | Write endpoints |
| `data/`, `scripts/seed_dynamodb.py` | Krish | Seed data and loader |
| `events/` | Owner of the matching handler | Sample requests |
| `tests/` | Everyone | Contract tests. Add tests for your own code |

Every stub runs today and returns the sample data from [`api.md`](api.md). Look for `TODO(<your name>)` and replace the stub body. Keep the function signatures.

Handlers import shared code as `from common.http import ...` and the AI as `from fraud_ai import score_withdrawal`. Both work the same locally and in Lambda.

## 4. Thomas: frontend

```powershell
cd frontend
npm install
npm run dev
```

Opens on http://localhost:5173 with mock data. To use the live API, copy `.env.example` to `.env.local` and set `VITE_API_URL` to the `ApiUrl` from your deploy. The top bar shows "Mock data" or "Live API".

Mock data lives in `src/mock/`. It filters by role the same way the backend does, so a view that works on mocks works on the live API.

## 5. Thomas: AI

`ai/fraud_ai/bedrock_client.py` already works: `converse(prompt)` and `converse_json(prompt)` call Opus 5, retry once, and fall back to Sonnet 5. Tested live on Oct 2 (3.6 seconds for a short JSON answer).

```powershell
$env:PYTHONPATH = "ai"
python -c "from fraud_ai.bedrock_client import converse_json; print(converse_json('Reply with only this JSON: {\"ok\": true}', max_tokens=500))"
```

Next: `signals.py`, then `score.py` with the prompt in `fraud_ai/prompts/memo.txt`.

## 6. Thomas: deploy

```powershell
cd infra
sam build
sam deploy
```

`samconfig.toml` already sets the stack name (`fraud-speed-bump`), region, and `lpl-hackathon` profile. The deploy prints `ApiUrl` and the four table names. Post all five in the team chat.

- Check `sam deploy` works early. If the event account blocks creating IAM roles, tell the team right away.
- Redeploy after every merge that touches `backend/`, `ai/`, or `infra/`.
- Lint without deploying: `pip install cfn-lint`, then `cfn-lint infra/template.yaml`.

## 7. Krish: data and write handlers

- Put `accounts.json` and `transactions.json` in `data/` using the shapes in [`api.md`](api.md).
- Once Thomas deploys, set the table names and run `python scripts/seed_dynamodb.py`.
- To run a handler against the real tables, set the same variables first:

```powershell
$env:ACCOUNTS_TABLE = "<from deploy output>"
$env:TRANSACTIONS_TABLE = "<from deploy output>"
$env:CASES_TABLE = "<from deploy output>"
$env:AUDIT_TABLE = "<from deploy output>"
python scripts/invoke_local.py submit_withdrawal
```

DynamoDB returns numbers as `Decimal`. Convert them in `db.py` so handlers only see `int` and `float`.
