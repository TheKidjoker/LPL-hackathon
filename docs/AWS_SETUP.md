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

Only use these models. Each was tested with a live call on Oct 2.

| Use | Model ID |
|---|---|
| Risk score and memo, scam-check chat (default) | `us.anthropic.claude-opus-5` |
| Backup if Opus 5 is slow or throttled | `us.anthropic.claude-sonnet-5` |
| Cheap model for bulk test runs | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Other fallbacks | `us.anthropic.claude-opus-4-8`, `us.anthropic.claude-opus-4-7`, `us.anthropic.claude-sonnet-4-6`, `us.anthropic.claude-opus-4-6-v1` |

On a 120-word memo, Opus 5 took about 6.7s and Sonnet 5 about 7.2s, so Opus costs no speed here. Keep the model ID in one config value so switching is a one-line change.

Opus 5 reasons before answering. Give it `maxTokens` of a few hundred or more, and read the block that has `text` (the first block is the reasoning).

Don't use these. They show up in `list-foundation-models` but fail:

- Opus 5.5, Fable 5.1, Sonnet 5.5: `AccessDeniedException`. The event's model allowlist blocks them.
- Fable 5: "data retention mode 'default' is not available for this model."

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
