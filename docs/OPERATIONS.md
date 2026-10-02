# Operations: Deploy, Run, and Demo

Everything runs in the event AWS account (`us-east-1`, profile `lpl-hackathon`). Thomas runs the deploys.

| What | Where |
|---|---|
| App (Amplify) | https://main.d1s6iogq4h15rg.amplifyapp.com |
| API | https://x9ku6sdgu3.execute-api.us-east-1.amazonaws.com/Prod |
| Stack | `fraud-speed-bump` (CloudFormation) |
| Amplify app | `second-look` (`d1s6iogq4h15rg`), branch `main` |

## Credentials

Event credentials expire. When AWS commands fail with `ExpiredToken`, copy fresh credentials from Workshop Studio and run `.\scripts\aws-login.ps1`. Details in [`AWS_SETUP.md`](AWS_SETUP.md).

## Deploy the backend

```powershell
cd infra
& "C:\Program Files\Amazon\AWSSAMCLI\bin\sam.cmd" build
& "C:\Program Files\Amazon\AWSSAMCLI\bin\sam.cmd" deploy
```

`samconfig.toml` sets the stack, region, and profile. Deploy from an up-to-date `main` after each merge. New routes can return `Missing Authentication Token` for a few seconds after a deploy while API Gateway updates.

## Deploy the frontend

```powershell
python scripts/deploy_frontend.py
```

Builds `frontend/` (production builds call the API in `frontend/.env.production`), uploads it to Amplify, waits, and prints the URL. Amplify is a manual deploy, not linked to GitHub, so **merging does not update the site**. Run this after frontend changes.

## Run the app locally

```powershell
cd frontend
npm install
npm run dev
```

http://localhost:5173 uses **mock data** unless `frontend/.env.local` contains:

```
VITE_API_URL=https://x9ku6sdgu3.execute-api.us-east-1.amazonaws.com/Prod
```

The top bar shows "Mock data" or "Live API".

## Before the demo

1. **Reset:** press **Reset demo** in the app (or `POST /demo/reset`). It deletes every case and audit row and reloads the 6 seed accounts.
2. **Warm up:** submit one withdrawal, then reset again. The first Bedrock call after a quiet period is the slowest.
3. **Pick the story** with the client view's demo account picker:
   - **Margaret Ellis**, $180,000 to CoinVault Exchange: the hero impostor scam. Held, score about 95
   - **Harold Brooks**, $95,000 by phone: the nephew and joint owner is the scammer. Held, and the fraud view shows him "not alerted: may be involved"
   - **Dorothy Nguyen**, no advisor: a romance and customs-fee scam. Take the scam-check chat
   - **Marcus Bell**, $600 to his own account: released in seconds, to show there are no false positives
4. Each view refreshes every 4 seconds, so a client's answer shows up on the fraud screen live.

## Show hold expiry

EventBridge Scheduler runs `HoldExpiryFunction` every 15 minutes. To show it without waiting 10 business days, invoke it as if the hold had ended:

```powershell
$fn = aws cloudformation describe-stack-resource --stack-name fraud-speed-bump --logical-resource-id HoldExpiryFunction --profile lpl-hackathon --query "StackResourceDetail.PhysicalResourceId" --output text
aws lambda invoke --function-name $fn --profile lpl-hackathon --cli-binary-format raw-in-base64-out --payload '{"asOf": "2026-10-17T12:00:00Z"}' out.json
```

Every open hold past its end date becomes ESCALATED, with an audit row. It never releases.

## Measure and evaluate

```powershell
python scripts/measure_scenarios.py --runs 3 --out docs/RESULTS.md   # live API, all scenarios
python ai/eval/run_eval.py                                            # scoring only, direct to Bedrock
python -m pytest                                                      # unit and contract tests, no AWS
```

## Logs and troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Missing Authentication Token` | That route doesn't exist (the API root, a typo), or a new route is still propagating after a deploy |
| `ExpiredToken` | Event credentials expired. Run `.\scripts\aws-login.ps1` again |
| Submit takes 20+ seconds | Opus was slow. The client hedges to Sonnet after 12s and gives up at 22s, so it can't time out |
| "Juno is unavailable" | Both models failed or timed out. Try again |
| Case shows score "?" and "manual review" | Scoring failed. The withdrawal is still held for a person to review |

Lambda logs are in CloudWatch under `/aws/lambda/fraud-speed-bump-*`. Guardrail interventions and model fallbacks are logged there. CloudTrail logs every API call and table read and write to the trail bucket (see the stack outputs).
