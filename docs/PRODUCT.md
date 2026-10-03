# Product Guide: What Second Look Does, Screen by Screen

Second Look protects clients from **authorized-push scams**: the real client logs in and sends their own money, because a scammer talked them into it. Every login and identity check passes, so tools built for account takeover miss it. Second Look adds a short, explained pause, and puts the client, their advisor, and the fraud team on one case.

**Juno** is the AI inside it. In the app it's always "Juno". Under the hood it's Claude Opus 5 on Amazon Bedrock. How Juno works is in [`AI.md`](AI.md), and the AWS design is in [`ARCHITECTURE.md`](ARCHITECTURE.md).

Switch roles with **View as: Client · Advisor · Fraud team** in the top bar. **Reset demo** reloads the seed data ([`DATA.md`](DATA.md)).

## Before any money moves: "Is this a scam?"

Most scams start with a call, a text, or a pop-up, days before the withdrawal. Clients can ask Juno about it first.

**Client view → Is this a scam? Ask Juno**

1. Pick how they were contacted: phone call, text, email, pop-up, social or dating site, in person.
2. Describe what happened, or tap an example ("Bank security" call, Grandson in trouble, Virus pop-up, Advisor voicemail).
3. Juno answers in about 5 seconds with:
   - a verdict: **This looks like a scam** (red), **Be careful with this** (amber), **This looks safe** (green), or one short follow-up question when it can't tell yet
   - the scam pattern, for example "Bank impersonation" or "Grandparent emergency scam"
   - a plain, warm reply written for an older adult. If the scammer is still on the line, Juno says first that it's safe to hang up
   - up to four next steps, and tap-to-ask follow-ups ("What if he calls back?")
4. **Check something else** starts a new conversation.

What makes it more than a chatbot:

- **The firm remembers.** Every check is saved to the client's contact log. The advisor and fraud team see it, tagged "Juno: likely scam", and if the client later tries to withdraw, Juno's risk score reads it. A client who asked about a "bank security" call on Tuesday and wires $180,000 on Wednesday is connected automatically.
- **It spots impersonation of the client's own advisor.** Juno knows the advisor's name, so "Daniel from the firm says wire $40,000 for a guaranteed 20% return" is caught even when the name is right.
- **It never makes things worse.** Juno never tells anyone to move money, never asks for passwords, codes, or account numbers, and never repeats a phone number the scammer gave. It only points to the number on the statement or the client's advisor.
- **It always answers.** If Claude is unavailable, the client still gets fixed safety advice, never an error.

## When a withdrawal comes in

**Client view → Withdraw funds.** The demo account picker loads one of six scenarios. Submitting shows a 4-step progress view ("Verifying the payee", "Checking 90 days of account activity", "Juno is reviewing the request", "Writing the case memo") while scoring runs, about 7 seconds.

Behind it, in order:

1. The case is saved as **HELD first**, so nothing can leave if anything later fails.
2. Seven rule checks run (new payee, payee added in the last 24 hours, 90%+ of the balance, client 65+, first crypto transfer, odd hours, 5x the largest past withdrawal).
3. Juno reads the account, 90 days of history, the rule checks, the client's note, **the firm's contact log, and the advisor's CRM notes**, then returns a 0 to 100 score, extra signals it found, a memo, and any contacts who look involved.
4. A score of 70+ (or a failed score) holds the withdrawal for 2 business days while the fraud team reviews. Anything lower is released.
5. Everyone who should know is alerted in the app, except anyone Juno flagged as possibly involved.

## Client: the held withdrawal

- **"We paused this withdrawal to protect you."** Amount, payee, and hold end date. Nothing has left the account.
- **Did you request this?** Yes or No. "No" tells them it's safe to hang up and that the fraud team will call on the number on file.
- **Common signs of a scam**, five plain warning signs.
- **Add an emergency contact**, who can be called but can't see the balance or move money.
- **Side panel:** their advisor, "We will never ask you to move money to keep it safe", and the FINRA basis for the hold.
- **Clients with no advisor** get a 1-minute scam-check chat instead (**Scam check** tab). Juno asks up to four questions (did someone contact you first, were you told to keep it secret, are you being rushed, were you told to give a false reason) and returns a risk update the fraud team sees.

The client never sees the score, the memo, or anyone's notes.

## Advisor

- **Case picker** across the top: every held case for their clients.
- **Banner:** "Walter Price has a held withdrawal", with **Call client · number on file**.
- **Juno risk summary:** score gauge, rule checks, what Juno found, and Juno's memo.
- **Client panel:** status, hold end, and the client's answer.
- **Notes for the fraud team:** what they learned on the call ("She's buying a house" or "This isn't like her").
- **Client history:** the firm's contact log and the advisor's own CRM notes, newest first. Calls from someone other than the client are tagged **Someone else**, and Juno checks are tagged with their verdict.
- **Ask Juno about this client:** questions about the case, answered only from case data.
- **Release hold** is visible but disabled: only the fraud team can release. Sometimes the advisor is the fraud.

Advisors never see who Juno flagged as possibly involved, or the audit trail.

## Fraud team

- **Impact strip:** dollars protected on hold, withdrawals held, released automatically, and the measured live-test results.
- **Case queue:** held cases first, then by risk score. The demo opens with five: the hero case plus four pre-seeded ones in every state (held, extended, escalated, released).
- **Case header:** client, account, request time, status, and the three decisions:
  - **Release:** requires a written reason, logged
  - **Extend hold:** to 15 business days after the request (Rule 2165's initial limit), once
  - **Escalate:** to investigations and Adult Protective Services. Escalated cases can still be released once investigators clear them
- **Risk score** gauge, **Hold ends** countdown with its FINRA basis, and the **held transaction**.
- **Signals:** rule checks and "Juno found" signals, shown separately so you can tell the rules from the reasoning.
- **Juno case memo,** with the FINRA rules it cites.
- **Client answer, advisor notes, who was alerted** (anyone left out is marked "not alerted: may be involved"), and the trusted contact.
- **What the firm already knew:** the contact log and advisor CRM notes, the same history Juno scored.
- **Ask Juno:** "Why was this held?", "What should I verify before releasing?", "Summarize the evidence for my notes", or anything else. Every question is written to the audit log.
- **Audit timeline:** every action by every role, with time and detail.

## How FINRA rules are cited

| Client | Rule cited | Hold |
|---|---|---|
| 65 or older (or impaired) | **FINRA Rule 2165** (in effect). Allows an initial 15-business-day hold, with extensions | 2-day review hold; extend goes to the 15-day limit |
| Under 65 | **The firm's fraud policy** | 2 business days, 15 if extended |
| Anyone | **Proposed FINRA Rule 2166** (filed with the SEC, Sept 2026, not yet approved) would allow up to 10 business days for any customer | Always called "proposed" |

Rule 2166's filing also lets firms skip notifying a contact who may be involved. That is what Juno's "not alerted: may be involved" does today.

## Safety rules the product never breaks

- Only the fraud team can release, extend, or escalate.
- A suspected scammer is never alerted.
- Clients confirm inside the app only, never by replying to a text or clicking an email link.
- A suspect withdrawal never leaves on its own: it's held before scoring, held if scoring fails, and escalated (never released) when the hold ends with no decision.
- Juno never gives investment advice, never decides a hold, and never tells anyone to move money.
- Every action, and every question to Juno, is on the record.

Where each rule is enforced in code: [`ARCHITECTURE.md`](ARCHITECTURE.md#safety-rules-and-where-each-is-enforced).
