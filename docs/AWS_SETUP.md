# AWS CLI Setup

Everyone uses the **same AWS account** and the **same region**. Confirm both at the Fri 12:30 PM setup session.
The region below (`us-east-1`) is a placeholder until then.

## 1. Install

Windows (PowerShell):

```powershell
winget install -e --id Amazon.AWSCLI
# Backend person only (runs sam deploy):
winget install -e --id Amazon.SAM-CLI
```

Mac: `brew install awscli aws-sam-cli`

Close and reopen your terminal, then check with `aws --version`.

## 2. Log in

Use whichever option matches what the organizers give you.

**A. SSO / access portal link** (most likely for an event account):

```bash
aws configure sso --profile lpl-hackathon
# SSO start URL: from organizers
# SSO region: from organizers
# Default region: us-east-1 (or whatever the team agrees on)
# Output format: json
```

When the session expires, run `aws sso login --profile lpl-hackathon`.

**B. Access key + secret (+ session token)** pasted from a portal:

```bash
aws configure --profile lpl-hackathon
# If you were also given a session token:
aws configure set aws_session_token <TOKEN> --profile lpl-hackathon
```

Never paste keys into code, chat, or a commit. They live only in `~/.aws/`.

## 3. Use the profile

```powershell
$env:AWS_PROFILE = "lpl-hackathon"   # PowerShell
```
```bash
export AWS_PROFILE=lpl-hackathon     # bash / mac
```

## 4. Verify (do this first thing Friday)

```bash
aws sts get-caller-identity                                  # you're logged in, right account
aws bedrock list-foundation-models --by-provider anthropic \
  --query "modelSummaries[].modelId" --output table          # Claude models are visible
```

If the Bedrock call is empty or denied, raise it at the setup session. Everything depends on Claude access.
