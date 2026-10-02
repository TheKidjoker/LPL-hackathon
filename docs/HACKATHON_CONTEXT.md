# LPL Financial Hackathon: Rules and Context

Pulled from the "Startup pitch category strategy" chat (Lpl Financial Hackathon project on claude.ai)
and the "Fraud Speed Bump: Team Game Plan" doc. All times are Eastern.

## The prompt

Build a **compliant, AI-powered startup** that helps **advisors, investors, or the teams that support them**.

## Timeline

| When | What |
|---|---|
| Fri 12:00 PM | Hacking starts |
| Fri 12:30 to 1:30 PM | AWS account setup support. Confirm Bedrock and Claude access right away. |
| Fri ~2:00 PM | Office-hours signup sheet posts (grab a 15-minute slot) |
| Fri 3:00 PM | Category selection form opens |
| Fri 4 to 5 PM, 8 to 9 PM | AWS office hours |
| Sat 6 to 7 AM | Morning office hours (last-minute bug fixes) |
| **Sat 12:00 PM** | **Hard deadline: deck, code ZIP, submission form** |
| Sat 12:30 to 2:00 PM | 5-minute pitch plus 5-minute Q&A |

Target: build done by about 6 AM Saturday, leaving time for the deck and backup video.

## Required deliverables (missing any one makes the team ineligible)

- [ ] Deck on the **LPL PowerPoint template** (not a custom design)
- [ ] Working prototype
- [ ] ZIP of the code (a GitHub export of this repo works)
- [ ] Project Submission Form

Optional, but do them:

- [ ] Backup demo video, in case the live demo breaks
- [ ] Architecture diagram (easy points with the AWS judge)

## Judging

- Each room has 2 LPL judges and 1 AWS judge. The LPL judges are mostly engineering leaders
  (VPs of software engineering, a principal engineer, an AIOps lead, developer experience).
- Best Use of AWS is considered automatically.
- Planned categories: **Startup We'd Buy Tomorrow** and **Best Technical Execution**.
  Business Impact is the fallback, but it asks for measurable business value, which is hard to prove with synthetic data.
- Winners present to the CIO, the EVP of Wealth Management Technology, and the SVP of AI Product Management.
  Be ready for "how does this fit with Cyan?" Answer: Cyan handles advisor workflows; we handle the fraud and
  protection layer it doesn't cover, and we can plug into it.
- Prize includes priority consideration for LPL early-career roles.

## Our idea: Fraud Speed Bump

An AI "speed bump" that catches scams where a client is tricked into moving their own money. When a risky
withdrawal comes in, the system pauses it, has Claude explain in plain English why it looks like fraud, and
alerts three people at once: the client, their financial advisor, and LPL's fraud team. Each one weighs in,
and the fraud team makes the final call.

**The gap:** LPL has cyber monitoring for hacking and account takeovers, a Cyber Fraud Guarantee that does
not cover money the client moves themselves, a human Senior Investor Protection team, and Cyan (advisor
workflows, not fraud). Nothing covers authorized-push scams with AI.

**Why now:** FINRA's proposed Rule 2166 would let firms pause a suspicious transaction for any client, not
just seniors, for up to 10 business days.

### Build priorities

1. **Core flow first:** flag, then AI memo, then alerts to all three roles, then fraud team decision.
2. Make Claude's work visible: an explainable memo that cites the rule and reasons over account history.
   Scoring that looks like plain if-statements will get noticed by technical judges.
3. Realistic synthetic data: believable account histories and scam scenarios.
4. Stretch: self-directed branch, AI interview, emergency contact nudge.

Planned AWS pieces mentioned so far: Bedrock (Claude), Step Functions workflow, Guardrails, role-based access,
audit trail.

### Pitch (5 minutes)

- 0:30, Margaret's story
- 0:30, the problem and Rule 2166
- 2:30, live demo (one transaction lights up three windows)
- 1:00, architecture and compliance
- 0:30, why LPL should buy it

Expect the question "doesn't LPL already have fraud monitoring?" Answer: probably for hacking; we are built
for scams where the client moves the money, and for the 2166 workflow.
