"""Build the frontend and publish it to AWS Amplify Hosting (manual deploy, no GitHub link).

    python scripts/deploy_frontend.py

Creates the Amplify app "second-look" and its "main" branch the first time, then uploads
frontend/dist as a new deployment and waits for it to go live. Production builds call the
API in frontend/.env.production. Prints the site URL.
"""

import io
import os
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
APP_NAME = "second-look"
BRANCH = "main"

session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", "lpl-hackathon"), region_name="us-east-1")
amplify = session.client("amplify")


def build():
    npm = "npm.cmd" if os.name == "nt" else "npm"
    subprocess.run([npm, "run", "build"], cwd=FRONTEND, check=True)
    if not (DIST / "index.html").exists():
        sys.exit("Build produced no dist/index.html")


def zip_dist():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path in DIST.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(DIST).as_posix())
    return buf.getvalue()


def app_id():
    for app in amplify.list_apps(maxResults=50)["apps"]:
        if app["name"] == APP_NAME:
            return app["appId"]
    app = amplify.create_app(name=APP_NAME, platform="WEB", description="Second Look demo frontend")["app"]
    print(f"Created Amplify app {APP_NAME} ({app['appId']})")
    return app["appId"]


def ensure_branch(app):
    branches = [b["branchName"] for b in amplify.list_branches(appId=app)["branches"]]
    if BRANCH not in branches:
        amplify.create_branch(appId=app, branchName=BRANCH, stage="PRODUCTION")
        print(f"Created branch {BRANCH}")


def deploy(app, archive):
    dep = amplify.create_deployment(appId=app, branchName=BRANCH)
    req = urllib.request.Request(dep["zipUploadUrl"], data=archive, method="PUT", headers={"Content-Type": "application/zip"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        if resp.status not in (200, 201):
            sys.exit(f"Upload failed: HTTP {resp.status}")
    amplify.start_deployment(appId=app, branchName=BRANCH, jobId=dep["jobId"])
    while True:
        status = amplify.get_job(appId=app, branchName=BRANCH, jobId=dep["jobId"])["job"]["summary"]["status"]
        if status in ("SUCCEED", "FAILED", "CANCELLED"):
            return status
        time.sleep(3)


def main():
    if "--no-build" not in sys.argv:
        build()
    archive = zip_dist()
    app = app_id()
    ensure_branch(app)
    status = deploy(app, archive)
    url = f"https://{BRANCH}.{app}.amplifyapp.com"
    print(f"Deployment {status}: {url}")
    sys.exit(0 if status == "SUCCEED" else 1)


if __name__ == "__main__":
    main()
