"""Create the three demo sign-ins in the Cognito user pool. Safe to re-run.

    python scripts/create_demo_users.py

Users demo-client, demo-advisor, and demo-fraud, each in the matching group. All three share
one password: DEMO_PASSWORD if set, otherwise a new random one printed once below. Never
commit it. Put it in frontend/.env.local (gitignored) as VITE_DEMO_PASSWORD.
"""

import os
import secrets
import string

import boto3

STACK = "fraud-speed-bump"
USERS = {"demo-client": "client", "demo-advisor": "advisor", "demo-fraud": "fraud"}

session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", "lpl-hackathon"), region_name="us-east-1")


def stack_outputs():
    stack = session.client("cloudformation").describe_stacks(StackName=STACK)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack.get("Outputs", [])}


def new_password():
    # Meets the pool policy: 12+ characters with lowercase, uppercase, and a number.
    alphabet = string.ascii_letters + string.digits
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(20))
        if any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw):
            return pw


def main():
    outputs = stack_outputs()
    pool, client_id = outputs["UserPoolId"], outputs["UserPoolClientId"]
    cognito = session.client("cognito-idp")
    password = os.environ.get("DEMO_PASSWORD")
    generated = not password
    password = password or new_password()

    for username, group in USERS.items():
        try:
            cognito.admin_create_user(UserPoolId=pool, Username=username, MessageAction="SUPPRESS")
            print(f"Created {username}")
        except cognito.exceptions.UsernameExistsException:
            print(f"{username} already exists")
        cognito.admin_set_user_password(UserPoolId=pool, Username=username, Password=password, Permanent=True)
        cognito.admin_add_user_to_group(UserPoolId=pool, Username=username, GroupName=group)

    print("\nAdd these to frontend/.env.local (gitignored), then rebuild or restart the dev server:")
    print(f"VITE_COGNITO_CLIENT_ID={client_id}")
    print(f"VITE_DEMO_PASSWORD={password}" if generated else "VITE_DEMO_PASSWORD=<the DEMO_PASSWORD you set>")
    if generated:
        print("\nThis password is shown only once. Store it somewhere safe.")


if __name__ == "__main__":
    main()
