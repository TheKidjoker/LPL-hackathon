# AWS CLI Setup

Everyone uses the **same event AWS account** in **us-east-1** (the only region the event allows).

## 1. Install

Windows (PowerShell):

```powershell
winget install -e --id Amazon.AWSCLI
# Backend person only (runs sam deploy):
winget install -e --id Amazon.SAM-CLI
```

Mac: `brew install awscli aws-sam-cli`

Close and reopen your terminal, then check with `aws --version`.

## 2. Get credentials from Workshop Studio

1. Open the event dashboard: https://catalog.workshops.aws/event/dashboard/en-US
2. In the left sidebar under **AWS account access**, click **Get AWS CLI credentials**.
3. Click the copy icon on the credentials block.

The credentials are temporary. When commands fail with `ExpiredToken`, copy fresh ones and repeat step 3.

## 3. Save them

Windows, from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\aws-login.ps1
```

This saves them to the `lpl-hackathon` profile, makes it your default, clears your clipboard, and prints the account ID.

Mac / bash: paste the "Linux or macOS (bash)" block straight into your terminal. It lasts for that terminal only.

Never paste keys into code, chat, or a commit.

## 4. Verify

```bash
aws sts get-caller-identity
aws bedrock list-foundation-models --by-provider anthropic \
  --query "modelSummaries[].modelId" --output table
```

If the Bedrock call is empty or denied, raise it at the setup session. Everything depends on Claude access.

## 5. Calling Claude

Use the `us.` inference-profile ID, not the bare model ID. `anthropic.claude-sonnet-5` fails with "on-demand throughput isn't supported"; `us.anthropic.claude-sonnet-5` works.

```python
import boto3

bedrock = boto3.Session(profile_name="lpl-hackathon").client("bedrock-runtime", region_name="us-east-1")
resp = bedrock.converse(
    modelId="us.anthropic.claude-sonnet-5",
    messages=[{"role": "user", "content": [{"text": "Reply with exactly: Bedrock OK"}]}],
    inferenceConfig={"maxTokens": 20},
)
print(resp["output"]["message"]["content"][0]["text"])
```

Windows PowerShell 5.1 mangles inline JSON passed to the CLI. Put `--messages` in a file and pass `file://msg.json` instead.
