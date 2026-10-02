"""scam_check_chat: the in-app scam check for clients with no advisor. Owner: Thomas.

Stub: returns a fixed first question. Replace with a Claude call that asks
"Did someone contact you first?" and "Were you told to keep this secret?",
then returns a risk update once it has enough answers.
"""


def scam_check_chat(case, messages):
    """messages: [{"role": "client" | "assistant", "text": str}, ...]

    Return {"reply": str, "riskUpdate": int | None, "done": bool}.
    """
    # TODO(Thomas): real implementation
    return {
        "reply": "Before we continue: did someone contact you first and ask you to move this money?",
        "riskUpdate": None,
        "done": False,
    }
