# Saves Workshop Studio temporary credentials to the "lpl-hackathon" AWS profile.
#
# 1. Workshop Studio event dashboard -> "Get AWS CLI credentials" -> click the copy icon (any tab works).
# 2. Run:  .\scripts\aws-login.ps1
#
# The credentials expire. When AWS commands start failing with ExpiredToken, repeat both steps.

$ErrorActionPreference = "Stop"
$ProfileName = "lpl-hackathon"
$Region = "us-east-1"

$clip = Get-Clipboard -Raw
if (-not $clip) { throw "Clipboard is empty. Copy the credentials from Workshop Studio first." }

function Get-Value($name) {
    $m = [regex]::Match($clip, "$name\s*[=\s]\s*[""']?([^""'\s]+)")
    if (-not $m.Success) { throw "Couldn't find $name in the clipboard. Copy the full credentials block." }
    $m.Groups[1].Value
}

$keyId = Get-Value "AWS_ACCESS_KEY_ID"
$secret = Get-Value "AWS_SECRET_ACCESS_KEY"
$token = Get-Value "AWS_SESSION_TOKEN"

aws configure set aws_access_key_id $keyId --profile $ProfileName
aws configure set aws_secret_access_key $secret --profile $ProfileName
aws configure set aws_session_token $token --profile $ProfileName
aws configure set region $Region --profile $ProfileName
aws configure set output json --profile $ProfileName

# Make this profile the default for this terminal and future ones.
$env:AWS_PROFILE = $ProfileName
[Environment]::SetEnvironmentVariable("AWS_PROFILE", $ProfileName, "User")

Set-Clipboard -Value " "
Write-Host "Saved profile '$ProfileName'. Checking access..."
aws sts get-caller-identity --query "Account" --output text
