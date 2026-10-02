# Business Impact

Older Americans reported losing **$7.7 billion** to online fraud in 2025, and losses grew **59%** in one year. Second Look catches the costliest kind, where the client is tricked into sending their own money, before the money leaves. In live tests it held every scam, released every normal withdrawal, and explained each decision in about 11 seconds, for about **3 cents per withdrawal** in AI cost.

## The problem, in numbers

| Figure | Value | Source |
|---|---|---|
| Losses reported by people 60+, 2025 | **$7.748 billion**, up **59%** from 2024 | FBI IC3 2025 Annual Report, Elder Fraud, p. 44 |
| Complaints from people 60+, 2025 | **201,266**, up 37% from 2024 | Same, p. 44 |
| Average loss per 60+ complainant | **$38,500** | Same, p. 44 |
| People 60+ who lost more than $100,000 | **12,444** | Same, p. 44 |
| Largest loss type for 60+ | Investment scams, **$3.52 billion**; tech/customer support **$1.04 billion** | Same, p. 46 |
| Older adults' reported fraud losses, FTC | **$2.4 billion in 2024**, up from about $600 million in 2020, "largely driven by reports of losses over $100,000" | FTC, Protecting Older Consumers 2024–2025 (Dec 2025) |

These are *reported* losses. Most fraud is never reported, so the real cost is higher.

**Why this is LPL's gap:** these are authorized-push scams. The real client logs in from their own device and passes every security check. LPL's Cyber Fraud Guarantee does not cover money the client moves themselves. FINRA's proposed Rule 2166 would let firms pause a suspicious transaction for clients of any age for up to 10 business days, which multiplies the number of holds a firm must triage. AI triage is how that scales.

## Measured results (live API, 3 runs × 6 scenarios)

From [`RESULTS.md`](RESULTS.md), produced by `python scripts/measure_scenarios.py --runs 3 --out docs/RESULTS.md`:

| Measure | Result |
|---|---|
| Scams held | **9 of 9** |
| Normal withdrawals released | **9 of 9 (0 false positives)** |
| Time to decision and memo | **10.9s average**, 13.6s slowest |
| Dollars held in scam scenarios | **$300,000 per run** |
| Joint-owner scammer kept out of the alerts | **3 of 3** |

The scenarios cover an impostor "bank security" call (the $180,000 hero), a relative and joint owner directing a transfer, a romance and customs-fee scam on a client with no advisor, and three normal withdrawals (a house closing to a known title company, a usual monthly transfer, and a small transfer to the client's own account). The data is synthetic.

## Cost per case

Measured token usage on Claude Opus 5, priced at Anthropic's list rates ($5 per million input tokens, $25 per million output). Bedrock on-demand pricing for these models was not yet listed on the AWS pricing page, so treat these as estimates.

| Step | Tokens (measured) | Cost |
|---|---|---|
| Score and memo, every withdrawal | ~3,044 in / ~656 out | **~$0.032** |
| One Juno question (fraud team or advisor) | 5,213 in / 594 out | ~$0.041 |
| One scam-check chat turn (no-advisor clients) | 615 in / 89 out | ~$0.005 |
| Guardrail masking on the memo | about 1 text unit at $0.10 per 1,000 | under $0.001 |
| Lambda, API Gateway, DynamoDB | per request | well under $0.001 |

- **A normal withdrawal** that is released costs about **3 cents**.
- **A held scam case** where the fraud team asks Juno 2 questions costs about **11 to 12 cents**, and with a 4-turn scam check about 13 cents.
- **Against the loss it prevents:** the average reported 60+ loss is $38,500. One prevented average loss pays for more than a million scored withdrawals ($38,500 / $0.032 ≈ 1.2 million).

## What it saves the fraud team

- **Triage in seconds instead of starting from scratch:** each held case arrives with a score, the rule signals, what Juno found, and a memo citing the rule.
- **Juno answers follow-up questions** from the case data ("What should I verify before releasing?") and logs every question to the audit trail.
- **Holds never fall through the cracks:** EventBridge Scheduler escalates any hold that reaches its end date without a decision.

## Sources

- [FBI IC3, 2025 IC3 Annual Report](https://www.ic3.gov/annualreport/reports/2025_ic3report.pdf) (Elder Fraud section, pp. 44 to 48)
- [FTC, "FTC Issues Annual Report to Congress on Agency's Actions to Protect Older Adults" (Dec 2025)](https://www.ftc.gov/news-events/news/press-releases/2025/12/ftc-issues-annual-report-congress-agencys-actions-protect-older-adults)
- [FTC, Protecting Older Consumers 2024–2025 (PDF)](https://www.ftc.gov/system/files/ftc_gov/pdf/P144400-OlderAdultsReportDec2025.pdf)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (Guardrails rates)
- Claude list pricing: Anthropic API pricing, Opus 5 $5 / $25 per million tokens
