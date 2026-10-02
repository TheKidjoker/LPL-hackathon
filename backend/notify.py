"""Alerts for a held case. Owner: Kaylin.

Core build: log who would be alerted and return their ids. Stretch: SNS and SES.
Alerts never carry a link or a reply option. They say "open the app".
"""

import logging

logger = logging.getLogger()


def notify_held(case, account):
    """Alert the client, advisor, and fraud team, skipping everyone in risk.doNotNotify.

    Returns the list of contact ids alerted, which the handler stores as case["notified"].
    """
    skip = set((case.get("risk") or {}).get("doNotNotify") or [])
    recipients = ["client", "fraud-team"]
    advisor = (account or {}).get("advisor")
    if advisor and advisor["contactId"] not in skip:
        recipients.append(advisor["contactId"])
    contact = (account or {}).get("emergencyContact")
    if contact and contact["contactId"] not in skip:
        recipients.append(contact["contactId"])
    # Stretch: send for real with SNS and SES
    logger.info("Alerting %s for case %s", recipients, case["caseId"])
    return recipients
